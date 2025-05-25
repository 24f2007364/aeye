#!/usr/bin/env python3
"""
Add comprehensive test data for Aeye promotion system
"""
import sys
import os
sys.path.append(os.path.dirname(__file__))

from app import app, db, User, Tool, AdCampaign, AdvertiserBalance, PaymentTransaction
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta
import json

def add_test_data():
    with app.app_context():
        print("Adding comprehensive test data...")
        
        # Create test advertiser user
        test_advertiser = User.query.filter_by(email='advertiser@test.com').first()
        if not test_advertiser:
            test_advertiser = User(
                email='advertiser@test.com',
                username='testadvertiser',
                password_hash=generate_password_hash('password123'),
                is_advertiser=True
            )
            db.session.add(test_advertiser)
            db.session.commit()
            print("✓ Created test advertiser user")
        else:
            print("✓ Test advertiser already exists")
        
        # Create test regular user
        test_user = User.query.filter_by(email='user@test.com').first()
        if not test_user:
            test_user = User(
                email='user@test.com',
                username='testuser',
                password_hash=generate_password_hash('password123'),
                is_advertiser=False
            )
            db.session.add(test_user)
            db.session.commit()
            print("✓ Created test regular user")
        else:
            print("✓ Test regular user already exists")
        
        # Add balance to advertiser
        balance_record = AdvertiserBalance.query.filter_by(user_id=test_advertiser.id).first()
        if not balance_record:
            balance_record = AdvertiserBalance(
                user_id=test_advertiser.id,
                balance=500.00,
                total_spent=0.00
            )
            db.session.add(balance_record)
            print("✓ Added $500 balance to advertiser")
        else:
            if balance_record.balance < 100:
                balance_record.balance = 500.00
                print("✓ Topped up advertiser balance to $500")
        
        # Create payment transaction record
        transaction = PaymentTransaction(
            user_id=test_advertiser.id,
            amount=500.00,
            transaction_type='deposit',
            payment_method='QR_CODE',
            transaction_id=f'TEST_TXN_{datetime.now().strftime("%Y%m%d_%H%M%S")}',
            description='Test deposit for campaign testing'
        )
        db.session.add(transaction)
        
        # Create diverse test tools
        test_tools = [
            {
                'name': 'ChatGPT Plus',
                'description': 'Advanced AI assistant for writing, coding, and analysis. Get faster responses and priority access.',
                'website_url': 'https://chat.openai.com/plus',
                'logo_url': 'https://images.unsplash.com/photo-1677442136019-21780ecad995?w=100&h=100&fit=crop&crop=face',
                'pricing_model': 'Subscription',
                'tags': ['AI Assistant', 'Writing', 'Coding', 'Analysis']
            },
            {
                'name': 'Midjourney Pro',
                'description': 'Create stunning AI-generated artwork and images from text descriptions. Professional quality results.',
                'website_url': 'https://midjourney.com/pro',
                'logo_url': 'https://images.unsplash.com/photo-1633356122544-f134324a6cee?w=100&h=100&fit=crop&crop=face',
                'pricing_model': 'Subscription',
                'tags': ['Image Generation', 'Art', 'Design', 'Creative']
            },
            {
                'name': 'Notion AI',
                'description': 'Supercharge your productivity with AI-powered writing assistance and content generation in Notion.',
                'website_url': 'https://notion.so/ai',
                'logo_url': 'https://images.unsplash.com/photo-1611224923853-80b023f02d71?w=100&h=100&fit=crop&crop=face',
                'pricing_model': 'Free + Premium',
                'tags': ['Productivity', 'Writing', 'Organization', 'Notes']
            },
            {
                'name': 'GitHub Copilot',
                'description': 'AI pair programmer that helps you write code faster with whole-line and function suggestions.',
                'website_url': 'https://github.com/features/copilot',
                'logo_url': 'https://images.unsplash.com/photo-1618477247222-acbdb0e159b3?w=100&h=100&fit=crop&crop=face',
                'pricing_model': 'Subscription',
                'tags': ['Coding', 'Programming', 'Developer Tools', 'AI Assistant']
            },
            {
                'name': 'Canva Magic Studio',
                'description': 'Design anything with AI-powered tools. Generate images, remove backgrounds, and create stunning visuals.',
                'website_url': 'https://canva.com/magic-studio',
                'logo_url': 'https://images.unsplash.com/photo-1611095790444-1dfa35c53bd1?w=100&h=100&fit=crop&crop=face',
                'pricing_model': 'Free + Premium',
                'tags': ['Design', 'Graphics', 'Marketing', 'Creative']
            }
        ]
        
        created_tools = []
        for tool_data in test_tools:
            existing_tool = Tool.query.filter_by(name=tool_data['name']).first()
            if not existing_tool:
                tool = Tool(
                    name=tool_data['name'],
                    description=tool_data['description'],
                    website_url=tool_data['website_url'],
                    logo_url=tool_data['logo_url'],
                    pricing_model=tool_data['pricing_model'],
                    tags=json.dumps(tool_data['tags']),
                    advertiser_id=test_advertiser.id,
                    is_approved=True,  # Auto-approve for testing
                    is_featured=False,
                    click_count=0,
                    rating=4.5 + (len(created_tools) * 0.1)  # Vary ratings
                )
                db.session.add(tool)
                created_tools.append(tool)
                print(f"✓ Created tool: {tool_data['name']}")
            else:
                created_tools.append(existing_tool)
                print(f"✓ Tool already exists: {tool_data['name']}")
        
        db.session.commit()
        
        # Create active campaigns for some tools
        campaign_data = [
            {
                'tool_name': 'ChatGPT Plus',
                'name': 'ChatGPT Pro Campaign',
                'budget': 100.00,
                'duration_days': 30
            },
            {
                'tool_name': 'Midjourney Pro',
                'name': 'AI Art Promotion',
                'budget': 75.00,
                'duration_days': 21
            },
            {
                'tool_name': 'GitHub Copilot',
                'name': 'Developer Tools Push',
                'budget': 150.00,
                'duration_days': 45
            }
        ]
        
        for campaign_info in campaign_data:
            tool = next((t for t in created_tools if t.name == campaign_info['tool_name']), None)
            if tool:
                existing_campaign = AdCampaign.query.filter_by(
                    tool_id=tool.id, 
                    name=campaign_info['name']
                ).first()
                
                if not existing_campaign:
                    campaign = AdCampaign(
                        tool_id=tool.id,
                        advertiser_id=test_advertiser.id,
                        name=campaign_info['name'],
                        budget=campaign_info['budget'],
                        cost_per_view=0.10,
                        cost_per_click=0.50,
                        duration_days=campaign_info['duration_days'],
                        target_tags=tool.tags,
                        is_active=True,
                        is_approved=True,  # Auto-approve for testing
                        start_date=datetime.utcnow(),
                        end_date=datetime.utcnow() + timedelta(days=campaign_info['duration_days']),
                        
                        # Add some test metrics
                        impressions=100 + (len(created_tools) * 25),
                        tool_views=20 + (len(created_tools) * 5),
                        website_clicks=5 + len(created_tools),
                        total_spend=10.50 + (len(created_tools) * 2.25)
                    )
                    db.session.add(campaign)
                    print(f"✓ Created campaign: {campaign_info['name']}")
                else:
                    print(f"✓ Campaign already exists: {campaign_info['name']}")
        
        db.session.commit()
        
        print("\n🎉 Test data added successfully!")
        print("\nTest accounts created:")
        print("📧 Advertiser: advertiser@test.com / password123")
        print("📧 Regular User: user@test.com / password123")
        print("\n💰 Advertiser has $500 balance and active campaigns")
        print("🛠️ Multiple AI tools with campaigns ready for testing")
        print("\n🚀 You can now test the complete promotion system!")

if __name__ == '__main__':
    add_test_data()
