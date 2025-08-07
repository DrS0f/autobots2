#!/usr/bin/env python3
"""
Database initialization script for Instagram automation system
Creates indexes, TTL collections, and seeds initial data
"""

import asyncio
import logging
import os
import sys
from datetime import datetime, timedelta

# Add backend directory to Python path
sys.path.append('/app/backend')

from ios_automation.database_models import get_db_manager, init_database, InteractionEvent, LatestInteraction
from ios_automation.deduplication_service import get_deduplication_service
from motor.motor_asyncio import AsyncIOMotorClient

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def init_collections_and_indexes():
    """Initialize database collections with proper indexes and TTL"""
    logger.info("Initializing database collections and indexes...")
    
    try:
        # Initialize database with indexes
        await init_database()
        logger.info("✅ Database indexes created successfully")
        
        db_manager = get_db_manager()
        
        # Verify collections exist
        collections = await db_manager.db.list_collection_names()
        logger.info(f"📊 Collections available: {collections}")
        
        # Verify indexes
        for collection_name in ['interactions_events', 'interactions_latest', 'settings']:
            if collection_name in collections:
                collection = db_manager.db[collection_name]
                indexes = await collection.index_information()
                logger.info(f"📇 {collection_name} indexes: {list(indexes.keys())}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize database: {e}")
        return False

async def seed_test_data():
    """Seed the database with test data for demonstration"""
    logger.info("Seeding test data...")
    
    try:
        db_manager = get_db_manager()
        
        # Create test interaction events
        test_events = [
            InteractionEvent(
                account_id="device_test_001",
                target_username="test_user_1",
                action="follow",
                status="success",
                reason="automated_test_follow",
                task_id="task_seed_001",
                device_id="device_test_001",
                latency_ms=150,
                ts=datetime.utcnow() - timedelta(hours=2),
                metadata={"test_data": True, "seed_script": True}
            ),
            InteractionEvent(
                account_id="device_test_001",
                target_username="test_user_2",
                action="like",
                status="success",
                reason="automated_test_like",
                task_id="task_seed_002",
                device_id="device_test_001",
                latency_ms=95,
                ts=datetime.utcnow() - timedelta(hours=1),
                metadata={"test_data": True, "seed_script": True}
            ),
            InteractionEvent(
                account_id="device_test_002",
                target_username="test_user_3",
                action="follow",
                status="dedupe_hit",
                reason="already_followed_recently",
                task_id="task_seed_003",
                device_id="device_test_002",
                latency_ms=45,
                ts=datetime.utcnow() - timedelta(minutes=30),
                metadata={"test_data": True, "seed_script": True}
            ),
            InteractionEvent(
                account_id="device_test_001",
                target_username="rate_limited_user",
                action="comment",
                status="rate_limited",
                reason="instagram_action_blocked",
                task_id="task_seed_004",
                device_id="device_test_001",
                latency_ms=2300,
                ts=datetime.utcnow() - timedelta(minutes=15),
                metadata={"test_data": True, "seed_script": True}
            ),
            InteractionEvent(
                account_id="device_test_003",
                target_username="private_user",
                action="follow",
                status="private_account",
                reason="account_is_private",
                task_id="task_seed_005",
                device_id="device_test_003",
                latency_ms=120,
                ts=datetime.utcnow() - timedelta(minutes=5),
                metadata={"test_data": True, "seed_script": True}
            )
        ]
        
        # Insert test events
        events_inserted = 0
        for event in test_events:
            success = await db_manager.record_interaction_event(event)
            if success:
                events_inserted += 1
        
        logger.info(f"✅ Inserted {events_inserted} test interaction events")
        
        # Create corresponding latest interaction records for deduplication
        latest_interactions = [
            LatestInteraction(
                account_id="device_test_001",
                target_username="test_user_1",
                action="follow",
                last_status="success",
                last_ts=datetime.utcnow() - timedelta(hours=2)
            ),
            LatestInteraction(
                account_id="device_test_001",
                target_username="test_user_2",
                action="like",
                last_status="success",
                last_ts=datetime.utcnow() - timedelta(hours=1)
            )
        ]
        
        # Insert latest interaction records
        latest_inserted = 0
        for interaction in latest_interactions:
            success = await db_manager.upsert_latest_interaction(interaction)
            if success:
                latest_inserted += 1
        
        logger.info(f"✅ Inserted {latest_inserted} deduplication records")
        
        # Initialize system settings
        default_settings = {
            "reengagement_days": 30,
            "rate_limit_steps": [60, 120, 300, 600],
            "cooldown_after_consecutive": 3,
            "cooldown_minutes": 45,
            "initialized_at": datetime.utcnow().isoformat(),
            "version": "1.0"
        }
        
        settings_success = await db_manager.update_settings(default_settings)
        if settings_success:
            logger.info("✅ Initialized system settings")
        else:
            logger.warning("⚠️ Failed to initialize system settings")
        
        # Verify data was inserted
        metrics = await db_manager.get_interaction_metrics()
        logger.info(f"📊 Database metrics: {metrics}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to seed test data: {e}")
        return False

async def verify_database_setup():
    """Verify the database setup is working correctly"""
    logger.info("Verifying database setup...")
    
    try:
        db_manager = get_db_manager()
        
        # Test database connectivity
        await db_manager.ensure_indexes()
        
        # Test interaction event retrieval
        events = await db_manager.get_interaction_events(limit=5)
        logger.info(f"✅ Retrieved {len(events)} interaction events")
        
        # Test deduplication service
        dedup_service = get_deduplication_service()
        should_engage, reason = await dedup_service.should_engage(
            "device_test_001", "test_user_1", "follow", "verify_task"
        )
        logger.info(f"✅ Deduplication test: should_engage={should_engage}, reason={reason}")
        
        # Test metrics retrieval
        metrics = await db_manager.get_interaction_metrics()
        logger.info(f"✅ System metrics: {metrics}")
        
        # Test settings retrieval
        settings = await db_manager.get_settings()
        logger.info(f"✅ System settings: {settings}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Database verification failed: {e}")
        return False

async def cleanup_test_data():
    """Remove test data (for clean production deployments)"""
    logger.info("Cleaning up test data...")
    
    try:
        mongo_url = os.environ.get('MONGO_URL')
        if not mongo_url:
            logger.error("MONGO_URL environment variable not set")
            return False
        
        client = AsyncIOMotorClient(mongo_url)
        db = client[os.environ.get('DB_NAME', 'instagram_automation')]
        
        # Remove test interaction events
        result = await db.interactions_events.delete_many({"metadata.test_data": True})
        logger.info(f"🗑️ Removed {result.deleted_count} test interaction events")
        
        # Remove test latest interaction records  
        result = await db.interactions_latest.delete_many({
            "account_id": {"$in": ["device_test_001", "device_test_002", "device_test_003"]}
        })
        logger.info(f"🗑️ Removed {result.deleted_count} test deduplication records")
        
        client.close()
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to cleanup test data: {e}")
        return False

async def main():
    """Main initialization function"""
    logger.info("🚀 Starting database initialization...")
    
    # Check environment variables
    mongo_url = os.environ.get('MONGO_URL')
    db_name = os.environ.get('DB_NAME', 'instagram_automation')
    
    if not mongo_url:
        logger.error("❌ MONGO_URL environment variable not set")
        sys.exit(1)
    
    logger.info(f"📡 Connecting to MongoDB: {mongo_url.split('@')[-1]}...")  # Hide credentials
    logger.info(f"🗄️ Database: {db_name}")
    
    try:
        # Step 1: Initialize collections and indexes
        if not await init_collections_and_indexes():
            logger.error("❌ Failed to initialize database collections")
            sys.exit(1)
        
        # Step 2: Seed test data (only in development)
        if os.environ.get('SEED_TEST_DATA', 'true').lower() == 'true':
            if not await seed_test_data():
                logger.error("❌ Failed to seed test data")
                sys.exit(1)
        else:
            logger.info("⏭️ Skipping test data seeding (SEED_TEST_DATA=false)")
        
        # Step 3: Verify setup
        if not await verify_database_setup():
            logger.error("❌ Database verification failed")
            sys.exit(1)
        
        logger.info("🎉 Database initialization completed successfully!")
        
        # Optional: Clean up test data if requested
        if os.environ.get('CLEANUP_TEST_DATA', 'false').lower() == 'true':
            await cleanup_test_data()
        
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())