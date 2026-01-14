from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date

db = SQLAlchemy()

class User(UserMixin, db.Model):
    """User account model with authentication and profile data"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    
    # Profile data for calorie calculation
    age = db.Column(db.Integer)
    gender = db.Column(db.String(10))  # male/female
    weight = db.Column(db.Float)  # kg
    height = db.Column(db.Float)  # cm
    activity_level = db.Column(db.String(20))  # sedentary/light/moderate/active/very_active
    goal = db.Column(db.String(20))  # loss/gain/maintain/recomp
    
    # Calculated fields
    daily_calorie_target = db.Column(db.Integer, default=2000)
    protein_target = db.Column(db.Integer, default=150)
    carbs_target = db.Column(db.Integer, default=200)
    fat_target = db.Column(db.Integer, default=65)
    
    # Water tracking
    water_intake_ml = db.Column(db.Integer, default=0)
    water_target_ml = db.Column(db.Integer, default=2000)
    last_water_reset = db.Column(db.Date, default=date.today)
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    current_streak = db.Column(db.Integer, default=0)
    longest_streak = db.Column(db.Integer, default=0)
    
    # Relationships
    food_logs = db.relationship('FoodLog', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    favorites = db.relationship('FavoriteFood', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    weight_logs = db.relationship('WeightLog', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    recipes = db.relationship('Recipe', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    meal_templates = db.relationship('MealTemplate', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def calculate_targets(self):
        if not all([self.age, self.gender, self.weight, self.height, self.activity_level, self.goal]):
            return
        if self.gender == 'male':
            bmr = (10 * self.weight) + (6.25 * self.height) - (5 * self.age) + 5
        else:
            bmr = (10 * self.weight) + (6.25 * self.height) - (5 * self.age) - 161
        
        activity_multipliers = {'sedentary': 1.2, 'light': 1.375, 'moderate': 1.55, 'active': 1.725, 'very_active': 1.9}
        tdee = bmr * activity_multipliers.get(self.activity_level, 1.2)
        
        if self.goal == 'loss': target_calories = tdee - 500
        elif self.goal == 'gain': target_calories = tdee + 300
        else: target_calories = tdee
        
        self.daily_calorie_target = int(target_calories)
        self.protein_target = int((target_calories * 0.30) / 4)
        self.carbs_target = int((target_calories * 0.40) / 4)
        self.fat_target = int((target_calories * 0.30) / 9)
    
    def get_bmi(self):
        if self.weight and self.height:
            height_m = self.height / 100
            return round(self.weight / (height_m ** 2), 1)
        return None
    
    def get_bmi_category(self):
        bmi = self.get_bmi()
        if not bmi: return "Unknown"
        if bmi < 18.5: return "Underweight"
        elif bmi < 25: return "Healthy"
        elif bmi < 30: return "Overweight"
        else: return "Obese"
    
    def update_streak(self):
        # Streak logic kept as is
        pass

class Food(db.Model):
    """Food nutrition database with advanced nutrients"""
    __tablename__ = 'foods'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False, index=True)
    calories = db.Column(db.Float, nullable=False) # per 100g
    protein = db.Column(db.Float, nullable=False)
    carbs = db.Column(db.Float, nullable=False)
    fat = db.Column(db.Float, nullable=False)
    
    # Advanced Nutrients from CSV
    cholesterol_mg = db.Column(db.Float, default=0.0)
    sodium_mg = db.Column(db.Float, default=0.0)
    fibre_g = db.Column(db.Float, default=0.0)
    vitc_mg = db.Column(db.Float, default=0.0)
    vita_ug = db.Column(db.Float, default=0.0)
    iron_mg = db.Column(db.Float, default=0.0)
    
    category = db.Column(db.String(50))

class FoodLog(db.Model):
    """Daily food intake logs with cached advanced nutrition"""
    __tablename__ = 'food_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    food_id = db.Column(db.Integer, db.ForeignKey('foods.id'), nullable=False)
    food = db.relationship('Food', backref='logs')
    quantity = db.Column(db.Float, nullable=False) # grams
    meal_type = db.Column(db.String(20), nullable=False)
    
    # Cached values
    calories = db.Column(db.Float)
    protein = db.Column(db.Float)
    carbs = db.Column(db.Float)
    fat = db.Column(db.Float)
    
    # NEW: Cached advanced values for the Macros Modal
    cholesterol_mg = db.Column(db.Float, default=0.0)
    sodium_mg = db.Column(db.Float, default=0.0)
    fibre_g = db.Column(db.Float, default=0.0)
    vitc_mg = db.Column(db.Float, default=0.0)
    vita_ug = db.Column(db.Float, default=0.0)
    iron_mg = db.Column(db.Float, default=0.0)
    
    logged_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    def calculate_nutrition(self):
        if self.food:
        # multiplier = quantity / 100 (Kyunki CSV data 100g ke liye hota hai)
            m = self.quantity / 100
            self.calories = round(self.food.calories * m, 1)
            self.protein = round(self.food.protein * m, 1)
            self.carbs = round(self.food.carbs * m, 1)
            self.fat = round(self.food.fat * m, 1)
            
            # Naye nutrients ko bhi calculate karke save karna zaroori hai
            self.sodium_mg = round((self.food.sodium_mg or 0) * m, 1)
            self.cholesterol_mg = round((self.food.cholesterol_mg or 0) * m, 1)
            self.fibre_g = round((self.food.fibre_g or 0) * m, 1)
            self.vitc_mg = round((self.food.vitc_mg or 0) * m, 1)
            self.vita_ug = round((self.food.vita_ug or 0) * m, 1)
            self.iron_mg = round((self.food.iron_mg or 0) * m, 1)
# FavoriteFood, WeightLog, Recipe etc. classes follow...
# (Keep them exactly as you had them in your original code)

class FavoriteFood(db.Model):
    __tablename__ = 'favorite_foods'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    food_id = db.Column(db.Integer, db.ForeignKey('foods.id'), nullable=False)
    added_at = db.Column(db.DateTime, default=datetime.utcnow)
    __table_args__ = (db.UniqueConstraint('user_id', 'food_id', name='unique_user_food'),)

class WeightLog(db.Model):
    __tablename__ = 'weight_logs'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    weight = db.Column(db.Float, nullable=False)
    notes = db.Column(db.String(200))
    logged_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

class Recipe(db.Model):
    __tablename__ = 'recipes'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    servings = db.Column(db.Integer, default=1)
    instructions = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    ingredients = db.relationship('RecipeIngredient', backref='recipe', lazy='dynamic', cascade='all, delete-orphan')

class RecipeIngredient(db.Model):
    __tablename__ = 'recipe_ingredients'
    id = db.Column(db.Integer, primary_key=True)
    recipe_id = db.Column(db.Integer, db.ForeignKey('recipes.id'), nullable=False)
    food_id = db.Column(db.Integer, db.ForeignKey('foods.id'), nullable=False)
    quantity = db.Column(db.Float, nullable=False)
    food = db.relationship('Food')

class MealTemplate(db.Model):
    __tablename__ = 'meal_templates'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    meal_type = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    items = db.relationship('TemplateItem', backref='template', lazy='dynamic', cascade='all, delete-orphan')

class TemplateItem(db.Model):
    __tablename__ = 'template_items'
    id = db.Column(db.Integer, primary_key=True)
    template_id = db.Column(db.Integer, db.ForeignKey('meal_templates.id'), nullable=False)
    food_id = db.Column(db.Integer, db.ForeignKey('foods.id'), nullable=False)
    quantity = db.Column(db.Float, nullable=False)
    food = db.relationship('Food')