from app import app, db, FoodLog
from datetime import datetime

with app.app_context():
    # Get all logs
    logs = FoodLog.query.order_by(FoodLog.logged_at.desc()).limit(10).all()
    
    print(f"Total logs in database: {FoodLog.query.count()}")
    print("\nLast 10 entries:")
    
    for log in logs:
        print(f"- {log.food.name} ({log.quantity}g) - {log.meal_type}")
        print(f"  Logged at: {log.logged_at}")
        print(f"  Calories: {log.calories}")