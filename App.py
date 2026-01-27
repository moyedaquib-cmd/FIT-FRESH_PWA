import os #Allows python to interact with the operating system
from flask import Flask, request, redirect, url_for, render_template #Imports flask which I will use to create my PWA, request which reads data sent from forms
from DB_Models import db, User #Imports the database controller object I created and the user table
from werkzeug.security import generate_password_hash #Allows plaintext passwords to be stored as hashed values
app = Flask(__name__) #This line creates the flask application
basedir = os.path.abspath(os.path.dirname(__file__)) #This line of code is used to turn the path into a fully resolved absolute path so that the program works on all operating systems. "__file__" relates to the full path of the file being executed. "os.path.dirname(__file__)" removes the file name 
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(basedir, "instance", "app.db") #This line builds the file path while telling flask exactly where the database is located. "SQLite:///" informs Flask to use SQLite and create an absolute path. "os.path.join" builds the file path. This makes it so that the program works with any operating systems and resolves correctly every time.
app.config["SECRET_KEY"] = "oJvneTznic84TgELjsKA" #This is a secret key used by flask to lock the login sessions so that people with no knowledge of the key cant access important information and tamper with cookies.
db.init_app(app) #Connects the database to the app
@app.route("/register", methods=["GET"])
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
@app.route("/")
def home():
    return "RUNNING"
if __name__ == "__main__":
    app.run(debug = True)
#with app.app_context():
    #db.create_all()