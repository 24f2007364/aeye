# Aeye - Professional AI Tools Discovery Platform

🧠 **Aeye** is a professional AI tools discovery platform featuring a clean, modern interface inspired by Anthropic/OpenAI design principles. The platform allows users to discover, rate, and compare AI tools while providing advertisers with analytics-driven dashboards.

## 🎨 Design Features
- **Professional Color Scheme**: Orange (#FF6B35) primary with neutral grays
- **Modern Typography**: Inter font family for clean, professional appearance
- **Responsive Design**: Bootstrap 5.3.2 with custom professional styling
- **Enhanced UI Components**: Professional cards, forms, and interactive elements

## 🎯 Vision
To become the largest searchable, review-based, professionally designed platform where users find the right AI tools for any task — complete with ratings, tags, pricing info, and advertiser support.

## 🛠️ Features
- **User Module**: Registration, search & discovery, tool details, reviews & ratings
- **Advertiser Module**: Tool listing, ad promotion, analytics dashboard
- **Admin Panel**: Tool moderation and management (hidden route)
- **Web Scraping**: Automated tool discovery and data collection

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- pip

### Installation
1. Clone the repository
2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Initialize the database:
```bash
python init_db.py
```

4. Run the application:
```bash
python app.py
```

5. Open your browser and navigate to `http://localhost:5000`

### Admin Access
- Access admin panel at `/admin_secret_panel`
- Default password: `admin123`

## 🎨 Design Guidelines
- **Aesthetic**: Gen-Z appeal with bold colors and smooth animations
- **Style**: Glassmorphism + Neumorphism mix
- **Fonts**: Outfit, Space Grotesk
- **Colors**: Blue gradient theme
- **Mode**: Dark mode by default
- **Responsive**: Mobile-first design

## 📄 Key Pages
- **Landing Page**: Hero section with search
- **Explore/Search**: Dynamic filters and results
- **Tool Details**: Comprehensive tool information
- **User Dashboard**: Personal tool management
- **Advertiser Dashboard**: Ad campaigns and analytics
- **Admin Panel**: Content moderation

## 🧱 Tech Stack
- **Frontend**: Vanilla JavaScript + Bootstrap CSS + Framer Motion
- **Backend**: Python Flask
- **Database**: SQLite
- **Analytics**: User and ad tracking
- **Search**: Advanced filtering and sorting

## 💰 Business Model
Revenue through advertiser promotions:
- Search result prioritization
- Homepage featured slots
- CPM/CPC pricing models

## 🔧 Development
The project follows a modular structure with separate blueprints for different functionalities:
- User management
- Tool discovery
- Advertising system
- Admin controls

## 📝 License
This project is proprietary and confidential.
