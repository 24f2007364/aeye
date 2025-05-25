# Aeye - AI Tools Discovery Platform

<!-- Use this file to provide workspace-specific custom instructions to Copilot. For more details, visit https://code.visualstudio.com/docs/copilot/copilot-customization#_use-a-githubcopilotinstructionsmd-file -->

## Project Overview
Aeye is an AI tools discovery platform - the "Amazon.com for AI tools" where users can discover, rate, and compare AI products, while advertisers can promote their tools with analytics-driven dashboards.

## Tech Stack
- **Frontend**: Vanilla JavaScript + Bootstrap CSS + Framer Motion
- **Backend**: Python Flask
- **Database**: SQLite
- **Payments**: QR Code
- **Analytics**: For both users & ads tracking

## Code Style Guidelines
- Use modern, clean code practices
- Follow Flask best practices for route organization
- Use Bootstrap classes for responsive design
- Implement dark mode by default
- Use modern fonts like Outfit and Space Grotesk
- Implement blue color gradients
- Follow Gen-Z appeal design with glassmorphism + neumorphism

## Key Features to Implement
1. User registration/login with email/password
2. AI-based search with autocomplete
3. Tool filtering by tags, pricing, ratings
4. Separate reviews for Free and Paid versions
5. Advertiser dashboard with analytics
6. Admin panel for tool moderation (hidden route)
7. Web scraping capabilities for adding new AI tools

## Security Notes
- Admin panel should be accessible via custom route with password protection
- Default admin password: admin123
- Implement proper session management
- Validate all user inputs
