import os #Allows python to interact with the operating system
from flask import Flask, request, redirect, url_for, render_template, session #Imports flask which I will use to create my PWA, request which reads data sent from forms, render_template to render HTML files from the templates directory, session to remember information like login status, redirect to send a user to a different URL, url_for to generate a path to a different URL without having to code an entirely new one
from DB_Models import db, User, Workout, CalorieEntry #Imports the database controller object I created and the user table
from datetime import datetime #Imports datetime which allows the user to have the time they logged their calories/workouts saved
from werkzeug.security import generate_password_hash, check_password_hash #Allows plaintext passwords to be stored as hashed values and checks between hashed passwords and plaintext passwords to match them
import pytz #A timezone database to convert to ohter timezones
app = Flask(__name__) #This line creates the flask application
basedir = os.path.abspath(os.path.dirname(__file__)) #This line of code is used to turn the path into a fully resolved absolute path so that the program works on all operating systems. "__file__" relates to the full path of the file being executed. "os.path.dirname(__file__)" removes the file name 
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(basedir, "instance", "app.db") #This line builds the file path while telling flask exactly where the database is located. "SQLite:///" informs Flask to use SQLite and create an absolute path. "os.path.join" builds the file path. This makes it so that the program works with any operating systems and resolves correctly every time.
app.config["SECRET_KEY"] = "oJvneTznic84TgELjsKA" #This is a secret key used by flask to lock the login sessions so that people with no knowledge of the key cant access important information and tamper with cookies.
db.init_app(app) #Connects the database to the app

def local_time(utc_dt): #A function that Converts UTC to Sydney Time
    local_tz = pytz.timezone("Australia/Sydney") #The tiemzone it converts to is Sydney, Australia
    return utc_dt.replace(tzinfo=pytz.utc).astimezone(local_tz) #Replaces UTC with the timezone of Sydney Australia

@app.route("/") #The home page
def home():
    return render_template("home.html")

@app.route("/register", methods=["GET", "POST"]) #This url is for the user to register an account.
def register_page():
    if request.method == "GET":
        return render_template("register.html")
    username = request.form.get("username") #Requests the following values to send to the server from the website
    password = request.form.get("password")
    role = request.form.get("role")
    if not username or not password or not role: #Stops empty submissions to prevent incomplete database records. Also returns HTTP 400 (Bad Request)
        return "Please fill in all the fields", 400
    existing_user = User.query.filter_by(username=username).first() #Checks for duplicate usernames by searching the user table and finding a maching username
    if existing_user: #Prevents duplicate accounts to avoid ambiguity and allow the databases to be unique.
        return "Username already exists", 400
    hashed_password = generate_password_hash(password) #Generates a secure hash from the password
    new_user = User(username=username, password_hash=hashed_password, role=role)
    db.session.add(new_user) #These lines save the program to the database "add()" stages the object while "Commit()" permanently saves it
    db.session.commit() #Confirms the user has successfully registered
    return redirect(url_for("login"))

@app.route("/login", methods=["POST", "GET"]) #The login page
def login():
    if request.method == "GET":
        return render_template("login.html")
    username = request.form.get("username")
    password = request.form.get("password")
    if not username or not password:
        return "Please fill in all the fields", 400
    user =  User.query.filter_by(username=username).first()
    if not user: #If no account exists with the username filled in, the PWA doesn't allows them to log in
        return "Invalid username or password", 401 #Invalid username or passwird increases safety as attackers dont know what is wrong with their login form
    if not check_password_hash(user.password_hash, password): #Checks the hashed password with the user table and compares the plaintext and hashed versions to see if the password is correct
        return "Invalid username or password", 401
    session["user_id"] = user.id #Stores the user's unique ID allowing easy identification of the logged-in user
    session["role"] = user.role #Stores the role of the user to enable role-based access control
    if user.role == "gym_goer": #Based ont the user's role, they're redirected to a particular dashboard
        return redirect(url_for("gym_goer_dashboard"))
    else:
        return redirect(url_for("personal_trainer_dashboard"))

@app.route("/gym-goer-dashboard") #dashboard only accessible to gym goers
def gym_goer_dashboard():
    if "user_id" not in session: #If they are not logged in, they're sent to the home page
        return redirect(url_for("home"))
    if session.get("role") != "gym_goer": #If they are not a gym goer they are shown an error message
        return "Only gym goers can access the dashboard", 403
    return render_template("gym_goer_dashboard.html")

@app.route("/personal-trainer-dashboard") #Personal trainer dashboard
def personal_trainer_dashboard():
    if "user_id" not in session:
        return redirect(url_for("home"))
    if session.get("role") == "gym_goer":
        return "Only personal trainers can access the dashboard", 403
    return render_template("personal_trainer_dashboard.html")

@app.route("/log-workout", methods=["GET", "POST"]) #Returns the page where the user can log workouts
def log_workout():
    if "user_id" not in session:  #Redirects the user to the home page if their details are not found in the database
        return redirect(url_for("home"))
    if request.method == "GET":
        return render_template("log_workout.html")
    exercise = request.form.get("exercise")
    sets = request.form.get("sets")
    reps = request.form.get("reps")
    weight = request.form.get("weight")
    if not exercise or not sets or not reps or not weight:
        return "Please fill in all the fields", 400
    workout = Workout(user_id = session["user_id"], exercise = exercise, sets = int(sets), reps = int(reps), weight = float(weight))
    db.session.add(workout)
    db.session.commit()
    return "Workout Logged!"

@app.route("/workout-history") #The place where the user can see their workout history (all the workouts they have logged)
def workout_history():
    if "user_id" not in session:
        return redirect(url_for("home"))
    workouts = Workout.query.filter_by(user_id = session["user_id"]).order_by(Workout.workout_date.desc()).all() #Workouts are sorted by the date that they are added (descending)
    return render_template("workout_history.html", workouts = workouts)

@app.route("/log-calories", methods = ["GET", "POST"]) #Returns the page where the user can log calories
def log_calories():
    if "user_id" not in session:
        return redirect(url_for("home"))
    if request.method == "GET":
        return render_template("log_calories.html")
    meal = request.form.get("meal")
    calories = request.form.get("calories")
    if not calories or not meal:
        return "Please fill in all the fields", 400
    calorie_entry = CalorieEntry(user_id = session["user_id"], meal = meal, calories = int(calories))
    db.session.add(calorie_entry)
    db.session.commit()
    return redirect(url_for("calorie_history"))
@app.route("/calorie-history")  #The place where the user can see their calorie history (all the calories they have tracked)
def calorie_history():
    if "user_id" not in session:
        return redirect(url_for("home"))
    entries = CalorieEntry.query.filter_by(user_id = session["user_id"]).order_by(CalorieEntry.entry_date.desc()).all()
    for entry in entries: #Converts UTC to local time
        entry.local_time = local_time(entry.entry_date)
    return render_template("calorie_tracker.html", entries = entries)

@app.route("/logout") #Ends the app if the user chooses to
def logout():
    session.clear()
    return redirect(url_for("home"))

if __name__ == "__main__":
    #with app.app_context():
        #db.create_all()
    app.run(debug = True)