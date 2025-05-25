from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, abort
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import os
import requests
from bs4 import BeautifulSoup
import json

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-change-in-production'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///aeye.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Template filters
@app.template_filter('fromjson')
def from_json(value):
    """Parse JSON string in templates"""
    try:
        return json.loads(value) if value else []
    except:
        return []

# Also add the filter with underscore name for compatibility
@app.template_filter('from_json')
def from_json_underscore(value):
    """Parse JSON string in templates (underscore version)"""
    try:
        return json.loads(value) if value else []
    except:
        return []

# Database Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    is_advertiser = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    reviews = db.relationship('Review', backref='user', lazy=True)
    bookmarks = db.relationship('Bookmark', backref='user', lazy=True)
    tools = db.relationship('Tool', backref='advertiser', lazy=True)

class Tool(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    website_url = db.Column(db.String(500), nullable=False)
    logo_url = db.Column(db.String(500))
    pricing_model = db.Column(db.String(50), nullable=False)  # Free, Paid, Semi-Free
    tags = db.Column(db.Text)  # JSON string of tags
    is_featured = db.Column(db.Boolean, default=False)
    click_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    advertiser_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    is_approved = db.Column(db.Boolean, default=True)
    
    # Relationships
    reviews = db.relationship('Review', backref='tool', lazy=True)
    bookmarks = db.relationship('Bookmark', backref='tool', lazy=True)
    ad_campaigns = db.relationship('AdCampaign', backref='tool', lazy=True)

class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    tool_id = db.Column(db.Integer, db.ForeignKey('tool.id'), nullable=False)
    version_type = db.Column(db.String(10), nullable=False)  # Free or Paid
    rating = db.Column(db.Integer, nullable=False)  # 1-5 stars
    review_text = db.Column(db.Text)
    helpful_votes = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Bookmark(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    tool_id = db.Column(db.Integer, db.ForeignKey('tool.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class AdCampaign(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tool_id = db.Column(db.Integer, db.ForeignKey('tool.id'), nullable=False)
    advertiser_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    budget = db.Column(db.Float, nullable=False)  # Total budget
    cost_per_view = db.Column(db.Float, default=0.10)  # $0.10 per view
    cost_per_click = db.Column(db.Float, default=0.50)  # $0.50 per website click
    duration_days = db.Column(db.Integer, nullable=False)
    target_tags = db.Column(db.Text)  # JSON string
    
    # Tracking metrics
    impressions = db.Column(db.Integer, default=0)  # How many times promoted listing was shown
    tool_views = db.Column(db.Integer, default=0)   # How many times tool detail was clicked from promoted
    website_clicks = db.Column(db.Integer, default=0)  # How many clicked "Visit Website" from promoted
    total_spend = db.Column(db.Float, default=0.0)
    
    # Campaign status
    is_active = db.Column(db.Boolean, default=True)
    is_approved = db.Column(db.Boolean, default=False)  # Admin approval required
    start_date = db.Column(db.DateTime, default=datetime.utcnow)
    end_date = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    advertiser = db.relationship('User', backref='ad_campaigns')

class PromotionTracking(db.Model):
    """Track individual promotion interactions"""
    id = db.Column(db.Integer, primary_key=True)
    campaign_id = db.Column(db.Integer, db.ForeignKey('ad_campaign.id'), nullable=False)
    event_type = db.Column(db.String(20), nullable=False)  # 'impression', 'tool_view', 'website_click'
    user_ip = db.Column(db.String(45))  # For basic deduplication
    user_agent = db.Column(db.Text)
    cost = db.Column(db.Float, default=0.0)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    campaign = db.relationship('AdCampaign', backref='tracking_events')

class AdvertiserBalance(db.Model):
    """Track advertiser account balance and transactions"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    balance = db.Column(db.Float, default=0.0)
    total_spent = db.Column(db.Float, default=0.0)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='advertiser_balance', uselist=False)

class PaymentTransaction(db.Model):
    """Track payment transactions for advertising"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    transaction_type = db.Column(db.String(20), nullable=False)  # 'deposit', 'charge', 'refund'
    description = db.Column(db.String(500))
    payment_method = db.Column(db.String(50), default='QR_CODE')  # QR_CODE, CARD, etc.
    transaction_id = db.Column(db.String(100))  # External payment processor ID
    status = db.Column(db.String(20), default='completed')  # pending, completed, failed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='payment_transactions')

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    tool_id = db.Column(db.Integer, db.ForeignKey('tool.id'), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('comment.id'))  # For replies
    content = db.Column(db.Text, nullable=False)
    likes_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='comments')
    tool = db.relationship('Tool', backref='comments')
    parent = db.relationship('Comment', remote_side=[id], backref='replies')
    likes = db.relationship('CommentLike', backref='comment', lazy=True, cascade='all, delete-orphan')

class CommentLike(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    comment_id = db.Column(db.Integer, db.ForeignKey('comment.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Ensure a user can only like a comment once
    __table_args__ = (db.UniqueConstraint('user_id', 'comment_id', name='unique_user_comment_like'),)

# Promotion Tracking Functions
def track_promotion_event(campaign_id, event_type, user_ip=None):
    """Track promotion events and charge advertiser"""
    campaign = db.session.get(AdCampaign, campaign_id)
    if not campaign or not campaign.is_active:
        return False
    
    # Check if campaign has budget remaining
    if campaign.total_spend >= campaign.budget:
        campaign.is_active = False
        db.session.commit()
        return False
    
    # Calculate cost based on event type
    cost = 0.0
    if event_type == 'impression':
        cost = 0.0  # Free impressions
    elif event_type == 'tool_view':
        cost = campaign.cost_per_view
    elif event_type == 'website_click':
        cost = campaign.cost_per_click
    
    # Check if advertiser has enough balance
    balance = get_advertiser_balance(campaign.advertiser_id)
    if balance < cost:
        campaign.is_active = False
        db.session.commit()
        return False
    
    # Create tracking record
    tracking = PromotionTracking(
        campaign_id=campaign_id,
        user_ip=user_ip or request.environ.get('REMOTE_ADDR'),
        event_type=event_type,
        cost=cost
    )
    db.session.add(tracking)
    
    # Update campaign metrics
    if event_type == 'impression':
        campaign.impressions += 1
    elif event_type == 'tool_view':
        campaign.tool_views += 1
    elif event_type == 'website_click':
        campaign.website_clicks += 1
    
    campaign.total_spend += cost
    
    # Charge advertiser
    if cost > 0:
        charge_advertiser(campaign.advertiser_id, cost, f"Promotion {event_type} for {campaign.name}")
    
    db.session.commit()
    return True

def get_advertiser_balance(user_id):
    """Get current advertiser balance"""
    balance_record = AdvertiserBalance.query.filter_by(user_id=user_id).first()
    return balance_record.balance if balance_record else 0.0

def charge_advertiser(user_id, amount, description=""):
    """Charge advertiser account"""
    balance_record = AdvertiserBalance.query.filter_by(user_id=user_id).first()
    if not balance_record:
        balance_record = AdvertiserBalance(user_id=user_id)
        db.session.add(balance_record)
    
    balance_record.balance -= amount
    balance_record.total_spent += amount
    
    # Create transaction record
    transaction = PaymentTransaction(
        user_id=user_id,
        amount=amount,
        transaction_type='charge',
        description=description
    )
    db.session.add(transaction)

def add_advertiser_funds(user_id, amount, payment_method='QR_CODE', transaction_id=None):
    """Add funds to advertiser account"""
    balance_record = AdvertiserBalance.query.filter_by(user_id=user_id).first()
    if not balance_record:
        balance_record = AdvertiserBalance(user_id=user_id)
        db.session.add(balance_record)
    
    balance_record.balance += amount
    
    # Create transaction record
    transaction = PaymentTransaction(
        user_id=user_id,
        amount=amount,
        transaction_type='deposit',
        description=f"Account top-up via {payment_method}",
        payment_method=payment_method,
        transaction_id=transaction_id
    )
    db.session.add(transaction)
    db.session.commit()

def get_active_promoted_tools(limit=3):
    """Get tools with active promotion campaigns - temporarily disabled for launch"""
    # Return empty list to hide promoted tools during launch
    return []

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

# Routes
@app.route('/')
def index():
    # Get promoted tools (active paid campaigns)
    promoted_tools = get_active_promoted_tools(limit=3)
    
    # Get featured tools (admin-selected)
    featured_tools = Tool.query.filter_by(is_featured=True, is_approved=True).limit(6).all()
    
    # Get popular tools (by click count)
    popular_tools = Tool.query.filter_by(is_approved=True).order_by(Tool.click_count.desc()).limit(6).all()
    
    # Calculate ratings for promoted tools
    for tool in promoted_tools:
        reviews = Review.query.filter_by(tool_id=tool.id).all()
        if reviews:
            tool.avg_rating = sum(r.rating for r in reviews) / len(reviews)
            tool.review_count = len(reviews)
        else:
            tool.avg_rating = 0
            tool.review_count = 0
    
    # Calculate ratings for featured tools
    for tool in featured_tools:
        reviews = Review.query.filter_by(tool_id=tool.id).all()
        if reviews:
            tool.avg_rating = sum(r.rating for r in reviews) / len(reviews)
            tool.review_count = len(reviews)
        else:
            tool.avg_rating = 0
            tool.review_count = 0
    
    # Calculate ratings for popular tools
    for tool in popular_tools:
        reviews = Review.query.filter_by(tool_id=tool.id).all()
        if reviews:
            tool.avg_rating = sum(r.rating for r in reviews) / len(reviews)
            tool.review_count = len(reviews)
        else:
            tool.avg_rating = 0
            tool.review_count = 0
    
    return render_template('index.html', 
                         promoted_tools=promoted_tools, 
                         featured_tools=featured_tools, 
                         popular_tools=popular_tools)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':        
        email = request.form['email']
        username = request.form['username']
        password = request.form['password']
        # Advertiser registration temporarily disabled for launch
        is_advertiser = False  # Force to False regardless of form input
        
        # Check if user exists
        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'error')
            return redirect(url_for('register'))
            
        if User.query.filter_by(username=username).first():
            flash('Username already taken', 'error')
            return redirect(url_for('register'))
        
        # Create new user
        user = User(
            email=email,
            username=username,
            password_hash=generate_password_hash(password),
            is_advertiser=is_advertiser
        )
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful!', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        user = User.query.filter_by(email=email).first()
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    if current_user.is_advertiser:
        return redirect(url_for('advertiser_dashboard'))
    
    # User dashboard
    bookmarks = Bookmark.query.filter_by(user_id=current_user.id).all()
    reviews = Review.query.filter_by(user_id=current_user.id).order_by(Review.created_at.desc()).all()
    return render_template('user_dashboard.html', bookmarks=bookmarks, reviews=reviews)

@app.route('/advertiser-dashboard')
@login_required
def advertiser_dashboard():
    # Advertiser functionality temporarily disabled for launch
    flash('Advertiser features are currently unavailable. Please check back later.', 'info')
    return redirect(url_for('dashboard'))
      # Get advertiser's tools and campaigns
    tools = Tool.query.filter_by(advertiser_id=current_user.id).all()
    campaigns = AdCampaign.query.filter_by(advertiser_id=current_user.id).order_by(AdCampaign.created_at.desc()).all()
    
    # Get advertiser balance
    balance_record = AdvertiserBalance.query.filter_by(user_id=current_user.id).first()
    balance = balance_record.balance if balance_record else 0.0
    total_spent = balance_record.total_spent if balance_record else 0.0
    
    # Calculate total deposited from payment transactions
    total_deposits = db.session.query(db.func.sum(PaymentTransaction.amount)).filter_by(
        user_id=current_user.id, 
        transaction_type='deposit'
    ).scalar() or 0.0
    
    # Calculate campaign analytics
    total_campaigns = len(campaigns)
    active_campaigns = len([c for c in campaigns if c.is_active and c.is_approved])
    total_impressions = sum(c.impressions for c in campaigns)
    total_tool_views = sum(c.tool_views for c in campaigns)
    total_website_clicks = sum(c.website_clicks for c in campaigns)
    total_campaign_spend = sum(c.total_spend for c in campaigns)
    
    # Calculate performance metrics
    avg_ctr = (total_tool_views / total_impressions * 100) if total_impressions > 0 else 0
    avg_conversion = (total_website_clicks / total_tool_views * 100) if total_tool_views > 0 else 0
      # Get recent transactions
    recent_transactions = PaymentTransaction.query.filter_by(
        user_id=current_user.id
    ).order_by(PaymentTransaction.created_at.desc()).limit(10).all()
    
    # Enhanced campaign data with performance metrics
    enhanced_campaigns = []
    for campaign in campaigns:
        # Calculate campaign-specific metrics
        campaign_ctr = (campaign.tool_views / campaign.impressions * 100) if campaign.impressions > 0 else 0
        campaign_conversion = (campaign.website_clicks / campaign.tool_views * 100) if campaign.tool_views > 0 else 0
        budget_utilization = (campaign.total_spend / campaign.budget * 100) if campaign.budget > 0 else 0
        
        # Estimate remaining days based on current spend rate
        days_elapsed = (datetime.utcnow() - campaign.start_date).days + 1
        daily_spend = campaign.total_spend / days_elapsed if days_elapsed > 0 else 0
        remaining_budget = campaign.budget - campaign.total_spend
        estimated_days_remaining = remaining_budget / daily_spend if daily_spend > 0 else campaign.duration_days
        
        enhanced_campaigns.append({
            'campaign': campaign,
            'ctr': campaign_ctr,
            'conversion': campaign_conversion,
            'budget_utilization': budget_utilization,
            'estimated_days_remaining': min(estimated_days_remaining, campaign.duration_days),
            'daily_spend': daily_spend
        })
        analytics_data = {
        'balance': balance,
        'total_spent': total_spent,
        'total_deposited': total_deposits,
        'total_campaigns': total_campaigns,
        'active_campaigns': active_campaigns,
        'total_impressions': total_impressions,
        'total_tool_views': total_tool_views,
        'total_website_clicks': total_website_clicks,
        'total_campaign_spend': total_campaign_spend,
        'avg_ctr': avg_ctr,
        'avg_conversion': avg_conversion
    }
    
    return render_template('advertiser_dashboard.html', 
                         tools=tools, 
                         campaigns=enhanced_campaigns,
                         analytics=analytics_data,
                         recent_transactions=recent_transactions)

@app.route('/create-campaign', methods=['POST'])
@login_required
def create_campaign():
    # Campaign creation temporarily disabled for launch
    flash('Campaign features are currently unavailable. Please check back later.', 'info')
    return redirect(url_for('dashboard'))
    
    tool_id = request.form['tool_id']
    name = request.form['name']
    budget = float(request.form['budget'])
    duration_days = int(request.form['duration_days'])
    target_tags = request.form.get('target_tags', '')
    
    # Verify tool belongs to current user
    tool = Tool.query.filter_by(id=tool_id, advertiser_id=current_user.id).first()
    if not tool:
        flash('Tool not found or access denied', 'error')
        return redirect(url_for('advertiser_dashboard'))
    
    # Validate budget
    if budget < 10:
        flash('Minimum budget is $10', 'error')
        return redirect(url_for('advertiser_dashboard'))
    
    # Process target tags
    if target_tags:
        target_tags = [tag.strip() for tag in target_tags.split(',')]
        target_tags = json.dumps(target_tags)
    else:
        target_tags = '[]'
      # Create campaign
    campaign = AdCampaign(
        tool_id=tool_id,
        advertiser_id=current_user.id,
        name=name,
        budget=budget,
        duration_days=duration_days,
        target_tags=target_tags
    )
    db.session.add(campaign)
    db.session.commit()
    
    flash(f'Campaign "{name}" created successfully!', 'success')
    return redirect(url_for('advertiser_dashboard'))

@app.route('/explore')
def explore():
    # Get filters from request
    search_query = request.args.get('search', '')
    pricing_filter = request.args.get('pricing', '')
    sort_by = request.args.get('sort', 'relevance')
    tags_filter = request.args.getlist('tags')
    
    # Get promoted tools first (only show if no specific search/filter to avoid confusion)    promoted_tools = []
    if not search_query and not pricing_filter and not tags_filter:
        promoted_tools = get_active_promoted_tools(limit=3)
        # Track impressions for promoted tools
        user_ip = request.environ.get('REMOTE_ADDR')
        for tool in promoted_tools:
            track_promotion_event(tool.campaign_id, 'impression', user_ip)
    
    # Base query for regular tools
    query = Tool.query.filter_by(is_approved=True)
    
    # Exclude promoted tools from regular listing to avoid duplication
    if promoted_tools:
        promoted_tool_ids = [tool.id for tool in promoted_tools]
        query = query.filter(~Tool.id.in_(promoted_tool_ids))
    
    # Apply filters
    if search_query:
        query = query.filter(Tool.name.contains(search_query) | Tool.description.contains(search_query))
    
    if pricing_filter:
        query = query.filter_by(pricing_model=pricing_filter)
    
    # Apply sorting
    if sort_by == 'popularity':
        query = query.order_by(Tool.click_count.desc())
    elif sort_by == 'newest':
        query = query.order_by(Tool.created_at.desc())
    elif sort_by == 'rating':
        # This would need a more complex query to calculate average ratings
        pass
    
    regular_tools = query.all()
    
    # Calculate ratings for all tools
    all_tools_for_rating = promoted_tools + regular_tools
    for tool in all_tools_for_rating:
        reviews = Review.query.filter_by(tool_id=tool.id).all()
        if reviews:
            tool.avg_rating = sum(r.rating for r in reviews) / len(reviews)
            tool.review_count = len(reviews)
        else:
            tool.avg_rating = 0
            tool.review_count = 0
    
    # Get all available tags for filter options
    all_tools = Tool.query.filter_by(is_approved=True).all()
    all_tags = set()
    for tool in all_tools:
        if tool.tags:
            tool_tags = json.loads(tool.tags)
            all_tags.update(tool_tags)
    
    return render_template('explore.html', 
                         promoted_tools=promoted_tools,
                         tools=regular_tools, 
                         all_tags=sorted(all_tags), 
                         search_query=search_query, 
                         pricing_filter=pricing_filter, 
                         sort_by=sort_by, 
                         tags_filter=tags_filter)

@app.route('/tool/<int:tool_id>')
def tool_detail(tool_id):
    tool = db.session.get(Tool, tool_id)
    if not tool:
        abort(404)
      # Check if this is a promoted tool view (from campaign parameter)
    campaign_id = request.args.get('campaign_id')
    if campaign_id:
        # Track promoted tool view
        user_ip = request.environ.get('REMOTE_ADDR')
        track_promotion_event(int(campaign_id), 'tool_view', user_ip)
    
    # Increment regular click count
    tool.click_count += 1
    db.session.commit()
    
    # Get reviews separated by version type
    free_reviews = Review.query.filter_by(tool_id=tool_id, version_type='Free').all()
    paid_reviews = Review.query.filter_by(tool_id=tool_id, version_type='Paid').all()
    
    # Calculate average ratings
    free_avg = sum(r.rating for r in free_reviews) / len(free_reviews) if free_reviews else 0
    paid_avg = sum(r.rating for r in paid_reviews) / len(paid_reviews) if paid_reviews else 0
      # Get comments with replies
    main_comments = Comment.query.filter_by(tool_id=tool_id, parent_id=None).order_by(Comment.created_at.desc()).all()
    all_comments = Comment.query.filter_by(tool_id=tool_id).order_by(Comment.created_at.asc()).all()
    
    # Get user likes for comments if user is authenticated
    user_liked_comments = set()
    if current_user.is_authenticated:
        liked_comment_ids = db.session.query(CommentLike.comment_id).filter_by(user_id=current_user.id).all()
        user_liked_comments = {like[0] for like in liked_comment_ids}
    
    # Check if user has bookmarked this tool
    is_bookmarked = False
    if current_user.is_authenticated:
        is_bookmarked = Bookmark.query.filter_by(user_id=current_user.id, tool_id=tool_id).first() is not None
    
    return render_template('tool_detail.html', tool=tool, free_reviews=free_reviews, 
                         paid_reviews=paid_reviews, free_avg=free_avg, paid_avg=paid_avg,
                         is_bookmarked=is_bookmarked, comments=main_comments, 
                         all_comments=all_comments, user_liked_comments=user_liked_comments)

@app.route('/add-tool', methods=['GET', 'POST'])
@login_required
def add_tool():
    if not current_user.is_advertiser:
        flash('Only advertisers can add tools', 'error')
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        website_url = request.form['website_url']
        logo_url = request.form.get('logo_url', '')
        pricing_model = request.form['pricing_model']
        tags = request.form.getlist('tags')
        
        # Check for duplicate tools by URL or name
        existing_tool_by_url = Tool.query.filter_by(website_url=website_url).first()
        existing_tool_by_name = Tool.query.filter(Tool.name.ilike(f'%{name}%')).first()
        
        if existing_tool_by_url:
            flash(f'A tool with this URL already exists: {existing_tool_by_url.name}', 'error')
            return render_template('add_tool.html')
        
        if existing_tool_by_name:
            flash(f'A tool with similar name already exists: {existing_tool_by_name.name}', 'error')
            return render_template('add_tool.html')
        
        # Create tool with admin approval required
        tool = Tool(
            name=name,
            description=description,
            website_url=website_url,
            logo_url=logo_url,
            pricing_model=pricing_model,
            tags=json.dumps(tags),
            advertiser_id=current_user.id,
            is_approved=False  # Require admin approval
        )
        db.session.add(tool)
        db.session.commit()
        
        flash('Tool submitted successfully! It will be reviewed by admin before going live.', 'success')
        return redirect(url_for('advertiser_dashboard'))
    
    return render_template('add_tool.html')

@app.route('/add-review/<int:tool_id>', methods=['POST'])
@login_required
def add_review(tool_id):
    # Prevent advertisers from reviewing tools
    if current_user.is_advertiser:
        flash('Advertisers cannot review tools to maintain objectivity', 'error')
        return redirect(url_for('tool_detail', tool_id=tool_id))
    
    version_type = request.form['version_type']
    rating = int(request.form['rating'])
    review_text = request.form.get('review_text', '')
    
    # Check if user already reviewed this version
    existing_review = Review.query.filter_by(
        user_id=current_user.id, 
        tool_id=tool_id, 
        version_type=version_type
    ).first()
    
    if existing_review:
        # Update existing review
        existing_review.rating = rating
        existing_review.review_text = review_text
    else:
        # Create new review
        review = Review(
            user_id=current_user.id,
            tool_id=tool_id,
            version_type=version_type,
            rating=rating,
            review_text=review_text
        )
        db.session.add(review)
    
    db.session.commit()
    flash('Review added successfully!', 'success')
    return redirect(url_for('tool_detail', tool_id=tool_id))

# Community Comments Routes
@app.route('/add-comment/<int:tool_id>', methods=['POST'])
def add_comment(tool_id):
    # Check if user is authenticated
    if not current_user.is_authenticated:
        return jsonify({'success': False, 'message': 'You must be logged in to comment'})
    
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'message': 'No data provided'})
    
    content = data.get('content', '').strip()
    parent_id = data.get('parent_id')
    
    if not content:
        return jsonify({'success': False, 'message': 'Comment cannot be empty'})
    
    # Validate tool exists
    tool = db.session.get(Tool, tool_id)
    if not tool:
        return jsonify({'success': False, 'message': 'Tool not found'})
    
    # Create comment
    comment = Comment(
        user_id=current_user.id,
        tool_id=tool_id,
        content=content,
        parent_id=int(parent_id) if parent_id else None
    )
    db.session.add(comment)
    db.session.commit()
    
    # Return comment data for immediate display
    return jsonify({
        'success': True,
        'comment': {
            'id': comment.id,
            'content': comment.content,
            'user_name': current_user.username,
            'created_at': comment.created_at.strftime('%B %d, %Y at %I:%M %p'),
            'likes_count': 0,
            'user_liked': False,
            'parent_id': comment.parent_id
        }
    })

@app.route('/toggle-comment-like/<int:comment_id>', methods=['POST'])
def toggle_comment_like(comment_id):
    # Check if user is authenticated
    if not current_user.is_authenticated:
        return jsonify({'success': False, 'message': 'You must be logged in to like comments'})
    
    comment = db.session.get(Comment, comment_id)
    if not comment:
        return jsonify({'success': False, 'message': 'Comment not found'})
    
    # Check if user already liked this comment
    existing_like = CommentLike.query.filter_by(
        user_id=current_user.id, 
        comment_id=comment_id    ).first()
    
    if existing_like:
        # Unlike
        db.session.delete(existing_like)
        comment.likes_count = max(0, comment.likes_count - 1)
        user_liked = False
    else:
        # Like
        like = CommentLike(user_id=current_user.id, comment_id=comment_id)
        db.session.add(like)
        comment.likes_count += 1
        user_liked = True
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'likes_count': comment.likes_count,
        'liked': user_liked
    })

@app.route('/categories')
def categories():
    # Get all approved tools
    all_tools = Tool.query.filter_by(is_approved=True).all()
    
    # Create categories with tools
    categories_data = {}
    for tool in all_tools:
        if tool.tags:
            tool_tags = json.loads(tool.tags)
            for tag in tool_tags:
                if tag not in categories_data:
                    categories_data[tag] = []
                categories_data[tag].append(tool)
    
    # Sort categories by tool count
    sorted_categories = sorted(categories_data.items(), key=lambda x: len(x[1]), reverse=True)
    
    return render_template('categories.html', categories=sorted_categories)

# Admin Panel (Hidden Route)
@app.route('/admin_secret_panel', methods=['GET', 'POST'])
def admin_panel():
    if request.method == 'POST' and 'password' in request.form:
        if request.form['password'] == 'admin123':
            session['admin_authenticated'] = True
            return redirect(url_for('admin_panel'))
        else:
            flash('Invalid admin password', 'error')
    
    if not session.get('admin_authenticated'):
        return render_template('admin_login.html')
      # Admin panel main page
    tools = Tool.query.all()
    users = User.query.all()
    pending_tools = Tool.query.filter_by(is_approved=False).all()
    
    # Get campaign data for the campaigns tab
    pending_campaigns = AdCampaign.query.filter_by(is_approved=False).all()
    active_campaigns = AdCampaign.query.filter_by(is_active=True, is_approved=True).all()
    
    return render_template('admin_panel.html', 
                         tools=tools, 
                         users=users, 
                         pending_tools=pending_tools,
                         pending_campaigns=pending_campaigns,
                         active_campaigns=active_campaigns)

@app.route('/admin/approve-tool/<int:tool_id>', methods=['POST'])
def admin_approve_tool(tool_id):
    if not session.get('admin_authenticated'):
        return jsonify({'success': False, 'message': 'Not authenticated'})
    
    tool = db.session.get(Tool, tool_id)
    if not tool:
        return jsonify({'success': False, 'message': 'Tool not found'})
    tool.is_approved = True
    db.session.commit()
    return jsonify({'success': True, 'message': f'Tool "{tool.name}" approved successfully!'})

@app.route('/admin/delete-tool/<int:tool_id>', methods=['POST'])
def admin_delete_tool(tool_id):
    if not session.get('admin_authenticated'):
        return jsonify({'success': False, 'message': 'Not authenticated'})
    
    tool = db.session.get(Tool, tool_id)
    if not tool:
        return jsonify({'success': False, 'message': 'Tool not found'})
    tool_name = tool.name
    
    # Delete related records first
    Review.query.filter_by(tool_id=tool_id).delete()
    Bookmark.query.filter_by(tool_id=tool_id).delete()
    AdCampaign.query.filter_by(tool_id=tool_id).delete()
    
    # Delete the tool
    db.session.delete(tool)
    db.session.commit()
    
    return jsonify({'success': True, 'message': f'Tool "{tool_name}" deleted successfully!'})

@app.route('/admin/toggle-featured/<int:tool_id>', methods=['POST'])
def admin_toggle_featured(tool_id):
    if not session.get('admin_authenticated'):
        return jsonify({'success': False, 'message': 'Not authenticated'})
    
    tool = db.session.get(Tool, tool_id)
    if not tool:
        return jsonify({'success': False, 'message': 'Tool not found'})
    tool.is_featured = not tool.is_featured
    db.session.commit()
    
    status = "featured" if tool.is_featured else "unfeatured"
    return jsonify({'success': True, 'message': f'Tool "{tool.name}" {status} successfully!'})

@app.route('/admin/approve-all', methods=['POST'])
def admin_approve_all():
    if not session.get('admin_authenticated'):
        return jsonify({'success': False, 'message': 'Not authenticated'})
    
    pending_tools = Tool.query.filter_by(is_approved=False).all()
    count = len(pending_tools)
    
    for tool in pending_tools:
        tool.is_approved = True
    
    db.session.commit()
    return jsonify({'success': True, 'message': f'Approved {count} tools successfully!'})

# Campaign Management Routes
@app.route('/admin/approve-campaign/<int:campaign_id>', methods=['POST'])
def admin_approve_campaign(campaign_id):
    if not session.get('admin_authenticated'):
        return jsonify({'success': False, 'message': 'Not authenticated'})
    
    campaign = db.session.get(AdCampaign, campaign_id)
    if not campaign:
        return jsonify({'success': False, 'message': 'Campaign not found'})
    
    campaign.is_approved = True
    # Activate campaign when approved if it's not already active
    if not campaign.is_active:
        campaign.is_active = True
    
    db.session.commit()
    return jsonify({'success': True, 'message': f'Campaign "{campaign.name}" approved successfully!'})

@app.route('/admin/reject-campaign/<int:campaign_id>', methods=['POST'])
def admin_reject_campaign(campaign_id):
    if not session.get('admin_authenticated'):
        return jsonify({'success': False, 'message': 'Not authenticated'})
    
    campaign = db.session.get(AdCampaign, campaign_id)
    if not campaign:
        return jsonify({'success': False, 'message': 'Campaign not found'})
    
    campaign_name = campaign.name
    
    # Delete related tracking records first
    PromotionTracking.query.filter_by(campaign_id=campaign_id).delete()
    
    # Delete the campaign
    db.session.delete(campaign)
    db.session.commit()
    
    return jsonify({'success': True, 'message': f'Campaign "{campaign_name}" rejected and deleted successfully!'})

@app.route('/admin/approve-all-campaigns', methods=['POST'])
def admin_approve_all_campaigns():
    if not session.get('admin_authenticated'):
        return jsonify({'success': False, 'message': 'Not authenticated'})
    
    pending_campaigns = AdCampaign.query.filter_by(is_approved=False).all()
    count = len(pending_campaigns)
    
    for campaign in pending_campaigns:
        campaign.is_approved = True
        # Activate campaign when approved if it's not already active
        if not campaign.is_active:
            campaign.is_active = True
    
    db.session.commit()
    return jsonify({'success': True, 'count': count, 'message': f'Approved {count} campaigns successfully!'})

@app.route('/admin/add-tool', methods=['POST'])
def admin_add_tool():
    if not session.get('admin_authenticated'):
        return jsonify({'success': False, 'message': 'Not authenticated'})
    
    try:
        name = request.form['name']
        description = request.form['description']
        website_url = request.form['website_url']
        logo_url = request.form.get('logo_url', '')
        pricing_model = request.form['pricing_model']
        
        # Handle both 'tags' and 'categories[]' field names
        tags_data = request.form.get('tags')
        if tags_data:
            # If tags come as JSON string (from JavaScript)
            try:
                categories = json.loads(tags_data)
            except:
                categories = []
        else:
            # If tags come as form list
            categories = request.form.getlist('categories[]') or request.form.getlist('tags')
        
        is_featured = 'is_featured' in request.form
        
        # Validate required fields
        if not all([name, description, website_url, pricing_model]):
            return jsonify({'success': False, 'message': 'Please fill in all required fields'})
        
        # Validate categories (minimum 1)
        if len(categories) < 1:
            return jsonify({'success': False, 'message': 'Please select at least 1 category'})
        
        tool = Tool(
            name=name,
            description=description,
            website_url=website_url,
            logo_url=logo_url,
            pricing_model=pricing_model,
            tags=json.dumps(categories),
            is_featured=is_featured,
            is_approved=True,  # Admin-added tools are automatically approved
            advertiser_id=None  # Admin tools don't have an advertiser
        )
        db.session.add(tool)
        db.session.commit()
        
        return jsonify({'success': True, 'message': f'Tool "{name}" added successfully!'})
    except Exception as e:
        print(f"Error adding tool: {e}")
        return jsonify({'success': False, 'message': f'Error adding tool: {str(e)}'})

@app.route('/admin/scrape-tools', methods=['POST'])
def admin_scrape_tools():
    if not session.get('admin_authenticated'):
        return jsonify({'success': False, 'message': 'Not authenticated'})
    
    try:
        # Enhanced web scraping functionality
        scraped_count = 0
        
        # Example scraping targets (you can expand this)
        scraping_sources = [
            'https://www.producthunt.com/topics/artificial-intelligence',
            'https://www.futuretools.io/',
            'https://www.toolify.ai/',
        ]
        
        # This is still a placeholder for demonstration
        # In a real implementation, you would:
        # 1. Scrape from AI tool directories
        # 2. Parse tool information
        # 3. Add tools to database
        # 4. Handle duplicates
        
        return jsonify({'success': True, 'message': f'Web scraping initiated. Found {scraped_count} new tools. (Feature in development)'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Scraping error: {str(e)}'})

@app.route('/admin/stats')
def admin_stats():
    if not session.get('admin_authenticated'):
        return redirect(url_for('admin_panel'))
    
    # Calculate dashboard stats
    total_tools = Tool.query.count()
    approved_tools = Tool.query.filter_by(is_approved=True).count()
    pending_tools = Tool.query.filter_by(is_approved=False).count()
    featured_tools = Tool.query.filter_by(is_featured=True).count()
    total_users = User.query.count()
    advertisers = User.query.filter_by(is_advertiser=True).count()
    total_reviews = Review.query.count()
    total_clicks = db.session.query(db.func.sum(Tool.click_count)).scalar() or 0
    
    return jsonify({
        'total_tools': total_tools,
        'approved_tools': approved_tools,
        'pending_tools': pending_tools,
        'featured_tools': featured_tools,
        'total_users': total_users,
        'advertisers': advertisers,
        'total_reviews': total_reviews,
        'total_clicks': total_clicks
    })

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_authenticated', None)
    flash('Admin logged out successfully!', 'success')
    return redirect(url_for('index'))

# API endpoints for autocomplete
@app.route('/api/search-suggestions')
def search_suggestions():
    query = request.args.get('q', '')
    if len(query) < 2:
        return jsonify([])
    
    tools = Tool.query.filter(
        Tool.name.contains(query) | Tool.description.contains(query)
    ).filter_by(is_approved=True).limit(5).all()
    
    suggestions = [{'name': tool.name, 'id': tool.id} for tool in tools]
    return jsonify(suggestions)

@app.route('/visit-website/<int:tool_id>')
def visit_website(tool_id):
    """Track website visits from promoted tools and redirect"""
    tool = db.session.get(Tool, tool_id)
    if not tool:
        abort(404)
    
    # Check if this is from a promoted campaign
    campaign_id = request.args.get('campaign_id')
    if campaign_id:        # Track promoted website click
        user_ip = request.environ.get('REMOTE_ADDR')
        track_promotion_event(int(campaign_id), 'website_click', user_ip)
    
    # Redirect to the actual website
    return redirect(tool.website_url)

# Test route for debugging comments
@app.route('/comment-test')
def comment_test():
    return render_template('comment_test.html')

@app.route('/create-promotion-campaign', methods=['POST'])
@login_required
def create_promotion_campaign():
    # Promotion campaigns temporarily disabled for launch
    flash('Promotion features are currently unavailable. Please check back later.', 'info')
    return redirect(url_for('dashboard'))
    
    tool_id = request.form['tool_id']
    name = request.form['name']
    budget = float(request.form['budget'])
    duration_days = int(request.form['duration_days'])
    cost_per_view = float(request.form.get('cost_per_view', 0.10))
    cost_per_click = float(request.form.get('cost_per_click', 0.50))
    target_tags = request.form.get('target_tags', '')
    
    # Verify tool belongs to current user
    tool = Tool.query.filter_by(id=tool_id, advertiser_id=current_user.id).first()
    if not tool:
        flash('Tool not found or access denied', 'error')
        return redirect(url_for('advertiser_dashboard'))
    
    # Validate budget
    if budget < 20:
        flash('Minimum budget is $20', 'error')
        return redirect(url_for('advertiser_dashboard'))
    
    # Check advertiser balance
    balance = get_advertiser_balance(current_user.id)
    if balance < budget:
        flash(f'Insufficient balance. You have ${balance:.2f}, but need ${budget:.2f}', 'error')
        return redirect(url_for('advertiser_dashboard'))
    
    # Process target tags
    if target_tags:
        target_tags = [tag.strip() for tag in target_tags.split(',')]
        target_tags = json.dumps(target_tags)
    else:
        target_tags = tool.tags  # Use tool's tags if none specified
    
    # Create campaign
    campaign = AdCampaign(
        tool_id=tool_id,
        advertiser_id=current_user.id,
        name=name,
        budget=budget,
        cost_per_view=cost_per_view,
        cost_per_click=cost_per_click,
        duration_days=duration_days,
        target_tags=target_tags,
        is_active=True,
        is_approved=False  # Requires admin approval
    )
    
    db.session.add(campaign)
    db.session.commit()
    
    flash(f'Promotion campaign "{name}" created successfully! Awaiting admin approval.', 'success')
    return redirect(url_for('advertiser_dashboard'))

@app.route('/toggle-campaign/<int:campaign_id>')
@login_required
def toggle_campaign(campaign_id):
    # Campaign management temporarily disabled for launch
    flash('Campaign features are currently unavailable. Please check back later.', 'info')
    return redirect(url_for('dashboard'))
    
    campaign.is_active = not campaign.is_active
    db.session.commit()
    
    status = "activated" if campaign.is_active else "paused"
    flash(f'Campaign "{campaign.name}" has been {status}', 'success')
    return redirect(url_for('advertiser_dashboard'))

@app.route('/add-funds', methods=['POST'])
@login_required
def add_funds():
    if not current_user.is_advertiser:
        flash('Only advertisers can add funds', 'error')
        return redirect(url_for('dashboard'))
    
    amount = float(request.form['amount'])
    payment_method = request.form.get('payment_method', 'QR_CODE')
    
    if amount < 10:
        flash('Minimum deposit is $10', 'error')
        return redirect(url_for('advertiser_dashboard'))
    
    # Simulate payment processing (in real app, integrate with payment gateway)
    transaction_id = f"TXN_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{current_user.id}"
    
    # Add funds to account
    add_advertiser_funds(current_user.id, amount, payment_method, transaction_id)
    
    flash(f'Successfully added ${amount:.2f} to your account!', 'success')
    return redirect(url_for('advertiser_dashboard'))

@app.route('/campaign-analytics/<int:campaign_id>')
@login_required
def campaign_analytics(campaign_id):
    # Campaign analytics temporarily disabled for launch
    flash('Analytics features are currently unavailable. Please check back later.', 'info')
    return redirect(url_for('dashboard'))
    
    # Get detailed tracking data
    tracking_events = PromotionTracking.query.filter_by(campaign_id=campaign_id).order_by(
        PromotionTracking.timestamp.desc()
    ).limit(100).all()
    
    # Group tracking by date for charts
    from collections import defaultdict
    daily_stats = defaultdict(lambda: {'impressions': 0, 'tool_views': 0, 'website_clicks': 0, 'cost': 0})
    
    for event in tracking_events:
        date_key = event.timestamp.strftime('%Y-%m-%d')
        daily_stats[date_key][event.action_type + 's'] += 1
        daily_stats[date_key]['cost'] += event.cost
    
    # Convert to list for frontend
    chart_data = [
        {
            'date': date,
            'impressions': stats['impressions'],
            'tool_views': stats['tool_views'], 
            'website_clicks': stats['website_clicks'],
            'cost': stats['cost']
        }
        for date, stats in sorted(daily_stats.items())
    ]
    
    return render_template('campaign_analytics.html', 
                         campaign=campaign, 
                         tracking_events=tracking_events[:20],  # Latest 20 events
                         chart_data=chart_data)

# Footer Page Routes
@app.route('/help-center')
def help_center():
    return render_template('help_center.html')

@app.route('/contact-us')
def contact_us():
    return render_template('contact_us.html')

@app.route('/about-us')
def about_us():
    return render_template('about_us.html')

@app.route('/privacy-policy')
def privacy_policy():
    return render_template('privacy_policy.html')

@app.route('/terms-of-service')
def terms_of_service():
    return render_template('terms_of_service.html')

@app.route('/cookie-policy')
def cookie_policy():
    return render_template('cookie_policy.html')

@app.route('/community-guidelines')
def community_guidelines():
    return render_template('community_guidelines.html')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        print("🚀 Aeye AI Tools Discovery Platform")
        print("📊 Database initialized")
        print("🌐 Server starting on http://localhost:5000")
        print("💰 Promotion system active")
    app.run(debug=True, host='0.0.0.0', port=5000)
