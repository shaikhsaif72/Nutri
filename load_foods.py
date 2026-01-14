from app import app, db, Food
from utils import load_nutrition_data

with app.app_context():
    # Create tables first if they don't exist
    db.create_all()
    print("✓ Database tables created/verified")
    
    # Clear existing foods
    Food.query.delete()
    db.session.commit()
    print("✓ Cleared existing foods")
    
    # Load from CSV
    count, error = load_nutrition_data('data/nutrition_data_converted.csv')
    
    if error:
        print(f"❌ Error: {error}")
    else:
        print(f"✅ Successfully loaded {count} foods!")
        
    # Verify
    total = Food.query.count()
    print(f"✓ Total foods in database: {total}")
    
    # Show first 5
    print("\nFirst 5 foods:")
    foods = Food.query.limit(5).all()
    for food in foods:
        print(f"  - {food.name}: {food.calories} cal")