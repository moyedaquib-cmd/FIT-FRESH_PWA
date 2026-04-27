import os #Allows python to interact with the operating system
from flask import Flask, request, redirect, url_for, render_template, session, flash #Flask: a lightweight web framework for Python that allows the creation of PWA, request: Allows Python to access data sent by the user, redirect: Send the user to a different URL, url_for: Uses the name of a function to create a URL path, render_template: Allows the use of Jinja2 to develop dynamic HTML pages, session: Allows users to store data across multiple HTTP requests, flash: Provides messages to the user that they can view
from DB_Models import get_db, init_db #Allows the database to be connected to the SQLite tables
from datetime import datetime #Datetime allows date and time to be viewed by the user
from werkzeug.security import generate_password_hash, check_password_hash #Werkzeug allows the hashing of passwords. generate_password_hash creates a hash from a password and check_password_hash checks the password with the hashed versions to verify the account
import pytz #A timezone database to convert to other timezones
app = Flask(__name__) #Creates the flask application
app.config["SECRET_KEY"] = "oJvneTznic84TgELjsKA" #This is a secret key used by flask to lock the login sessions so that people with no knowledge of the key cant access important information and tamper with cookies.

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
    workouts = conn.execute( "SELECT * FROM workout WHERE user_id = ? ORDER BY workout_date DESC",(session["user_id"],)).fetchall() #Retrieves all workouts for the logged-in user, sorted by most recent first
    conn.close()
    return render_template("workout_history.html", workouts = workouts) #Returns the page with workout data

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

#The page where users can view the exercises
@app.route("/exercises") 
def exercises():  
    conn = get_db()
    all_exercises = conn.execute("SELECT * FROM exercise").fetchall() #Retrieves every exercise from the table
    conn.close()
    return render_template("exercises.html", exercises = all_exercises) #Returns the page, displaying it to the user. The template can loop, showcasing each piece of data

#Users can click on the exercise to view details about it.
@app.route("/exercise/<int:exercise_id>") 
def exercise_detail(exercise_id):  
    conn = get_db()
    exercise = conn.execute("SELECT * FROM exercise WHERE id = ?", (exercise_id,)).fetchone()
    if not exercise:
        conn.close()
        return "Exercise not found", 404
    reviews = conn.execute("SELECT review_exercise.*, user.username FROM review_exercise JOIN user ON review_exercise.user_id = user.id WHERE review_exercise.exercise_id = ?", (exercise_id,)).fetchall() #Retrieves all reviews for the exercise and joins to the user table to get the username of the reviewers
    is_favourite = False

    #Checks if the logged-in user has favourited the exercise
    if "user_id" in session:
        fav = conn.execute("SELECT id FROM favourite_exercise WHERE user_id = ? AND exercise_id = ?", (session["user_id"], exercise_id)).fetchone()
        is_favourite = fav is not None #If fav is a row, is_favourite becomes True otherwise if fav is None, is_favourite becomes False
    conn.close()
    return render_template("exercise_detail.html", exercise = exercise, is_favourite = is_favourite, reviews = reviews) 

#A feature that allows user to favourite an exercise and save it
@app.route("/toggle-favourite/<int:exercise_id>", methods = ["POST"]) 
def toggle_favourite(exercise_id):  
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

#Where the users can view their saved exercises
@app.route("/view-favourites") 
def view_favourites():  
    if "user_id" not in session: 
        return redirect(url_for("home")) 
    conn = get_db()
    favourite_exercises = conn.execute("SELECT exercise.* FROM exercise JOIN favourite_exercise ON favourite_exercise.exercise_id = exercise.id WHERE favourite_exercise.user_id = ?", (session["user_id"],)).fetchall() #Selects exercise data by joining the exercise and favourite_exercise tables, filtered to the logged-in user's favourites
    conn.close()
    return render_template("view_favourites.html", exercises = favourite_exercises) # Returns the page, displaying it to the user. The template can loop, showcasing each piece of data

#Allows users to add reviews
@app.route("/add-review/<int:exercise_id>", methods = ["POST"])
def add_review(exercise_id): 
    if "user_id" not in session:
        return redirect(url_for("home")) 
    rating = float(request.form.get("rating")) 
    comment = request.form.get("comment")
    #Doesn't allow invalid ratings
    if rating < 1 or rating > 5:
        flash("Rating must be between 1 and 5")
        return redirect(url_for("exercise_detail", exercise_id = exercise_id)) 
    conn = get_db()
    existing_review = conn.execute("SELECT id FROM review_exercise WHERE user_id = ? AND exercise_id = ?",(session["user_id"], exercise_id)).fetchone() #Checks if the user has already reviewed this exercise
    
    #The user is not allowed to leave more than 1 review
    if existing_review:
        conn.close()
        flash("You can't leave more than 1 review")
        return redirect(url_for("exercise_detail", exercise_id = exercise_id)) 
    conn.execute("INSERT INTO review_exercise (user_id, exercise_id, rating, comment) VALUES (?, ?, ?, ?)", (session["user_id"], exercise_id, int(rating), comment)) #Inserts the new review into the review_exercise table
    conn.commit()
    conn.close()
    flash("Review added!") 
    return redirect(url_for("exercise_detail", exercise_id = exercise_id)) #Returns the page, displaying it to the user. The template can loop, showcasing each piece of data

#Logs the user by clearing their session
@app.route("/logout") 
def logout(): 
    session.clear() 
    return redirect(url_for("home"))

if __name__ == "__main__" : #Ensures the app runs when the file is executed
    with app.app_context():
        init_db()
    app.run(debug = True) #Starts the flask server and allows for real-time debugging