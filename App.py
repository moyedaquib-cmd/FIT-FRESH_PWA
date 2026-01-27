import os #Allows python to interact with the operating system
from flask import Flask, request, redirect, url_for, render_template, session #Imports flask which I will use to create my PWA, request which reads data sent from forms, render_template to render HTML files from the templates directory, session to remember information like login status, redirect to send a user to a different URL, url_for to generate a path to a different URL without having to code an entirely new one
from DB_Models import db, User, Workout #Imports the database controller object I created and the user table
from werkzeug.security import generate_password_hash, check_password_hash #Allows plaintext passwords to be stored as hashed values and checks between hashed passwords and plaintext passwords to match them
app = Flask(__name__) #This line creates the flask application
basedir = os.path.abspath(os.path.dirname(__file__)) #This line of code is used to turn the path into a fully resolved absolute path so that the program works on all operating systems. "__file__" relates to the full path of the file being executed. "os.path.dirname(__file__)" removes the file name 
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(basedir, "instance", "app.db") #This line builds the file path while telling flask exactly where the database is located. "SQLite:///" informs Flask to use SQLite and create an absolute path. "os.path.join" builds the file path. This makes it so that the program works with any operating systems and resolves correctly every time.
app.config["SECRET_KEY"] = "oJvneTznic84TgELjsKA" #This is a secret key used by flask to lock the login sessions so that people with no knowledge of the key cant access important information and tamper with cookies.
db.init_app(app) #Connects the database to the app
@app.route("/register", methods=["GET"]) #Returns the actual register page where the user can view and register an account
def register_page():
    return render_template("register.html")
@app.route("/register", methods=["POST"]) #This url is for the user to register an account. It aonly accepts POST requests as it handles sensitive data (passwords)
def register(): #This function runs when "/register" receives a POST request
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
    return "Successfully registered"
@app.route("/login", methods=["POST", "GET"]) #This function runs when "/login" receives a POST request
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
    return redirect(url_for("home"))
@app.route("/log-workout", methods=["GET"]) #Returns the page where the user can log workouts
def log_workout_page(): 
    if "user_id" not in session: #Redirects the user to the login page if their details are not found in the database
        return redirect(url_for("login"))
    return render_template("log_workout.html")
@app.route("/log-workout", methods=["POST"])
def log_workout():
    if "user_id" not in session: 
        return redirect (url_for("login"))
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
@app.route("/")
def home():
    return "RUNNING"
if __name__ == "__main__":
    #with app.app_context():
        #db.create_all()
    app.run(debug = True)