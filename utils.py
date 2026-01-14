import pandas as pd
import os
from datetime import datetime, timedelta, date
from model import db, Food, FoodLog
from sqlalchemy import func

def load_nutrition_data(csv_path):
    """CSV Loader - Specific for your nutrition_data.csv"""
    try:
        if not os.path.exists(csv_path):
            print(f"❌ File not found at: {csv_path}")
            return 0, "File not found"

        # Reading with latin-1 to avoid encoding errors
        df = pd.read_csv(csv_path, encoding='latin-1')
        df.columns = df.columns.str.strip() # Remove spaces from headers

        # Clear old data
        Food.query.delete()
        
        foods = []
        for _, row in df.iterrows():
            try:
                name = str(row.get('food_name', '')).strip()
                if not name or name == 'nan': continue
                
                food = Food(
                    name=name,
                    calories=float(row.get('energy_kcal', 0)),
                    protein=float(row.get('protein_g', 0)),
                    carbs=float(row.get('carb_g', 0)),
                    fat=float(row.get('fat_g', 0)),
                    # Advanced Nutrients for Modal
                    cholesterol_mg=float(row.get('cholesterol_mg', 0)),
                    sodium_mg=float(row.get('sodium_mg', 0)),
                    fibre_g=float(row.get('fibre_g', 0)),
                    vitc_mg=float(row.get('vitc_mg', 0)),
                    vita_ug=float(row.get('vita_ug', 0)),
                    iron_mg=float(row.get('iron_mg', 0)),
                    category='General'
                )
                foods.append(food)
            except:
                continue

        db.session.bulk_save_objects(foods)
        db.session.commit()
        print(f"✅ Loaded {len(foods)} foods successfully!")
        return len(foods), None
        
    except Exception as e:
        db.session.rollback()
        return 0, str(e)

def get_daily_summary(user_id, target_date=None):
    if target_date is None: target_date = date.today()
    start = datetime.combine(target_date, datetime.min.time())
    end = datetime.combine(target_date, datetime.max.time())
    
    logs = FoodLog.query.filter(FoodLog.user_id == user_id, 
                               FoodLog.logged_at.between(start, end)).all()
    
    if not logs:
        return {'calories': 0, 'protein': 0, 'carbs': 0, 'fat': 0, 'meal_count': 0,
                'cholesterol_mg': 0, 'sodium_mg': 0, 'fibre_g': 0, 'vitc_mg': 0, 'vita_ug': 0, 'iron_mg': 0}

    return {
        'calories': round(sum(l.calories or 0 for l in logs), 1),
        'protein': round(sum(l.protein or 0 for l in logs), 1),
        'carbs': round(sum(l.carbs or 0 for l in logs), 1),
        'fat': round(sum(l.fat or 0 for l in logs), 1),
        'sodium_mg': round(sum(l.sodium_mg or 0 for l in logs), 1),
        'cholesterol_mg': round(sum(l.cholesterol_mg or 0 for l in logs), 1),
        'fibre_g': round(sum(l.fibre_g or 0 for l in logs), 1),
        'vitc_mg': round(sum(l.vitc_mg or 0 for l in logs), 1),
        'vita_ug': round(sum(l.vita_ug or 0 for l in logs), 1),
        'iron_mg': round(sum(l.iron_mg or 0 for l in logs), 1),
        'meal_count': len(logs)
    }

def get_meal_breakdown(user_id, target_date=None):
    if target_date is None: target_date = date.today()
    start = datetime.combine(target_date, datetime.min.time())
    end = datetime.combine(target_date, datetime.max.time())
    meals = db.session.query(FoodLog.meal_type, func.sum(FoodLog.calories).label('calories')).filter(
        FoodLog.user_id == user_id, FoodLog.logged_at.between(start, end)).group_by(FoodLog.meal_type).all()
    return {m.meal_type: round(m.calories or 0, 1) for m in meals}

def get_weekly_data(user_id):
    today = date.today()
    return [{'date': (today - timedelta(days=i)).strftime('%a'), 
             'calories': get_daily_summary(user_id, today - timedelta(days=i))['calories']} 
            for i in range(6, -1, -1)]

def get_recent_foods(user_id, limit=5):
    recent = Food.query.join(FoodLog).filter(FoodLog.user_id == user_id).order_by(FoodLog.logged_at.desc()).all()
    res = []
    [res.append(x) for x in recent if x not in res]
    return res[:limit]

def get_streak_badge(streak):
    if streak >= 7: return "🔥", "Warrior"
    if streak >= 3: return "💪", "Consistent"
    return "🎯", "Start Streak"



def export_food_diary_csv(user_id, days=30):
    logs = FoodLog.query.filter(FoodLog.user_id == user_id).all()
    return pd.DataFrame([{'Date': l.logged_at, 'Food': l.food.name, 'Calories': l.calories} for l in logs])