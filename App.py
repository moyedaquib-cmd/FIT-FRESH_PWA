import os #Lets python interact with the computer's operating system
import re #Regular expression module lets Python search, match and manipuate text using advanced patterns.
from flask import Flask, request, redirect, url_for, render_template, session, flash, send_from_directory #Essential components of the Flask framework to handle web routing, user sessions, page rendering, HTML forms and file serving
from DB_Models import get_db, init_db #Imports two functions from DB_Models.py to initialise the database structure and manage active database connections.
from datetime import datetime, timedelta #Tools for handling exact calendar dates, specific times and calculating time differences
from werkzeug.security import generate_password_hash, check_password_hash #Imports security functions to securely encrypt passwords and verify user logins against the stored hashed
import pytz #Allows Python to accurately work with cross-platform timezone calculations and conversions
app = Flask(__name__) #Initialises a new Flask web application
app.config["SECRET_KEY"] = "oJvneTznic84TgELjsKA" #Signs the session cookies so its contents can't be forged

#Jinja template filter to format numeric values inside HTML files
@app.template_filter("fmt_num")
def fmt_num(value):
    try: 
        f = round(float(value), 2) #Converts the input into a decimal number rounded to two decimal places
        if f == int(f): #Returns the value as a clean integer string if it has no decimals
            return str(int(f))
        return f'{f:.2f}'.rstrip("0") #Returns a decimal string with trailing zeros removed from the second decimal place
    except: #Returns to original unchanged value if any step causes an error
        return value

#Coverts UTC timestamp string into Sydney local time
def local_time(utc_dt_str):
    local_tz = pytz.timezone("Australia/Sydney") #Sets the local time zone to Australia/Sydney
    utc_dt = datetime.strptime(utc_dt_str, "%Y-%m-%d %H:%M:%S") #Converts the raw input text string into a native Python datetime object
    return utc_dt.replace(tzinfo=pytz.utc).astimezone(local_tz) #Tags the datetime as UTC and shifts it to the corresponding Sydney time zone

#Validates whether a string is either empty or a valid web link
def is_valid_image_url(url):
    if not url or url.strip() == "": #Returns true if the image link is entirely missing, blank, or consists only of whitespace
        return True
    return url.strip().startswith("http") #Returns true if the cleaned text link begins with standard web protocol prefixes

#The home page for the PWA
@app.route("/") 
def home():
    return render_template("home.html") #Renders and sends the HTML file to the user's browser

#Registration page
@app.route("/register", methods=["GET", "POST"]) 
def register_page():
    if request.method == "GET":
        return render_template("register.html") #Displays the registration page
    
    #Extracts the submitted credentials and account role from the incoming form data
    username = request.form.get("username") 
    password = request.form.get("password")
    role = request.form.get("role")

    #Rejects the registration with an error if any required form input is missing
    if not username or not password or not role:
        return "Please fill in all the fields", 400
    
    #Enforces that the usernames must be a reasonable length for system display and storage
    if len(username) <3 or len(username) > 50: 
        flash("Username must be between 3 and 50 characters")
        return redirect(url_for("register_page"))
    
    #Uses a regular expression to restrict usernames to safe, alphanumeric characters and underscores
    if not re.match(r"^[a-zA-Z0-9_]+$", username):
        flash("Username can only contain letters, numbers and underscores")
        return redirect(url_for("register_page"))
    
    #Enforces a minimum password length requirement to ensure basic account security
    if len(password) < 6: 
        flash("Password must be at least 6 characters")
        return redirect(url_for("register_page"))
    
    #Opens a connection to the database 
    conn = get_db() 
    cursor = conn.cursor() 
    existing_user = cursor.execute("SELECT id FROM user WHERE username = ?", (username,)).fetchone() #Searches the database to verify if the requested username is already taken
    
    #Aborts registration and alerts the user if the username is already registered
    if existing_user:
        conn.close() 
        flash("Username already exists") 
        return redirect(url_for("register_page"))
    hashed_password = generate_password_hash(password) #Securely hashes the plain text password before saving it to protect user data
    cursor.execute("INSERT INTO user (username, password_hash, role) VALUES (?, ?, ?)", (username, hashed_password, role)) 
    
    #Saves the database changes permanently and closes the active network connection
    conn.commit()
    conn.close()
    
    # Notifies the user of success and sends them to the login page to sign in
    flash("Account created successfully. Please log in") 
    return redirect(url_for("login"))

#Login page
@app.route("/login", methods=["POST", "GET"])
def login(): 
    if request.method == "GET": 
        return render_template("login.html") #Displays the login page
    
    #Extracts the submitted credentials from the incoming form data
    username = request.form.get("username")
    password = request.form.get("password")
    
    #Rejects the authentication request if any fields are left blank
    if not username or not password:
        return "Please fill in all the fields", 400 
    
    #Establishes a connection to the database to find the user record
    conn = get_db() 
    user = conn.execute("SELECT * FROM user WHERE username = ?", (username,)).fetchone() 
    
    #Triggers a generic error message if the username is not found
    if not user: 
        conn.close()
        flash("Invalid username or password") 
        return redirect(url_for("login")) 
    
    #Configures the maximum allowed consecutive login failures and the lockout duration
    LOCK_THRESHOLD = 5
    LOCK_MINUTES = 15
    current_attempts = user["failed_attempts"]
    if user["locked_until"]: #Checks if the user account currently has an active lockout time restriction set
        locked_until = datetime.strptime(user["locked_until"], "%Y-%m-%d %H:%M:%S")
        
        #Enforces the lockout and denies access if the current time is before the unlock time
        if datetime.now() < locked_until:
            conn.close()
            flash("Account locked due to too many failed attempts. Please try again later.")
            return redirect(url_for("login"))
        
        #Resets the lockout restrictions in the database if the lock time has safely expired
        else:
            conn.execute("UPDATE user SET failed_attempts = 0, locked_until = NULL WHERE id = ?", (user["id"],))
            conn.commit()
            current_attempts = 0
    
    #Verifies the submitted password against the securely encrypted hash from the database
    if not check_password_hash(user["password_hash"], password): 
        new_attempts = current_attempts + 1 
        
        #Triggers a formal lockout if the user reaches the maximum allowed of failed attempts
        if new_attempts >= LOCK_THRESHOLD:
            lock_time = (datetime.now() + timedelta(minutes=LOCK_MINUTES)).strftime("%Y-%m-%d %H:%M:%S") 
            conn.execute("UPDATE user SET failed_attempts = ?, locked_until = ? WHERE id = ?", (new_attempts, lock_time, user["id"]))
            conn.commit()
            conn.close()
            flash("Account locked due to too many failed attempts. Please try again in 15 minutes.")
            return redirect(url_for("login"))
        
         #Updates the failed attempts counter and warns the user of remaining chances
        else: 
            conn.execute("UPDATE user SET failed_attempts = ? WHERE id = ?", (new_attempts, user["id"]))
            conn.commit()
            conn.close()
            attempts_left = LOCK_THRESHOLD - new_attempts 
            flash(f"Invalid username or password. {attempts_left} attempt(s) remaining before lockout.")
            return redirect(url_for("login"))
    
    #Resets all tracking metrics back to zero upon a fully successful password match
    conn.execute("UPDATE user SET failed_attempts = 0, locked_until = NULL WHERE id = ?", (user["id"],))
    conn.commit()
    conn.close()

    #Stores the authenticated user's profile details securely within the browser session
    session["user_id"] = user["id"]
    session["role"] = user["role"]
    session["username"] = user["username"] 
    
    #Directs users to their specific dashboard
    if user["role"] == "gym_goer": 
        flash("Logged in successfully") 
        return redirect(url_for("gym_goer_dashboard")) 
    else: 
        flash("Logged in successfully") 
        return redirect(url_for("personal_trainer_dashboard")) 

#Gym-goer dashboard
@app.route("/gym-goer-dashboard") 
def gym_goer_dashboard(): 
    if "user_id" not in session: #Redirects users to the home page if they are not logged into an account
        return redirect(url_for("home")) 
    if session.get("role") != "gym_goer": #Rejects the request with a permission error if the logged-in user is not a gym-goer
        return "Only gym goers can access the dashboard", 403 
    return render_template("gym_goer_dashboard.html") 

#Personal trainer dashboard
@app.route("/personal-trainer-dashboard") 
def personal_trainer_dashboard():  
    if "user_id" not in session: #Redirects users to the home page if they are not logged into an account
        return redirect(url_for("home")) 
    if session.get("role") == "gym_goer": #Rejects the request with a permission error if the logged-in user is a gym-goer
        return "Only personal trainers can access the dashboard", 403 
    return render_template("personal_trainer_dashboard.html") 

#Workout logging page
@app.route("/log-workout", methods=["GET", "POST"]) 
def log_workout(): 
    if "user_id" not in session: #Redirects users to the home page if they are not logged into an account
        return redirect(url_for("home")) 
    if request.method == "GET":  
        return render_template("log_workout.html") #Renders the workout logging page
    
    #Extracts the submitted input from the form data
    exercise = request.form.get("exercise")
    sets = request.form.get("sets")
    reps = request.form.get("reps")
    weight = request.form.get("weight")

    #Rejects the submission with an error if any required metrics are missing
    if not exercise or not sets or not reps or not weight:
        return "Please fill in all the fields", 400
    
    #Validates that the input is not a negative value
    if int(sets) < 0: 
        return "Sets must be positive", 400
    if int(reps) < 0:
        return "Reps must be positive", 400
    if float(weight) < 0:
        return "Weight must be positive", 400
    
    #Opens a connection to the database and inserts the data directly linked to the logged-in user's profile 
    conn = get_db()
    conn.execute( "INSERT INTO workout (user_id, exercise, sets, reps, weight) VALUES (?, ?, ?, ?, ?)", (session["user_id"], exercise, int(sets), int(reps), float(weight)))
    conn.commit()
    conn.close()
    return redirect(url_for("workout_history")) #Redirects the user to their workout history upon a successful save

#Workout history page
@app.route("/workout-history") 
def workout_history(): 
    if "user_id" not in session: #Redirects users to the home page if they are not logged into an account  
        return redirect(url_for("home")) 
    conn = get_db() #Opens a database connection to query the user's exercise records
    workouts = conn.execute( "SELECT * FROM workout WHERE user_id = ? ORDER BY workout_date DESC, id DESC",(session["user_id"],)).fetchall() #Retrieves all workouts for the logged-in user, sorted by most recent first
    conn.close()
    grouped_workouts = {} #Initializes an empty dictionary to organize raw workout rows by their calendar dates
    
    #Iterates through the fetched logs to categorize each exercise entry under its respective date
    for workout in workouts:
        date_key = workout["workout_date"]
        if date_key not in grouped_workouts:
            grouped_workouts[date_key] = [] 
        grouped_workouts[date_key].append(workout) 
    grouped_list = [] #Initialises an empty list to store the final structured timeline data for the frontend
    
    #Loops through the grouped records to apply human-readable date labels to each section
    for date_key, day_workouts in grouped_workouts.items(): 
        try:
            formatted = datetime.strptime(date_key, "%Y-%m-%d").strftime("%A, %d %B %Y") #Converts the standard date text string into a calendar format
        except (ValueError, TypeError): #Uses the raw, unformatted date text string if parsing fails
            formatted = date_key
        grouped_list.append((date_key, formatted, day_workouts))
    return render_template("workout_history.html", workouts = workouts, grouped_workouts = grouped_list) 

#Calorie tracking page
@app.route("/log-calories", methods = ["GET", "POST"]) 
def log_calories(): 
    if "user_id" not in session: #Redirects users to the home page if they are not logged into an account
        return redirect(url_for("home")) 
    if request.method == "GET": 
        return render_template("log_calories.html") #Renders the calorie tracking page

    #Extracts the submitted input from the form data
    meal = request.form.get("meal")
    calories = request.form.get("calories")
    
    #Rejects the submission with an error if any required metrics are missing
    if not calories or not meal:
        return "Please fill in all the fields", 400
    
    #Validates that the input is not a negative value
    if float(calories) < 0:
        return "Calories must be positive", 400
    
    #Opens a connection to the database and inserts the data directly linked to the logged-in user's profile 
    conn = get_db()
    conn.execute("INSERT INTO calorie_entry (user_id, meal, calories) VALUES (?, ?, ?)", (session["user_id"], meal, float(calories))) 
    conn.commit()
    conn.close()
    return redirect(url_for("calorie_history")) #Redirects the user to their calorie history upon a successful save

#Calorie history page
@app.route("/calorie-history") 
def calorie_history(): 
    if "user_id" not in session: #Redirects users to the home page if they are not logged into an account
        return redirect(url_for("home")) 
    conn = get_db() #Opens a database connection to query the user's exercise records
    entries = conn.execute("SELECT * FROM calorie_entry WHERE user_id = ? ORDER BY entry_date DESC", (session["user_id"],)).fetchall() #Retrieves all workouts for the logged-in user, sorted by most recent first
    conn.close()
    processed_entries = [] #Initialises an empty list to store database records converted into editable Python dictionaries
    
    #Standardizes the timestamps of each calorie entry into local time objects.
    for entry in entries:
        entry_dict = dict(entry) 
        entry_dict["local_time"] = local_time(entry["entry_date"]) #Appends a new key holding the entry's timestamp converted to Sydney local time
        
        #Converts the raw date text string into a native Python datetime object for sorting
        entry_dict["entry_date"] = datetime.strptime(entry["entry_date"], "%Y-%m-%d %H:%M:%S") 
        processed_entries.append(entry_dict)
    grouped_entries = {} #Initialises an empty dictionary to organise the processed meals by their calendar day
    
    #Categorises each meal entry into the dictionary under its respective local date key
    for entry in processed_entries:
        date_key = entry["local_time"].strftime("%Y-%m-%d")
        if date_key not in grouped_entries:
            grouped_entries[date_key] = []
        grouped_entries[date_key].append(entry)
    grouped_list = [] #Initializes an empty list to store the final structured timeline data for the frontend
    
    #Loops through the grouped records to apply human-readable date labels to each section
    for date_key, day_entries in grouped_entries.items():
        try: 
            formatted = datetime.strptime(date_key, "%Y-%m-%d").strftime("%A, %d %B %Y") #Converts the standard date text string into a calendar format
        except (ValueError, TypeError): #Uses the raw, unformatted date text string if parsing fails
            formatted = date_key
        grouped_list.append((date_key, formatted, day_entries))
    return render_template("calorie_tracker.html", entries = processed_entries, grouped_entries = grouped_list)

#Allows users to edit items in their workout history
@app.route("/edit-workout/<int:workout_id>", methods = ["GET", "POST"]) 
def edit_workout(workout_id): 
    if "user_id" not in session: #Redirects users to the home page if they are not logged into an account
        return redirect(url_for("home")) 
    
    #Opens a database connection to query the requested workout record
    conn = get_db()
    workout = conn.execute("SELECT * FROM workout WHERE id = ?", (workout_id,)).fetchone() 
    
    #Triggers an error if the unique workout ID does not exist
    if not workout:
        conn.close()
        return "Workout not found", 404

    #Blocks users from editing workouts that belong to other accounts
    if workout["user_id"] != session["user_id"]:
        conn.close()
        return "Unasuthorised user", 403

    #Renders the edit form populated with the current workout details 
    if request.method == "GET": 
        conn.close()
        return render_template("edit_workout.html", workout = workout)
    
    #Extracts and converts the modified form parameters into their appropriate numeric data types
    exercise = request.form.get("exercise")
    sets = int(request.form.get("sets"))
    reps = int(request.form.get("reps"))
    weight = float(request.form.get("weight"))

    #Updates the database record with the newly submitted exercise metrics
    conn.execute("UPDATE workout SET exercise = ?, sets = ?, reps = ?, weight = ? WHERE id = ?", (exercise, sets, reps, weight, workout_id))
    conn.commit()
    conn.close()

    #Notifies the user of the successful change and returns them to their history log
    flash("Workout Updated") 
    return redirect(url_for("workout_history")) 

#Allows users to delete items in their workout history
@app.route("/delete-workout/<int:workout_id>", methods = ["POST"]) 
def delete_workout(workout_id):
    if "user_id" not in session: #Redirects users to the home page if they are not logged into an account
        return redirect(url_for("home")) 
    
    #Opens a database connection to find the specified workout record
    conn = get_db()
    workout = conn.execute("SELECT * FROM workout WHERE id = ?", (workout_id,)).fetchone() 
    
    #Returns an error if the unique workout ID does not exist
    if not workout:
        conn.close()
        return "Workout not found", 404
    
    #Blocks users from deleting any records that belong to another user
    if workout["user_id"] != session["user_id"]:
        conn.close()
        return "Unauthorised user", 403
    
    #Permanently deletes the workout record matching the ID from the tracking table
    conn.execute("DELETE FROM workout WHERE id = ?", (workout_id,))
    conn.commit() 
    conn.close()

    #Notifies the user of the successful change and returns them to their history log
    flash("Workout Deleted") 
    return redirect(url_for("workout_history")) 

#Allows users to edit items in their calorie history
@app.route("/edit-calories/<int:entry_id>", methods = ["GET", "POST"]) 
def edit_calories(entry_id): 
    if "user_id" not in session: #Redirects users to the home page if they are not logged into an account
        return redirect(url_for("home")) 
    
    #Opens a database connection to query the requested calorie record
    conn = get_db()
    entry = conn.execute("SELECT * FROM calorie_entry WHERE id = ?", (entry_id,)).fetchone() 
    
    #Triggers an error if the unique entry ID does not exist
    if not entry:
        conn.close()
        return "Entry not found", 404
    
    #Blocks users from editing logs that belong to other accounts
    if entry["user_id"] != session["user_id"]:
        conn.close()
        return "Unauthorised user", 403
    
    #Renders the edit form populated with the current meal details 
    if request.method == "GET": 
        conn.close()
        return render_template("edit_calories.html", entry = entry)
    
    #Extracts data from the inputs
    meal = request.form.get("meal") 
    calories = float(request.form.get("calories"))
    
    #Updates the database record with the newly submitted nutritional metrics
    conn.execute("UPDATE calorie_entry SET meal = ?, calories = ? WHERE id = ?", (meal, calories, entry_id)) 
    conn.commit()
    conn.close()
    
    #Notifies the user of the successful change and returns them to their history log
    flash("Calories Updated")
    return redirect(url_for("calorie_history")) 

#Allows users to delete items in their calorie history
@app.route("/delete-calories/<int:entry_id>", methods = ["POST"]) 
def delete_calories(entry_id): 
    if "user_id" not in session: #Redirects users to the home page if they are not logged into an account
        return redirect(url_for("home"))
    
    #Opens a database connection to find the specified calorie record
    conn = get_db()
    entry = conn.execute("SELECT * FROM calorie_entry WHERE id = ?", (entry_id,)).fetchone()
    
    #Returns an error if the unique entry ID does not exist
    if not entry:
        conn.close()
        return "Entry not found", 404
    
    #Blocks users from deleting any records that belong to another user
    if entry["user_id"] != session["user_id"]:
        conn.close()
        return "Unauthorised user", 403
    
    #Permanently deletes the calorie record matching the ID from the tracking table
    conn.execute("DELETE FROM calorie_entry WHERE id = ?", (entry_id,)) 
    conn.commit()
    conn.close()
    
    #Notifies the user of the successful change and returns them to their history log
    flash("Calories Deleted") 
    return redirect(url_for("calorie_history")) 

#Exercise library
@app.route("/exercises") 
def exercises():  
    conn = get_db() #Opens a connection to the database to fetch exercise data
    all_exercises = conn.execute("SELECT exercise.*, user.username as trainer_username FROM exercise JOIN user ON exercise.trainer_id = user.id").fetchall() #Retrieves all exercises while merging user table information to append the creator's username
    conn.close()
    return render_template("exercises.html", exercises = all_exercises) 

#Exercise details page
@app.route("/exercise/<int:exercise_id>") 
def exercise_detail(exercise_id):  
    conn = get_db() #Opens a connection to the database to fetch exercise data
    exercise = conn.execute("SELECT exercise.*, user.username as trainer_username FROM exercise JOIN user ON exercise.trainer_id = user.id WHERE exercise.id = ?", (exercise_id,)).fetchone() #Retrieves the specified exercise details while joining the user table to get the creator's username
    
    #Stops execution and returns a 404 error if the unique exercise ID does not exist in the system
    if not exercise:
        conn.close()
        return "Exercise not found", 404    
    reviews = conn.execute("SELECT review_exercise.*, user.username, user.role FROM review_exercise JOIN user ON review_exercise.user_id = user.id WHERE review_exercise.exercise_id = ?", (exercise_id,)).fetchall() #Retrieves all user reviews and ratings left for this specific exercise
    
    #Checks if the currently logged-in user has added this exercise to their favourites
    if "user_id" in session:
        fav = conn.execute("SELECT id FROM favourite_exercise WHERE user_id = ? AND exercise_id = ?", (session["user_id"], exercise_id)).fetchone()
        is_favourite = fav is not None 
    is_owner = "user_id" in session and exercise["trainer_id"] == session["user_id"] #Verifies if the logged-in user is the specific personal trainer who created this exercise record
    
    #Checks if the logged-in user has already submitted a review
    has_reviewed = False
    if "user_id" in session:
        existing = conn.execute("SELECT id FROM review_exercise WHERE user_id = ? AND exercise_id = ?", (session["user_id"], exercise_id)).fetchone()
        has_reviewed = existing is not None
    conn.close()
    return render_template("exercise_detail.html", exercise = exercise, is_favourite = is_favourite, reviews = reviews, is_owner = is_owner, has_reviewed = has_reviewed) 

#Toggles when an exercise is added to or removed from favourites
@app.route("/toggle-favourite-exercise/<int:exercise_id>", methods = ["POST"]) 
def toggle_favourite_exercise(exercise_id):  
    if "user_id" not in session: #Redirects users to the home page if they are not logged into an account
        return redirect(url_for("home")) 
    conn = get_db() #Opens a database connection to check the user's favorite entries
    favourite = conn.execute("SELECT id FROM favourite_exercise WHERE user_id = ? AND exercise_id = ?", (session["user_id"], exercise_id)).fetchone() #Searches the database to see if the user has already favorited this specific exercise
    
    #Removes the entry from the favorites list
    if favourite:
        conn.execute("DELETE FROM favourite_exercise WHERE id = ?", (favourite["id"],))
        flash("Removed from Favourites")
    
    #Inserts a new favorite entry
    else: 
        conn.execute("INSERT INTO favourite_exercise (user_id, exercise_id) VALUES (?, ?)", (session["user_id"], exercise_id))
        flash("Added to favourites")
    conn.commit()
    conn.close()
    return redirect(url_for("exercise_detail", exercise_id = exercise_id))

#Handles the submission and validation of user reviews for a specific exercise
@app.route("/add-review-exercise/<int:exercise_id>", methods = ["POST"])
def add_review_exercise(exercise_id): 
    if "user_id" not in session: #Redirects users to the home page if they are not logged into an account
        return redirect(url_for("home")) 
    
    #Extracts the rating and review from the form data
    rating = float(request.form.get("rating")) 
    comment = request.form.get("comment")
    
    #Enforces that the numerical rating score falls within the 1-5 range
    if rating < 1 or rating > 5:
        flash("Rating must be between 1 and 5")
        return redirect(url_for("exercise_detail", exercise_id = exercise_id)) 
    
    #Opens a database connection to query the exercise record details
    conn = get_db()
    exercise = conn.execute("SELECT trainer_id FROM exercise WHERE id = ?", (exercise_id,)).fetchone()
    
    #Prevents the creator from reviewing their own content
    if exercise and exercise["trainer_id"] == session["user_id"]:
        conn.close()
        flash("You can't review your own content")
        return redirect(url_for("exercise_detail", exercise_id = exercise_id))
    existing_review = conn.execute("SELECT id FROM review_exercise WHERE user_id = ? AND exercise_id = ?",(session["user_id"], exercise_id)).fetchone() #Searches the database to verify if this user account has already reviewed this particular item
    
    #Restricts users to a maximum of one review per item
    if existing_review:
        conn.close()
        flash("You can't leave more than 1 review")
        return redirect(url_for("exercise_detail", exercise_id = exercise_id)) 
    conn.execute("INSERT INTO review_exercise (user_id, exercise_id, rating, comment) VALUES (?, ?, ?, ?)", (session["user_id"], exercise_id, int(rating), comment)) #Inserts the finalised score and comment text into the database table
    conn.commit()
    conn.close()

    #Informs the user on success and redirects back to the details page
    flash("Review added!") 
    return redirect(url_for("exercise_detail", exercise_id = exercise_id)) 

#Allows trainers to add exercises to the exercise library
@app.route("/add-exercise", methods = ["GET", "POST"]) 
def add_exercise(): 
    #Blocks unauthenticated visitors and gym-goers from using trainer-only content tools
    if "user_id" not in session or session.get("role") == "gym_goer": 
        flash("Access denied!") 
        return redirect(url_for("home")) 
    
    #Processes the incoming form data when a trainer submits a new exercise record and extracts the inputs
    if request.method == "POST":  
        name = request.form["name"]
        description = request.form["description"]
        muscle_group = request.form["muscle_group"]
        image_url = request.form.get("image_url")
        difficulty = request.form["difficulty"]
        
        #Server-side image URL validation
        if not is_valid_image_url(image_url):
            flash("Image URL must start with http")
            return redirect(url_for("add_content")) 
        
        #Inserts the completed exercise catalogue into database
        conn = get_db()
        conn.execute("INSERT INTO exercise (name, description, muscle_group, difficulty, image_url, trainer_id) VALUES (?, ?, ?, ?, ?, ?)", (name, description, muscle_group, difficulty, image_url, session["user_id"])) 
        conn.commit()
        conn.close()
        
        #Alerts the trainer of the success and sends them back to their dashboard
        flash("Exercise added successfully! ") 
        return redirect(url_for("personal_trainer_dashboard"))
    return render_template("add_exercise.html")

#Meal plans library
@app.route("/meal-plans")
#Functions the same as the exercises library
def meal_plans():
    conn = get_db()
    all_meal_plans = conn.execute("SELECT meal_plan.*, user.username AS trainer_username FROM meal_plan JOIN user ON meal_plan.trainer_id = user.id").fetchall() 
    conn.close()
    return render_template("meal_plans.html", meal_plans = all_meal_plans)

#Meal plan details page
@app.route("/meal-plan/<int:plan_id>")
def meal_plan_detail(plan_id):
    conn = get_db()
    plan = conn.execute("SELECT meal_plan.*, user.username AS trainer_username FROM meal_plan JOIN user ON meal_plan.trainer_id = user.id WHERE meal_plan.id = ?", (plan_id,)).fetchone() 
    if not plan:
        conn.close()
        return "Meal plan not found", 404
    reviews = conn.execute("SELECT review_meal_plan.*, user.username, user.role FROM review_meal_plan JOIN user ON review_meal_plan.user_id = user.id WHERE review_meal_plan.meal_plan_id = ?", (plan_id,)).fetchall() 
    is_favourite = False
    if "user_id" in session:
        fav = conn.execute("SELECT id FROM favourite_meal_plan WHERE user_id = ? AND meal_plan_id = ?", (session["user_id"], plan_id)).fetchone()
        is_favourite = fav is not None
    is_owner = "user_id" in session and plan["trainer_id"] == session["user_id"]
    has_reviewed = False
    if "user_id" in session:
        existing = conn.execute("SELECT id FROM review_meal_plan WHERE user_id = ? AND meal_plan_id = ?", (session["user_id"], plan_id)).fetchone()
        has_reviewed = existing is not None
    all_meals = conn.execute("SELECT * FROM meal WHERE meal_plan_id = ?", (plan_id,)).fetchall() #Retrieves all individual meal items that are linked directly to this main plan ID
    
    #Sorts the meal items
    category_order = ["Breakfast", "Lunch", "Dinner", "Snack"]
    grouped_meals = [] 
    for category in category_order:
        meals_in_cat = [m for m in all_meals if m["category"] == category] 
        if meals_in_cat:
            grouped_meals.append((category, meals_in_cat))
    conn.close()
    return render_template("meal_plan_detail.html", plan=plan, is_favourite=is_favourite, reviews=reviews, is_owner = is_owner, grouped_meals = grouped_meals, has_reviewed=has_reviewed)

#Allows trainers to add meal plans to the meal plan library
@app.route("/add-meal-plan", methods = ["GET", "POST"])
def add_meal_plan():
    if "user_id" not in session or session.get("role") == "gym_goer":
        flash("Access denied!")
        return redirect(url_for("home"))
    if request.method == "POST":
        name = request.form["name"]
        description = request.form["description"]
        
        # Captures the raw text blocks entered by the trainer for each individual meal category
        categories = {"Breakfast": request.form.get("breakfast", ""), "Lunch": request.form.get("lunch", ""), "Dinner": request.form.get("dinner", ""), "Snack": request.form.get("snack", "")}
        image_url = request.form.get("image_url", "")
        if not name or not description:
            return "Please fill in all fields", 400
        
        #Validates that the trainer has added text to the input field
        if not any(text.strip() for text in categories.values()):
            return "Please add at least one meal", 400
        if not is_valid_image_url(image_url): 
            flash("Image URL must start with http")
            return redirect(url_for("add_content")) 
        conn = get_db()
        cursor = conn.execute("INSERT INTO meal_plan (name, description, meals, image_url, trainer_id) VALUES (?, ?, ?, ?, ?)", (name, description, "See structured meals", image_url, session["user_id"]))
        new_plan_id = cursor.lastrowid #Extracts the newly generated unique database auto-increment ID
        
        #Loops through each category text block to split multi-line instructions into separate child meal records
        for category, text in categories.items(): 
            for line in text.split("\n"):
                meal_desc = line.strip()
                if meal_desc:
                    conn.execute("INSERT INTO meal (meal_plan_id, category, description) VALUES (?, ?, ?)", (new_plan_id, category, meal_desc))
        conn.commit()
        conn.close()
        flash("Meal plan added successfully!")
        return redirect(url_for("personal_trainer_dashboard"))
    return render_template("add_meal_plan.html")

#Toggles when a meal plan is added to or removed from favourites
@app.route("/toggle-favourite-meal-plan/<int:plan_id>", methods=["POST"])
#Functions the same as toggle_favourite_exercise
def toggle_favourite_meal_plan(plan_id):
    if "user_id" not in session:
        return redirect(url_for("home"))
    conn = get_db()
    favourite =  conn.execute("SELECT id FROM favourite_meal_plan WHERE user_id = ? AND meal_plan_id = ?", (session["user_id"], plan_id)).fetchone()
    if favourite:
        conn.execute("DELETE FROM favourite_meal_plan WHERE id = ?", (favourite["id"],))
        flash("Removed from Favourites")
    else:
        conn.execute("INSERT INTO favourite_meal_plan (user_id, meal_plan_id) VALUES (?, ?)", (session["user_id"], plan_id))
        flash("Added to Favourites")
    conn.commit()
    conn.close()
    return redirect(url_for("meal_plan_detail", plan_id = plan_id))

#Handles the submission and validation of user reviews for a specific meal plan
@app.route("/add-meal-plan-review/<int:plan_id>", methods=["POST"])
#Functions the same as add_exercise_review
def add_meal_plan_review(plan_id):
    if "user_id" not in session:
        return redirect(url_for("home"))
    rating = float(request.form.get("rating"))
    comment = request.form.get("comment")
    if rating < 1 or rating > 5:
        flash("Rating must be between 1 and 5")
        return redirect(url_for("meal_plan_detail", plan_id = plan_id))
    conn = get_db()
    plan = conn.execute("SELECT trainer_id FROM meal_plan WHERE id = ?", (plan_id,)).fetchone()
    if plan and plan["trainer_id"] == session["user_id"]:
        conn.close()
        flash("You can't review your own content")
        return redirect(url_for("meal_plan_detail", plan_id = plan_id)) 
    existing = conn.execute("SELECT id FROM review_meal_plan WHERE user_id = ? AND meal_plan_id = ?", (session["user_id"], plan_id)).fetchone()
    if existing:
        conn.close()
        flash("You can't leave more than 1 review")
        return redirect(url_for("meal_plan_detail", plan_id=plan_id))
    conn.execute("INSERT INTO review_meal_plan (user_id, meal_plan_id, rating, comment) VALUES (?, ?, ?, ?)", (session["user_id"], plan_id, int(rating), comment))
    conn.commit()
    conn.close()
    flash("Review Added!")
    return redirect(url_for("meal_plan_detail", plan_id=plan_id))

#Workout routines library
@app.route("/workout-routines")
#Functions the same as the exercises & meal plans library
def workout_routines():
    conn = get_db()
    all_workout_routines = conn.execute("SELECT workout_routine.*, user.username AS trainer_username FROM workout_routine JOIN user ON workout_routine.trainer_id = user.id").fetchall()
    conn.close()
    return render_template("workout_routines.html", routines = all_workout_routines)

#Workout routines details page
@app.route("/workout-routines/<int:routine_id>")
#Functions the same as exercise_detail
def routine_detail(routine_id):
    conn = get_db()
    routine = conn.execute("SELECT workout_routine.*, user.username AS trainer_username FROM workout_routine JOIN user ON workout_routine.trainer_id = user.id WHERE workout_routine.id = ?", (routine_id,)).fetchone()
    if not routine:
        conn.close()
        return "Routine not found", 404
    reviews = conn.execute("SELECT review_routine.*, user.username, user.role FROM review_routine JOIN user ON review_routine.user_id = user.id WHERE review_routine.routine_id = ?", (routine_id,)).fetchall() 
    is_favourite = False
    if "user_id" in session:
        fav = conn.execute("SELECT id FROM favourite_routine WHERE user_id = ? AND routine_id = ?", (session["user_id"], routine_id)).fetchone()
        is_favourite = fav is not None
    is_owner = "user_id" in session and routine["trainer_id"] == session["user_id"]
    has_reviewed = False
    if "user_id" in session:
        existing = conn.execute("SELECT id FROM review_routine WHERE user_id = ? AND routine_id = ?", (session["user_id"], routine_id)).fetchone()
        has_reviewed = existing is not None
    conn.close()
    return render_template("workout_routine_detail.html", routine=routine, is_favourite=is_favourite, reviews=reviews, is_owner=is_owner, has_reviewed=has_reviewed)

#Allows trainers to add workout routines to the routine library
@app.route("/add-workout-routine", methods=["GET", "POST"])
def add_workout_routine():
    if "user_id" not in session or session.get("role") == "gym_goer":
        flash("Access denied!")
        return redirect(url_for("home"))
    if request.method == "POST":
        name = request.form["name"]
        description = request.form["description"]
        difficulty = request.form["difficulty"]
        exercises_list = request.form["exercises_list"]
        image_url = request.form.get("image_url", "")

        #Checks if any structural parameters needed for completing the core workout template are missing
        if not name or not description or not difficulty or not exercises_list:
            return "Please fill in all fields", 400
        if not is_valid_image_url(image_url): 
            flash("Image URL must start with http")
            return redirect(url_for("add_content"))   
        conn = get_db()
        
        #aves the completed multi-exercise training split record directly into the database library
        conn.execute("INSERT INTO workout_routine (name, description, difficulty, exercises_list, image_url, trainer_id) VALUES (?, ?, ?, ?, ?, ?)", (name, description, difficulty, exercises_list, image_url, session["user_id"])) 
        conn.commit()
        conn.close()
        flash("Workout routine added successfully!")
        return redirect(url_for("personal_trainer_dashboard"))
    return render_template("add_workout_routine.html")

#Toggles when a workout routine is added to or removed from favourites
@app.route("/toggle-favourite-workout-routine/<int:routine_id>", methods=["POST"])
#Functions the same as toggle_favourite_exercise & toggle_favourite_meal_plan
def toggle_favourite_workout_routine(routine_id):
    if "user_id" not in session:
        return redirect(url_for("home"))
    conn = get_db()
    fav = conn.execute("SELECT id FROM favourite_routine WHERE user_id = ? AND routine_id = ?", (session["user_id"], routine_id)).fetchone() 
    if fav: 
        conn.execute("DELETE FROM favourite_routine WHERE id = ?", (fav["id"],))
        flash("Removed from Favourites")
    else:
        conn.execute("INSERT INTO favourite_routine (user_id, routine_id) VALUES (?, ?)", (session["user_id"], routine_id))
        flash("Added to Favourites")
    conn.commit()
    conn.close()
    return redirect(url_for("routine_detail", routine_id=routine_id))

#Handles the submission and validation of user reviews for a specific meal plan
@app.route("/add-workout-routine-review/<int:routine_id>", methods=["POST"])
#Functions the same as add_exercise_review & add_meal_plan_review
def add_workout_routine_review(routine_id):
    if "user_id" not in session:
        return redirect(url_for("home"))
    rating = float(request.form.get("rating"))
    comment = request.form.get("comment")
    if rating < 1 or rating > 5: 
        flash("Rating must be between 1 and 5")
        return redirect(url_for("routine_detail", routine_id=routine_id))
    conn = get_db()
    routine = conn.execute("SELECT trainer_id FROM workout_routine WHERE id = ?", (routine_id,)).fetchone()
    if routine and routine["trainer_id"] == session["user_id"]:
        conn.close()
        flash("You can't review your own content")
        return redirect(url_for("routine_detail", routine_id=routine_id))
    existing = conn.execute("SELECT id FROM review_routine WHERE user_id = ? AND routine_id = ?", (session["user_id"], routine_id)).fetchone() 
    if existing: 
        conn.close()
        flash("You can't leave more than 1 review")
        return redirect(url_for("routine_detail", routine_id=routine_id))
    conn.execute("INSERT INTO review_routine (user_id, routine_id, rating, comment) VALUES (?, ?, ?, ?)", (session["user_id"], routine_id, int(rating), comment))
    conn.commit()
    conn.close()
    flash("Review added!")
    return redirect(url_for("routine_detail", routine_id=routine_id))

#Favourites page
@app.route("/view-favourites") 
def view_favourites():  
    if "user_id" not in session: 
        return redirect(url_for("home")) 
    conn = get_db()

    #Queries all exercises, meal_plans and workout routines cross-referenced against the user's specific favorites table
    favourite_exercises = conn.execute("SELECT exercise.* FROM exercise JOIN favourite_exercise ON favourite_exercise.exercise_id = exercise.id WHERE favourite_exercise.user_id = ?", (session["user_id"],)).fetchall() 
    favourite_meal_plans = conn.execute("SELECT meal_plan.* FROM meal_plan JOIN favourite_meal_plan ON favourite_meal_plan.meal_plan_id = meal_plan.id WHERE favourite_meal_plan.user_id = ?", (session["user_id"],)).fetchall()
    favourite_workout_routines = conn.execute("SELECT workout_routine.* FROM workout_routine JOIN favourite_routine ON favourite_routine.routine_id = workout_routine.id WHERE favourite_routine.user_id = ?", (session["user_id"],)).fetchall()
    conn.close()
    return render_template("view_favourites.html", exercises = favourite_exercises, meal_plans = favourite_meal_plans, routines = favourite_workout_routines)

#Allows trainers to edit their own content
@app.route("/edit-exercise/<int:exercise_id>", methods=["POST"])
def edit_exercise(exercise_id):
    if "user_id" not in session or session.get("role") == "gym_goer": 
        return redirect(url_for("home"))
    conn = get_db()
    exercise = conn.execute("SELECT * FROM exercise WHERE id = ?", (exercise_id,)).fetchone() 
    if not exercise:
        conn.close()
        return "Exercise not found", 404
    
    #Doesn't allow trainers who didn't create the content to edit it
    if exercise["trainer_id"] != session["user_id"]: 
        conn.close()
        return "You can only edit your own content", 403
    name = request.form.get("name")
    description = request.form.get("description")
    muscle_group = request.form.get("muscle_group")
    image_url = request.form.get("image_url")
    difficulty = request.form.get("difficulty")
    if not name or not description or not muscle_group or not difficulty:
        conn.close()
        return "Please fill in all fields", 400
    if not is_valid_image_url(image_url): 
            flash("Image URL must start with http")
            return redirect(url_for("exercise_detail", exercise_id=exercise_id)) 
    
    #Updates the table with the newly submitted data
    conn.execute("UPDATE exercise SET name = ?, description = ?, muscle_group = ?, image_url = ?, difficulty = ? WHERE id = ?", (name, description, muscle_group, image_url, difficulty, exercise_id))
    conn.commit()
    conn.close()
    flash("Exercise updated successfully!")
    return redirect(url_for("exercise_detail", exercise_id=exercise_id))

#Allows trainers to delete their own content
@app.route("/delete-exercise/<int:exercise_id>", methods=["POST"])
def delete_exercise(exercise_id):
    if "user_id" not in session or session.get("role") == "gym_goer":
        return redirect(url_for("home"))
    conn = get_db()
    exercise = conn.execute("SELECT * FROM exercise WHERE id = ?", (exercise_id,)).fetchone()
    if not exercise:
        conn.close()
        return "Exercise not found", 404
    if exercise["trainer_id"] != session["user_id"]:
        conn.close()
        return "You can only delete your own content", 403
    conn.execute("DELETE FROM favourite_exercise WHERE exercise_id = ?", (exercise_id,)) #Clears out any dependent favorite bookmarks to prevent database foreign key constraints from blocking the deletion
    conn.execute("DELETE FROM review_exercise WHERE exercise_id = ?", (exercise_id,)) #Clears out any dependent user rating entries associated with this specific exercise profile
    conn.execute("DELETE FROM exercise WHERE id = ?", (exercise_id,)) #Deletes all existing individual rows linked to this exercise before rebuilding them with the new updates
    conn.commit()
    conn.close()
    flash("Exercise deleted successfully!")
    return redirect(url_for("exercises"))

#Allows trainers to edit their own content
@app.route("/edit-meal-plan/<int:plan_id>", methods=["POST"])
#Functions the same as edit_exercise
def edit_meal_plan(plan_id):
    if "user_id" not in session or session.get("role") == "gym_goer":
        return redirect(url_for("home"))
    conn = get_db()
    plan = conn.execute("SELECT * FROM meal_plan WHERE id = ?", (plan_id,)).fetchone()
    if not plan:
        conn.close()
        return "Meal plan not found", 404
    if plan["trainer_id"] != session["user_id"]: 
        conn.close()
        return "You can only edit your own content", 403
    name = request.form.get("name")
    description = request.form.get("description")
    categories = {"Breakfast": request.form.get("breakfast", ""), "Lunch": request.form.get("lunch", ""), "Dinner": request.form.get("dinner", ""), "Snack": request.form.get("snack", "")}
    image_url = request.form.get("image_url", "")
    if not name or not description:
        conn.close()
        return "Please fill in all fields", 400
    if not any(text.strip() for text in categories.values()):
        conn.close()
        return "Please add at least one meal", 400
    if not is_valid_image_url(image_url): 
            flash("Image URL must start with http")
            return redirect(url_for("meal_plan_detail", plan_id=plan_id)) 
    conn.execute("UPDATE meal_plan SET name = ?, description = ?, image_url = ? WHERE id = ?", (name, description, image_url, plan_id)) 
    conn.execute("DELETE FROM meal WHERE meal_plan_id = ?", (plan_id,)) 
    for category, text in categories.items():
        for line in text.split("\n"):
            meal_desc = line.strip()
            if meal_desc:
                conn.execute("INSERT INTO meal (meal_plan_id, category, description) VALUES (?, ?, ?)", (plan_id, category, meal_desc))
    conn.commit()
    conn.close()
    flash("Meal plan updated successfully!")
    return redirect(url_for("meal_plan_detail", plan_id=plan_id))

#Allows trainers to delete their own content
@app.route("/delete-meal-plan/<int:plan_id>", methods=["POST"])
def delete_meal_plan(plan_id):
    if "user_id" not in session or session.get("role") == "gym_goer":
        return redirect(url_for("home"))
    conn = get_db()
    plan = conn.execute("SELECT * FROM meal_plan WHERE id = ?", (plan_id,)).fetchone()
    if not plan:
        conn.close()
        return "Meal plan not found", 404
    if plan["trainer_id"] != session["user_id"]: 
        conn.close()
        return "You can only delete your own content", 403
    conn.execute("DELETE FROM favourite_meal_plan WHERE meal_plan_id = ?", (plan_id,))
    conn.execute("DELETE FROM review_meal_plan WHERE meal_plan_id = ?", (plan_id,))
    
    # Clears out all individual food menu entries connected to the parent meal plan row
    conn.execute("DELETE FROM meal WHERE meal_plan_id = ?", (plan_id,))
    conn.execute("DELETE FROM meal_plan WHERE id = ?", (plan_id,))
    conn.commit()
    conn.close()
    flash("Meal plan deleted successfully!")
    return redirect(url_for("meal_plans"))

#Allows trainers to edit their own content
@app.route("/edit-workout-routine/<int:routine_id>", methods=["POST"])
#Functions the same as edit_exercise & edit_meal_plan
def edit_workout_routine(routine_id):
    if "user_id" not in session or session.get("role") == "gym_goer":
        return redirect(url_for("home"))
    conn = get_db()
    routine = conn.execute("SELECT * FROM workout_routine WHERE id = ?", (routine_id,)).fetchone()
    if not routine:
        conn.close()
        return "Routine not found", 404
    if routine["trainer_id"] != session["user_id"]:
        conn.close()
        return "You can only edit your own content", 403
    name = request.form.get("name")
    description = request.form.get("description")
    difficulty = request.form.get("difficulty")
    exercises_list = request.form.get("exercises_list")
    image_url = request.form.get("image_url", "")
    if not name or not description or not difficulty or not exercises_list:
        conn.close()
        return "Please fill in all fields", 400
    if not is_valid_image_url(image_url): 
            flash("Image URL must start with http")
            return redirect(url_for("routine_detail", routine_id=routine_id)) 
    conn.execute("UPDATE workout_routine SET name = ?, description = ?, difficulty = ?, exercises_list = ?, image_url = ? WHERE id = ?", (name, description, difficulty, exercises_list, image_url, routine_id))
    conn.commit()
    conn.close()
    flash("Workout routine updated successfully!")
    return redirect(url_for("routine_detail", routine_id=routine_id))

#Allows trainers to delete their own content
@app.route("/delete-workout-routine/<int:routine_id>", methods=["POST"])
#Functions the same as delete_exercise
def delete_workout_routine(routine_id):
    if "user_id" not in session or session.get("role") == "gym_goer":
        return redirect(url_for("home"))
    conn = get_db()
    routine = conn.execute("SELECT * FROM workout_routine WHERE id = ?", (routine_id,)).fetchone()
    if not routine:
        conn.close()
        return "Routine not found", 404
    if routine["trainer_id"] != session["user_id"]:
        conn.close()
        return "You can only delete your own content", 403
    conn.execute("DELETE FROM favourite_routine WHERE routine_id = ?", (routine_id,))
    conn.execute("DELETE FROM review_routine WHERE routine_id = ?", (routine_id,))
    conn.execute("DELETE FROM workout_routine WHERE id = ?", (routine_id,))
    conn.commit()
    conn.close()
    flash("Workout routine deleted successfully!")
    return redirect(url_for("workout_routines"))

#Centralised content creation page for trainers
@app.route("/add-content")
def add_content():
    if "user_id" not in session or session.get("role") == "gym_goer":
        flash("Access denied!")
        return redirect(url_for("home"))
    return render_template("add_content.html")

#Serves the PWA service worker file 
@app.route("/service-worker.js")
def service_worker():
    return send_from_directory("static", "service-worker.js", mimetype="application/javascript")

#Serves the web app manifest configuration file with the required JSON data type for installations
@app.route("/manifest.json")
def manifest():
    return send_from_directory("static", "manifest.json", mimetype="application/manifest+json")

#Displays a fallback page when a user loses their internet connection.
@app.route("/offline")
def offline():
    return render_template("offline.html")

#Clears the active user session data to securely log the person out of the app
@app.route("/logout") 
def logout(): 
    session.clear() 
    return redirect(url_for("home"))

#Constructs the initial local database tables before launching the active server
if __name__ == "__main__" : 
    #with app.app_context():
        #init_db()
    app.run(debug = True)