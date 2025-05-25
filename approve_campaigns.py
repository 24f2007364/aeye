#!/usr/bin/env python3
"""
Quick script to approve pending campaigns for testing
"""
import sys
import os
sys.path.append(os.path.dirname(__file__))

from app import app, db, AdCampaign

def approve_all_campaigns():
    with app.app_context():
        print("Approving all pending campaigns...")
        
        # Get all pending campaigns
        pending_campaigns = AdCampaign.query.filter_by(is_approved=False).all()
        
        if not pending_campaigns:
            print("No pending campaigns to approve.")
            return
        
        for campaign in pending_campaigns:
            campaign.is_approved = True
            print(f"✓ Approved campaign: {campaign.name} (Tool: {campaign.tool.name})")
        
        db.session.commit()
        print(f"\n🎉 Successfully approved {len(pending_campaigns)} campaigns!")
        
        # Verify the promoted tools are now available
        approved_campaigns = AdCampaign.query.filter_by(is_active=True, is_approved=True).all()
        print(f"\n📊 Total active & approved campaigns: {len(approved_campaigns)}")
        
        for campaign in approved_campaigns:
            print(f"  - {campaign.name} (Tool: {campaign.tool.name})")

if __name__ == '__main__':
    approve_all_campaigns()
