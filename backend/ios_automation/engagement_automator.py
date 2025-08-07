"""
Engagement-Based Instagram Automation Engine
Handles crawling users from posts and performing engagement actions (follow, like, comment)
Enhanced with Phase 4: Deduplication and advanced error handling
"""

import asyncio
import logging
import random
import time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from appium.webdriver.common.appiumby import AppiumBy

from .human_behavior import HumanBehaviorEngine, HumanBehaviorProfile, GestureType
from .device_manager import IOSDevice
from .deduplication_service import should_engage_user, record_successful_engagement, record_failed_engagement, InteractionStatus
from .error_handling import handle_automation_error, is_account_ready, mark_interaction_success

logger = logging.getLogger(__name__)

class EngagementAction(Enum):
    CRAWL_USERS = "crawl_users"
    VISIT_PROFILE = "visit_profile"
    FOLLOW_USER = "follow_user"
    LIKE_POST = "like_post"
    COMMENT_POST = "comment_post"
    VALIDATE_PROFILE = "validate_profile"

@dataclass
class EngagementTask:
    task_id: str
    device_udid: str
    target_pages: List[str]  # List of Instagram usernames to crawl from
    comment_list: List[str]  # List of possible comments
    actions: Dict[str, bool]  # {"follow": True, "like": True, "comment": True}
    max_users_per_page: int = 20
    profile_validation: Dict[str, bool] = None  # {"public_only": True, "min_posts": 2}
    skip_rate: float = 0.15  # 15% skip rate for realism
    status: str = "pending"
    error_message: Optional[str] = None
    completed_actions: List[str] = None
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    crawled_users: List[Dict] = None
    engagement_stats: Dict = None

class EngagementAutomator:
    """Main engagement automation engine"""
    
    def __init__(self, behavior_engine: HumanBehaviorEngine = None, account_id: str = "default_account"):
        self.behavior_engine = behavior_engine or HumanBehaviorEngine()
        self.account_id = account_id  # Account identifier for deduplication
        
        # Instagram UI selectors for engagement
        self.selectors = {
            'search_tab': '//XCUIElementTypeTabBar//XCUIElementTypeButton[@name="Search and Explore"]',
            'search_field': '//XCUIElementTypeSearchField[@name="Search"]',
            'search_result_first': '//XCUIElementTypeTable//XCUIElementTypeCell[1]',
            'home_tab': '//XCUIElementTypeTabBar//XCUIElementTypeButton[@name="Home"]',
            'profile_posts_grid': '//XCUIElementTypeCollectionView',
            'post_image': '//XCUIElementTypeImage[@name="Photo"]',
            'post_first': '//XCUIElementTypeCollectionView//XCUIElementTypeCell[1]',
            'like_button': '//XCUIElementTypeButton[@name="Like"]',
            'liked_button': '//XCUIElementTypeButton[@name="Unlike"]',
            'comment_button': '//XCUIElementTypeButton[@name="Comment"]',
            'comment_field': '//XCUIElementTypeTextView[@name="Add a comment..."]',
            'comment_send': '//XCUIElementTypeButton[@name="Post"]',
            'follow_button': '//XCUIElementTypeButton[@name="Follow"]',
            'following_button': '//XCUIElementTypeButton[@name="Following"]',
            'likes_list': '//XCUIElementTypeButton[@name="Likes"]',
            'comments_list': '//XCUIElementTypeButton[@name="View all comments"]',
            'user_avatar': '//XCUIElementTypeImage[@name="User Avatar"]',
            'username_link': '//XCUIElementTypeButton[contains(@name, "@")]',
            'back_button': '//XCUIElementTypeButton[@name="Back"]',
            'close_button': '//XCUIElementTypeButton[@name="Close"]',
            'post_count': '//XCUIElementTypeStaticText[contains(@name, "posts")]',
            'private_account': '//XCUIElementTypeStaticText[@name="This Account is Private"]'
        }
        
        # Performance tracking
        self.action_logs = []
        self.engagement_stats = {}

    async def execute_engagement_task(self, task: EngagementTask, device: IOSDevice) -> dict:
        """Execute a complete engagement automation task"""
        if not device.driver:
            return {"success": False, "error": "Device driver not available"}
        
        # Check if account is available (not in cooldown)
        account_available, availability_reason = await is_account_ready(self.account_id)
        if not account_available:
            logger.warning(f"Account {self.account_id} not available: {availability_reason}")
            return {
                "success": False, 
                "error": f"Account unavailable: {availability_reason}",
                "task_id": task.task_id
            }
        
        task.status = "running"
        task.started_at = time.time()
        task.completed_actions = []
        task.crawled_users = []
        task.engagement_stats = {
            "users_crawled": 0,
            "users_followed": 0,
            "posts_liked": 0,
            "comments_posted": 0,
            "profiles_skipped": 0,
            "errors": 0
        }
        
        self.behavior_engine.start_session()
        driver = device.driver
        
        try:
            logger.info(f"Starting engagement task {task.task_id} on device {device.name}")
            
            # Ensure we're on home screen
            await self._ensure_home_screen(driver)
            
            # Process each target page
            for target_page in task.target_pages:
                logger.info(f"Processing target page: @{target_page}")
                
                # Navigate to target profile
                await self._navigate_to_profile(driver, target_page, task)
                
                # Get latest post and crawl users
                crawled_users = await self._crawl_users_from_latest_post(driver, task)
                task.crawled_users.extend(crawled_users)
                task.engagement_stats["users_crawled"] += len(crawled_users)
                
                # Process each crawled user
                for user_data in crawled_users:
                    if await self._should_skip_user(task.skip_rate):
                        task.engagement_stats["profiles_skipped"] += 1
                        logger.info(f"Skipping user @{user_data['username']} (random skip)")
                        continue
                    
                    try:
                        await self._process_user(driver, user_data, task)
                    except Exception as e:
                        logger.error(f"Error processing user @{user_data['username']}: {e}")
                        task.engagement_stats["errors"] += 1
                        continue
                    
                    # Rate limiting delay between users
                    await self.behavior_engine.pre_action_delay(GestureType.TAP)
                
                # Delay between target pages
                await self.behavior_engine.pre_action_delay(GestureType.SCROLL)
            
            task.status = "completed"
            task.completed_at = time.time()
            
            logger.info(f"Successfully completed engagement task {task.task_id}")
            logger.info(f"Stats: {task.engagement_stats}")
            
            return {
                "success": True,
                "task_id": task.task_id,
                "completed_actions": task.completed_actions,
                "duration": task.completed_at - task.started_at,
                "engagement_stats": task.engagement_stats,
                "crawled_users_count": len(task.crawled_users),
                "session_stats": self.behavior_engine.get_session_stats()
            }
            
        except Exception as e:
            logger.error(f"Engagement task {task.task_id} failed: {e}")
            task.status = "failed"
            task.error_message = str(e)
            task.completed_at = time.time()
            
            return {
                "success": False,
                "task_id": task.task_id,
                "error": str(e),
                "completed_actions": task.completed_actions,
                "engagement_stats": task.engagement_stats
            }

    async def _ensure_home_screen(self, driver):
        """Ensure we're on the Instagram home screen"""
        try:
            home_tab = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((AppiumBy.XPATH, self.selectors['home_tab']))
            )
            
            if not home_tab.get_attribute('selected'):
                await self.behavior_engine.pre_action_delay(GestureType.TAP)
                home_tab.click()
                await asyncio.sleep(2)
                
        except TimeoutException:
            logger.warning("Could not locate home tab")

    async def _navigate_to_profile(self, driver, username: str, task: EngagementTask):
        """Navigate to a specific Instagram profile"""
        await self.behavior_engine.pre_action_delay(GestureType.TAP)
        
        try:
            # Go to search tab
            search_tab = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((AppiumBy.XPATH, self.selectors['search_tab']))
            )
            search_tab.click()
            await asyncio.sleep(random.uniform(2, 4))
            
            # Search for user
            search_field = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((AppiumBy.XPATH, self.selectors['search_field']))
            )
            search_field.click()
            await asyncio.sleep(random.uniform(1, 2))
            
            # Type username with human-like delays
            search_field.clear()
            for char in username:
                search_field.send_keys(char)
                await asyncio.sleep(random.uniform(0.1, 0.3))
            
            await asyncio.sleep(random.uniform(2, 4))
            
            # Click first result
            first_result = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((AppiumBy.XPATH, self.selectors['search_result_first']))
            )
            await self.behavior_engine.pre_action_delay(GestureType.TAP)
            first_result.click()
            
            # Wait for profile to load
            await asyncio.sleep(random.uniform(3, 5))
            
            task.completed_actions.append({
                "action": "navigate_to_profile",
                "username": username,
                "timestamp": time.time(),
                "success": True
            })
            
        except Exception as e:
            logger.error(f"Failed to navigate to profile @{username}: {e}")
            raise

    async def _crawl_users_from_latest_post(self, driver, task: EngagementTask) -> List[Dict]:
        """Crawl users who liked/commented on the latest post"""
        crawled_users = []
        
        try:
            # Find and click on the first (latest) post
            posts_grid = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((AppiumBy.XPATH, self.selectors['profile_posts_grid']))
            )
            
            first_post = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((AppiumBy.XPATH, self.selectors['post_first']))
            )
            
            await self.behavior_engine.pre_action_delay(GestureType.TAP)
            first_post.click()
            await asyncio.sleep(random.uniform(3, 5))
            
            # Crawl users from likes
            likes_users = await self._crawl_users_from_likes(driver, task)
            crawled_users.extend(likes_users)
            
            # Crawl users from comments
            comments_users = await self._crawl_users_from_comments(driver, task)
            crawled_users.extend(comments_users)
            
            # Go back to profile
            await self._navigate_back(driver)
            
            # Limit users per page
            if len(crawled_users) > task.max_users_per_page:
                crawled_users = random.sample(crawled_users, task.max_users_per_page)
            
            logger.info(f"Crawled {len(crawled_users)} users from latest post")
            
            return crawled_users
            
        except Exception as e:
            logger.error(f"Failed to crawl users from post: {e}")
            return []

    async def _crawl_users_from_likes(self, driver, task: EngagementTask) -> List[Dict]:
        """Extract usernames from post likes"""
        users = []
        
        try:
            # Look for likes button/count
            likes_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((AppiumBy.XPATH, self.selectors['likes_list']))
            )
            
            await self.behavior_engine.pre_action_delay(GestureType.TAP)
            likes_button.click()
            await asyncio.sleep(random.uniform(2, 4))
            
            # Scroll and collect usernames from likes list
            for scroll_attempt in range(3):  # Limit scrolling
                try:
                    # Find username elements in likes list
                    username_elements = driver.find_elements(AppiumBy.XPATH, self.selectors['username_link'])
                    
                    for element in username_elements:
                        try:
                            username_text = element.get_attribute('name')
                            if username_text and username_text.startswith('@'):
                                username = username_text[1:]  # Remove @ symbol
                                if username not in [u['username'] for u in users]:
                                    users.append({
                                        'username': username,
                                        'source': 'likes',
                                        'discovered_at': time.time()
                                    })
                        except Exception as e:
                            continue
                    
                    # Scroll down to load more
                    if scroll_attempt < 2:
                        await self._human_scroll(driver, direction="down", distance=300)
                        await asyncio.sleep(random.uniform(1, 2))
                    
                except Exception as e:
                    logger.warning(f"Error collecting usernames from likes: {e}")
                    break
            
            # Go back from likes list
            await self._navigate_back(driver)
            await asyncio.sleep(1)
            
            logger.info(f"Collected {len(users)} users from likes")
            return users
            
        except TimeoutException:
            logger.info("No likes button found or post has no likes")
            return []
        except Exception as e:
            logger.error(f"Error crawling likes: {e}")
            return []

    async def _crawl_users_from_comments(self, driver, task: EngagementTask) -> List[Dict]:
        """Extract usernames from post comments"""
        users = []
        
        try:
            # Look for comments section or comments button
            comments_section = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((AppiumBy.XPATH, self.selectors['comments_list']))
            )
            
            # Scroll through comments and collect usernames
            for scroll_attempt in range(2):  # Limit comment scrolling
                try:
                    # Find username elements in comments
                    comment_usernames = driver.find_elements(AppiumBy.XPATH, self.selectors['username_link'])
                    
                    for element in comment_usernames:
                        try:
                            username_text = element.get_attribute('name')
                            if username_text and username_text.startswith('@'):
                                username = username_text[1:]  # Remove @ symbol
                                if username not in [u['username'] for u in users]:
                                    users.append({
                                        'username': username,
                                        'source': 'comments',
                                        'discovered_at': time.time()
                                    })
                        except Exception as e:
                            continue
                    
                    # Scroll down to load more comments
                    if scroll_attempt < 1:
                        await self._human_scroll(driver, direction="down", distance=200)
                        await asyncio.sleep(random.uniform(1, 2))
                    
                except Exception as e:
                    logger.warning(f"Error collecting usernames from comments: {e}")
                    break
            
            logger.info(f"Collected {len(users)} users from comments")
            return users
            
        except TimeoutException:
            logger.info("No comments found or comments not accessible")
            return []
        except Exception as e:
            logger.error(f"Error crawling comments: {e}")
            return []

    async def _process_user(self, driver, user_data: Dict, task: EngagementTask):
        """Process individual user (visit profile, validate, follow, like, comment)"""
        username = user_data['username']
        logger.info(f"Processing user @{username}")
        
        # Navigate to user's profile
        await self._navigate_to_profile(driver, username, task)
        
        # Validate profile if required
        if task.profile_validation:
            if not await self._validate_profile(driver, username, task):
                logger.info(f"Profile @{username} failed validation, skipping")
                task.engagement_stats["profiles_skipped"] += 1
                return
        
        # Follow user if enabled
        if task.actions.get('follow', False):
            success = await self._follow_user(driver, username, task)
            if success:
                task.engagement_stats["users_followed"] += 1
        
        # Like user's latest post if enabled
        if task.actions.get('like', False):
            success = await self._like_latest_post(driver, username, task)
            if success:
                task.engagement_stats["posts_liked"] += 1
        
        # Comment on user's latest post if enabled
        if task.actions.get('comment', False) and task.comment_list:
            success = await self._comment_on_latest_post(driver, username, task)
            if success:
                task.engagement_stats["comments_posted"] += 1
        
        # Human-like delay before next user
        await self.behavior_engine.pre_action_delay(GestureType.TAP)

    async def _validate_profile(self, driver, username: str, task: EngagementTask) -> bool:
        """Validate profile based on criteria (public, post count, etc.)"""
        try:
            validation = task.profile_validation or {}
            
            # Check if account is private
            if validation.get('public_only', True):
                try:
                    private_indicator = driver.find_element(AppiumBy.XPATH, self.selectors['private_account'])
                    if private_indicator:
                        logger.info(f"Profile @{username} is private, skipping")
                        return False
                except NoSuchElementException:
                    # Not private, continue
                    pass
            
            # Check minimum posts count
            min_posts = validation.get('min_posts', 2)
            if min_posts > 0:
                try:
                    post_count_element = driver.find_element(AppiumBy.XPATH, self.selectors['post_count'])
                    post_count_text = post_count_element.get_attribute('name')
                    # Extract number from text like "123 posts"
                    post_count = int(''.join(filter(str.isdigit, post_count_text)))
                    
                    if post_count < min_posts:
                        logger.info(f"Profile @{username} has {post_count} posts (< {min_posts}), skipping")
                        return False
                except (NoSuchElementException, ValueError):
                    logger.warning(f"Could not determine post count for @{username}")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating profile @{username}: {e}")
            return False

    async def _follow_user(self, driver, username: str, task: EngagementTask) -> bool:
        """Follow the user if not already following (with deduplication)"""
        action_start = time.time()
        
        try:
            # Check deduplication first
            should_engage, reason = await should_engage_user(
                account_id=self.account_id,
                target_username=username,
                action="follow",
                task_id=task.task_id,
                device_id=task.device_udid
            )
            
            if not should_engage:
                logger.info(f"Skipping follow for @{username}: {reason}")
                task.completed_actions.append({
                    "action": "follow_user",
                    "username": username,
                    "timestamp": time.time(),
                    "success": False,
                    "reason": reason
                })
                return False
            
            follow_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((AppiumBy.XPATH, self.selectors['follow_button']))
            )
            
            await self.behavior_engine.pre_action_delay(GestureType.TAP)
            follow_button.click()
            await asyncio.sleep(random.uniform(1, 2))
            
            # Calculate latency
            latency_ms = int((time.time() - action_start) * 1000)
            
            # Record successful follow
            await record_successful_engagement(
                account_id=self.account_id,
                target_username=username,
                action="follow",
                task_id=task.task_id,
                device_id=task.device_udid,
                latency_ms=latency_ms,
                metadata={"method": "engagement_follow", "source": "crawled_user"}
            )
            
            # Mark account interaction as successful
            await mark_interaction_success(self.account_id)
            
            logger.info(f"Successfully followed @{username}")
            
            task.completed_actions.append({
                "action": "follow_user",
                "username": username,
                "timestamp": time.time(),
                "success": True
            })
            
            return True
            
        except TimeoutException:
            # Check if already following
            try:
                following_button = driver.find_element(AppiumBy.XPATH, self.selectors['following_button'])
                logger.info(f"Already following @{username}")
                
                # Record as dedupe hit since we're already following
                latency_ms = int((time.time() - action_start) * 1000)
                await record_failed_engagement(
                    account_id=self.account_id,
                    target_username=username,
                    action="follow",
                    status=InteractionStatus.DEDUPE_HIT,
                    reason="already_following",
                    task_id=task.task_id,
                    device_id=task.device_udid,
                    latency_ms=latency_ms
                )
                
                return False
            except NoSuchElementException:
                latency_ms = int((time.time() - action_start) * 1000)
                await record_failed_engagement(
                    account_id=self.account_id,
                    target_username=username,
                    action="follow",
                    status=InteractionStatus.FAILED,
                    reason="follow_button_not_found",
                    task_id=task.task_id,
                    device_id=task.device_udid,
                    latency_ms=latency_ms
                )
                
                logger.warning(f"Could not find follow button for @{username}")
                return False
        except Exception as e:
            latency_ms = int((time.time() - action_start) * 1000)
            
            # Handle error with advanced error handling
            should_retry, delay, error_reason = await handle_automation_error(
                error_message=str(e),
                account_id=self.account_id,
                device_id=task.device_udid,
                task_id=task.task_id,
                element_context="follow_button",
                metadata={"action": "follow_user", "target": username, "method": "engagement"}
            )
            
            await record_failed_engagement(
                account_id=self.account_id,
                target_username=username,
                action="follow",
                status=InteractionStatus.FAILED,
                reason=error_reason,
                task_id=task.task_id,
                device_id=task.device_udid,
                latency_ms=latency_ms
            )
            
            logger.error(f"Error following @{username}: {e}")
            return False

    async def _like_latest_post(self, driver, username: str, task: EngagementTask) -> bool:
        """Like the user's latest post"""
        try:
            # Find and click first post
            first_post = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((AppiumBy.XPATH, self.selectors['post_first']))
            )
            
            await self.behavior_engine.pre_action_delay(GestureType.TAP)
            first_post.click()
            await asyncio.sleep(random.uniform(2, 3))
            
            # Like the post
            like_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((AppiumBy.XPATH, self.selectors['like_button']))
            )
            
            # Check if already liked
            if like_button.get_attribute('selected') == 'true':
                logger.info(f"Post already liked for @{username}")
                await self._navigate_back(driver)
                return False
            
            await self.behavior_engine.pre_action_delay(GestureType.TAP)
            like_button.click()
            await asyncio.sleep(random.uniform(0.5, 1.0))
            
            # Go back to profile
            await self._navigate_back(driver)
            await asyncio.sleep(1)
            
            logger.info(f"Successfully liked latest post from @{username}")
            
            task.completed_actions.append({
                "action": "like_post",
                "username": username,
                "timestamp": time.time(),
                "success": True
            })
            
            return True
            
        except Exception as e:
            logger.error(f"Error liking post from @{username}: {e}")
            return False

    async def _comment_on_latest_post(self, driver, username: str, task: EngagementTask) -> bool:
        """Comment on the user's latest post"""
        try:
            # Navigate to latest post if not already there
            try:
                first_post = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((AppiumBy.XPATH, self.selectors['post_first']))
                )
                await self.behavior_engine.pre_action_delay(GestureType.TAP)
                first_post.click()
                await asyncio.sleep(random.uniform(2, 3))
            except:
                pass  # Might already be on post view
            
            # Click comment button
            comment_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((AppiumBy.XPATH, self.selectors['comment_button']))
            )
            await self.behavior_engine.pre_action_delay(GestureType.TAP)
            comment_button.click()
            await asyncio.sleep(random.uniform(1, 2))
            
            # Find comment input field
            comment_field = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((AppiumBy.XPATH, self.selectors['comment_field']))
            )
            comment_field.click()
            await asyncio.sleep(random.uniform(1, 2))
            
            # Select random comment from list
            comment_text = random.choice(task.comment_list)
            
            # Type comment with human-like delays
            for char in comment_text:
                comment_field.send_keys(char)
                await asyncio.sleep(random.uniform(0.05, 0.15))
            
            await asyncio.sleep(random.uniform(1, 2))
            
            # Post comment
            post_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((AppiumBy.XPATH, self.selectors['comment_send']))
            )
            await self.behavior_engine.pre_action_delay(GestureType.TAP)
            post_button.click()
            await asyncio.sleep(random.uniform(2, 3))
            
            # Go back to profile
            await self._navigate_back(driver)
            await asyncio.sleep(1)
            
            logger.info(f"Successfully commented '{comment_text}' on @{username}'s post")
            
            task.completed_actions.append({
                "action": "comment_post",
                "username": username,
                "comment": comment_text,
                "timestamp": time.time(),
                "success": True
            })
            
            return True
            
        except Exception as e:
            logger.error(f"Error commenting on @{username}'s post: {e}")
            return False

    async def _should_skip_user(self, skip_rate: float) -> bool:
        """Determine if user should be skipped based on skip rate"""
        return random.random() < skip_rate

    async def _navigate_back(self, driver):
        """Navigate back using back button or gesture"""
        try:
            back_button = driver.find_element(AppiumBy.XPATH, self.selectors['back_button'])
            await self.behavior_engine.pre_action_delay(GestureType.TAP)
            back_button.click()
        except NoSuchElementException:
            # Use swipe gesture to go back
            await self._swipe_back(driver)

    async def _swipe_back(self, driver):
        """Perform swipe gesture to go back"""
        size = driver.get_window_size()
        start_x = 20
        start_y = size['height'] // 2
        end_x = size['width'] // 2
        end_y = size['height'] // 2
        
        # Use mobile gesture for swipe back
        driver.execute_script("mobile: swipe", {
            "startX": start_x,
            "startY": start_y,
            "endX": end_x,
            "endY": end_y,
            "duration": 800
        })
        
        await asyncio.sleep(1)

    async def _human_scroll(self, driver, direction: str = "down", distance: int = 300):
        """Perform human-like scrolling"""
        size = driver.get_window_size()
        
        if direction == "down":
            start_y = size['height'] * 0.7
            end_y = start_y - distance
        else:
            start_y = size['height'] * 0.3
            end_y = start_y + distance
        
        center_x = size['width'] // 2
        
        # Use mobile gesture for scrolling
        driver.execute_script("mobile: swipe", {
            "startX": center_x,
            "startY": int(start_y),
            "endX": center_x,
            "endY": int(end_y),
            "duration": 800
        })
        
        # Random pause after scroll
        scroll_behavior = self.behavior_engine.generate_scroll_behavior(distance)
        if scroll_behavior['should_pause']:
            await asyncio.sleep(scroll_behavior['pause_duration'])