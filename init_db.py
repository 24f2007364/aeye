from app import app, db

def init_database():
    """Initialize the database with tables."""
    with app.app_context():
        # Create all tables
        db.create_all()
        print("Database tables created successfully!")
        
        # You can add initial data here if needed
        print("Database initialization complete!")

if __name__ == '__main__':
    init_database()
