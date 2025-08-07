// MongoDB initialization script
// This script runs when MongoDB container starts for the first time

print('🚀 Starting MongoDB initialization...');

// Switch to the application database
db = db.getSiblingDB(process.env.MONGO_INITDB_DATABASE || 'instagram_automation');

print('📚 Connected to database: ' + db.getName());

// Create application user (if needed)
if (process.env.MONGO_APP_USERNAME && process.env.MONGO_APP_PASSWORD) {
    print('👤 Creating application user...');
    db.createUser({
        user: process.env.MONGO_APP_USERNAME,
        pwd: process.env.MONGO_APP_PASSWORD,
        roles: [
            { role: 'readWrite', db: db.getName() },
            { role: 'dbAdmin', db: db.getName() }
        ]
    });
    print('✅ Application user created successfully');
}

// Create initial collections (they will be created automatically when first document is inserted)
// But we can pre-create them with specific options

print('📦 Pre-creating collections...');

// Interactions events collection (capped collection for performance)
db.createCollection('interactions_events', {
    validator: {
        $jsonSchema: {
            bsonType: 'object',
            required: ['platform', 'account_id', 'target_username', 'action', 'status', 'ts'],
            properties: {
                platform: { bsonType: 'string' },
                account_id: { bsonType: 'string' },
                target_username: { bsonType: 'string' },
                action: { bsonType: 'string', enum: ['follow', 'like', 'comment', 'view'] },
                status: { bsonType: 'string', enum: ['success', 'failed', 'skipped', 'retry', 'dedupe_hit', 'rate_limited', 'private_account', 'target_unavailable'] },
                reason: { bsonType: 'string' },
                task_id: { bsonType: 'string' },
                device_id: { bsonType: 'string' },
                latency_ms: { bsonType: 'int', minimum: 0 },
                ts: { bsonType: 'date' },
                metadata: { bsonType: 'object' }
            }
        }
    }
});

// Interactions latest collection for deduplication
db.createCollection('interactions_latest', {
    validator: {
        $jsonSchema: {
            bsonType: 'object',
            required: ['platform', 'account_id', 'target_username', 'action', 'last_ts'],
            properties: {
                platform: { bsonType: 'string' },
                account_id: { bsonType: 'string' },
                target_username: { bsonType: 'string' },
                action: { bsonType: 'string' },
                last_status: { bsonType: 'string' },
                last_ts: { bsonType: 'date' },
                expires_at: { bsonType: 'date' }
            }
        }
    }
});

// Settings collection
db.createCollection('settings');

print('✅ Collections created successfully');

// Insert initial system metadata
db.system_metadata.insertOne({
    _id: 'initialization',
    initialized_at: new Date(),
    version: '1.0.0',
    environment: process.env.NODE_ENV || 'development',
    initialized_by: 'mongo-init.js'
});

print('📊 System metadata inserted');
print('🎉 MongoDB initialization completed successfully!');

// Display database status
print('📈 Database statistics:');
print('Collections: ' + db.getCollectionNames().length);
print('Database size: ' + (db.stats().dataSize / 1024 / 1024).toFixed(2) + ' MB');