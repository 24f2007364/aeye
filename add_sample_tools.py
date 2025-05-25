#!/usr/bin/env python3
"""
Add Sample Tools to Aeye Database
This script adds sample AI tools to test the promotion system.
"""

import sqlite3
import json
from datetime import datetime

def add_sample_tools():
    """Add sample AI tools to the database"""
    db_path = 'instance/aeye.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("Adding sample AI tools...")
    
    # Sample AI tools data
    sample_tools = [
        {
            'name': 'ChatGPT',
            'description': 'Advanced AI conversational model for natural language processing, content creation, and problem-solving across various domains.',
            'website_url': 'https://chat.openai.com',
            'logo_url': 'https://cdn.openai.com/brand/openai-logo.png',
            'pricing_model': 'Semi-Free',
            'tags': json.dumps(['AI Chat', 'Natural Language', 'Content Creation', 'Programming']),
            'is_featured': True,
            'advertiser_id': 1
        },
        {
            'name': 'Midjourney',
            'description': 'AI-powered image generation tool that creates stunning artwork and designs from text prompts with exceptional quality.',
            'website_url': 'https://midjourney.com',
            'logo_url': 'https://cdn.midjourney.com/brand/midjourney-logo.png',
            'pricing_model': 'Paid',
            'tags': json.dumps(['Image Generation', 'Art', 'Design', 'Creative']),
            'is_featured': True,
            'advertiser_id': 2
        },
        {
            'name': 'GitHub Copilot',
            'description': 'AI-powered code completion and programming assistant that helps developers write code faster and more efficiently.',
            'website_url': 'https://github.com/features/copilot',
            'logo_url': 'https://github.githubassets.com/images/modules/site/copilot/copilot-logo.png',
            'pricing_model': 'Paid',
            'tags': json.dumps(['Programming', 'Code Assistant', 'Development', 'Automation']),
            'is_featured': False,
            'advertiser_id': 1
        },
        {
            'name': 'Jasper AI',
            'description': 'AI content creation platform for marketing copy, blog posts, social media content, and business communications.',
            'website_url': 'https://jasper.ai',
            'logo_url': 'https://jasper.ai/assets/jasper-logo.png',
            'pricing_model': 'Paid',
            'tags': json.dumps(['Content Creation', 'Marketing', 'Copywriting', 'Business']),
            'is_featured': False,
            'advertiser_id': 2
        },
        {
            'name': 'Stable Diffusion',
            'description': 'Open-source AI image generation model that creates high-quality images from text descriptions with full customization.',
            'website_url': 'https://stability.ai',
            'logo_url': 'https://stability.ai/assets/stability-logo.png',
            'pricing_model': 'Free',
            'tags': json.dumps(['Image Generation', 'Open Source', 'Art', 'Machine Learning']),
            'is_featured': True,
            'advertiser_id': 1
        },
        {
            'name': 'Claude AI',
            'description': 'Advanced AI assistant by Anthropic for safe, helpful conversations, analysis, and creative tasks with strong reasoning.',
            'website_url': 'https://claude.ai',
            'logo_url': 'https://anthropic.com/assets/claude-logo.png',
            'pricing_model': 'Semi-Free',
            'tags': json.dumps(['AI Chat', 'Analysis', 'Research', 'Writing']),
            'is_featured': False,
            'advertiser_id': 2
        },
        {
            'name': 'Runway ML',
            'description': 'AI-powered video editing and generation platform for creators, with tools for video effects and content creation.',
            'website_url': 'https://runwayml.com',
            'logo_url': 'https://runwayml.com/assets/runway-logo.png',
            'pricing_model': 'Semi-Free',
            'tags': json.dumps(['Video Editing', 'Creative', 'Media', 'Generation']),
            'is_featured': True,
            'advertiser_id': 1
        },
        {
            'name': 'Notion AI',
            'description': 'AI-enhanced productivity workspace that helps with writing, planning, and organizing information intelligently.',
            'website_url': 'https://notion.so/ai',
            'logo_url': 'https://notion.so/assets/notion-logo.png',
            'pricing_model': 'Semi-Free',
            'tags': json.dumps(['Productivity', 'Writing', 'Organization', 'Workspace']),
            'is_featured': False,
            'advertiser_id': 2
        }
    ]
    
    try:
        # Clear existing tools for fresh start
        cursor.execute("DELETE FROM tool")
        print("✓ Cleared existing tools")
        
        # Insert sample tools
        for tool_data in sample_tools:
            cursor.execute('''
                INSERT INTO tool (name, description, website_url, logo_url, pricing_model, 
                                tags, is_featured, advertiser_id, is_approved, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                tool_data['name'],
                tool_data['description'], 
                tool_data['website_url'],
                tool_data['logo_url'],
                tool_data['pricing_model'],
                tool_data['tags'],
                tool_data['is_featured'],
                tool_data['advertiser_id'],
                True,  # is_approved
                datetime.now()
            ))
            print(f"✓ Added tool: {tool_data['name']}")
        
        # Update existing campaigns to use the new tool IDs
        cursor.execute("SELECT id FROM tool LIMIT 3")
        tool_ids = [row[0] for row in cursor.fetchall()]
        
        cursor.execute("SELECT id FROM ad_campaign")
        campaign_ids = [row[0] for row in cursor.fetchall()]
        
        # Update campaigns with new tool IDs
        for i, campaign_id in enumerate(campaign_ids[:len(tool_ids)]):
            cursor.execute("UPDATE ad_campaign SET tool_id = ? WHERE id = ?", 
                         (tool_ids[i], campaign_id))
            print(f"✓ Updated campaign {campaign_id} with tool {tool_ids[i]}")
        
        conn.commit()
        print(f"\n🎉 Successfully added {len(sample_tools)} sample tools!")
        print("✓ Tools are ready for promotion testing")
        
        # Show summary
        cursor.execute("SELECT COUNT(*) FROM tool")
        tool_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM ad_campaign WHERE is_active=1 AND is_approved=1")
        active_campaigns = cursor.fetchone()[0]
        
        print(f"\n📊 Database Summary:")
        print(f"   • Total tools: {tool_count}")
        print(f"   • Active campaigns: {active_campaigns}")
        print(f"   • Ready for testing!")
        
    except Exception as e:
        print(f"❌ Error adding sample tools: {e}")
        conn.rollback()
        
    finally:
        conn.close()

if __name__ == '__main__':
    add_sample_tools()
