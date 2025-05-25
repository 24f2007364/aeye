#!/usr/bin/env python3
from app import app, db, AdCampaign, Tool, User, get_active_promoted_tools

with app.app_context():
    print("=== ALL CAMPAIGNS ===")
    campaigns = AdCampaign.query.all()
    print(f"Total campaigns: {len(campaigns)}")
    
    for c in campaigns:
        print(f"Campaign {c.id}: {c.name}")
        print(f"  - Active: {c.is_active}")
        print(f"  - Approved: {c.is_approved}")
        print(f"  - Spend: ${c.total_spend}/{c.budget}")
        print(f"  - Tool: {c.tool.name}")
        print(f"  - Tool Approved: {c.tool.is_approved}")
        print()
    
    print("=== PROMOTED TOOLS CHECK ===")
    promoted = get_active_promoted_tools()
    print(f"Promoted tools found: {len(promoted)}")
    
    if promoted:
        for tool in promoted:
            print(f"- {tool.name} (Campaign ID: {tool.campaign_id})")
    else:
        print("No promoted tools found!")
        
        # Let's debug why
        print("\n=== DEBUGGING ===")
        active_campaigns = AdCampaign.query.filter_by(is_active=True).all()
        print(f"Active campaigns: {len(active_campaigns)}")
        
        approved_campaigns = AdCampaign.query.filter_by(is_approved=True).all()
        print(f"Approved campaigns: {len(approved_campaigns)}")
        
        both = AdCampaign.query.filter_by(is_active=True, is_approved=True).all()
        print(f"Active AND approved campaigns: {len(both)}")
        
        # Check if there are any campaigns that need approval
        pending = AdCampaign.query.filter_by(is_active=True, is_approved=False).all()
        print(f"Active but not approved campaigns: {len(pending)}")
        
        if pending:
            print("Campaigns waiting for approval:")
            for c in pending:
                print(f"  - {c.name} (Tool: {c.tool.name})")
