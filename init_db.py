from app import app, init_database
if __name__ == "__main__":
    print("Creating database tables...")
    init_database()
    print("Database initialized!")