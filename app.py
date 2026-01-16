from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from datetime import datetime, date
from io import BytesIO
import os
import google.generativeai as genai
import markdown
from config import Config
from model import db, User, Food, FoodLog, FavoriteFood
from utils import (
    load_nutrition_data, get_daily_summary, get_weekly_data,
    get_meal_breakdown, get_recent_foods, export_food_diary_csv, get_streak_badge
)

# Initialize Flask app
app = Flask(__name__)

# ============================================================================
# AI CHATBOT SECTION
# ============================================================================

# 1. API Key Setup (Isse app config hone ke baad ya imports ke niche rakhein)
# Agar environment variable nahi milta toh error se bachne ke liye empty string rakha hai
genai.configure(api_key=os.environ.get('GOOGLE_API_KEY'))

@app.route('/api/chat', methods=['POST'])
@login_required
def chat_with_ai():
    """
    Ye route frontend se message lega, user ka health data add karega,
    aur AI se personalized jawab lekar wapas bhejega.
    """
    data = request.get_json()
    user_message = data.get('message', '')
    
    if not user_message:
        return jsonify({'error': 'No message provided'}), 400

    try:
        # 2. Context Create Karo (Taaki AI ko pata ho wo kisse baat kar raha hai)
        # Hum current_user ka data use kar rahe hain jo database se aa raha hai
        context = (
            f"You are a friendly Nutritionist AI assistant named 'NutriCoach'. "
            f"The user's profile details are: "
            f"Current Weight: {current_user.weight}kg, "
            f"Height: {current_user.height}cm, "
            f"Goal: {current_user.goal} (Loss/Gain/Maintain), "
            f"Daily Calorie Target: {current_user.daily_calorie_target} kcal, "
            f"Diet Preference: {current_user.activity_level} activity level. "
            f"Answer the user's question briefly (under 100 words) and strictly related to their health data. "
            f"Use emojis to be friendly."
        )

        # 3. AI Model Load Karo
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # 4. Chat Start Karo
        # Pehle hum system context bhejte hain, fir user ka sawal
        chat = model.start_chat(history=[])
        response = chat.send_message(f"System Context: {context}\n\nUser Question: {user_message}")
        
        # 5. Markdown ko HTML mein badlo (Taaki bullet points acche dikhe)
        bot_reply = markdown.markdown(response.text)
        
        return jsonify({'reply': bot_reply})
        
    except Exception as e:
        print(f"AI Error: {e}")
        # Agar API key galat hai ya limit khatam ho gayi to ye error dikhega
        return jsonify({'error': 'AI is currently offline. Please check API Key.'}), 500
    
@app.context_processor
def inject_now():
    return {'now': datetime.now()} # Bracket yahan honge, template mein nahi
app.config.from_object(Config)

# Initialize extensions
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'info'


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# ============================================================================
# DATABASE INITIALIZATION
# ============================================================================

def init_database():
    """Initialize database and load nutrition data"""
    with app.app_context():
        # Create all tables
        db.create_all()
        
        # Load nutrition data if foods table is empty
        if Food.query.count() == 0:
            csv_path = app.config['NUTRITION_CSV_PATH']
            if os.path.exists(csv_path):
                count, error = load_nutrition_data(csv_path)
                if error:
                    print(f"Error loading nutrition data: {error}")
                else:
                    print(f"Loaded {count} foods into database")
            else:
                print(f"Warning: Nutrition CSV not found at {csv_path}")
                # Create sample data for demo
                create_sample_foods()


def create_sample_foods():
    """Create sample food database if CSV doesn't exist"""
    sample_foods = [
        # Indian Foods
        {'name': 'Chapati (Wheat)', 'calories': 297, 'protein': 11.0, 'carbs': 54.0, 'fat': 4.0, 'category': 'Indian'},
        {'name': 'White Rice (Cooked)', 'calories': 130, 'protein': 2.7, 'carbs': 28.0, 'fat': 0.3, 'category': 'Indian'},
        {'name': 'Dal (Cooked)', 'calories': 116, 'protein': 9.0, 'carbs': 20.0, 'fat': 0.4, 'category': 'Indian'},
        {'name': 'Paneer', 'calories': 265, 'protein': 18.3, 'carbs': 1.2, 'fat': 20.8, 'category': 'Indian'},
        {'name': 'Chicken Curry', 'calories': 180, 'protein': 22.0, 'carbs': 8.0, 'fat': 7.0, 'category': 'Indian'},
        {'name': 'Aloo Sabzi', 'calories': 89, 'protein': 2.0, 'carbs': 18.0, 'fat': 1.5, 'category': 'Indian'},
        {'name': 'Dosa (Plain)', 'calories': 168, 'protein': 3.6, 'carbs': 24.0, 'fat': 6.0, 'category': 'Indian'},
        {'name': 'Idli', 'calories': 58, 'protein': 2.0, 'carbs': 11.0, 'fat': 0.5, 'category': 'Indian'},
        {'name': 'Samosa', 'calories': 262, 'protein': 5.0, 'carbs': 28.0, 'fat': 14.0, 'category': 'Indian'},
        
        # Proteins
        {'name': 'Chicken Breast', 'calories': 165, 'protein': 31.0, 'carbs': 0.0, 'fat': 3.6, 'category': 'Protein'},
        {'name': 'Egg (Whole)', 'calories': 155, 'protein': 13.0, 'carbs': 1.1, 'fat': 11.0, 'category': 'Protein'},
        {'name': 'Greek Yogurt', 'calories': 59, 'protein': 10.0, 'carbs': 3.6, 'fat': 0.4, 'category': 'Protein'},
        {'name': 'Tuna', 'calories': 132, 'protein': 28.0, 'carbs': 0.0, 'fat': 1.3, 'category': 'Protein'},
        {'name': 'Tofu', 'calories': 76, 'protein': 8.0, 'carbs': 1.9, 'fat': 4.8, 'category': 'Protein'},
        
        # Carbs
        {'name': 'Brown Rice (Cooked)', 'calories': 111, 'protein': 2.6, 'carbs': 23.0, 'fat': 0.9, 'category': 'Carbs'},
        {'name': 'Oats', 'calories': 389, 'protein': 16.9, 'carbs': 66.3, 'fat': 6.9, 'category': 'Carbs'},
        {'name': 'Sweet Potato', 'calories': 86, 'protein': 1.6, 'carbs': 20.0, 'fat': 0.1, 'category': 'Carbs'},
        {'name': 'Quinoa (Cooked)', 'calories': 120, 'protein': 4.4, 'carbs': 21.3, 'fat': 1.9, 'category': 'Carbs'},
        {'name': 'Whole Wheat Bread', 'calories': 247, 'protein': 13.0, 'carbs': 41.0, 'fat': 3.4, 'category': 'Carbs'},
        
        # Vegetables
        {'name': 'Broccoli', 'calories': 34, 'protein': 2.8, 'carbs': 7.0, 'fat': 0.4, 'category': 'Vegetables'},
        {'name': 'Spinach', 'calories': 23, 'protein': 2.9, 'carbs': 3.6, 'fat': 0.4, 'category': 'Vegetables'},
        {'name': 'Tomato', 'calories': 18, 'protein': 0.9, 'carbs': 3.9, 'fat': 0.2, 'category': 'Vegetables'},
        {'name': 'Carrot', 'calories': 41, 'protein': 0.9, 'carbs': 10.0, 'fat': 0.2, 'category': 'Vegetables'},
        
        # Fruits
        {'name': 'Banana', 'calories': 89, 'protein': 1.1, 'carbs': 23.0, 'fat': 0.3, 'category': 'Fruits'},
        {'name': 'Apple', 'calories': 52, 'protein': 0.3, 'carbs': 14.0, 'fat': 0.2, 'category': 'Fruits'},
        {'name': 'Orange', 'calories': 47, 'protein': 0.9, 'carbs': 12.0, 'fat': 0.1, 'category': 'Fruits'},
        {'name': 'Mango', 'calories': 60, 'protein': 0.8, 'carbs': 15.0, 'fat': 0.4, 'category': 'Fruits'},
        
        # Snacks
        {'name': 'Almonds', 'calories': 579, 'protein': 21.0, 'carbs': 22.0, 'fat': 50.0, 'category': 'Snacks'},
        {'name': 'Peanut Butter', 'calories': 588, 'protein': 25.0, 'carbs': 20.0, 'fat': 50.0, 'category': 'Snacks'},
        {'name': 'Dark Chocolate', 'calories': 546, 'protein': 4.9, 'carbs': 61.0, 'fat': 31.0, 'category': 'Snacks'},
    ]
    
    for food_data in sample_foods:
        food = Food(**food_data)
        db.session.add(food)
    
    db.session.commit()
    print(f"Created {len(sample_foods)} sample foods")


# ============================================================================
# AUTHENTICATION ROUTES
# ============================================================================

@app.route('/')
def index():
    """Landing page - redirect to dashboard or login"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        # Validation
        if not all([email, username, password]):
            flash('All fields are required', 'danger')
            return render_template('register.html')
        
        if password != confirm_password:
            flash('Passwords do not match', 'danger')
            return render_template('register.html')
        
        if len(password) < 6:
            flash('Password must be at least 6 characters', 'danger')
            return render_template('register.html')
        
        # Check if user exists
        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'danger')
            return render_template('register.html')
        
        if User.query.filter_by(username=username).first():
            flash('Username already taken', 'danger')
            return render_template('register.html')
        
        # Create new user
        user = User(email=email, username=username)
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        remember = request.form.get('remember', False)
        
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            login_user(user, remember=remember)
            user.last_login = datetime.utcnow()
            db.session.commit()
            
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password', 'danger')
    
    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    """User logout"""
    logout_user()
    flash('You have been logged out', 'info')
    return redirect(url_for('login'))


# ============================================================================
# MAIN DASHBOARD
# ============================================================================

@app.route('/dashboard')
@login_required
def dashboard():
    """Main nutrition tracking dashboard"""
    # Update streak
    current_user.update_streak()
    db.session.commit()
    
    # Get today's data
    today_summary = get_daily_summary(current_user.id)
    meal_breakdown = get_meal_breakdown(current_user.id)
    weekly_data = get_weekly_data(current_user.id)
    recent_foods = get_recent_foods(current_user.id)
    
    # Get today's logs grouped by meal
    today_start = datetime.combine(date.today(), datetime.min.time())
    today_end = datetime.combine(date.today(), datetime.max.time())
    
    logs = FoodLog.query.filter(
        FoodLog.user_id == current_user.id,
        FoodLog.logged_at >= today_start,
        FoodLog.logged_at <= today_end
    ).order_by(FoodLog.logged_at.desc()).all()
    
    # Group by meal type
    meals = {
        'breakfast': [],
        'lunch': [],
        'dinner': [],
        'snack': []
    }
    for log in logs:
        meals[log.meal_type].append(log)
    
    # Calculate remaining calories
    remaining_calories = current_user.daily_calorie_target - today_summary['calories']
    calories_percentage = min(100, (today_summary['calories'] / current_user.daily_calorie_target) * 100) if current_user.daily_calorie_target > 0 else 0
    
    # Macro percentages
    protein_percentage = min(100, (today_summary['protein'] / current_user.protein_target) * 100) if current_user.protein_target > 0 else 0
    carbs_percentage = min(100, (today_summary['carbs'] / current_user.carbs_target) * 100) if current_user.carbs_target > 0 else 0
    fat_percentage = min(100, (today_summary['fat'] / current_user.fat_target) * 100) if current_user.fat_target > 0 else 0
    
    # Streak badge
    streak_emoji, streak_text = get_streak_badge(current_user.current_streak)
    
    # Favorites
    favorites = [fav.food for fav in current_user.favorites.all()]
    
    return render_template('dashboard.html',
        today_summary=today_summary,
        meal_breakdown=meal_breakdown,
        weekly_data=weekly_data,
        recent_foods=recent_foods,
        meals=meals,
        remaining_calories=remaining_calories,
        calories_percentage=calories_percentage,
        protein_percentage=protein_percentage,
        carbs_percentage=carbs_percentage,
        fat_percentage=fat_percentage,
        streak_emoji=streak_emoji,
        streak_text=streak_text,
        favorites=favorites
    )


# ============================================================================
# PROFILE & SETTINGS
# ============================================================================

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """User profile and goal settings"""
    if request.method == 'POST':
        # Update profile data
        current_user.age = int(request.form.get('age', 25))
        current_user.gender = request.form.get('gender', 'male')
        current_user.weight = float(request.form.get('weight', 70))
        current_user.height = float(request.form.get('height', 170))
        current_user.activity_level = request.form.get('activity_level', 'moderate')
        current_user.goal = request.form.get('goal', 'maintain')
        
        # Recalculate targets
        current_user.calculate_targets()
        
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('profile'))
    
    return render_template('profile.html')


# ============================================================================
# FOOD LOGGING API
# ============================================================================

@app.route('/api/search-food')
@login_required
def search_food():
    """Search food database"""
    query = request.args.get('q', '').strip()
    
    if len(query) < 2:
        return jsonify([])
    
    # Search by name (case-insensitive)
    foods = Food.query.filter(
        Food.name.ilike(f'%{query}%')
    ).limit(20).all()
    
    results = [{
        'id': food.id,
        'name': food.name,
        'calories': food.calories,
        'protein': food.protein,
        'carbs': food.carbs,
        'fat': food.fat
    } for food in foods]
    
    return jsonify(results)


@app.route('/api/log-food', methods=['POST'])
@login_required
def log_food():
    """Log food entry with smart unit conversion"""
    data = request.get_json()
    
    food_id = data.get('food_id')
    raw_quantity = float(data.get('quantity', 100))
    unit = data.get('unit', 'g') # Frontend se unit receive karna
    meal_type = data.get('meal_type', 'snack')
    
    # Validation
    if not food_id or raw_quantity <= 0:
        return jsonify({'success': False, 'error': 'Invalid input'}), 400
    
    food = Food.query.get(food_id)
    if not food:
        return jsonify({'success': False, 'error': 'Food not found'}), 404

    # --- NEW CONVERSION LOGIC BLOCK ---
    multiplier = 1.0
    if unit == 'bowl': multiplier = 180.0  # 1 bowl approx 180g
    elif unit == 'cup': multiplier = 240.0 # 1 cup approx 240g
    elif unit == 'pc': multiplier = 60.0   # 1 piece approx 60g
    
    # Final quantity for database calculation
    final_quantity = raw_quantity * (multiplier if unit not in ['g', 'ml'] else 1.0)
    # ----------------------------------

    try:
        # Humne upar 'food' object pehle hi fetch kiya hai (Line 273 par)
        # Usi object ko direct pass karein taaki relationship turant available ho
        log = FoodLog(
            user_id=current_user.id,
            food=food,  # <--- CHANGE: 'food_id' ki jagah 'food' object pass karein
            quantity=final_quantity, 
            meal_type=meal_type,
            logged_at=datetime.now()
        )
        
        # Ab kyunki humne 'food' object pass kiya hai, ye function sahi chalega
        log.calculate_nutrition() 
        
        db.session.add(log)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'log': {'id': log.id, 'food_name': food.name, 'calories': log.calories}
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/delete-log/<int:log_id>', methods=['DELETE'])
@login_required
def delete_log(log_id):
    """Delete food log entry"""
    log = FoodLog.query.get(log_id)
    
    if not log or log.user_id != current_user.id:
        return jsonify({'success': False, 'error': 'Not found'}), 404
    
    db.session.delete(log)
    db.session.commit()
    
    return jsonify({'success': True})


@app.route('/api/toggle-favorite/<int:food_id>', methods=['POST'])
@login_required
def toggle_favorite(food_id):
    """Add or remove food from favorites"""
    food = Food.query.get(food_id)
    if not food:
        return jsonify({'success': False, 'error': 'Food not found'}), 404
    
    # Check if already favorite
    favorite = FavoriteFood.query.filter_by(
        user_id=current_user.id,
        food_id=food_id
    ).first()
    
    if favorite:
        # Remove favorite
        db.session.delete(favorite)
        db.session.commit()
        return jsonify({'success': True, 'action': 'removed'})
    else:
        # Add favorite
        favorite = FavoriteFood(user_id=current_user.id, food_id=food_id)
        db.session.add(favorite)
        db.session.commit()
        return jsonify({'success': True, 'action': 'added'})


# ============================================================================
# DATA EXPORT
# ============================================================================

@app.route('/export-csv')
@login_required
def export_csv():
    """Export food diary as CSV"""
    days = request.args.get('days', 30, type=int)
    
    df = export_food_diary_csv(current_user.id, days)
    
    # Create CSV in memory
    output = BytesIO()
    df.to_csv(output, index=False, encoding='utf-8')
    output.seek(0)
    
    filename = f'nutritrack_export_{datetime.now().strftime("%Y%m%d")}.csv'
    
    return send_file(
        output,
        output_name=filename,
        mimetype='text/csv',
        as_attachment=True
    )


# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500


# ============================================================================
# APPLICATION ENTRY POINT
# ============================================================================

if __name__ == '__main__':
    init_database()

    app.run(debug=True, host='0.0.0.0', port=5000)
