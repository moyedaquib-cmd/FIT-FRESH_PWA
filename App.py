import os #Allows python to interact with the operating system
from flask import Flask, request, redirect, url_for, render_template, session, flash #Flask: a lightweight web framework for Python that allows the creation of PWA, request: Allows Python to access data sent by the user, redirect: Send the user to a different URL, url_for: Uses the name of a function to create a URL path, render_template: Allows the use of Jinja2 to develop dynamic HTML pages, session: Allows users to store data across multiple HTTP requests, flash: Provides messages to the user that they can view
from DB_Models import db, User, Workout, CalorieEntry, Exercise, Favourite_Exercise, Review_Exercise #Imports all of the databases I created.
from datetime import datetime #Datetime allows date and time to be viewed by the user
from werkzeug.security import generate_password_hash, check_password_hash #Werkzeug allows the hashing of passwords. generate_password_hash creates a hash from a password and check_password_hash checks the password with the hashed versions to verify the account
import pytz #A timezone database to convert to other timezones
app = Flask(__name__) #Creates the flask application
basedir = os.path.abspath(os.path.dirname(__file__)) #\Turns the path into a fully resolved absolute path so that the program works on all operating systems. "__file__" relates to the full path of the file being executed. "os.path.dirname(__file__)" removes the file name 
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(basedir, "instance", "app.db") #Builds the file path while telling flask exactly where the database is located. "SQLite:///" informs Flask to use SQLite and create an absolute path. "os.path.join" builds the file path. This makes it so that the program works with any operating systems and resolves correctly every time.
app.config["SECRET_KEY"] = "oJvneTznic84TgELjsKA" #This is a secret key used by flask to lock the login sessions so that people with no knowledge of the key cant access important information and tamper with cookies.
db.init_app(app) #Connects the database to the app

def local_time(utc_dt): #A function that Converts UTC to Sydney Time
    local_tz = pytz.timezone("Australia/Sydney") #The timezone it converts to is Sydney, Australia
    return utc_dt.replace(tzinfo=pytz.utc).astimezone(local_tz) #Replaces UTC with the timezone of Sydney Australia

#Home Page
@app.route("/") #Tells flask to run the function below this decorator when someone visits the url
def home(): #The function that runs when someone visits the url
    return render_template("home.html") #Loads an html file from the templates folder

#Register page where a new user can create an account
@app.route("/register", methods=["GET", "POST"]) #Tells flask to run the function below this decorator when someone visits the url. The route can respond to both GET requests (occurs when the user loads the page) and POST requests (occurs when the user submits a form)
def register_page():  #The function that runs when someone visits the url
    if request.method == "GET": #What happens when it's a GET request
        return render_template("register.html")
    #Requests the following values to send to the server from the website
    username = request.form.get("username")
    password = request.form.get("password")
    role = request.form.get("role")
    if not username or not password or not role: #Stops empty submissions to prevent incomplete database records. Also returns HTTP 400 (Bad Request)
        return "Please fill in all the fields", 400
    existing_user = User.query.filter_by(username=username).first() #Checks for duplicate usernames by searching the user table and finding a maching username
    if existing_user: #Prevents duplicate accounts to avoid ambiguity and allow the databases to be unique.
        flash("Username already exists") #Showcases a message to the user
        return redirect(url_for("register_page")) #Redirects the user to a particular page
    hashed_password = generate_password_hash(password) #Generates a secure hash from the password
    #Creates and saves the information to the respective table
    new_user = User(username=username, password_hash=hashed_password, role=role)
    db.session.add(new_user) 
    db.session.commit() 
    flash("Account created successfully. Please log in") #Showcases a message to the user
    return redirect(url_for("login"))  #Redirects the user to a particular page

#Login page where existing users can access their account
@app.route("/login", methods=["POST", "GET"]) #Tells flask to run the function below this decorator when someone visits the url. The route can respond to both GET requests (occurs when the user loads the page) and POST requests (occurs when the user submits a form)
def login(): #The function that runs when someone visits the url
    if request.method == "GET": #What happens when it's a GET request
        return render_template("login.html") #Returns the page, displaying it to the user
    #Requests the following values to send to the server from the website
    username = request.form.get("username")
    password = request.form.get("password")
    if not username or not password:
        return "Please fill in all the fields", 400 #Stops empty submissions to prevent incomplete database records. Also returns HTTP 400 (Bad Request)
    user =  User.query.filter_by(username=username).first() #Checks if the username matches
    if not user: #If no account exists with the username, the PWA doesn't allows them to log in
        flash("Invalid username or password") #Showcases a message to the user
        return redirect(url_for("login")) #Redirects the user to a particular page
    if not check_password_hash(user.password_hash, password): #Checks the hashed password with the user table and compares the plaintext and hashed versions to see if the password is correct
        return "Invalid username or password", 401 #401 Error indicates that the request failed due to unauthorised credentials.
    session["user_id"] = user.id #Stores the user's unique ID allowing easy identification of the logged-in user
    session["role"] = user.role #Stores the role of the user to enable role-based access control
    #Based on the user's role, they're redirected to a particular dashboard
    if user.role == "gym_goer": 
        flash("Logged in successfully") #Showcases a message to the user
        return redirect(url_for("gym_goer_dashboard")) #Redirects the user to a particular page
    else: 
        flash("Logged in successfully") #Showcases a message to the user
        return redirect(url_for("personal_trainer_dashboard")) #Redirects the user to a particular page


#The dashboard for gym_goers where they can access features only accessible to them
@app.route("/gym-goer-dashboard") #Tells flask to run the function below this decorator when someone visits the url.
def gym_goer_dashboard(): #The function that runs when someone visits the url
    if "user_id" not in session: #If they are not logged in, they're sent to the home page
        return redirect(url_for("home")) #Redirects the user to a particular page
    if session.get("role") != "gym_goer": #If they are not a gym goer they are shown an error message
        return "Only gym goers can access the dashboard", 403 #403 Error indicates that the user is unauthorised from accessing the information
    return render_template("gym_goer_dashboard.html") #Returns the page, displaying it to the user

#The dashboard for gym_goers where they can access features only accessible to them
@app.route("/personal-trainer-dashboard") #Tells flask to run the function below this decorator when someone visits the url.
def personal_trainer_dashboard():  #The function that runs when someone visits the url
    if "user_id" not in session: #If they are not logged in, they're sent to the home page
        return redirect(url_for("home")) #Redirects the user to a particular page
    if session.get("role") == "gym_goer": #If they are a gym goer they are shown an error message
        return "Only personal trainers can access the dashboard", 403 #403 Error indicates that the user is unauthorised from accessing the information
    return render_template("personal_trainer_dashboard.html") #Returns the page, displaying it to the user

#A feature where users can log workouts
@app.route("/log-workout", methods=["GET", "POST"]) #Tells flask to run the function below this decorator when someone visits the url. The route can respond to both GET requests (occurs when the user loads the page) and POST requests (occurs when the user submits a form)
def log_workout(): #The function that runs when someone visits the url
    if "user_id" not in session:  #Redirects the user to the home page if their details are not found in the database
        return redirect(url_for("home")) #Redirects the user to a particular page
    if request.method == "GET":  #What happens when it's a GET request
        return render_template("log_workout.html") #Returns the page, displaying it to the user
    #Requests the following values to send to the server from the website
    exercise = request.form.get("exercise")
    sets = request.form.get("sets")
    reps = request.form.get("reps")
    weight = request.form.get("weight")
    #Stops empty / wrong submissions to prevent incomplete / incorrect database records. Also returns HTTP 400 (Bad Request)
    if not exercise or not sets or not reps or not weight:
        return "Please fill in all the fields", 400
    if int(sets) < 0:
        return "Sets must be positive", 400
    if int(reps) < 0:
        return "Reps must be positive", 400
    if float(weight) < 0:
        return "Weight must be positive", 400
    #Creates and saves the information to the respective table
    workout = Workout(user_id = session["user_id"], exercise = exercise, sets = int(sets), reps = int(reps), weight = float(weight))
    db.session.add(workout)
    db.session.commit()
    return redirect(url_for("workout_history")) #Returns the page, displaying it to the user

#The place where the user can see their workout history (all the workouts they have logged)
@app.route("/workout-history") #Tells flask to run the function below this decorator when someone visits the url.
def workout_history(): #The function that runs when someone visits the url
    if "user_id" not in session:  #Redirects the user to the home page if their details are not found in the database
        return redirect(url_for("home")) #Redirects the user to a particular page
    workouts = Workout.query.filter_by(user_id = session["user_id"]).order_by(Workout.workout_date.desc()).all() #Workouts are sorted by the date that they are added (descending)
    return render_template("workout_history.html", workouts = workouts) # Returns the page, displaying it to the user. The template can loop, showcasing each piece of data

#The page where the user can log calories
@app.route("/log-calories", methods = ["GET", "POST"])  #Tells flask to run the function below this decorator when someone visits the url. The route can respond to both GET requests (occurs when the user loads the page) and POST requests (occurs when the user submits a form)
def log_calories(): #The function that runs when someone visits the url
    if "user_id" not in session: #Redirects the user to the home page if their details are not found in the database
        return redirect(url_for("home")) #Redirects the user to a particular page
    if request.method == "GET": #What happens when it's a GET request
        return render_template("log_calories.html") #Returns the page, displaying it to the user
    #Requests the following values to send to the server from the website
    meal = request.form.get("meal")
    calories = request.form.get("calories")
    #Stops empty / wrong submissions to prevent incomplete / incorrect database records. Also returns HTTP 400 (Bad Request)
    if not calories or not meal:
        return "Please fill in all the fields", 400
    if float(calories) < 0:
        return "Calories must be positive", 400
    #Creates and saves the information to the respective table
    calorie_entry = CalorieEntry(user_id = session["user_id"], meal = meal, calories = float(calories))
    db.session.add(calorie_entry)
    db.session.commit()
    return redirect(url_for("calorie_history")) #Redirects the user to a particular page

#The place where the user can see their calorie history (all the calories they have tracked)
@app.route("/calorie-history") #Tells flask to run the function below this decorator when someone visits the url.
def calorie_history(): #The function that runs when someone visits the url
    if "user_id" not in session: #Redirects the user to the home page if their details are not found in the database
        return redirect(url_for("home")) #Redirects the user to a particular page
    entries = CalorieEntry.query.filter_by(user_id = session["user_id"]).order_by(CalorieEntry.entry_date.desc()).all() #Calories are sorted by the date that they are added (descending)
    for entry in entries: #Loop converts each entry's UTC to local time and stores it in a variable
        entry.local_time = local_time(entry.entry_date)
    return render_template("calorie_tracker.html", entries = entries) # Returns the page, displaying it to the user. The template can loop, showcasing each piece of data

#A page to allows users to edit their data
@app.route("/edit-workout/<int:workout_id>", methods = ["GET", "POST"]) #Tells flask to run the function below this decorator when someone visits the url. The route can respond to both GET requests (occurs when the user loads the page) and POST requests (occurs when the user submits a form). This is a dynamic route based on the id of the object
def edit_workout(workout_id): #The function that runs when someone visits the url. The parameter informs which object the user wants to edit.
    if "user_id" not in session: #Redirects the user to the home page if their details are not found in the database
        return redirect(url_for("home")) #Redirects the user to a particular page
    workout = Workout.query.get_or_404(workout_id) #Searches the table and returns a 404 error (the object doesn't exist) if nothing is found
    if workout.user_id != session ["user_id"]: #Confirms that the object belongs to the user
        return "Unauthorised user", 403 #403 Error indicates that the user is unauthorised from accessing the information
    if request.method == "GET": #What happens when it's a GET request
        return render_template("edit_workout.html", workout = workout) # Returns the page, displaying it to the user. The template can loop, showcasing each piece of data
    #Requests the following values to send to the server from the database
    workout.exercise = request.form.get("exercise")
    workout.sets = int(request.form.get("sets"))
    workout.reps = int(request.form.get("reps"))
    workout.weight = float(request.form.get("weight"))
    #Saves the information to the respective table
    db.session.commit() 
    flash("Workout Updated") #Showcases a message to the user
    return redirect(url_for("workout_history")) #Redirects the user to a particular page

#Allows users to delete data
@app.route("/delete-workout/<int:workout_id>", methods = ["POST"]) #Tells flask to run the function below this decorator when someone visits the url. The route can respond to POST requests (occurs when the user submits a form). This is a dynamic route based on the id of the object
def delete_workout(workout_id): #The function that runs when someone visits the url. The parameter informs which object the user wants to edit
    if "user_id" not in session: #Redirects the user to the home page if their details are not found in the database
        return redirect(url_for("home")) #Redirects the user to a particular page
    workout = Workout.query.get_or_404(workout_id) #Searches the table and returns a 404 error (the object doesn't exist) if nothing is found
    if workout.user_id != session ["user_id"]: #Confirms that the object belongs to the user
        return "Unauthorised user", 403 #403 Error indicates that the user is unauthorised from accessing the information
    #Deletes the information from the respective table and saves the new one
    db.session.delete(workout)
    db.session.commit()
    flash("Workout Deleted") #Showcases a message to the user
    return redirect(url_for("workout_history")) #Redirects the user to a particular page

#A page to allows users to edit their data
@app.route("/edit-calories/<int:entry_id>", methods = ["GET", "POST"]) #Tells flask to run the function below this decorator when someone visits the url. The route can respond to both GET requests (occurs when the user loads the page) and POST requests (occurs when the user submits a form). This is a dynamic route based on the id of the object
def edit_calories(entry_id): #The function that runs when someone visits the url. The parameter informs which object the user wants to edit
    if "user_id" not in session: #Redirects the user to the home page if their details are not found in the database
        return redirect(url_for("home")) #Redirects the user to a particular page
    entry = CalorieEntry.query.get_or_404(entry_id) #Searches the table and returns a 404 error (the object doesn't exist) if nothing is found
    if entry.user_id != session ["user_id"]: #Confirms that the object belongs to the user
        return "Unauthorised user", 403 #403 Error indicates that the user is unauthorised from accessing the information
    if request.method == "GET": #What happens when it's a GET request
        return render_template("edit_calories.html", entry = entry) # Returns the page, displaying it to the user. The template can loop, showcasing each piece of data
     #Requests the following values to send to the server from the database
    entry.meal = request.form.get("meal") 
    entry.calories = float(request.form.get("calories"))
    #Saves the information to the respective table
    db.session.commit()
    flash("Calories Updated") #Showcases a message to the user
    return redirect(url_for("calorie_history")) #Redirects the user to a particular page

#Allows users to delete data
@app.route("/delete-calories/<int:entry_id>", methods = ["POST"])  #Tells flask to run the function below this decorator when someone visits the url. The route can respond to POST requests (occurs when the user submits a form). This is a dynamic route based on the id of the object
def delete_calories(entry_id): #The function that runs when someone visits the url. The parameter informs which object the user wants to edit
    if "user_id" not in session: #Redirects the user to the home page if their details are not found in the database
        return redirect(url_for("home")) #Redirects the user to a particular page
    entry = CalorieEntry.query.get_or_404(entry_id) #Searches the table and returns a 404 error (the object doesn't exist) if nothing is found
    if entry.user_id != session ["user_id"]: #Confirms that the object belongs to the user
        return "Unauthorised user", 403 #403 Error indicates that the user is unauthorised from accessing the information
    #Deletes the information from the respective table and saves the new one
    db.session.delete(entry)
    db.session.commit()
    flash("Calories Deleted") #Showcases a message to the user
    return redirect(url_for("calorie_history")) #Redirects the user to a particular page

#Allows trainers to add an exercise which people can view
@app.route("/add-exercise", methods = ["GET", "POST"]) #Tells flask to run the function below this decorator when someone visits the url. The route can respond to both GET requests (occurs when the user loads the page) and POST requests (occurs when the user submits a form).
def add_exercise(): #The function that runs when someone visits the url
    if "user_id" not in session or session.get("role") == "gym_goer": #Redirects the user to the home page if their details are not found in the database or they are a gym_goer
        flash("Access denied!") #Showcases a message to the user
        return redirect(url_for("home")) #Redirects the user to a particular page
    if request.method == "POST":  #What happens when it's a POST request
        #Requests the following values to send to the server from the webpage
        name = request.form["name"]
        description = request.form["description"]
        muscle_group = request.form["muscle_group"]
        image_url = request.form.get("image_url")
        difficulty = request.form["difficulty"]
        #Saves the information to the respective table
        exercise = Exercise(name = name, description = description, muscle_group = muscle_group,  difficulty = difficulty, image_url = image_url, trainer_id = session["user_id"])
        db.session.add(exercise)
        db.session.commit()
        flash("Exercise added successfully! ") #Showcases a message to the user
        return redirect(url_for("personal_trainer_dashboard")) #Redirects the user to a particular page
    return render_template("add_exercise.html") # Returns the page, displaying it to the user.

#The page where users can view the exercises
@app.route("/exercises") #Tells flask to run the function below this decorator when someone visits the url.
def exercises():  #The function that runs when someone visits the url
    exercises = Exercise.query.all() #Retrieves every record from the table
    return render_template("exercises.html", exercises = exercises) # Returns the page, displaying it to the user. The template can loop, showcasing each piece of data

#Users can click on the exercise to view details about it.
@app.route("/exercise/<int:exercise_id>") #Tells flask to run the function below this decorator when someone visits the url. This is a dynamic route based on the id of the object
def exercise_detail(exercise_id):  #The function that runs when someone visits the url. The parameter informs which object the user wants to view
    exercise = Exercise.query.get_or_404(exercise_id) #Searches the table and returns a 404 error (the object doesn't exist) if nothing is found
    is_favourite = False
    reviews = Review_Exercise.query.filter_by(exercise_id = exercise.id).all()
    if "user_id" in session:
        is_favourite = Favourite_Exercise.query.filter_by(user_id = session["user_id"], exercise_id = exercise.id).first() is not None
    return render_template("exercise_detail.html", exercise = exercise, is_favourite = is_favourite, reviews = reviews) # Returns the page, displaying it to the user. The template can loop, showcasing each piece of data

#A feature that allows user to favourite an exercise and save it
@app.route("/toggle-favourite/<int:exercise_id>", methods = ["POST"]) #Tells flask to run the function below this decorator when someone visits the url. The route can respond to POST requests (occurs when the user submits a form). This is a dynamic route based on the id of the object  
def toggle_favourite(exercise_id):  #The function that runs when someone visits the url. The parameter informs which object the user wants to view
    if "user_id" not in session:  #Redirects the user to the home page if their details are not found in the database
        return redirect(url_for("home")) #Redirects the user to a particular page
    favourite = Favourite_Exercise.query.filter_by(user_id = session["user_id"], exercise_id = exercise_id).first() #Looks for a row in the Favourite table that matches the current user and the exercise they clicked on
    if favourite: #If the favourite exists it removes it
        db.session.delete(favourite)
        db.session.commit()
        flash("Removed from Favourites")
    else:  #If the favourite doesn't exist it adds it to the table
        new_favourite = Favourite_Exercise(user_id = session["user_id"], exercise_id = exercise_id)
        db.session.add(new_favourite)
        flash("Added to favourites")
        db.session.commit()
    return redirect(url_for("exercise_detail", exercise_id = exercise_id)) #redirects the user to the exercise_detail page

#Where the users can view their saved exercises
@app.route("/view-favourites") #Tells flask to run the function below this decorator when someone visits the url.
def view_favourites():  #The function that runs when someone visits the url.
    if "user_id" not in session: #Redirects the user to the home page if their details are not found in the database
        return redirect(url_for(home)) #Redirects the user to a particular page
    favourite_exercises = db.session.query(Exercise).join(Favourite_Exercise, Favourite_Exercise.exercise_id == Exercise.id).filter(Favourite_Exercise.user_id == session ["user_id"]) #Selects data from the exercise table and joins it to the favourite_exercise table and filters the data to the ones only the logged-in users can view
    return render_template("view_favourites.html", exercises = favourite_exercises) # Returns the page, displaying it to the user. The template can loop, showcasing each piece of data

#Allows users to add reviews
@app.route("/add-review/<int:exercise_id>", methods = ["POST"]) #Tells flask to run the function below this decorator when someone visits the url. The route can respond to POST requests (occurs when the user submits a form). This is a dynamic route based on the id of the object
def add_review(exercise_id): #The function that runs when someone visits the url.
    if "user_id" not in session: #Redirects the user to the home page if their details are not found in the database
        return redirect(url_for("home")) #Redirects the user to a particular page
    #Requests the following values to send to the server from the webpage
    rating = float(request.form.get("rating")) 
    comment = request.form.get("comment")
    #Doesn't allow invalid ratings
    if rating < 1 or rating > 5:
        flash("Rating must be between 1 and 5")
        return redirect(url_for("exercise_detail", exercise_id = exercise_id)) #Redirects the user to a particular page
    existing_Review = Review_Exercise.query.filter_by(user_id = session["user_id"], exercise_id = exercise_id).first() #Looks for a row in the Review_Exercise table that matches the current user and the review they left
    if existing_Review: #Doesn't allow users to leave more than 1 review
        flash("You can't leave more than 1 review")
        return redirect(url_for("exercise_detail", exercise_id = exercise_id)) #Redirects the user to a particular page. 
    #Saves the information to the respective table
    review = Review_Exercise(user_id = session["user_id"], exercise_id = exercise_id, rating = rating, comment = comment) 
    db.session.add(review)
    db.session.commit()
    flash("Review added!") #Showcases a message to the user
    return redirect(url_for("exercise_detail", exercise_id = exercise_id)) #Returns the page, displaying it to the user. The template can loop, showcasing each piece of data

#Ends the app if the user chooses to
@app.route("/logout") #Tells flask to run the function below this decorator when someone visits the url.
def logout(): #The function that runs when someone visits the url.
    session.clear() #Removes all data stored in the user’s session.
    return redirect(url_for("home")) #Redirects the user to a particular page

if __name__ == "__main__": #Ensures the app runs when the file is executed
    #with app.app_context():
        #db.create_all()
    app.run(debug = True) #Starts the flask server and allows for real-time debugging