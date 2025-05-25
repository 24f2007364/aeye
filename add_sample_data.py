#!/usr/bin/env python3
"""
Add comprehensive sample data to test the Aeye promotion system
"""

import sqlite3
import json
from datetime import datetime, timedelta

def add_sample_data():
    """Add sample tools, users, and campaigns"""
    conn = sqlite3.connect('instance/aeye.db')
    cursor = conn.cursor()
    
    print("Adding sample data...")
    
    try:
        # Sample AI tools with comprehensive data
        sample_tools = [
            {
                'name': 'ChatGPT',
                'description': 'Advanced conversational AI that can help with writing, coding, analysis, and creative tasks. Features natural language understanding and generation.',
                'website_url': 'https://chat.openai.com',
                'logo_url': 'https://upload.wikimedia.org/wikipedia/commons/0/04/ChatGPT_logo.svg',
                'pricing_model': 'Semi-Free',
                'tags': '["AI", "chatbot", "writing", "coding", "analysis"]',
                'is_featured': True,
                'advertiser_id': 1
            },
            {
                'name': 'Midjourney',
                'description': 'AI art generator that creates stunning images from text descriptions. Perfect for creative professionals and digital artists.',
                'website_url': 'https://midjourney.com',
                'logo_url': 'https://seeklogo.com/images/M/midjourney-logo-CD09A0B9D0-seeklogo.com.png',
                'pricing_model': 'Paid',
                'tags': '["AI", "art", "image generation", "creative", "design"]',
                'is_featured': True,
                'advertiser_id': 2
            },
            {
                'name': 'GitHub Copilot',
                'description': 'AI-powered code completion tool that helps developers write code faster with intelligent suggestions and auto-completion.',
                'website_url': 'https://github.com/features/copilot',
                'logo_url': 'https://github.com/features/copilot/images/logo.png',
                'pricing_model': 'Paid',
                'tags': '["AI", "coding", "development", "programming", "productivity"]',
                'is_featured': False,
                'advertiser_id': 1
            },
            {
                'name': 'Grammarly',
                'description': 'AI writing assistant that helps improve grammar, spelling, clarity, and writing style across all platforms.',
                'website_url': 'https://grammarly.com',
                'logo_url': 'https://static.grammarly.com/assets/files/efe57d016d9efff36da7884c193b646b/grammarly_logo_150x150.png',
                'pricing_model': 'Semi-Free',
                'tags': '["AI", "writing", "grammar", "editing", "productivity"]',
                'is_featured': False,
                'advertiser_id': 2
            },
            {
                'name': 'Notion AI',
                'description': 'Integrated AI assistant within Notion that helps with writing, brainstorming, and organizing your workspace more efficiently.',
                'website_url': 'https://notion.so/product/ai',
                'logo_url': 'https://upload.wikimedia.org/wikipedia/commons/4/45/Notion_app_logo.png',
                'pricing_model': 'Semi-Free',
                'tags': '["AI", "productivity", "writing", "organization", "workspace"]',
                'is_featured': True,
                'advertiser_id': 1
            },
            {
                'name': 'Canva AI',
                'description': 'AI-powered design platform that creates professional graphics, presentations, and social media content in seconds.',
                'website_url': 'https://canva.com/ai',
                'logo_url': 'https://static.canva.com/static/images/canva_logo_small.png',
                'pricing_model': 'Semi-Free',
                'tags': '["AI", "design", "graphics", "social media", "presentations"]',
                'is_featured': False,
                'advertiser_id': 2
            },
            {
                'name': 'Jasper AI',
                'description': 'AI content creation platform for marketing teams. Generate blog posts, ads, emails, and social media content at scale.',
                'website_url': 'https://jasper.ai',
                'logo_url': 'https://assets-global.website-files.com/61a6713b2b2bf5e13005b0c8/61a6713b2b2bf5e13005b18a_jasper-logo.svg',
                'pricing_model': 'Paid',
                'tags': '["AI", "content creation", "marketing", "copywriting", "business"]',
                'is_featured': False,
                'advertiser_id': 1
            },
            {
                'name': 'Loom AI',
                'description': 'AI-enhanced video messaging platform with automatic transcriptions, summaries, and action items from your recordings.',
                'website_url': 'https://loom.com',
                'logo_url': 'https://cdn.loom.com/assets/img/logo.svg',
                'pricing_model': 'Semi-Free',
                'tags': '["AI", "video", "communication", "productivity", "collaboration"]',
                'is_featured': False,
                'advertiser_id': 2
            }
        ]
        
        # Insert sample tools
        for tool in sample_tools:
            cursor.execute('''
                INSERT OR IGNORE INTO tool 
                (name, description, website_url, logo_url, pricing_model, tags, is_featured, advertiser_id, is_approved, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                tool['name'], tool['description'], tool['website_url'], tool['logo_url'],
                tool['pricing_model'], tool['tags'], tool['is_featured'], tool['advertiser_id'],
                True, datetime.now()
            ))
            print(f"✓ Added tool: {tool['name']}")
        
        # Check if we have enough users and balance
        cursor.execute("SELECT COUNT(*) FROM user WHERE is_advertiser = TRUE")
        advertiser_count = cursor.fetchone()[0]
        
        if advertiser_count < 2:
            print("Creating additional advertisers...")
            # Create additional advertisers
            advertisers = [
                ('advertiser1@aeye.com', 'TechCorp Advertiser', 'password123', True),
                ('advertiser2@aeye.com', 'AI Solutions Inc', 'password123', True)
            ]
            
            for email, name, password, is_advertiser in advertisers:
                cursor.execute('''
                    INSERT OR IGNORE INTO user (email, name, password, is_advertiser, created_at) 
                    VALUES (?, ?, ?, ?, ?)
                ''', (email, name, password, is_advertiser, datetime.now()))
                print(f"✓ Created advertiser: {name}")
        
        # Update advertiser balances to ensure they have enough funds
        cursor.execute("SELECT id FROM user WHERE is_advertiser = TRUE")
        advertiser_ids = [row[0] for row in cursor.fetchall()]
        
        for advertiser_id in advertiser_ids:
            cursor.execute('''
                INSERT OR REPLACE INTO advertiser_balance (user_id, balance, total_spent, last_updated)
                VALUES (?, ?, ?, ?)
            ''', (advertiser_id, 1000.00, 0.00, datetime.now()))
            print(f"✓ Set balance for advertiser {advertiser_id}: $1000.00")
        
        # Create enhanced promotion campaigns
        cursor.execute("SELECT id, name, advertiser_id FROM tool WHERE is_approved = TRUE ORDER BY id LIMIT 5")
        tools = cursor.fetchall()
        
        campaign_templates = [
            {
                'name': 'Premium AI Assistant Promotion',
                'budget': 200.00,
                'cost_per_view': 0.15,
                'cost_per_click': 0.75,
                'duration_days': 30,
                'target_tags': '["AI", "assistant", "productivity"]'
            },
            {
                'name': 'Creative AI Tools Campaign',
                'budget': 150.00,
                'cost_per_view': 0.12,
                'cost_per_click': 0.60,
                'duration_days': 45,
                'target_tags': '["AI", "creative", "design", "art"]'
            },
            {
                'name': 'Developer Tools Spotlight',
                'budget': 300.00,
                'cost_per_view': 0.18,
                'cost_per_click': 0.80,
                'duration_days': 60,
                'target_tags': '["AI", "coding", "development", "programming"]'
            },
            {
                'name': 'Business AI Solutions',
                'budget': 250.00,
                'cost_per_view': 0.14,
                'cost_per_click': 0.70,
                'duration_days': 30,
                'target_tags': '["AI", "business", "productivity", "marketing"]'
            },
            {
                'name': 'Content Creation Suite',
                'budget': 180.00,
                'cost_per_view': 0.13,
                'cost_per_click': 0.65,
                'duration_days': 40,
                'target_tags': '["AI", "content", "writing", "marketing"]'
            }
        ]
        
        # Create campaigns for available tools
        for i, (tool_id, tool_name, tool_advertiser_id) in enumerate(tools):
            if i < len(campaign_templates):
                campaign = campaign_templates[i]
                start_date = datetime.now()
                end_date = start_date + timedelta(days=campaign['duration_days'])
                
                cursor.execute('''
                    INSERT OR REPLACE INTO ad_campaign 
                    (tool_id, advertiser_id, name, budget, cost_per_view, cost_per_click, 
                     duration_days, target_tags, is_active, is_approved, start_date, end_date, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    tool_id, tool_advertiser_id, campaign['name'], campaign['budget'],
                    campaign['cost_per_view'], campaign['cost_per_click'], campaign['duration_days'],
                    campaign['target_tags'], True, True, start_date, end_date, datetime.now()
                ))
                print(f"✓ Created campaign: {campaign['name']} for {tool_name}")
        
        # Add some sample reviews
        sample_reviews = [
            (1, 1, 'Free', 5, 'Amazing AI tool! The free tier is very generous and the responses are incredibly helpful.'),
            (1, 1, 'Paid', 5, 'ChatGPT Plus is worth every penny. Faster responses and priority access make a huge difference.'),
            (2, 2, 'Paid', 4, 'Incredible image generation quality. The subscription gives access to more features and faster processing.'),
            (1, 3, 'Paid', 5, 'As a developer, GitHub Copilot has significantly improved my coding speed and quality.'),
            (2, 4, 'Free', 4, 'Great for basic grammar checking. The free version covers most of my needs.'),
            (2, 4, 'Paid', 5, 'Premium features like tone detection and advanced suggestions are game-changers.'),
        ]
        
        for user_id, tool_id, version_type, rating, review_text in sample_reviews:
            cursor.execute('''
                INSERT OR IGNORE INTO review 
                (user_id, tool_id, version_type, rating, review_text, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (user_id, tool_id, version_type, rating, review_text, datetime.now()))
        
        print("✓ Added sample reviews")
        
        # Add some transaction history for advertisers
        sample_transactions = [
            (1, 500.00, 'deposit', 'Initial account funding via QR Code'),
            (2, 750.00, 'deposit', 'Campaign budget top-up via QR Code'),
            (1, 25.50, 'charge', 'Promotion charges for Premium AI Assistant Campaign'),
            (2, 18.75, 'charge', 'Promotion charges for Creative AI Tools Campaign'),
        ]
        
        for user_id, amount, transaction_type, description in sample_transactions:
            cursor.execute('''
                INSERT OR IGNORE INTO payment_transaction 
                (user_id, amount, transaction_type, description, payment_method, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, amount, transaction_type, description, 'QR_CODE', 'completed', datetime.now()))
        
        print("✓ Added sample transactions")
        
        conn.commit()
        print("\n🎉 Sample data added successfully!")
        print("✓ AI tools with detailed information")
        print("✓ Advertiser accounts with funding")
        print("✓ Active promotion campaigns")
        print("✓ Sample reviews and ratings")
        print("✓ Transaction history")
        print("\n📈 Ready to test the complete promotion system!")
        
    except Exception as e:
        print(f"❌ Error adding sample data: {str(e)}")
        conn.rollback()
        
    finally:
        conn.close()

if __name__ == '__main__':
    add_sample_data()
