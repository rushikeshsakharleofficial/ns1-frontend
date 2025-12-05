// MongoDB initialization script
// This runs automatically when the container is first created

// Switch to admin database to create application user
db = db.getSiblingDB('admin');

// Create dnsadmin user with readWrite access to dns_manager database
// Note: MONGO_INITDB_ROOT_PASSWORD is automatically available from Docker environment
db.createUser({
    user: 'dnsadmin',
    pwd: process.env.MONGO_INITDB_ROOT_PASSWORD,
    roles: [
        { role: 'readWrite', db: 'dns_manager' },
        { role: 'dbAdmin', db: 'dns_manager' }
    ]
});

print('Created dnsadmin user');

// Switch to dns_manager database
db = db.getSiblingDB('dns_manager');

// Create collections with validation
db.createCollection('users', {
    validator: {
        $jsonSchema: {
            bsonType: 'object',
            required: ['username', 'password_hash', 'role', 'created_at'],
            properties: {
                username: {
                    bsonType: 'string',
                    description: 'Username - must be unique'
                },
                password_hash: {
                    bsonType: 'string',
                    description: 'Bcrypt hashed password'
                },
                role: {
                    enum: ['admin', 'user'],
                    description: 'User role - must be admin or user'
                },
                created_at: {
                    bsonType: 'date',
                    description: 'Account creation timestamp'
                },
                last_login: {
                    bsonType: 'date',
                    description: 'Last successful login timestamp'
                }
            }
        }
    }
});

db.createCollection('event_logs', {
    validator: {
        $jsonSchema: {
            bsonType: 'object',
            required: ['timestamp', 'user', 'action', 'status'],
            properties: {
                timestamp: {
                    bsonType: 'date',
                    description: 'Event timestamp'
                },
                user: {
                    bsonType: 'string',
                    description: 'Username who performed the action'
                },
                action: {
                    enum: ['login', 'logout', 'add_record', 'update_record', 'delete_record', 'reload_zone', 'restart_service'],
                    description: 'Type of action performed'
                },
                zone: {
                    bsonType: 'string',
                    description: 'DNS zone name (optional for some actions)'
                },
                record_type: {
                    bsonType: 'string',
                    description: 'DNS record type (A, AAAA, MX, etc.)'
                },
                details: {
                    bsonType: 'object',
                    description: 'Additional details about the action'
                },
                status: {
                    enum: ['success', 'failure'],
                    description: 'Whether the action succeeded or failed'
                },
                error_message: {
                    bsonType: 'string',
                    description: 'Error message if status is failure'
                }
            }
        }
    }
});

// Create indexes for better query performance
db.users.createIndex({ username: 1 }, { unique: true });
db.event_logs.createIndex({ timestamp: -1 });
db.event_logs.createIndex({ user: 1, timestamp: -1 });
db.event_logs.createIndex({ action: 1, timestamp: -1 });

print('DNS Manager database initialized successfully');
