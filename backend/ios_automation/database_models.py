"""
Database Models for Phase 4: Session Integrity & Persistent Logging
Handles MongoDB collections for user interactions and deduplication
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum
from motor.motor_asyncio import AsyncIOMotorClient
import os

logger = logging.getLogger(__name__)

class InteractionAction(Enum):
    FOLLOW = "follow"
    LIKE = "like"
    COMMENT = "comment"
    VIEW = "view"

class InteractionStatus(Enum):
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"
    RETRY = "retry"
    DEDUPE_HIT = "dedupe_hit"
    RATE_LIMITED = "rate_limited"
    PRIVATE_ACCOUNT = "private_account"
    TARGET_UNAVAILABLE = "target_unavailable"

@dataclass
class InteractionEvent:
    """Immutable audit log entry for all interactions"""
    platform: str = "instagram"
    account_id: str = ""  # Our Instagram account ID
    target_username: str = ""
    action: str = ""  # follow|like|comment|view
    status: str = ""  # success|failed|skipped|retry|dedupe_hit
    reason: str = ""  # Detailed reason/error message
    task_id: str = ""
    device_id: str = ""
    latency_ms: int = 0
    ts: datetime = None  # ISO datetime
    metadata: Dict[str, Any] = None  # Additional context

    def __post_init__(self):
        if self.ts is None:
            self.ts = datetime.utcnow()
        if self.metadata is None:
            self.metadata = {}

@dataclass
class LatestInteraction:
    """Deduplication control record"""
    platform: str = "instagram"
    account_id: str = ""
    target_username: str = ""
    action: str = ""  # follow|like|comment
    last_status: str = ""
    last_ts: datetime = None
    expires_at: datetime = None

    def __post_init__(self):
        if self.last_ts is None:
            self.last_ts = datetime.utcnow()
        if self.expires_at is None:
            # Default 30 days re-engagement window
            reengagement_days = int(os.environ.get('REENGAGEMENT_DAYS_DEFAULT', '30'))
            self.expires_at = datetime.utcnow() + timedelta(days=reengagement_days)

class DatabaseManager:
    """MongoDB database manager for interactions and deduplication"""
    
    def __init__(self, db_client: AsyncIOMotorClient = None):
        if db_client is None:
            mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
            self.client = AsyncIOMotorClient(mongo_url)
            self.db = self.client[os.environ.get('DB_NAME', 'test_database')]
        else:
            self.client = db_client
            self.db = self.client[os.environ.get('DB_NAME', 'test_database')]
        
        # Collections
        self.interactions_events = self.db.interactions_events
        self.interactions_latest = self.db.interactions_latest
        
        # Settings
        self.settings = self.db.settings
        
        self._indexes_created = False

    async def ensure_indexes(self):
        """Create MongoDB indexes for optimal performance"""
        if self._indexes_created:
            return
        
        try:
            # Interactions Events Collection Indexes
            await self.interactions_events.create_index([
                ("account_id", 1),
                ("target_username", 1), 
                ("action", 1),
                ("ts", -1)
            ], name="interactions_compound_idx")
            
            await self.interactions_events.create_index([
                ("task_id", 1)
            ], name="task_id_idx")
            
            await self.interactions_events.create_index([
                ("ts", -1)
            ], name="timestamp_idx")
            
            await self.interactions_events.create_index([
                ("status", 1)
            ], name="status_idx")

            # Interactions Latest Collection Indexes
            await self.interactions_latest.create_index([
                ("account_id", 1),
                ("target_username", 1),
                ("action", 1)
            ], unique=True, name="deduplication_unique_idx")
            
            # TTL index on expires_at (auto-deletion)
            await self.interactions_latest.create_index([
                ("expires_at", 1)
            ], expireAfterSeconds=0, name="ttl_idx")
            
            self._indexes_created = True
            logger.info("Database indexes created successfully")
            
        except Exception as e:
            logger.error(f"Error creating database indexes: {e}")
            raise

    async def record_interaction_event(self, event: InteractionEvent) -> bool:
        """Record an interaction event in the immutable audit log"""
        try:
            # Ensure indexes exist
            await self.ensure_indexes()
            
            # Convert to dict for MongoDB
            event_dict = asdict(event)
            
            # Insert into events collection
            result = await self.interactions_events.insert_one(event_dict)
            
            if result.inserted_id:
                logger.debug(f"Recorded interaction event: {event.action} on {event.target_username}")
                return True
            else:
                logger.error("Failed to insert interaction event")
                return False
                
        except Exception as e:
            logger.error(f"Error recording interaction event: {e}")
            return False

    async def upsert_latest_interaction(self, interaction: LatestInteraction) -> bool:
        """Upsert latest interaction for deduplication control"""
        try:
            # Ensure indexes exist
            await self.ensure_indexes()
            
            # Convert to dict
            interaction_dict = asdict(interaction)
            
            # Upsert using unique compound key
            filter_query = {
                "account_id": interaction.account_id,
                "target_username": interaction.target_username,
                "action": interaction.action
            }
            
            result = await self.interactions_latest.replace_one(
                filter_query, 
                interaction_dict, 
                upsert=True
            )
            
            logger.debug(f"Upserted latest interaction: {interaction.action} on {interaction.target_username}")
            return True
            
        except Exception as e:
            logger.error(f"Error upserting latest interaction: {e}")
            return False

    async def check_interaction_exists(self, account_id: str, target_username: str, action: str) -> Optional[LatestInteraction]:
        """Check if interaction exists and is not expired"""
        try:
            await self.ensure_indexes()
            
            result = await self.interactions_latest.find_one({
                "account_id": account_id,
                "target_username": target_username,
                "action": action
            })
            
            if result:
                # Remove MongoDB _id field before creating dataclass
                result.pop('_id', None)
                
                # Convert back to dataclass
                latest = LatestInteraction(**result)
                
                # Check if expired
                if latest.expires_at and latest.expires_at > datetime.utcnow():
                    return latest
                else:
                    # Expired, can re-engage
                    return None
            
            return None
            
        except Exception as e:
            logger.error(f"Error checking interaction existence: {e}")
            return None

    async def get_interaction_events(
        self, 
        account_id: Optional[str] = None,
        target_username: Optional[str] = None,
        action: Optional[str] = None,
        status: Optional[str] = None,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        limit: int = 100,
        skip: int = 0
    ) -> List[Dict]:
        """Query interaction events with filters and pagination"""
        try:
            await self.ensure_indexes()
            
            # Build filter query
            filter_query = {}
            
            if account_id:
                filter_query["account_id"] = account_id
            if target_username:
                filter_query["target_username"] = target_username
            if action:
                filter_query["action"] = action
            if status:
                filter_query["status"] = status
            
            # Date range filter
            if from_date or to_date:
                date_filter = {}
                if from_date:
                    date_filter["$gte"] = from_date
                if to_date:
                    date_filter["$lte"] = to_date
                filter_query["ts"] = date_filter
            
            # Execute query with pagination
            cursor = self.interactions_events.find(filter_query).sort("ts", -1).skip(skip).limit(limit)
            results = await cursor.to_list(length=limit)
            
            logger.debug(f"Retrieved {len(results)} interaction events")
            return results
            
        except Exception as e:
            logger.error(f"Error querying interaction events: {e}")
            return []

    async def get_interaction_metrics(self, account_id: Optional[str] = None, days: int = 30) -> Dict[str, int]:
        """Get interaction metrics for dashboard"""
        try:
            await self.ensure_indexes()
            
            # Date filter for recent activity
            since_date = datetime.utcnow() - timedelta(days=days)
            
            base_filter = {"ts": {"$gte": since_date}}
            if account_id:
                base_filter["account_id"] = account_id
            
            # Aggregate metrics
            pipeline = [
                {"$match": base_filter},
                {"$group": {
                    "_id": {"action": "$action", "status": "$status"},
                    "count": {"$sum": 1}
                }}
            ]
            
            results = await self.interactions_events.aggregate(pipeline).to_list(None)
            
            # Process results into metrics
            metrics = {
                "total_interactions": 0,
                "successful_follows": 0,
                "successful_likes": 0,
                "successful_comments": 0,
                "dedupe_hits": 0,
                "rate_limit_events": 0,
                "failed_interactions": 0,
                "private_accounts": 0,
                "target_unavailable": 0
            }
            
            for result in results:
                action = result["_id"]["action"]
                status = result["_id"]["status"]
                count = result["count"]
                
                metrics["total_interactions"] += count
                
                if status == "success":
                    if action == "follow":
                        metrics["successful_follows"] += count
                    elif action == "like":
                        metrics["successful_likes"] += count
                    elif action == "comment":
                        metrics["successful_comments"] += count
                elif status == "dedupe_hit":
                    metrics["dedupe_hits"] += count
                elif status == "rate_limited":
                    metrics["rate_limit_events"] += count
                elif status == "failed":
                    metrics["failed_interactions"] += count
                elif status == "private_account":
                    metrics["private_accounts"] += count
                elif status == "target_unavailable":
                    metrics["target_unavailable"] += count
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error getting interaction metrics: {e}")
            return {}

    async def cleanup_expired_interactions(self) -> int:
        """Manually cleanup expired interactions (TTL backup)"""
        try:
            await self.ensure_indexes()
            
            result = await self.interactions_latest.delete_many({
                "expires_at": {"$lt": datetime.utcnow()}
            })
            
            deleted_count = result.deleted_count
            if deleted_count > 0:
                logger.info(f"Cleaned up {deleted_count} expired interactions")
            
            return deleted_count
            
        except Exception as e:
            logger.error(f"Error cleaning up expired interactions: {e}")
            return 0

    async def get_settings(self) -> Dict[str, Any]:
        """Get system settings"""
        try:
            settings = await self.settings.find_one({"_id": "system_settings"})
            if settings:
                # Remove MongoDB _id field
                settings.pop("_id", None)
                return settings
            else:
                # Return default settings
                return self._get_default_settings()
                
        except Exception as e:
            logger.error(f"Error getting settings: {e}")
            return self._get_default_settings()

    async def update_settings(self, settings_update: Dict[str, Any]) -> bool:
        """Update system settings"""
        try:
            result = await self.settings.replace_one(
                {"_id": "system_settings"},
                {"_id": "system_settings", **settings_update},
                upsert=True
            )
            
            logger.info(f"Updated system settings: {settings_update}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating settings: {e}")
            return False

    def _get_default_settings(self) -> Dict[str, Any]:
        """Get default system settings"""
        return {
            "reengagement_days": int(os.environ.get('REENGAGEMENT_DAYS_DEFAULT', '30')),
            "rate_limit_steps": [int(x) for x in os.environ.get('RATE_LIMIT_STEPS', '60,120,300,600').split(',')],
            "cooldown_after_consecutive": int(os.environ.get('COOLDOWN_AFTER_CONSECUTIVE', '3')),
            "cooldown_minutes": int(os.environ.get('COOLDOWN_MINUTES', '45'))
        }

    async def close(self):
        """Close database connection"""
        if hasattr(self, 'client'):
            self.client.close()
            logger.info("Database connection closed")

# Global database manager instance
db_manager = None

def get_db_manager() -> DatabaseManager:
    """Get global database manager instance"""
    global db_manager
    if db_manager is None:
        db_manager = DatabaseManager()
    return db_manager

async def init_database():
    """Initialize database with indexes"""
    manager = get_db_manager()
    await manager.ensure_indexes()
    logger.info("Database initialized successfully")