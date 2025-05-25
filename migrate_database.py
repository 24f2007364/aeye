#!/usr/bin/env python3
"""
Database Migration Script for Aeye Promotion System
This script updates the existing database with new promotion tables and columns.
"""

import sqlite3
import os
from datetime import datetime

def migrate_database():
    """Migrate the database to support the new promotion system."""
    db_path = os.path.join('instance', 'aeye.db')
    
    if not os.path.exists(db_path):
        print("Database file not found. Please run init_db.py first.")
        return False
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("Starting database migration...")
    
    try:
        # Check if ad_campaign table exists and has the old structure
        cursor.execute("PRAGMA table_info(ad_campaign)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'advertiser_id' not in columns:
            print("Updating ad_campaign table...")
            
            # Drop the old ad_campaign table if it exists
            cursor.execute("DROP TABLE IF EXISTS ad_campaign")
            
            # Create new ad_campaign table with proper structure
            cursor.execute('''
                CREATE TABLE ad_campaign (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tool_id INTEGER NOT NULL,
                    advertiser_id INTEGER NOT NULL,
                    name VARCHAR(100) NOT NULL,
                    budget DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
                    cost_per_view DECIMAL(5, 2) NOT NULL DEFAULT 0.10,
                    cost_per_click DECIMAL(5, 2) NOT NULL DEFAULT 0.50,
                    duration_days INTEGER NOT NULL DEFAULT 30,
                    target_tags TEXT,
                    impressions INTEGER DEFAULT 0,
                    tool_views INTEGER DEFAULT 0,
                    website_clicks INTEGER DEFAULT 0,
                    total_spend DECIMAL(10, 2) DEFAULT 0.00,
                    is_active BOOLEAN DEFAULT TRUE,
                    is_approved BOOLEAN DEFAULT FALSE,
                    start_date DATETIME,
                    end_date DATETIME,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (tool_id) REFERENCES tool (id),
                    FOREIGN KEY (advertiser_id) REFERENCES user (id)
                )
            ''')
            print("✓ ad_campaign table updated")
        
        # Create promotion_tracking table
        cursor.execute("DROP TABLE IF EXISTS promotion_tracking")
        cursor.execute('''
            CREATE TABLE promotion_tracking (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                campaign_id INTEGER NOT NULL,
                event_type VARCHAR(20) NOT NULL,
                user_ip VARCHAR(45),
                user_agent TEXT,
                cost DECIMAL(5, 2) NOT NULL DEFAULT 0.00,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (campaign_id) REFERENCES ad_campaign (id)
            )
        ''')
        print("✓ promotion_tracking table created")
        
        # Create advertiser_balance table
        cursor.execute("DROP TABLE IF EXISTS advertiser_balance")
        cursor.execute('''
            CREATE TABLE advertiser_balance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER UNIQUE NOT NULL,
                balance DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
                total_spent DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
                last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES user (id)
            )
        ''')
        print("✓ advertiser_balance table created")
        
        # Create payment_transaction table
        cursor.execute("DROP TABLE IF EXISTS payment_transaction")
        cursor.execute('''
            CREATE TABLE payment_transaction (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                amount DECIMAL(10, 2) NOT NULL,
                transaction_type VARCHAR(20) NOT NULL,
                description TEXT,
                payment_method VARCHAR(50),
                transaction_id VARCHAR(100),
                status VARCHAR(20) DEFAULT 'completed',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES user (id)
            )
        ''')
        print("✓ payment_transaction table created")
        
        # Add is_advertiser column to user table if it doesn't exist
        cursor.execute("PRAGMA table_info(user)")
        user_columns = [row[1] for row in cursor.fetchall()]
        
        if 'is_advertiser' not in user_columns:
            cursor.execute("ALTER TABLE user ADD COLUMN is_advertiser BOOLEAN DEFAULT FALSE")
            print("✓ Added is_advertiser column to user table")
        
        # Create some sample advertisers and balances
        print("Creating sample advertisers...")
        
        # Check if we have any users first
        cursor.execute("SELECT COUNT(*) FROM user")
        user_count = cursor.fetchone()[0]
        
        if user_count == 0:
            # Create sample users including advertisers
            sample_users = [
                ('advertiser1@example.com', 'Advertiser One', 'hashed_password_1', True),
                ('advertiser2@example.com', 'Advertiser Two', 'hashed_password_2', True),
                ('user1@example.com', 'Regular User', 'hashed_password_3', False)
            ]
            
            for email, name, password, is_advertiser in sample_users:
                cursor.execute('''
                    INSERT INTO user (email, name, password, is_advertiser, created_at) 
                    VALUES (?, ?, ?, ?, ?)
                ''', (email, name, password, is_advertiser, datetime.now()))
                print(f"✓ Created user: {name}")
        else:
            # Update existing users to be advertisers
            cursor.execute("UPDATE user SET is_advertiser = TRUE WHERE id <= 2")
            print("✓ Updated existing users as advertisers")
        
        # Create advertiser balances
        cursor.execute("SELECT id FROM user WHERE is_advertiser = TRUE")
        advertiser_ids = [row[0] for row in cursor.fetchall()]
        
        for advertiser_id in advertiser_ids:
            cursor.execute('''
                INSERT OR REPLACE INTO advertiser_balance (user_id, balance, total_spent, last_updated)
                VALUES (?, 1000.00, 0.00, ?)
            ''', (advertiser_id, datetime.now()))
            print(f"✓ Created balance for advertiser ID: {advertiser_id}")
        
        # Create sample campaigns if we have tools
        cursor.execute("SELECT COUNT(*) FROM tool")
        tool_count = cursor.fetchone()[0]
        
        if tool_count > 0 and advertiser_ids:
            print("Creating sample campaigns...")
            cursor.execute("SELECT id FROM tool LIMIT 3")
            tool_ids = [row[0] for row in cursor.fetchall()]
            
            sample_campaigns = [
                ('Premium AI Tool Promotion', 100.00, 0.10, 0.50, 30, 'AI,machine learning,automation'),
                ('Featured Analytics Tool', 150.00, 0.15, 0.60, 45, 'analytics,data,business'),
                ('Top Design Assistant', 200.00, 0.12, 0.55, 60, 'design,creative,UI/UX')
            ]
            
            for i, (name, budget, cost_per_view, cost_per_click, duration, tags) in enumerate(sample_campaigns):
                if i < len(tool_ids) and i < len(advertiser_ids):
                    start_date = datetime.now()
                    cursor.execute('''
                        INSERT INTO ad_campaign 
                        (tool_id, advertiser_id, name, budget, cost_per_view, cost_per_click, 
                         duration_days, target_tags, is_active, is_approved, start_date, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, TRUE, TRUE, ?, ?)
                    ''', (tool_ids[i], advertiser_ids[i % len(advertiser_ids)], name, budget, 
                          cost_per_view, cost_per_click, duration, tags, start_date, datetime.now()))
                    print(f"✓ Created campaign: {name}")
        
        conn.commit()
        print("\n🎉 Database migration completed successfully!")
        print("✓ All promotion system tables created")
        print("✓ Sample data initialized")
        print("✓ Ready to run the application")
        
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {str(e)}")
        conn.rollback()
        return False
        
    finally:
        conn.close()

if __name__ == '__main__':
    migrate_database()
