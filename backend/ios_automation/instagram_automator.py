"""
Instagram Automation Engine
Handles all Instagram-specific automation tasks with human-like behavior
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
from selenium.webdriver.common.action_chains import ActionChains

from .human_behavior import HumanBehaviorEngine, HumanBehaviorProfile, GestureType
from .device_manager import IOSDevice
from .deduplication_service import should_engage_user, record_successful_engagement, record_failed_engagement, InteractionStatus
from .error_handling import handle_automation_error, is_account_ready, mark_interaction_success

logger = logging.getLogger(__name__)

class InstagramAction(Enum):
    OPEN_APP = "open_app"
    SEARCH_USER = "search_user"
    VIEW_PROFILE = "view_profile"
    LIKE_POST = "like_post"
    FOLLOW_USER = "follow_user"
    SCROLL_FEED = "scroll_feed"
    NAVIGATE_HOME = "navigate_home"
    EXPLORE_POSTS = "explore_posts"

@dataclass
class InstagramTask:
    task_id: str
    device_udid: str
    target_username: str
    actions: List[InstagramAction]
    max_likes: int = 3
    max_follows: int = 1
    session_duration: int = 300  # seconds
    status: str = "pending"
    error_message: Optional[str] = None
    completed_actions: List[str] = None
    started_at: Optional[float] = None
    completed_at: Optional[float] = None

class InstagramAutomator:
    """Main Instagram automation engine"""
    
    def __init__(self, behavior_engine: HumanBehaviorEngine = None, account_id: str = "default_account"):
        self.behavior_engine = behavior_engine or HumanBehaviorEngine()
        self.account_id = account_id  # Account identifier for deduplication
        
        # Instagram UI selectors (iOS XCUITest)
        self.selectors = {
            'search_tab': '//XCUIElementTypeTabBar//XCUIElementTypeButton[@name="Search and Explore"]',
            'search_field': '//XCUIElementTypeSearchField[@name="Search"]',
            'search_result_first': '//XCUIElementTypeTable//XCUIElementTypeCell[1]',
            'follow_button': '//XCUIElementTypeButton[@name="Follow"]',
            'following_button': '//XCUIElementTypeButton[@name="Following"]',
            'home_tab': '//XCUIElementTypeTabBar//XCUIElementTypeButton[@name="Home"]',
            'like_button': '//XCUIElementTypeButton[@name="Like"]',
            'liked_button': '//XCUIElementTypeButton[@name="Unlike"]',
            'post_image': '//XCUIElementTypeImage[@name="Photo"]',
            'profile_posts_grid': '//XCUIElementTypeCollectionView',
            'back_button': '//XCUIElementTypeButton[@name="Back"]',
            'close_button': '//XCUIElementTypeButton[@name="Close"]'
        }
        
        # Performance tracking
        self.action_logs = []
        self.session_stats = {}

    async def execute_task(self, task: InstagramTask, device: IOSDevice) -> dict:
        """Execute a complete Instagram automation task"""
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
        
        self.behavior_engine.start_session()
        driver = device.driver
        
        try:
            logger.info(f"Starting Instagram automation task {task.task_id} on device {device.name}")
            
            # Step 1: Open Instagram app
            await self._execute_action(InstagramAction.OPEN_APP, driver, task)
            
            # Step 2: Wait for app to load and navigate to home
            await self.behavior_engine.pre_action_delay(GestureType.TAP)
            await self._ensure_home_screen(driver)
            
            # Step 3: Navigate to search
            await self._execute_action(InstagramAction.SEARCH_USER, driver, task)
            
            # Step 4: Search for target user
            await self._search_for_user(driver, task.target_username, task)
            
            # Step 5: View profile and explore posts
            await self._execute_action(InstagramAction.VIEW_PROFILE, driver, task)
            
            # Step 6: Scroll through and like posts
            await self._explore_and_interact_with_posts(driver, task)
            
            # Step 7: Follow user if specified
            if InstagramAction.FOLLOW_USER in task.actions:
                await self._execute_action(InstagramAction.FOLLOW_USER, driver, task)
            
            # Step 8: Return to home screen
            await self._execute_action(InstagramAction.NAVIGATE_HOME, driver, task)
            
            task.status = "completed"
            task.completed_at = time.time()
            
            logger.info(f"Successfully completed task {task.task_id}")
            
            return {
                "success": True,
                "task_id": task.task_id,
                "completed_actions": task.completed_actions,
                "duration": task.completed_at - task.started_at,
                "session_stats": self.behavior_engine.get_session_stats()
            }
            
        except Exception as e:
            logger.error(f"Task {task.task_id} failed: {e}")
            task.status = "failed"
            task.error_message = str(e)
            task.completed_at = time.time()
            
            # Try to return to home screen on error
            try:
                await self._safe_navigate_home(driver)
            except:
                pass
            
            return {
                "success": False,
                "task_id": task.task_id,
                "error": str(e),
                "completed_actions": task.completed_actions
            }

    async def _execute_action(self, action: InstagramAction, driver, task: InstagramTask):
        """Execute a single Instagram action with logging"""
        action_start = time.time()
        
        try:
            if action == InstagramAction.OPEN_APP:
                await self._open_instagram_app(driver)
            elif action == InstagramAction.NAVIGATE_HOME:
                await self._navigate_to_home(driver)
            elif action == InstagramAction.SEARCH_USER:
                await self._navigate_to_search(driver)
            elif action == InstagramAction.VIEW_PROFILE:
                await self._view_user_profile(driver)
            elif action == InstagramAction.FOLLOW_USER:
                await self._follow_user(driver)
            
            # Log successful action
            task.completed_actions.append({
                "action": action.value,
                "timestamp": time.time(),
                "duration": time.time() - action_start,
                "success": True
            })
            
            logger.info(f"Completed action: {action.value}")
            
        except Exception as e:
            # Log failed action
            task.completed_actions.append({
                "action": action.value,
                "timestamp": time.time(),
                "duration": time.time() - action_start,
                "success": False,
                "error": str(e)
            })
            raise

    async def _open_instagram_app(self, driver):
        """Open Instagram app and wait for it to load"""
        await self.behavior_engine.pre_action_delay(GestureType.TAP)
        
        try:
            # Launch Instagram app
            driver.activate_app("com.burbn.instagram")
            
            # Wait for app to load (check for main UI elements)
            await asyncio.sleep(random.uniform(3, 6))  # App loading time
            
            # Check if login is required (handle existing session)
            try:
                login_field = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((AppiumBy.XPATH, '//XCUIElementTypeTextField'))
                )
                logger.warning("Instagram login required - user needs to login manually")
                await asyncio.sleep(10)  # Give time for manual login
            except TimeoutException:
                # Already logged in, continue
                pass
                
        except Exception as e:
            logger.error(f"Failed to open Instagram app: {e}")
            raise

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

    async def _navigate_to_search(self, driver):
        """Navigate to search/explore tab"""
        await self.behavior_engine.pre_action_delay(GestureType.TAP)
        
        try:
            search_tab = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((AppiumBy.XPATH, self.selectors['search_tab']))
            )
            search_tab.click()
            
            # Wait for search screen to load
            await asyncio.sleep(random.uniform(2, 4))
            
        except TimeoutException:
            logger.error("Could not find search tab")
            raise

    async def _search_for_user(self, driver, username: str, task: InstagramTask):
        """Search for a specific user"""
        await self.behavior_engine.pre_action_delay(GestureType.TAP)
        
        try:
            # Find and tap search field
            search_field = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((AppiumBy.XPATH, self.selectors['search_field']))
            )
            search_field.click()
            
            await asyncio.sleep(random.uniform(1, 2))
            
            # Clear and type username
            search_field.clear()
            
            # Type with human-like delays between characters
            for char in username:
                search_field.send_keys(char)
                await asyncio.sleep(random.uniform(0.1, 0.3))
            
            # Wait for search results to appear
            await asyncio.sleep(random.uniform(2, 4))
            
            # Tap first search result
            first_result = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((AppiumBy.XPATH, self.selectors['search_result_first']))
            )
            
            await self.behavior_engine.pre_action_delay(GestureType.TAP)
            first_result.click()
            
            # Wait for profile to load
            await asyncio.sleep(random.uniform(3, 5))
            
        except TimeoutException:
            logger.error(f"Could not search for user: {username}")
            raise

    async def _view_user_profile(self, driver):
        """View user profile and simulate reading"""
        # Simulate reading profile info
        reading_time = self.behavior_engine.generate_reading_pause(content_length=150)
        await asyncio.sleep(reading_time)
        
        # Scroll down to see posts grid
        await self._human_scroll(driver, direction="down", distance=300)

    async def _explore_and_interact_with_posts(self, driver, task: InstagramTask):
        """Scroll through posts and like random ones"""
        likes_given = 0
        max_likes = task.max_likes
        
        try:
            # Find posts grid
            posts_grid = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((AppiumBy.XPATH, self.selectors['profile_posts_grid']))
            )
            
            # Get all post elements
            posts = driver.find_elements(AppiumBy.XPATH, '//XCUIElementTypeCollectionView//XCUIElementTypeCell')
            
            if not posts:
                logger.warning("No posts found in profile")
                return
            
            # Randomly select posts to interact with
            posts_to_check = min(len(posts), random.randint(5, 12))
            selected_posts = random.sample(posts, min(posts_to_check, len(posts)))
            
            for i, post in enumerate(selected_posts[:posts_to_check]):
                if likes_given >= max_likes:
                    break
                
                # Scroll to make post visible if needed
                driver.execute_script("mobile: scroll", {"direction": "down"})
                await asyncio.sleep(random.uniform(0.5, 1.5))
                
                # Tap on post to open it
                await self.behavior_engine.pre_action_delay(GestureType.TAP)
                post.click()
                
                # Wait for post to load
                await asyncio.sleep(random.uniform(2, 4))
                
                # Decide whether to like this post
                like_probability = self.behavior_engine.generate_like_probability()
                if random.random() < like_probability:
                    # Generate a simple post identifier (could be enhanced with actual post ID extraction)
                    post_id = f"post_{i+1}"
                    success = await self._like_current_post(driver, task, post_id)
                    if success:
                        likes_given += 1
                
                # View the post for a human-like duration
                viewing_time = self.behavior_engine.generate_reading_pause(content_length=50)
                await asyncio.sleep(viewing_time)
                
                # Go back to profile
                await self._navigate_back(driver)
                await asyncio.sleep(random.uniform(1, 2))
                
                # Random chance to scroll between posts
                if random.random() < 0.4:  # 40% chance
                    scroll_behavior = self.behavior_engine.generate_scroll_behavior(200)
                    await self._human_scroll(driver, direction="down", distance=scroll_behavior['distance'])
            
            logger.info(f"Liked {likes_given} posts out of {posts_to_check} viewed")
            
        except Exception as e:
            logger.error(f"Error exploring posts: {e}")

    async def _like_current_post(self, driver, task: InstagramTask, post_id: str = "unknown") -> bool:
        """Like the currently viewed post (with deduplication)"""
        action_start = time.time()
        
        try:
            # For likes, we use a combination of username and post identifier for deduplication
            target_identifier = f"{task.target_username}_{post_id}"
            
            # Check deduplication 
            should_engage, reason = await should_engage_user(
                account_id=self.account_id,
                target_username=target_identifier,
                action="like",
                task_id=task.task_id,
                device_id=task.device_udid
            )
            
            if not should_engage:
                logger.info(f"Skipping like for {target_identifier}: {reason}")
                return False
            
            # Look for like button (heart icon)
            like_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((AppiumBy.XPATH, self.selectors['like_button']))
            )
            
            # Check if already liked
            if like_button.get_attribute('selected') == 'true':
                logger.info("Post already liked, skipping")
                return False
            
            await self.behavior_engine.pre_action_delay(GestureType.TAP)
            like_button.click()
            
            # Wait for like animation
            await asyncio.sleep(random.uniform(0.5, 1.0))
            
            # Calculate latency
            latency_ms = int((time.time() - action_start) * 1000)
            
            # Record successful like
            await record_successful_engagement(
                account_id=self.account_id,
                target_username=target_identifier,
                action="like",
                task_id=task.task_id,
                device_id=task.device_udid,
                latency_ms=latency_ms,
                metadata={"method": "post_like", "post_id": post_id}
            )
            
            # Mark account interaction as successful
            await mark_interaction_success(self.account_id)
            
            logger.info("Successfully liked post")
            return True
            
        except TimeoutException:
            latency_ms = int((time.time() - action_start) * 1000)
            
            await record_failed_engagement(
                account_id=self.account_id,
                target_username=f"{task.target_username}_{post_id}",
                action="like",
                status=InteractionStatus.FAILED,
                reason="like_button_not_found",
                task_id=task.task_id,
                device_id=task.device_udid,
                latency_ms=latency_ms
            )
            
            logger.warning("Could not find like button")
            return False
        except Exception as e:
            latency_ms = int((time.time() - action_start) * 1000)
            
            # Handle error with advanced error handling
            should_retry, delay, error_reason = await handle_automation_error(
                error_message=str(e),
                account_id=self.account_id,
                device_id=task.device_udid,
                task_id=task.task_id,
                element_context="like_button",
                metadata={"action": "like_post", "target": task.target_username, "post_id": post_id}
            )
            
            await record_failed_engagement(
                account_id=self.account_id,
                target_username=f"{task.target_username}_{post_id}",
                action="like",
                status=InteractionStatus.FAILED,
                reason=error_reason,
                task_id=task.task_id,
                device_id=task.device_udid,
                latency_ms=latency_ms
            )
            
            logger.error(f"Error liking post: {e}")
            return False

    async def _follow_user(self, driver, task: InstagramTask):
        """Follow the current user if not already following (with deduplication)"""
        action_start = time.time()
        
        try:
            # Check deduplication first
            should_engage, reason = await should_engage_user(
                account_id=self.account_id,
                target_username=task.target_username,
                action="follow",
                task_id=task.task_id,
                device_id=task.device_udid
            )
            
            if not should_engage:
                logger.info(f"Skipping follow for {task.target_username}: {reason}")
                return False
            
            # Look for follow button
            follow_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((AppiumBy.XPATH, self.selectors['follow_button']))
            )
            
            await self.behavior_engine.pre_action_delay(GestureType.TAP)
            follow_button.click()
            
            # Wait for follow action to complete
            await asyncio.sleep(random.uniform(1, 2))
            
            # Calculate latency
            latency_ms = int((time.time() - action_start) * 1000)
            
            # Record successful follow
            await record_successful_engagement(
                account_id=self.account_id,
                target_username=task.target_username,
                action="follow",
                task_id=task.task_id,
                device_id=task.device_udid,
                latency_ms=latency_ms,
                metadata={"method": "profile_follow"}
            )
            
            # Mark account interaction as successful (reset error counters)
            await mark_interaction_success(self.account_id)
            
            logger.info("Successfully followed user")
            return True
            
        except TimeoutException:
            # Check if already following
            try:
                following_button = driver.find_element(AppiumBy.XPATH, self.selectors['following_button'])
                logger.info("Already following this user")
                return False
            except NoSuchElementException:
                # Record failed follow
                latency_ms = int((time.time() - action_start) * 1000)
                await record_failed_engagement(
                    account_id=self.account_id,
                    target_username=task.target_username,
                    action="follow",
                    status=InteractionStatus.FAILED,
                    reason="follow_button_not_found",
                    task_id=task.task_id,
                    device_id=task.device_udid,
                    latency_ms=latency_ms
                )
                
                logger.warning("Could not find follow button")
                return False
        except Exception as e:
            # Handle error with advanced error handling
            latency_ms = int((time.time() - action_start) * 1000)
            
            should_retry, delay, error_reason = await handle_automation_error(
                error_message=str(e),
                account_id=self.account_id,
                device_id=task.device_udid,
                task_id=task.task_id,
                element_context="follow_button",
                metadata={"action": "follow_user", "target": task.target_username}
            )
            
            # Record failed follow
            await record_failed_engagement(
                account_id=self.account_id,
                target_username=task.target_username,
                action="follow",
                status=InteractionStatus.FAILED,
                reason=error_reason,
                task_id=task.task_id,
                device_id=task.device_udid,
                latency_ms=latency_ms
            )
            
            logger.error(f"Error following user: {e}")
            if should_retry and delay > 0:
                logger.info(f"Will retry after {delay}s: {error_reason}")
                # Note: Actual retry logic would be handled at task level
                
            return False

    async def _navigate_to_home(self, driver):
        """Navigate back to home screen"""
        await self.behavior_engine.pre_action_delay(GestureType.TAP)
        
        try:
            home_tab = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((AppiumBy.XPATH, self.selectors['home_tab']))
            )
            home_tab.click()
            
            await asyncio.sleep(random.uniform(2, 3))
            
        except TimeoutException:
            logger.error("Could not navigate to home")
            raise

    async def _navigate_back(self, driver):
        """Navigate back using back button or gesture"""
        try:
            # Try to find back button
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
        
        # Use mobile gesture instead of TouchAction
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
        
        # Generate human-like swipe pattern
        swipe_points = self.behavior_engine.generate_swipe_pattern(
            (center_x, int(start_y)), 
            (center_x, int(end_y))
        )
        
        # Use mobile gesture for scrolling instead of TouchAction
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

    async def _safe_navigate_home(self, driver):
        """Safely navigate to home screen with error handling"""
        try:
            await self._navigate_to_home(driver)
        except Exception as e:
            logger.warning(f"Could not safely navigate to home: {e}")
            # Try alternative method - app restart
            try:
                driver.activate_app("com.burbn.instagram")
                await asyncio.sleep(3)
            except Exception:
                pass