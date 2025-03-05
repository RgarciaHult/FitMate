import os
import sqlite3
import random
import re
from collections import defaultdict
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash

# =============================================================================
# APPLICATION & DATABASE SETUP
# =============================================================================

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # A secure key for sessions
DATABASE = 'database/fitmate.db'

def get_db_connection():
    """
    Ensures the directory for the database exists, then connects to the SQLite DB.
    Uses row_factory for named-column access.
    """
    os.makedirs(os.path.dirname(DATABASE), exist_ok=True)
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def create_tables():
    """
    Creates all necessary tables if they do not exist yet.
    This includes 'users', 'meals', 'favorites', and 'user_meals'.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # Users table to store account credentials and personal info
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            name TEXT,
            lastname TEXT,
            age INTEGER,
            gender TEXT,
            height REAL,
            height_unit TEXT,
            weight REAL,
            weight_unit TEXT,
            dietary_preferences TEXT,
            allergies TEXT
        )
    ''')

    # Meals table to store all meal data (type, categories, instructions, etc.)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS meals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT,
            name TEXT NOT NULL,
            identifier TEXT UNIQUE,
            categories TEXT,
            prep_time INTEGER,
            overnight INTEGER,
            equipment TEXT,
            ingredients TEXT,
            instructions TEXT,
            image TEXT
        )
    ''')

    # Favorites table to link users to their favorite meals
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS favorites (
            user_id INTEGER,
            meal_id INTEGER,
            PRIMARY KEY (user_id, meal_id),
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (meal_id) REFERENCES meals(id)
        )
    ''')

    # User meals table to store the user's assigned meals (plan)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_meals (
            user_id INTEGER,
            day INTEGER,
            meal_type TEXT,
            meal_id INTEGER,
            status TEXT DEFAULT 'pending',
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (meal_id) REFERENCES meals(id)
        )
    ''')
    conn.commit()
    conn.close()

# =============================================================================
# USER & FAVORITES MANAGEMENT
# =============================================================================

def register_user(username, password):
    """
    Inserts a new user into the 'users' table with a hashed password.
    Returns True if successful, False if username already exists.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    hashed_password = generate_password_hash(password)
    try:
        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)",
                       (username, hashed_password))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def verify_user(username, password):
    """
    Checks if the username exists and verifies the hashed password.
    Returns the user row if valid, otherwise None.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    conn.close()
    if user and check_password_hash(user['password'], password):
        return user
    return None

def add_favorite(user_id, meal_id):
    """
    Adds a meal to a user's favorites list in the 'favorites' table.
    Returns True if added, False if duplicate or error.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO favorites (user_id, meal_id) VALUES (?, ?)", (user_id, meal_id))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def remove_favorite(user_id, meal_id):
    """
    Removes a meal from the user's favorites in the 'favorites' table.
    Returns True after the deletion.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM favorites WHERE user_id = ? AND meal_id = ?", (user_id, meal_id))
    conn.commit()
    conn.close()
    return True

@app.route('/add_favorite/<int:meal_id>', methods=['POST'])
def add_favorite_route(meal_id):
    """
    POST route to add a meal to the user's favorites, then redirect to the dashboard.
    """
    if 'user_id' not in session:
        return redirect(url_for('login'))
    success = add_favorite(session['user_id'], meal_id)
    if success:
        flash("Meal added to favorites!")
    else:
        flash("Meal is already in favorites or an error occurred.")
    return redirect(url_for('dashboard'))

# =============================================================================
# MEAL PLAN GENERATION
# =============================================================================

def generate_meal_plan(goals, meals_per_day, duration, user_id):
    """
    Generates a meal plan for the user based on:
      - Chosen goals
      - Meals per day
      - Duration
    Ensures no meal is repeated within the same day, and avoids repeats overall unless forced.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM meals")
    all_meals = cursor.fetchall()
    conn.close()

    def normalize_categories(cat_str):
        if not cat_str:
            return set()
        return {c.strip() for c in cat_str.split(';')}

    goal_set = set(goals)
    possible_meals = []
    for meal in all_meals:
        meal_categories = normalize_categories(meal['categories'])
        # Keep the meal if it intersects with user goals
        if meal_categories & goal_set:
            possible_meals.append(meal)

    # Separate breakfast vs. lunch/dinner
    breakfasts = [m for m in possible_meals if m['type'].lower() == 'breakfast']
    lunch_dinners = [m for m in possible_meals if m['type'].lower() == 'lunch/dinner']

    # Map user's meals-per-day choice to actual slots
    meal_type_map = {
        'Breakfast': ['Breakfast'],
        'Lunch': ['Lunch'],
        'Dinner': ['Dinner'],
        'All 3': ['Breakfast', 'Lunch', 'Dinner'],
        'Breakfast & Lunch': ['Breakfast', 'Lunch'],
        'Breakfast & Dinner': ['Breakfast', 'Dinner'],
        'Lunch & Dinner': ['Lunch', 'Dinner']
    }
    slot_types = meal_type_map.get(meals_per_day, ['Breakfast', 'Lunch', 'Dinner'])

    # Clear existing plan for the user
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM user_meals WHERE user_id = ?", (user_id,))

    used_meals_overall = set()
    for day in range(1, duration + 1):
        used_meals_this_day = set()
        for slot in slot_types:
            subset = breakfasts if slot == 'Breakfast' else lunch_dinners
            day_filtered = [m for m in subset if m['id'] not in used_meals_this_day]
            new_meals = [m for m in day_filtered if m['id'] not in used_meals_overall]

            if new_meals:
                meal = random.choice(new_meals)
            else:
                # If no new meals remain, allow repeats from day_filtered
                if day_filtered:
                    meal = random.choice(day_filtered)
                else:
                    # If no meals are left at all, fail
                    conn.close()
                    return False

            cursor.execute('''
                INSERT INTO user_meals (user_id, day, meal_type, meal_id)
                VALUES (?, ?, ?, ?)
            ''', (user_id, day, slot, meal['id']))

            used_meals_this_day.add(meal['id'])
            used_meals_overall.add(meal['id'])

    conn.commit()
    conn.close()
    return True

# =============================================================================
# RETRIEVING MEAL PLANS
# =============================================================================

def get_user_meal_plan(user_id):
    """
    Retrieves all user meals joined with meal details, sorted by day and meal type.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT um.day, um.meal_type, um.status, m.*
        FROM user_meals um
        JOIN meals m ON um.meal_id = m.id
        WHERE um.user_id = ?
        ORDER BY 
            um.day,
            CASE
                WHEN um.meal_type = 'Breakfast' THEN 1
                WHEN um.meal_type = 'Lunch' THEN 2
                WHEN um.meal_type = 'Dinner' THEN 3
                ELSE 4
            END
    ''', (user_id,))
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_earliest_incomplete_day_meals(user_id):
    """
    Finds the earliest day in the plan that still has a meal 'pending'.
    Returns (day, [meals]) or (None, None) if all are done/skipped.
    """
    user_meals = get_user_meal_plan(user_id)
    days_dict = defaultdict(list)
    for row in user_meals:
        days_dict[row['day']].append(row)
    for day in sorted(days_dict.keys()):
        if any(meal_row['status'] not in ['done', 'skipped'] for meal_row in days_dict[day]):
            return day, days_dict[day]
    return None, None

# =============================================================================
# FLASK ROUTES
# =============================================================================

@app.route('/')
def index():
    """Home page with sign-up/log-in options."""
    return render_template('index.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    """
    Sign-up route. Registers a new user if valid credentials are provided.
    Automatically logs them in and redirects to personal info page.
    """
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        if password != confirm_password:
            flash('Passwords do not match!')
            return redirect(url_for('signup'))
        if register_user(username, password):
            flash('Account created successfully! Please fill in your personal info.')
            user = verify_user(username, password)
            if user:
                session['user_id'] = user['id']
                session['username'] = user['username']
            return redirect(url_for('personal_info'))
        else:
            flash('Username already exists!')
            return redirect(url_for('signup'))
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    Login route. Verifies user credentials and redirects to dashboard if valid.
    """
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = verify_user(username, password)
        if user:
            session['user_id'] = user['id']
            session['username'] = user['username']
            flash('Logged in successfully!')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid credentials!')
            return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/personal_info', methods=['GET', 'POST'])
def personal_info():
    """
    Form for user to enter/update personal details (name, age, height, weight, allergies).
    """
    if 'user_id' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        name = request.form['name']
        lastname = request.form['lastname']
        age = request.form['age']
        gender = request.form['gender']
        height = request.form['height']
        height_unit = request.form['height_unit']
        weight = request.form['weight']
        weight_unit = request.form['weight_unit']
        dietary_preferences = request.form.get('dietary_preferences', '')
        allergies = request.form.get('allergies', '')
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE users
            SET name = ?, lastname = ?, age = ?, gender = ?, height = ?, height_unit = ?,
                weight = ?, weight_unit = ?, dietary_preferences = ?, allergies = ?
            WHERE id = ?
        ''', (name, lastname, age, gender, height, height_unit,
              weight, weight_unit, dietary_preferences, allergies, session['user_id']))
        conn.commit()
        conn.close()
        flash('Personal information updated!')
        return redirect(url_for('dashboard'))
    return render_template('personal_info.html')

@app.route('/my_account', methods=['GET', 'POST'])
def my_account():
    """
    Displays and updates the user's account info if they are logged in.
    """
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = get_db_connection()
    cursor = conn.cursor()
    if request.method == 'POST':
        name = request.form['name']
        lastname = request.form['lastname']
        age = request.form['age']
        gender = request.form['gender']
        height = request.form['height']
        height_unit = request.form['height_unit']
        weight = request.form['weight']
        weight_unit = request.form['weight_unit']
        dietary_preferences = request.form.get('dietary_preferences', '')
        allergies = request.form.get('allergies', '')
        cursor.execute('''
            UPDATE users
            SET name = ?, lastname = ?, age = ?, gender = ?, height = ?, height_unit = ?,
                weight = ?, weight_unit = ?, dietary_preferences = ?, allergies = ?
            WHERE id = ?
        ''', (name, lastname, age, gender, height, height_unit,
              weight, weight_unit, dietary_preferences, allergies, session['user_id']))
        conn.commit()
        flash('Changes saved!')
        return redirect(url_for('my_account'))
    else:
        cursor.execute("SELECT * FROM users WHERE id = ?", (session['user_id'],))
        user = cursor.fetchone()
        conn.close()
        return render_template('my_account.html', user=user)

@app.route('/meal_plan', methods=['GET', 'POST'])
def meal_plan():
    """
    Page where user selects a goal, number of meals per day, and plan duration.
    Generates a new meal plan on submission.
    """
    if 'user_id' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        goal = request.form.get('goal')
        if not goal:
            flash("Please select a goal.")
            return redirect(url_for('meal_plan'))
        goals = [goal]
        meals_per_day = request.form.get('meals_per_day')
        duration = int(request.form.get('duration', 1))
        success = generate_meal_plan(goals, meals_per_day, duration, session['user_id'])
        if not success:
            flash('Not enough meals in the database to satisfy your plan.')
            return redirect(url_for('meal_plan'))
        return redirect(url_for('review_meal_plan'))
    return render_template('meal_plan.html')

@app.route('/review_meal_plan', methods=['GET', 'POST'])
def review_meal_plan():
    """
    Shows the newly generated meal plan in a table for final review.
    Users can confirm or return to change meals.
    """
    if 'user_id' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        flash('Meal plan confirmed!')
        return redirect(url_for('dashboard'))
    user_meals = get_user_meal_plan(session['user_id'])
    days_map = defaultdict(list)
    for row in user_meals:
        days_map[row['day']].append(row)
    days_map = dict(days_map)
    return render_template('review_meal_plan.html', days_map=days_map)

@app.route('/dashboard')
def dashboard():
    """
    Shows the earliest incomplete day in the user's plan.
    Each meal card can be done, skipped, or favorited on hover.
    """
    if 'user_id' not in session:
        return redirect(url_for('login'))
    day, day_meals = get_earliest_incomplete_day_meals(session['user_id'])
    if day is None:
        return render_template('dashboard_completed.html')
    return render_template('dashboard.html', day=day, day_meals=day_meals)

@app.route('/meal_details/<int:meal_id>')
def meal_details(meal_id):
    """
    Provides detailed instructions, ingredients, and equipment for a specific meal.
    """
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM meals WHERE id = ?", (meal_id,))
    meal_row = cursor.fetchone()
    conn.close()
    if not meal_row:
        flash("Meal not found.")
        return redirect(url_for('dashboard'))
    meal = dict(meal_row)

    # Clean up instructions
    raw_instructions = meal.get('instructions', '') or ''
    raw_instructions = raw_instructions.replace('\n', '. ')
    steps_raw = [s.strip() for s in raw_instructions.split('.') if s.strip()]
    cleaned_steps = []
    for step in steps_raw:
        step = re.sub(r'^[\d\(\)]+\.?\s*', '', step)
        if not step or re.match(r'^\d+$', step):
            continue
        step = step[0].upper() + step[1:] if len(step) > 1 else step.upper()
        cleaned_steps.append(step)
    meal['instructions_list'] = cleaned_steps

    # Clean up ingredients
    raw_ingredients = meal.get('ingredients', '') or ''
    ingredients_raw = [i.strip() for i in raw_ingredients.split(';') if i.strip()]
    cleaned_ingredients = []
    for ing in ingredients_raw:
        ing = re.sub(r'\(.*?\)', '', ing)
        ing = ing.strip()
        if ing:
            ing = ing[0].upper() + ing[1:]
            cleaned_ingredients.append(ing)
    meal['ingredients_list'] = cleaned_ingredients

    # Clean up equipment
    raw_equipment = meal.get('equipment', '') or ''
    equipment_raw = [e.strip() for e in raw_equipment.split(',') if e.strip()]
    cleaned_equipment = []
    for eq in equipment_raw:
        eq = re.sub(r'\(.*?\)', '', eq)
        eq = eq.strip()
        if eq:
            eq = eq[0].upper() + eq[1:]
            cleaned_equipment.append(eq)
    meal['equipment_list'] = cleaned_equipment

    return render_template('meal_details.html', meal=meal)

@app.route('/skip_meal/<int:meal_id>/<int:day>/<string:meal_type>', methods=['POST'])
def skip_meal(meal_id, day, meal_type):
    """
    Marks a meal as 'skipped' for a given user, day, and meal type.
    """
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE user_meals
        SET status = 'skipped'
        WHERE meal_id = ? AND user_id = ? AND day = ? AND meal_type = ?
    ''', (meal_id, session['user_id'], day, meal_type))
    conn.commit()
    conn.close()
    return redirect(url_for('dashboard'))

@app.route('/done_meal/<int:meal_id>/<int:day>/<string:meal_type>', methods=['POST'])
def done_meal(meal_id, day, meal_type):
    """
    Marks a meal as 'done' for a given user, day, and meal type.
    """
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE user_meals
        SET status = 'done'
        WHERE meal_id = ? AND user_id = ? AND day = ? AND meal_type = ?
    ''', (meal_id, session['user_id'], day, meal_type))
    conn.commit()
    conn.close()
    return redirect(url_for('dashboard'))

@app.route('/change_meal/<int:day>/<string:meal_type>', methods=['GET', 'POST'])
def change_meal(day, meal_type):
    """
    A two-step route allowing users to pick a category, then pick a meal
    from that category to update their meal plan for a given day and meal type.
    """
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT um.*, m.name AS old_meal_name
        FROM user_meals um
        JOIN meals m ON um.meal_id = m.id
        WHERE um.user_id = ? AND um.day = ? AND um.meal_type = ?
    ''', (user_id, day, meal_type))
    current_record = cursor.fetchone()
    conn.close()

    if not current_record:
        flash("No meal found for that day/slot.")
        return redirect(url_for('review_meal_plan'))

    if request.method == 'POST':
        step = request.form.get('step')
        if step == 'pick_category':
            chosen_category = request.form.get('chosen_category')
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM meals")
            all_meals = cursor.fetchall()
            conn.close()

            def normalize_cat_str(cat_str):
                if not cat_str:
                    return set()
                return {c.strip().lower().replace(' ', '_') for c in cat_str.split(';') if c.strip()}

            possible_meals = []
            for m in all_meals:
                cat_set = normalize_cat_str(m['categories'])
                if chosen_category in cat_set:
                    possible_meals.append(m)

            return render_template('change_meal_pick_meal.html',
                                   day=day,
                                   meal_type=meal_type,
                                   current_record=current_record,
                                   chosen_category=chosen_category,
                                   possible_meals=possible_meals)
        elif step == 'update_meal':
            new_meal_id = request.form.get('new_meal_id')
            if not new_meal_id:
                flash("Please select a meal.")
                return redirect(url_for('change_meal', day=day, meal_type=meal_type))
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE user_meals
                SET meal_id = ?
                WHERE user_id = ? AND day = ? AND meal_type = ?
            ''', (new_meal_id, user_id, day, meal_type))
            conn.commit()
            conn.close()
            flash("Meal updated successfully!")
            return redirect(url_for('review_meal_plan'))

    return render_template('change_meal_pick_category.html',
                           day=day,
                           meal_type=meal_type,
                           current_record=current_record)

@app.route('/favorites')
def favorites():
    """
    Displays a list of meals the user has marked as favorites.
    """
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT m.* FROM meals m
        JOIN favorites f ON m.id = f.meal_id
        WHERE f.user_id = ?
    ''', (session['user_id'],))
    fav_meals = cursor.fetchall()
    conn.close()
    return render_template('favorites.html', meals=fav_meals)

@app.route('/logout')
def logout():
    """
    Logs out the user by clearing the session data and redirects to the home page.
    """
    session.clear()
    flash('Logged out successfully!')
    return redirect(url_for('index'))

# =============================================================================
# APPLICATION ENTRY POINT
# =============================================================================
def main():
    """
    Main entry point to create tables and run the Flask development server.
    """
    create_tables()
    app.run(debug=True)

if __name__ == '__main__':
    main()