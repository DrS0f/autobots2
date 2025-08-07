"""
Deduplication Service for Phase 4
Handles cross-session deduplication and re-engagement control
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from enum import Enum

from .database_models import (
    DatabaseManager, 
    InteractionEvent, 
    LatestInteraction, 
    InteractionAction, 
    InteractionStatus,
    get_db_manager
)

logger = logging.getLogger(__name__)

class DeduplicationService:
    """Service to handle deduplication checks and interaction tracking"""
    
    def __init__(self, db_manager: DatabaseManager = None):
        self.db_manager = db_manager or get_db_manager()
        
        # Cache for frequent lookups
        self._cache = {}
        self._cache_ttl = 300  # 5 minutes
        
        # Statistics
        self.stats = {
            "total_checks": 0,
            "dedupe_hits": 0,
            "cache_hits": 0,
            "cache_misses": 0
        }

    async def should_engage(
        self, 
        account_id: str, 
        target_username: str, 
        action: str,
        task_id: str = "",
        device_id: str = ""
    ) -> Tuple[bool, str]:
        """
        Check if we should engage with a user for a specific action
        
        Returns:
            Tuple[bool, str]: (should_engage, reason)
        """
        self.stats["total_checks"] += 1
        
        try:
            # Clean inputs
            target_username = target_username.strip().lower()
            action = action.lower()
            
            # Check cache first
            cache_key = f"{account_id}:{target_username}:{action}"
            if self._is_cached(cache_key):
                self.stats["cache_hits"] += 1
                cached_result = self._cache[cache_key]
                
                # Check if cache entry is still valid
                if time.time() - cached_result["timestamp"] < self._cache_ttl:
                    return cached_result["should_engage"], cached_result["reason"]
                else:
                    # Cache expired, remove it
                    del self._cache[cache_key]
            
            self.stats["cache_misses"] += 1
            
            # Check database for existing interaction
            existing_interaction = await self.db_manager.check_interaction_exists(
                account_id, target_username, action
            )
            
            if existing_interaction:
                # User was already engaged with this action and it's not expired
                self.stats["dedupe_hits"] += 1
                reason = f"dedupe_hit - last {action} on {existing_interaction.last_ts.strftime('%Y-%m-%d %H:%M:%S')}"
                
                # Record dedupe hit event
                await self.record_interaction_event(
                    account_id=account_id,
                    target_username=target_username,
                    action=action,
                    status=InteractionStatus.DEDUPE_HIT.value,
                    reason=reason,
                    task_id=task_id,
                    device_id=device_id
                )
                
                # Cache the negative result
                self._cache[cache_key] = {
                    "should_engage": False,
                    "reason": reason,
                    "timestamp": time.time()
                }
                
                return False, reason
            else:
                # No existing interaction or it expired, can engage
                reason = "allowed - no recent interaction found"
                
                # Cache the positive result (shorter TTL for positive results)
                self._cache[cache_key] = {
                    "should_engage": True,
                    "reason": reason,
                    "timestamp": time.time()
                }
                
                return True, reason
                
        except Exception as e:
            logger.error(f"Error in should_engage check: {e}")
            # On error, default to allowing engagement but log it
            reason = f"error_check_failed - {str(e)}"
            return True, reason

    async def record_successful_interaction(
        self,
        account_id: str,
        target_username: str,
        action: str,
        task_id: str = "",
        device_id: str = "",
        latency_ms: int = 0,
        metadata: Dict = None
    ) -> bool:
        """Record a successful interaction and update deduplication records"""
        try:
            target_username = target_username.strip().lower()
            action = action.lower()
            
            # Record the event
            success = await self.record_interaction_event(
                account_id=account_id,
                target_username=target_username,
                action=action,
                status=InteractionStatus.SUCCESS.value,
                reason="interaction_completed",
                task_id=task_id,
                device_id=device_id,
                latency_ms=latency_ms,
                metadata=metadata
            )
            
            if success:
                # Update latest interaction for deduplication
                latest_interaction = LatestInteraction(
                    account_id=account_id,
                    target_username=target_username,
                    action=action,
                    last_status=InteractionStatus.SUCCESS.value,
                    last_ts=datetime.utcnow()
                )
                
                await self.db_manager.upsert_latest_interaction(latest_interaction)
                
                # Invalidate cache for this user/action combination
                cache_key = f"{account_id}:{target_username}:{action}"
                if cache_key in self._cache:
                    del self._cache[cache_key]
                
                logger.debug(f"Recorded successful {action} for {target_username}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error recording successful interaction: {e}")
            return False

    async def record_failed_interaction(
        self,
        account_id: str,
        target_username: str,
        action: str,
        status: InteractionStatus,
        reason: str,
        task_id: str = "",
        device_id: str = "",
        latency_ms: int = 0,
        metadata: Dict = None
    ) -> bool:
        """Record a failed interaction"""
        try:
            target_username = target_username.strip().lower()
            action = action.lower()
            
            # Record the event
            success = await self.record_interaction_event(
                account_id=account_id,
                target_username=target_username,
                action=action,
                status=status.value,
                reason=reason,
                task_id=task_id,
                device_id=device_id,
                latency_ms=latency_ms,
                metadata=metadata
            )
            
            # For certain failures, we may still want to update deduplication records
            # to avoid retrying immediately
            if status in [InteractionStatus.PRIVATE_ACCOUNT, InteractionStatus.TARGET_UNAVAILABLE]:
                latest_interaction = LatestInteraction(
                    account_id=account_id,
                    target_username=target_username,
                    action=action,
                    last_status=status.value,
                    last_ts=datetime.utcnow()
                )
                
                await self.db_manager.upsert_latest_interaction(latest_interaction)
                
                # Invalidate cache
                cache_key = f"{account_id}:{target_username}:{action}"
                if cache_key in self._cache:
                    del self._cache[cache_key]
            
            logger.debug(f"Recorded failed {action} for {target_username}: {reason}")
            return success
            
        except Exception as e:
            logger.error(f"Error recording failed interaction: {e}")
            return False

    async def record_interaction_event(
        self,
        account_id: str,
        target_username: str,
        action: str,
        status: str,
        reason: str,
        task_id: str = "",
        device_id: str = "",
        latency_ms: int = 0,
        metadata: Dict = None
    ) -> bool:
        """Record an interaction event in the audit log"""
        try:
            event = InteractionEvent(
                platform="instagram",
                account_id=account_id,
                target_username=target_username.strip().lower(),
                action=action.lower(),
                status=status,
                reason=reason,
                task_id=task_id,
                device_id=device_id,
                latency_ms=latency_ms,
                ts=datetime.utcnow(),
                metadata=metadata or {}
            )
            
            return await self.db_manager.record_interaction_event(event)
            
        except Exception as e:
            logger.error(f"Error creating interaction event: {e}")
            return False

    async def get_user_interaction_history(
        self, 
        account_id: str, 
        target_username: str,
        limit: int = 10
    ) -> List[Dict]:
        """Get interaction history for a specific user"""
        try:
            events = await self.db_manager.get_interaction_events(
                account_id=account_id,
                target_username=target_username.strip().lower(),
                limit=limit
            )
            
            return events
            
        except Exception as e:
            logger.error(f"Error getting user interaction history: {e}")
            return []

    async def bulk_check_users(
        self,
        account_id: str,
        users_and_actions: List[Tuple[str, str]],
        task_id: str = ""
    ) -> Dict[Tuple[str, str], Tuple[bool, str]]:
        """
        Bulk check multiple users and actions for engagement eligibility
        
        Args:
            users_and_actions: List of (username, action) tuples
            
        Returns:
            Dict mapping (username, action) -> (should_engage, reason)
        """
        results = {}
        
        try:
            for username, action in users_and_actions:
                should_engage, reason = await self.should_engage(
                    account_id, username, action, task_id
                )
                results[(username, action)] = (should_engage, reason)
            
            logger.debug(f"Bulk checked {len(users_and_actions)} user/action combinations")
            return results
            
        except Exception as e:
            logger.error(f"Error in bulk check: {e}")
            # Return default "allow" for all on error
            for username, action in users_and_actions:
                results[(username, action)] = (True, f"bulk_check_error - {str(e)}")
            return results

    def _is_cached(self, cache_key: str) -> bool:
        """Check if a result is cached and valid"""
        return cache_key in self._cache

    def get_stats(self) -> Dict[str, int]:
        """Get deduplication service statistics"""
        return self.stats.copy()

    def clear_cache(self):
        """Clear the deduplication cache"""
        self._cache.clear()
        logger.info("Deduplication cache cleared")

    async def cleanup_service(self):
        """Cleanup service resources"""
        self.clear_cache()
        if hasattr(self, 'db_manager'):
            await self.db_manager.cleanup_expired_interactions()

# Global service instance
_deduplication_service = None

def get_deduplication_service() -> DeduplicationService:
    """Get global deduplication service instance"""
    global _deduplication_service
    if _deduplication_service is None:
        _deduplication_service = DeduplicationService()
    return _deduplication_service

# Convenience functions for common operations
async def should_engage_user(
    account_id: str, 
    target_username: str, 
    action: str,
    task_id: str = "",
    device_id: str = ""
) -> Tuple[bool, str]:
    """Convenience function to check if we should engage with a user"""
    service = get_deduplication_service()
    return await service.should_engage(account_id, target_username, action, task_id, device_id)

async def record_successful_engagement(
    account_id: str,
    target_username: str,
    action: str,
    task_id: str = "",
    device_id: str = "",
    latency_ms: int = 0,
    metadata: Dict = None
) -> bool:
    """Convenience function to record successful engagement"""
    service = get_deduplication_service()
    return await service.record_successful_interaction(
        account_id, target_username, action, task_id, device_id, latency_ms, metadata
    )

async def record_failed_engagement(
    account_id: str,
    target_username: str,
    action: str,
    status: InteractionStatus,
    reason: str,
    task_id: str = "",
    device_id: str = "",
    latency_ms: int = 0,
    metadata: Dict = None
) -> bool:
    """Convenience function to record failed engagement"""
    service = get_deduplication_service()
    return await service.record_failed_interaction(
        account_id, target_username, action, status, reason, task_id, device_id, latency_ms, metadata
    )