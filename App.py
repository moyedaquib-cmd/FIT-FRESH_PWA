import os #Allows python to interact with the operating system
from flask import Flask, request, redirect, url_for, render_template, session, flash #Flask: a lightweight web framework for Python that allows the creation of PWA, request: Allows Python to access data sent by the user, redirect: Send the user to a different URL, url_for: Uses the name of a function to create a URL path, render_template: Allows the use of Jinja2 to develop dynamic HTML pages, session: Allows users to store data across multiple HTTP requests, flash: Provides messages to the user that they can view
from DB_Models import get_db, init_db #Allows the database to be connected to the SQLite tables
from datetime import datetime #Datetime allows date and time to be viewed by the user
from werkzeug.security import generate_password_hash, check_password_hash #Werkzeug allows the hashing of passwords. generate_password_hash creates a hash from a password and check_password_hash checks the password with the hashed versions to verify the account
import pytz #A timezone database to convert to other timezones
app = Flask(__name__) #Creates the flask application
app.config["SECRET_KEY"] = "oJvneTznic84TgELjsKA" #This is a secret key used by flask to lock the login sessions so that people with no knowledge of the key cant access important information and tamper with cookies.

@app.template_filter("fmt_num") #Formats numbers by removing unnecessary trailing zeroes
def fmt_num(value):
    try: 
        f = round(float(value), 2) #Rounds to a max of 2 decimal places
        #If the number is a whole number, it's displayed with no decimal points, otherwise all trailing zeroes are removed
        if f == int(f):
            return str(int(f))
        return f'{f:.2f}'.rstrip("0")
    except:
        return value

def local_time(utc_dt_str): #A function that Converts UTC to Sydney Time
    local_tz = pytz.timezone("Australia/Sydney") #The timezone it converts to is Sydney, Australia
    utc_dt = datetime.strptime(utc_dt_str, "%Y-%m-%d %H:%M:%S") #Converts the stored UTC string into a datetime object
    return utc_dt.replace(tzinfo=pytz.utc).astimezone(local_tz) #Replaces UTC with the timezone of Sydney Australia

#Home Page
@app.route("/") #Tells flask to run the function below this decorator when someone visits the url
def home(): #The function that runs when someone visits the url
    return render_template("home.html") #Loads an html file from the templates folder

#Register page where a new user can create an account
@app.route("/register", methods=["GET", "POST"]) #The route can respond to both GET requests (occurs when the user loads the page) and POST requests (occurs when the user submits a form)
def register_page():
    if request.method == "GET": #What happens when it's a GET request
        return render_template("register.html")
    #Requests the following values to send to the server from the website
    username = request.form.get("username")
    password = request.form.get("password")
    role = request.form.get("role")
    if not username or not password or not role: #Stops empty submissions to prevent incomplete database records. Returns HTTP 400 (Bad Request)
        return "Please fill in all the fields", 400
    if len(username) <3 or len(username) > 50: #Username length check
        flash("Username must be between 3 and 50 characters")
        return redirect(url_for("register_page"))
    if len(password) < 6: #Password length check
        flash("Password must be at least 6 characters")
        return redirect(url_for("register_page"))
    conn = get_db() #Creates a database connection
    cursor = conn.cursor() #Creates a cursor object which acts as a connector between the python code and SQLite
    existing_user = cursor.execute("SELECT id FROM user WHERE username = ?", (username,)).fetchone() #Checks for duplicate usernames by querying the user table
    if existing_user: #Prevents duplicate accounts to avoid ambiguity and allow the databases to be unique.
        conn.close() #Terminates the connection between Python and SQLite
        flash("Username already exists") #Flash is used to showcase a message to the user
        return redirect(url_for("register_page")) #Redirects the user to a particular page
    hashed_password = generate_password_hash(password) #Generates a secure hash from the password
    cursor.execute("INSERT INTO user (username, password_hash, role) VALUES (?, ?, ?)", (username, hashed_password, role)) #Inserts the new user into the user table
    conn.commit() #Saves the record
    conn.close()
    flash("Account created successfully. Please log in") 
    return redirect(url_for("login"))

#Login page where existing users can access their account
@app.route("/login", methods=["POST", "GET"])
def login(): 
    if request.method == "GET": 
        return render_template("login.html") 
    username = request.form.get("username")
    password = request.form.get("password")
    if not username or not password:
        return "Please fill in all the fields", 400 
    conn = get_db() 
    user = conn.execute("SELECT * FROM user WHERE username = ?", (username,)).fetchone() #Searches the user table for a matching username
    conn.close()
    if not user: #If no account exists with the username, the PWA doesn't allows them to log in
        flash("Invalid username or password") 
        return redirect(url_for("login")) 
    if not check_password_hash(user["password_hash"], password): #Checks the hashed password with the user table and compares the plaintext and hashed versions to see if the password is correct
        return "Invalid username or password", 401 #401 Error indicates that the request failed due to unauthorised credentials.
    session["user_id"] = user["id"] #Stores the user's unique ID allowing easy identification of the logged-in user
    session["role"] = user["role"] #Stores the role of the user to enable role-based access control
    session["username"] = user["username"] #Stores the username 
    #Based on the user's role, they're redirected to a particular dashboard
    if user["role"] == "gym_goer": 
        flash("Logged in successfully") 
        return redirect(url_for("gym_goer_dashboard")) 
    else: 
        flash("Logged in successfully") 
        return redirect(url_for("personal_trainer_dashboard")) 


#The dashboard for gym_goers where they can access features only accessible to them
@app.route("/gym-goer-dashboard") 
def gym_goer_dashboard(): 
    
    #If they are not logged in, they're sent to the home page
    if "user_id" not in session: 
        return redirect(url_for("home")) 
    
    #If they are not a gym goer they are shown an error message
    if session.get("role") != "gym_goer": 
        return "Only gym goers can access the dashboard", 403 #403 Error indicates that the user is unauthorised from accessing the information
    return render_template("gym_goer_dashboard.html") 

#The dashboard for gym_goers where they can access features only accessible to them
@app.route("/personal-trainer-dashboard") 
def personal_trainer_dashboard():  
    if "user_id" not in session: 
        return redirect(url_for("home")) 
    
    #If they are a gym goer they are shown an error message
    if session.get("role") == "gym_goer": 
        return "Only personal trainers can access the dashboard", 403 
    return render_template("personal_trainer_dashboard.html") 

#A feature where users can log workouts
@app.route("/log-workout", methods=["GET", "POST"]) 
def log_workout(): 
    #Redirects the user to the home page if their details are not found in the database
    if "user_id" not in session:  
        return redirect(url_for("home")) #Redirects the user to a particular page
    
    if request.method == "GET":  
        return render_template("log_workout.html") 
    exercise = request.form.get("exercise")
    sets = request.form.get("sets")
    reps = request.form.get("reps")
    weight = request.form.get("weight")
    #Stops wrong and invalid submissions to prevent incorrect database records.
    if not exercise or not sets or not reps or not weight:
        return "Please fill in all the fields", 400
    if int(sets) < 0:
        return "Sets must be positive", 400
    if int(reps) < 0:
        return "Reps must be positive", 400
    if float(weight) < 0:
        return "Weight must be positive", 400
    conn = get_db()
    
    #Inserts the new workout into the workout table
    conn.execute( "INSERT INTO workout (user_id, exercise, sets, reps, weight) VALUES (?, ?, ?, ?, ?)", (session["user_id"], exercise, int(sets), int(reps), float(weight)))
    conn.commit()
    conn.close()
    return redirect(url_for("workout_history"))

#The place where the user can see their workout history (all the workouts they have logged)
@app.route("/workout-history") 
def workout_history(): 
    if "user_id" not in session:  
        return redirect(url_for("home")) 
    conn = get_db()    
    workouts = conn.execute( "SELECT * FROM workout WHERE user_id = ? ORDER BY workout_date DESC, id DESC",(session["user_id"],)).fetchall() #Retrieves all workouts for the logged-in user, sorted by most recent first
    conn.close()
    grouped_workouts = {} #Workouts can be grouped by date so the user can view them under specific date headings
    for workout in workouts:
        date_key = workout["workout_date"]
        if date_key not in grouped_workouts:
            grouped_workouts[date_key] = [] #Creates a new list the first time a date is seen
        grouped_workouts[date_key].append(workout) #Adds the workout to the date's list
    grouped_list = []    
    for date_key, day_workouts in grouped_workouts.items(): #Displays a list of information stored
        try:
            formatted = datetime.strptime(date_key, "%Y-%m-%d").strftime("%A, %d %B %Y")
        except (ValueError, TypeError): #Converts from statistical looking dates to friendly readable timestamps
            formatted = date_key
        grouped_list.append((date_key, formatted, day_workouts))
    return render_template("workout_history.html", workouts = workouts, grouped_workouts = grouped_list) #Returns the page with workout data

#The page where the user can log calories
@app.route("/log-calories", methods = ["GET", "POST"]) 
def log_calories(): 
    if "user_id" not in session: 
        return redirect(url_for("home")) 
    if request.method == "GET": 
        return render_template("log_calories.html") 
    meal = request.form.get("meal")
    calories = request.form.get("calories")
    if not calories or not meal:
        return "Please fill in all the fields", 400
    if float(calories) < 0:
        return "Calories must be positive", 400
    conn = get_db()
    conn.execute("INSERT INTO calorie_entry (user_id, meal, calories) VALUES (?, ?, ?)", (session["user_id"], meal, float(calories))) #Inserts the new calorie entry into the calorie_entry table
    conn.commit()
    conn.close()
    return redirect(url_for("calorie_history")) #Redirects the user to a particular page

#The place where the user can see their calorie history (all the calories they have tracked)
@app.route("/calorie-history") 
def calorie_history(): 
    if "user_id" not in session: 
        return redirect(url_for("home")) 
    conn = get_db()
    entries = conn.execute("SELECT * FROM calorie_entry WHERE user_id = ? ORDER BY entry_date DESC", (session["user_id"],)).fetchall() #Retrieves all calorie entries for the logged-in user, sorted by most recent first
    conn.close()
    
    #Converts each entry's stored UTC date sting to a Sydney DateTime object
    processed_entries = []
    for entry in entries:
        entry_dict = dict(entry) #Converts the Row object to a regular dictionary so new fields can be added
        entry_dict["local_time"] = local_time(entry["entry_date"]) #Converts UTC to Sydney Time
        entry_dict["entry_date"] = datetime.strptime(entry["entry_date"], "%Y-%m-%d %H:%M:%S") #Parses the entry_date string back into a datetime object for formatting
        processed_entries.append(entry_dict)
    return render_template("calorie_tracker.html", entries = processed_entries) # Returns the page with the calorie data

#A page to allows users to edit their data
@app.route("/edit-workout/<int:workout_id>", methods = ["GET", "POST"]) #This is a dynamic route based on the id of the object
def edit_workout(workout_id): #The parameter specifies which object to edit
    if "user_id" not in session: 
        return redirect(url_for("home")) 
    conn = get_db()
    workout = conn.execute("SELECT * FROM workout WHERE id = ?", (workout_id,)).fetchone() #Searches for the object based on its ID
    
    #Returns a 404 error if workout is not found
    if not workout:
        conn.close()
        return "Workout not found", 404
    
    #Confirms the workout belongs to the logged-in user
    if workout["user_id"] != session["user_id"]:
        conn.close()
        return "Unasuthorised user", 403
   
    if request.method == "GET": 
        conn.close()
        return render_template("edit_workout.html", workout = workout) #Returns the edit form
    exercise = request.form.get("exercise")
    sets = int(request.form.get("sets"))
    reps = int(request.form.get("reps"))
    weight = float(request.form.get("weight"))
    conn.execute("UPDATE workout SET exercise = ?, sets = ?, reps = ?, weight = ? WHERE id = ?", (exercise, sets, reps, weight, workout_id))
    conn.commit()
    conn.close()
    flash("Workout Updated") 
    return redirect(url_for("workout_history")) 

#Allows users to delete data
@app.route("/delete-workout/<int:workout_id>", methods = ["POST"]) 
def delete_workout(workout_id):
    if "user_id" not in session:
        return redirect(url_for("home")) 
    conn = get_db()
    workout = conn.execute("SELECT * FROM workout WHERE id = ?", (workout_id,)).fetchone() 
    if not workout:
        conn.close()
        return "Workout not found", 404
    if workout["user_id"] != session["user_id"]:
        conn.close()
        return "Unauthorised user", 403
    conn.execute("DELETE FROM workout WHERE id = ?", (workout_id,)) #Removes the workout record from the database
    conn.commit() 
    conn.close()
    flash("Workout Deleted") 
    return redirect(url_for("workout_history")) 

#A page to allows users to edit their data
@app.route("/edit-calories/<int:entry_id>", methods = ["GET", "POST"]) 
def edit_calories(entry_id): 
    if "user_id" not in session: 
        return redirect(url_for("home")) 
    conn = get_db()
    entry = conn.execute("SELECT * FROM calorie_entry WHERE id = ?", (entry_id,)).fetchone() #Searches for the entry by ID
    if not entry:
        conn.close()
        return "Entry not found", 404
    if entry["user_id"] != session["user_id"]:
        conn.close()
        return "Unauthorised user", 403
    if request.method == "GET": 
        conn.close()
        return render_template("edit_calories.html", entry = entry)
    meal = request.form.get("meal") 
    calories = float(request.form.get("calories"))
    conn.execute("UPDATE calorie_entry SET meal = ?, calories = ? WHERE id = ?", (meal, calories, entry_id)) #Updates the calorie entry record in the database
    conn.commit()
    conn.close()
    flash("Calories Updated")
    return redirect(url_for("calorie_history")) 

#Allows users to delete data
@app.route("/delete-calories/<int:entry_id>", methods = ["POST"]) 
def delete_calories(entry_id): 
    if "user_id" not in session: 
        return redirect(url_for("home"))
    conn = get_db()
    entry = conn.execute("SELECT * FROM calorie_entry WHERE id = ?", (entry_id,)).fetchone()
    if not entry:
        conn.close()
        return "Entry not found", 404
    if entry["user_id"] != session["user_id"]:
        conn.close()
        return "Unauthorised user", 403
    conn.execute("DELETE FROM calorie_entry WHERE id = ?", (entry_id,)) #Removes the calorie entry from the database
    conn.commit()
    conn.close()
    flash("Calories Deleted") 
    return redirect(url_for("calorie_history")) #

                                                        #EXERCISES PAGE WHERE USERS CAN VIEW, FAVOURITE AND REVIEW EXERCISES

#The page where users can view the exercises listed
@app.route("/exercises") 
def exercises():  
    conn = get_db()
    all_exercises = conn.execute("SELECT * FROM exercise").fetchall() #Retrieves every object from the table
    conn.close()
    return render_template("exercises.html", exercises = all_exercises) #Returns the page, displaying it to the user. The template can loop, showcasing each piece of data

#Users can click on the exercise to view details about it.
@app.route("/exercise/<int:exercise_id>") 
def exercise_detail(exercise_id):  
    conn = get_db()
    exercise = conn.execute("SELECT * FROM exercise WHERE id = ?", (exercise_id,)).fetchone() #Retrieves a particular object through searching by ID
    if not exercise:
        conn.close()
        return "Exercise not found", 404
    reviews = conn.execute("SELECT review_exercise.*, user.username, user.role FROM review_exercise JOIN user ON review_exercise.user_id = user.id WHERE review_exercise.exercise_id = ?", (exercise_id,)).fetchall() #Retrieves all reviews for the object and joins to the user table to get the username of the reviewers
    is_favourite = False

    #Checks if the logged-in user has favourited the exercise
    if "user_id" in session:
        fav = conn.execute("SELECT id FROM favourite_exercise WHERE user_id = ? AND exercise_id = ?", (session["user_id"], exercise_id)).fetchone()
        is_favourite = fav is not None #If exercise_fav is a row, is_favourite becomes True otherwise if it is None, is_favourite becomes False
    is_owner = "user_id" in session and exercise["trainer_id"] == session["user_id"] #True if the logged-in trainer created the content
    
    #Tracks whether the logged-in user has already reviewd this exercise
    has_reviewed = False
    if "user_id" in session:
        existing = conn.execute("SELECT id FROM review_exercise WHERE user_id = ? AND exercise_id = ?", (session["user_id"], exercise_id)).fetchone()
        has_reviewed = existing is not None
    conn.close()
    return render_template("exercise_detail.html", exercise = exercise, is_favourite = is_favourite, reviews = reviews, is_owner = is_owner, has_reviewed = has_reviewed) 

#A feature that allows user to favourite an exercise and save it
@app.route("/toggle-favourite-exercise/<int:exercise_id>", methods = ["POST"]) 
def toggle_favourite_exercise(exercise_id):  
    if "user_id" not in session:  
        return redirect(url_for("home")) #Redirects the user to a particular page
    conn = get_db()
    favourite = conn.execute("SELECT id FROM favourite_exercise WHERE user_id = ? AND exercise_id = ?", (session["user_id"], exercise_id)).fetchone() #Looks for an existing favourite record for this user and exercise
    #If the favourite exists, it's removed
    if favourite:
        conn.execute("DELETE FROM favourite_exercise WHERE id = ?", (favourite["id"],))
        flash("Removed from Favourites")
    
    #If the favourite doesn't exist, It's added to the table
    else: 
        conn.execute("INSERT INTO favourite_exercise (user_id, exercise_id) VALUES (?, ?)", (session["user_id"], exercise_id))
        flash("Added to favourites")
    conn.commit()
    conn.close()
    return redirect(url_for("exercise_detail", exercise_id = exercise_id)) #redirects the user to the exercise_detail page

#Allows users to add reviews for exercises
@app.route("/add-review-exercise/<int:exercise_id>", methods = ["POST"])
def add_review_exercise(exercise_id): 
    if "user_id" not in session:
        return redirect(url_for("home")) 
    rating = float(request.form.get("rating")) 
    comment = request.form.get("comment")
    
    #Doesn't allow invalid ratings
    if rating < 1 or rating > 5:
        flash("Rating must be between 1 and 5")
        return redirect(url_for("exercise_detail", exercise_id = exercise_id)) 
    conn = get_db()

    #Blocks trainer from reviewing their own content
    exercise = conn.execute("SELECT trainer_id FROM exercise WHERE id = ?", (exercise_id,)).fetchone()
    if exercise and exercise["trainer_id"] == session["user_id"]:
        conn.close()
        flash("You can't review your own content")
        return redirect(url_for("exercise_detail", exercise_id = exercise_id))
    
    #The user is not allowed to leave more than 1 review
    existing_review = conn.execute("SELECT id FROM review_exercise WHERE user_id = ? AND exercise_id = ?",(session["user_id"], exercise_id)).fetchone() #Checks if the user has already reviewed this exercise
    if existing_review:
        conn.close()
        flash("You can't leave more than 1 review")
        return redirect(url_for("exercise_detail", exercise_id = exercise_id)) 
    conn.execute("INSERT INTO review_exercise (user_id, exercise_id, rating, comment) VALUES (?, ?, ?, ?)", (session["user_id"], exercise_id, int(rating), comment)) #Inserts the new review into the review_exercise table
    conn.commit()
    conn.close()
    flash("Review added!") 
    return redirect(url_for("exercise_detail", exercise_id = exercise_id)) #Returns the page, displaying it to the user. The template can loop, showcasing each piece of data

#Allows trainers to add an exercise which people can view
@app.route("/add-exercise", methods = ["GET", "POST"]) 
def add_exercise(): 
    if "user_id" not in session or session.get("role") == "gym_goer": #Redirects the user to the home page if their details are not found in the database or they are a gym_goer
        flash("Access denied!") 
        return redirect(url_for("home")) 
    if request.method == "POST":  
        name = request.form["name"]
        description = request.form["description"]
        muscle_group = request.form["muscle_group"]
        image_url = request.form.get("image_url")
        difficulty = request.form["difficulty"]
        conn = get_db()
        conn.execute("INSERT INTO exercise (name, description, muscle_group, difficulty, image_url, trainer_id) VALUES (?, ?, ?, ?, ?, ?)", (name, description, muscle_group, difficulty, image_url, session["user_id"])) #Inserts the new exercise into the exercise table
        conn.commit()
        conn.close()
        flash("Exercise added successfully! ") #Showcases a message to the user
        return redirect(url_for("personal_trainer_dashboard")) #Redirects the user to a particular page
    return render_template("add_exercise.html") # Returns the page, displaying it to the user.

                                                        #MEAL PLANS PAGE WHERE USERS CAN VIEW, FAVOURITE AND REVIEW MEAL PLANS

#The page where all meal plans are listed
@app.route("/meal-plans")
def meal_plans():
    conn = get_db()
    all_meal_plans = conn.execute("SELECT * FROM meal_plan").fetchall() 
    conn.close()
    return render_template("meal_plans.html", meal_plans = all_meal_plans)

#Users can click on the meal plan to view details about it
@app.route("/meal-plan/<int:plan_id>")
def meal_plan_detail(plan_id):
    conn = get_db()
    plan = conn.execute("SELECT * FROM meal_plan WHERE id = ?", (plan_id,)).fetchone() 
    if not plan:
        conn.close()
        return "Meal plan not found", 404
    reviews = conn.execute("SELECT review_meal_plan.*, user.username, user.role FROM review_meal_plan JOIN user ON review_meal_plan.user_id = user.id WHERE review_meal_plan.meal_plan_id = ?", (plan_id,)).fetchall() 
    is_favourite = False
    if "user_id" in session:
        fav = conn.execute("SELECT id FROM favourite_meal_plan WHERE user_id = ? AND meal_plan_id = ?", (session["user_id"], plan_id)).fetchone()
        is_favourite = fav is not None
    is_owner = "user_id" in session and plan["trainer_id"] == session["user_id"]
    
    #Tracks whether users have already reviewed the plan
    has_reviewed = False
    if "user_id" in session:
        existing = conn.execute("SELECT id FROM review_meal_plan WHERE user_id = ? AND meal_plan_id = ?", (session["user_id"], plan_id)).fetchone()
        has_reviewed = existing is not None

    #Fetch all meals for this plan and group them by category
    all_meals = conn.execute("SELECT * FROM meal WHERE meal_plan_id = ?", (plan_id,)).fetchall()
    category_order = ["Breakfast", "Lunch", "Dinner", "Snack"]
    grouped_meals = [] # A list of category and meals so that template loops in order
    for category in category_order:
        meals_in_cat = [m for m in all_meals if m["category"] == category] #Fetches all meals in the category
        if meals_in_cat:
            grouped_meals.append((category, meals_in_cat))
    conn.close()
    return render_template("meal_plan_detail.html", plan=plan, is_favourite=is_favourite, reviews=reviews, is_owner = is_owner, grouped_meals = grouped_meals, has_reviewed=has_reviewed)

#Allows trainers to add a meal plan
@app.route("/add-meal-plan", methods = ["GET", "POST"])
def add_meal_plan():
    if "user_id" not in session or session.get("role") == "gym_goer":
        flash("Access denied!")
        return redirect(url_for("home"))
    if request.method == "POST":
        name = request.form["name"]
        description = request.form["description"]
        categories = {"Breakfast": request.form.get("breakfast", ""), "Lunch": request.form.get("lunch", ""), "Dinner": request.form.get("dinner", ""), "Snack": request.form.get("snack", "")} #Fetched meals from four separate category textareas
        image_url = request.form.get("image_url", "")
        if not name or not description:
            return "Please fill in all fields", 400
        if not any(text.strip() for text in categories.values()):
            return "Please add at least one meal", 400
        conn = get_db()
        cursor = conn.execute("INSERT INTO meal_plan (name, description, meals, image_url, trainer_id) VALUES (?, ?, ?, ?, ?)", (name, description, "See structured meals", image_url, session["user_id"]))
        new_plan_id = cursor.lastrowid
        for category, text in categories.items(): #Each catgegroy is split into lines and each line becomes its own meal row
            for line in text.split("\n"): #Each line is treated as a separate meal
                meal_desc = line.strip()
                if meal_desc:
                    conn.execute("INSERT INTO meal (meal_plan_id, category, description) VALUES (?, ?, ?)", (new_plan_id, category, meal_desc))
        conn.commit()
        conn.close()
        flash("Meal plan added successfully!")
        return redirect(url_for("personal_trainer_dashboard"))
    return render_template("add_meal_plan.html")

#Allows users to favourite a meal plan
@app.route("/toggle-favourite-meal-plan/<int:plan_id>", methods=["POST"])
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

#Allows users to leave reviews for the meal plans
@app.route("/add-meal-plan-review/<int:plan_id>", methods=["POST"])
def add_meal_plan_review(plan_id):
    if "user_id" not in session:
        return redirect(url_for("home"))
    rating = float(request.form.get("rating"))
    comment = request.form.get("comment")
    if rating < 1 or rating > 5:
        flash("Rating must be between 1 and 5")
        return redirect(url_for("meal_plan_detail", plan_id = plan_id))
    conn = get_db()
    
    #Blocks trainers from reviewing their own content
    plan = conn.execute("SELECT trainer_id FROM meal_plan WHERE id = ?", (plan_id,)).fetchone()
    if plan and plan["trainer_id"] == session["user_id"]:
        conn.close()
        flash("You can't review your own content")
        return redirect(url_for("meal_plan_detail", plan_id = plan_id))

    #Users can't leave more than 1 review    
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

                                                        #WORKOUT ROUTINES PAGE WHERE USERS CAN VIEW, FAVOURITE AND REVIEW WORKOUT ROUTINES

#The page where all workout routines are listed
@app.route("/workout-routines")
def workout_routines():
    conn = get_db()
    all_workout_routines = conn.execute("SELECT * FROM workout_routine").fetchall()
    conn.close()
    return render_template("workout_routines.html", routines = all_workout_routines)

#Users can click on the workout routine to view details about it
@app.route("/workout-routines/<int:routine_id>")
def routine_detail(routine_id):
    conn = get_db()
    routine = conn.execute("SELECT * FROM workout_routine WHERE id = ?", (routine_id,)).fetchone()
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

#Allows trainers to create a workout routine
@app.route("/add-workout-routine", methods=["GET", "POST"])
def add_workout_routine():
    if "user_id" not in session or session.get("role") == "gym_goer":
        flash("Access denied!")
        return redirect(url_for("home"))
    if request.method == "POST":
        name = request.form["name"]
        description = request.form["description"]
        difficulty = request.form["difficulty"]
        exercises_list = request.form["exercises_list"] #A text list of exercises included in this routine
        image_url = request.form.get("image_url", "")
        if not name or not description or not difficulty or not exercises_list:
            return "Please fill in all fields", 400
        conn = get_db()
        conn.execute("INSERT INTO workout_routine (name, description, difficulty, exercises_list, image_url, trainer_id) VALUES (?, ?, ?, ?, ?, ?)", (name, description, difficulty, exercises_list, image_url, session["user_id"])) #Inserts the new routine into the workout_routine table
        conn.commit()
        conn.close()
        flash("Workout routine added successfully!")
        return redirect(url_for("personal_trainer_dashboard"))
    return render_template("add_workout_routine.html")

#Allows users to favourite a workout routine
@app.route("/toggle-favourite-workout-routine/<int:routine_id>", methods=["POST"])
def toggle_favourite_workout_routine(routine_id):
    if "user_id" not in session:
        return redirect(url_for("home"))
    conn = get_db()
    fav = conn.execute("SELECT id FROM favourite_routine WHERE user_id = ? AND routine_id = ?", (session["user_id"], routine_id)).fetchone() #Looks for an existing favourite record
    if fav: #If the favourite already exists, remove it
        conn.execute("DELETE FROM favourite_routine WHERE id = ?", (fav["id"],))
        flash("Removed from Favourites")
    else: #If the favourite doesn't exist, add it
        conn.execute("INSERT INTO favourite_routine (user_id, routine_id) VALUES (?, ?)", (session["user_id"], routine_id))
        flash("Added to Favourites")
    conn.commit()
    conn.close()
    return redirect(url_for("routine_detail", routine_id=routine_id))

#Allows users to leave reviews for the workout routines
@app.route("/add-workout-routine-review/<int:routine_id>", methods=["POST"])
def add_workout_routine_review(routine_id):
    if "user_id" not in session:
        return redirect(url_for("home"))
    rating = float(request.form.get("rating"))
    comment = request.form.get("comment")
    if rating < 1 or rating > 5: #Prevents invalid ratings outside the 1-5 range
        flash("Rating must be between 1 and 5")
        return redirect(url_for("routine_detail", routine_id=routine_id))
    conn = get_db()
    routine = conn.execute("SELECT trainer_id FROM workout_routine WHERE id = ?", (routine_id,)).fetchone()
    if routine and routine["trainer_id"] == session["user_id"]:
        conn.close()
        flash("You can't review your own content")
        return redirect(url_for("routine_detail", routine_id=routine_id))
    existing = conn.execute("SELECT id FROM review_routine WHERE user_id = ? AND routine_id = ?", (session["user_id"], routine_id)).fetchone() #Checks if the user has already reviewed this routine
    if existing: #Prevents more than one review per routine per user
        conn.close()
        flash("You can't leave more than 1 review")
        return redirect(url_for("routine_detail", routine_id=routine_id))
    conn.execute("INSERT INTO review_routine (user_id, routine_id, rating, comment) VALUES (?, ?, ?, ?)", (session["user_id"], routine_id, int(rating), comment))
    conn.commit()
    conn.close()
    flash("Review added!")
    return redirect(url_for("routine_detail", routine_id=routine_id))

#Where users can view their favourites
@app.route("/view-favourites") 
def view_favourites():  
    if "user_id" not in session: 
        return redirect(url_for("home")) 
    conn = get_db()
    favourite_exercises = conn.execute("SELECT exercise.* FROM exercise JOIN favourite_exercise ON favourite_exercise.exercise_id = exercise.id WHERE favourite_exercise.user_id = ?", (session["user_id"],)).fetchall() #Retrieves favourited exercises
    favourite_meal_plans = conn.execute("SELECT meal_plan.* FROM meal_plan JOIN favourite_meal_plan ON favourite_meal_plan.meal_plan_id = meal_plan.id WHERE favourite_meal_plan.user_id = ?", (session["user_id"],)).fetchall() #Retrieves favourited meal plans
    favourite_workout_routines = conn.execute("SELECT workout_routine.* FROM workout_routine JOIN favourite_routine ON favourite_routine.routine_id = workout_routine.id WHERE favourite_routine.user_id = ?", (session["user_id"],)).fetchall() #Retrieves favourited workout routines
    conn.close()
    return render_template("view_favourites.html", exercises = favourite_exercises, meal_plans = favourite_meal_plans, routines = favourite_workout_routines) # Returns the page, displaying it to the user. The template can loop, showcasing each piece of data

#Allows trainers to edit exercises they created
@app.route("/edit-exercise/<int:exercise_id>", methods=["POST"])
def edit_exercise(exercise_id):
    if "user_id" not in session or session.get("role") == "gym_goer": 
        return redirect(url_for("home"))
    conn = get_db()
    exercise = conn.execute("SELECT * FROM exercise WHERE id = ?", (exercise_id,)).fetchone() 
    if not exercise:
        conn.close()
        return "Exercise not found", 404
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
    conn.execute("UPDATE exercise SET name = ?, description = ?, muscle_group = ?, image_url = ?, difficulty = ? WHERE id = ?", (name, description, muscle_group, image_url, difficulty, exercise_id))
    conn.commit()
    conn.close()
    flash("Exercise updated successfully!")
    return redirect(url_for("exercise_detail", exercise_id=exercise_id))

#Allows a trainer to delete an exercise they created
@app.route("/delete-exercise/<int:exercise_id>", methods=["POST"])
def delete_exercise(exercise_id):
    if "user_id" not in session or session.get("role") == "gym_goer":
        return redirect(url_for("home"))
    conn = get_db()
    exercise = conn.execute("SELECT * FROM exercise WHERE id = ?", (exercise_id,)).fetchone()
    if not exercise:
        conn.close()
        return "Exercise not found", 404
    if exercise["trainer_id"] != session["user_id"]: #Ownership check
        conn.close()
        return "You can only delete your own content", 403
    #Deletes related favourites and reviews first to maintain referential integrity
    conn.execute("DELETE FROM favourite_exercise WHERE exercise_id = ?", (exercise_id,))
    conn.execute("DELETE FROM review_exercise WHERE exercise_id = ?", (exercise_id,))
    conn.execute("DELETE FROM exercise WHERE id = ?", (exercise_id,))
    conn.commit()
    conn.close()
    flash("Exercise deleted successfully!")
    return redirect(url_for("exercises"))

#Allows a trainer to edit a meal plan they created
@app.route("/edit-meal-plan/<int:plan_id>", methods=["POST"])
def edit_meal_plan(plan_id):
    if "user_id" not in session or session.get("role") == "gym_goer":
        return redirect(url_for("home"))
    conn = get_db()
    plan = conn.execute("SELECT * FROM meal_plan WHERE id = ?", (plan_id,)).fetchone()
    if not plan:
        conn.close()
        return "Meal plan not found", 404
    if plan["trainer_id"] != session["user_id"]: #Ownership check
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
    conn.execute("UPDATE meal_plan SET name = ?, description = ?, image_url = ? WHERE id = ?", (name, description, image_url, plan_id)) 
    conn.execute("DELETE FROM meal WHERE meal_plan_id = ?", (plan_id,)) #Deletes all existing meals for this plans then re-inserts the updated ones
    for category, text in categories.items():
        for line in text.split("\n"):
            meal_desc = line.strip()
            if meal_desc:
                conn.execute("INSERT INTO meal (meal_plan_id, category, description) VALUES (?, ?, ?)", (plan_id, category, meal_desc))
    conn.commit()
    conn.close()
    flash("Meal plan updated successfully!")
    return redirect(url_for("meal_plan_detail", plan_id=plan_id))

#Allows a trainer to delete a meal plan they created
@app.route("/delete-meal-plan/<int:plan_id>", methods=["POST"])
def delete_meal_plan(plan_id):
    if "user_id" not in session or session.get("role") == "gym_goer":
        return redirect(url_for("home"))
    conn = get_db()
    plan = conn.execute("SELECT * FROM meal_plan WHERE id = ?", (plan_id,)).fetchone()
    if not plan:
        conn.close()
        return "Meal plan not found", 404
    if plan["trainer_id"] != session["user_id"]: #Ownership check
        conn.close()
        return "You can only delete your own content", 403
    conn.execute("DELETE FROM favourite_meal_plan WHERE meal_plan_id = ?", (plan_id,))
    conn.execute("DELETE FROM review_meal_plan WHERE meal_plan_id = ?", (plan_id,))
    conn.execute("DELETE FROM meal_plan WHERE meal_plan_id = ?", (plan_id,))
    conn.execute("DELETE FROM meal WHERE meal_plan_id = ?", (plan_id,))
    conn.commit()
    conn.close()
    flash("Meal plan deleted successfully!")
    return redirect(url_for("meal_plans"))

#Allows a trainer to edit a workout routine they created
@app.route("/edit-workout-routine/<int:routine_id>", methods=["POST"])
def edit_workout_routine(routine_id):
    if "user_id" not in session or session.get("role") == "gym_goer":
        return redirect(url_for("home"))
    conn = get_db()
    routine = conn.execute("SELECT * FROM workout_routine WHERE id = ?", (routine_id,)).fetchone()
    if not routine:
        conn.close()
        return "Routine not found", 404
    if routine["trainer_id"] != session["user_id"]: #Ownership check
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
    conn.execute("UPDATE workout_routine SET name = ?, description = ?, difficulty = ?, exercises_list = ?, image_url = ? WHERE id = ?", (name, description, difficulty, exercises_list, image_url, routine_id))
    conn.commit()
    conn.close()
    flash("Workout routine updated successfully!")
    return redirect(url_for("routine_detail", routine_id=routine_id))

#Allows a trainer to delete a workout routine they created
@app.route("/delete-workout-routine/<int:routine_id>", methods=["POST"])
def delete_workout_routine(routine_id):
    if "user_id" not in session or session.get("role") == "gym_goer":
        return redirect(url_for("home"))
    conn = get_db()
    routine = conn.execute("SELECT * FROM workout_routine WHERE id = ?", (routine_id,)).fetchone()
    if not routine:
        conn.close()
        return "Routine not found", 404
    if routine["trainer_id"] != session["user_id"]: #Ownership check
        conn.close()
        return "You can only delete your own content", 403
    conn.execute("DELETE FROM favourite_routine WHERE routine_id = ?", (routine_id,))
    conn.execute("DELETE FROM review_routine WHERE routine_id = ?", (routine_id,))
    conn.execute("DELETE FROM workout_routine WHERE id = ?", (routine_id,))
    conn.commit()
    conn.close()
    flash("Workout routine deleted successfully!")
    return redirect(url_for("workout_routines"))

#Single unified page for trainers where they can add exercises, meal plans and routines. The form posts to the relevant existing route
@app.route("/add-content")
def add_content():
    if "user_id" not in session or session.get("role") == "gym_goer":
        flash("Access denied!")
        return redirect(url_for("home"))
    return render_template("add_content.html")

#Logs out the user by clearing their session
@app.route("/logout") 
def logout(): 
    session.clear() 
    return redirect(url_for("home"))

if __name__ == "__main__" : #Ensures the app runs when the file is executed
    #with app.app_context():
        #init_db()
    app.run(debug = True) #Starts the flask server and allows for real-time debugging