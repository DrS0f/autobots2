"""
Human Behavior Modeling Engine
Creates realistic, randomized interactions that mimic human behavior patterns
"""

import random
import asyncio
import math
from typing import Tuple, List
from dataclasses import dataclass
from enum import Enum

class GestureType(Enum):
    TAP = "tap"
    SWIPE = "swipe"
    SCROLL = "scroll"
    PINCH = "pinch"
    LONG_PRESS = "long_press"

@dataclass
class HumanBehaviorProfile:
    """Profile defining human behavior characteristics"""
    
    # Timing patterns (in seconds)
    min_action_delay: float = 1.5
    max_action_delay: float = 4.0
    thinking_delay_min: float = 2.0
    thinking_delay_max: float = 8.0
    
    # Gesture patterns
    swipe_speed_min: int = 500  # ms
    swipe_speed_max: int = 1200  # ms
    tap_duration_min: int = 50  # ms
    tap_duration_max: int = 150  # ms
    
    # Scroll patterns
    scroll_distance_variance: float = 0.3  # 30% variance
    scroll_pause_probability: float = 0.15  # 15% chance to pause mid-scroll
    
    # Error simulation
    miss_tap_probability: float = 0.02  # 2% chance to slightly miss target
    back_navigation_probability: float = 0.05  # 5% chance to go back occasionally
    
    # Session patterns
    session_fatigue_factor: float = 1.2  # Actions get slower over time
    break_probability: float = 0.08  # 8% chance to take a short break

class HumanBehaviorEngine:
    """Engine that generates human-like behavior patterns"""
    
    def __init__(self, profile: HumanBehaviorProfile = None):
        self.profile = profile or HumanBehaviorProfile()
        self.session_start_time = None
        self.action_count = 0
        self.last_action_time = 0
        
        # Behavior pattern tracking
        self.recent_actions = []
        self.session_patterns = {
            'scroll_direction_history': [],
            'interaction_rhythm': [],
            'focus_areas': []
        }

    def start_session(self):
        """Initialize a new human behavior session"""
        self.session_start_time = asyncio.get_event_loop().time()
        self.action_count = 0
        self.recent_actions.clear()
        self.session_patterns = {
            'scroll_direction_history': [],
            'interaction_rhythm': [],
            'focus_areas': []
        }

    async def pre_action_delay(self, action_type: GestureType = None) -> float:
        """Generate realistic delay before an action"""
        base_delay = random.uniform(
            self.profile.min_action_delay,
            self.profile.max_action_delay
        )
        
        # Apply session fatigue
        if self.session_start_time:
            session_duration = asyncio.get_event_loop().time() - self.session_start_time
            fatigue_multiplier = 1 + (session_duration / 300) * (self.profile.session_fatigue_factor - 1)
            base_delay *= fatigue_multiplier
        
        # Add thinking delay for complex actions
        if action_type in [GestureType.SWIPE, GestureType.SCROLL]:
            if random.random() < 0.3:  # 30% chance for thinking delay
                thinking_delay = random.uniform(
                    self.profile.thinking_delay_min,
                    self.profile.thinking_delay_max
                )
                base_delay += thinking_delay
        
        # Simulate random break
        if random.random() < self.profile.break_probability:
            break_duration = random.uniform(3.0, 12.0)
            base_delay += break_duration
            
        await asyncio.sleep(base_delay)
        self.action_count += 1
        self.last_action_time = asyncio.get_event_loop().time()
        
        return base_delay

    def generate_tap_coordinates(self, element_bounds: dict, accuracy: float = 0.95) -> Tuple[int, int]:
        """Generate human-like tap coordinates with natural variance"""
        x = element_bounds.get('x', 0)
        y = element_bounds.get('y', 0)
        width = element_bounds.get('width', 50)
        height = element_bounds.get('height', 50)
        
        # Calculate center point
        center_x = x + width // 2
        center_y = y + height // 2
        
        # Add human-like variance
        if random.random() > accuracy:
            # Intentional "miss" - still within element but off-center
            variance_x = random.uniform(-width * 0.3, width * 0.3)
            variance_y = random.uniform(-height * 0.3, height * 0.3)
        else:
            # Normal variance
            variance_x = random.uniform(-width * 0.1, width * 0.1)
            variance_y = random.uniform(-height * 0.1, height * 0.1)
        
        final_x = int(center_x + variance_x)
        final_y = int(center_y + variance_y)
        
        # Ensure coordinates are within element bounds
        final_x = max(x, min(x + width, final_x))
        final_y = max(y, min(y + height, final_y))
        
        return (final_x, final_y)

    def generate_swipe_pattern(self, start_point: Tuple[int, int], 
                             end_point: Tuple[int, int]) -> List[Tuple[int, int, int]]:
        """Generate natural swipe pattern with multiple points"""
        start_x, start_y = start_point
        end_x, end_y = end_point
        
        # Calculate distance and create intermediate points
        distance = math.sqrt((end_x - start_x)**2 + (end_y - start_y)**2)
        num_points = max(3, int(distance / 50))  # One point every ~50 pixels
        
        swipe_points = []
        for i in range(num_points + 1):
            progress = i / num_points
            
            # Use easing function for natural acceleration/deceleration
            eased_progress = self._ease_in_out_cubic(progress)
            
            x = int(start_x + (end_x - start_x) * eased_progress)
            y = int(start_y + (end_y - start_y) * eased_progress)
            
            # Add natural variance to path
            if 0 < i < num_points:  # Don't modify start/end points
                variance_x = random.uniform(-5, 5)
                variance_y = random.uniform(-5, 5)
                x += int(variance_x)
                y += int(variance_y)
            
            # Generate timestamp for this point
            timestamp = int(progress * random.uniform(self.profile.swipe_speed_min, 
                                                    self.profile.swipe_speed_max))
            
            swipe_points.append((x, y, timestamp))
        
        return swipe_points

    def generate_scroll_behavior(self, scroll_distance: int) -> dict:
        """Generate natural scrolling behavior"""
        # Add variance to scroll distance
        variance = scroll_distance * self.profile.scroll_distance_variance
        actual_distance = scroll_distance + random.uniform(-variance, variance)
        
        # Determine scroll pattern
        scroll_pattern = {
            'distance': int(actual_distance),
            'speed': random.uniform(0.5, 2.0),  # Scroll speed multiplier
            'should_pause': random.random() < self.profile.scroll_pause_probability,
            'pause_duration': random.uniform(0.5, 2.0) if random.random() < 0.3 else 0
        }
        
        # Track scroll direction for pattern analysis
        direction = 'down' if actual_distance > 0 else 'up'
        self.session_patterns['scroll_direction_history'].append(direction)
        
        # Limit history to last 10 scrolls
        if len(self.session_patterns['scroll_direction_history']) > 10:
            self.session_patterns['scroll_direction_history'].pop(0)
        
        return scroll_pattern

    def should_simulate_back_navigation(self) -> bool:
        """Determine if user should navigate back (simulate getting lost/curious)"""
        return random.random() < self.profile.back_navigation_probability

    def generate_reading_pause(self, content_length: int = 100) -> float:
        """Generate realistic reading pause based on content length"""
        # Base reading time: ~200-300 words per minute
        base_reading_time = content_length / 250 * 60  # seconds
        
        # Add human variance
        variance = base_reading_time * 0.4
        actual_time = base_reading_time + random.uniform(-variance, variance)
        
        # Minimum and maximum reading times
        return max(0.5, min(8.0, actual_time))

    def generate_like_probability(self, post_context: dict = None) -> float:
        """Generate probability of liking a post based on context"""
        base_probability = 0.15  # 15% base like rate
        
        # Adjust based on session fatigue
        if self.action_count > 50:
            fatigue_factor = max(0.5, 1 - (self.action_count - 50) / 200)
            base_probability *= fatigue_factor
        
        # Add randomness for human unpredictability
        variance = random.uniform(-0.05, 0.1)
        return max(0.02, min(0.8, base_probability + variance))

    def _ease_in_out_cubic(self, t: float) -> float:
        """Cubic easing function for natural movement"""
        return 4 * t * t * t if t < 0.5 else 1 - pow(-2 * t + 2, 3) / 2

    def get_session_stats(self) -> dict:
        """Get current session behavior statistics"""
        current_time = asyncio.get_event_loop().time()
        session_duration = (current_time - self.session_start_time) if self.session_start_time else 0
        
        return {
            'session_duration': session_duration,
            'action_count': self.action_count,
            'actions_per_minute': (self.action_count / (session_duration / 60)) if session_duration > 0 else 0,
            'scroll_pattern': self._analyze_scroll_pattern(),
            'interaction_rhythm': self._analyze_interaction_rhythm()
        }

    def _analyze_scroll_pattern(self) -> dict:
        """Analyze scrolling patterns for realistic behavior"""
        if not self.session_patterns['scroll_direction_history']:
            return {'pattern': 'none'}
        
        recent_scrolls = self.session_patterns['scroll_direction_history'][-5:]
        down_count = recent_scrolls.count('down')
        up_count = recent_scrolls.count('up')
        
        if down_count > up_count * 2:
            pattern = 'exploring_downward'
        elif up_count > down_count * 2:
            pattern = 'reviewing_upward'
        else:
            pattern = 'mixed_exploration'
        
        return {
            'pattern': pattern,
            'down_ratio': down_count / len(recent_scrolls),
            'up_ratio': up_count / len(recent_scrolls)
        }

    def _analyze_interaction_rhythm(self) -> dict:
        """Analyze interaction timing patterns"""
        if len(self.session_patterns['interaction_rhythm']) < 3:
            return {'rhythm': 'establishing'}
        
        recent_intervals = self.session_patterns['interaction_rhythm'][-5:]
        avg_interval = sum(recent_intervals) / len(recent_intervals)
        variance = sum(abs(interval - avg_interval) for interval in recent_intervals) / len(recent_intervals)
        
        if variance < avg_interval * 0.2:
            rhythm = 'consistent'
        elif variance > avg_interval * 0.5:
            rhythm = 'erratic'
        else:
            rhythm = 'natural'
        
        return {
            'rhythm': rhythm,
            'avg_interval': avg_interval,
            'variance': variance
        }