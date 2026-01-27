import os #Allows python to interact with the operating system
from flask import Flask #Imports flask which I will use to create my PWA
from DB_Models import db #Imports the database controller object I created
app = Flask(__name__) #This line creates the flask application
basedir = os.path.abspath(os.path.dirname(__file__)) #This line of code is used to turn the path into a fully resolved absolute path so that the program works on all operating systems. "__file__" relates to the full path of the file being executed. "os.path.dirname(__file__)" removes the file name 
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(basedir, "instance", "app.db") #This line builds the file path while telling flask exactly where the database is located. "SQLite:///" informs Flask to use SQLite and create an absolute path. "os.path.join" builds the file path. This makes it so that the program works with any operating systems and resolves correctly every time.
app.config["SECRET_KEY"] = "oJvneTznic84TgELjsKA" #This is a secret key used by flask to lock the login sessions so that people with no knowledge of the key cant access important information and tamper with cookies.
db.init_app(app) #Connects the database to the app

#with app.app_context():
    #db.create_all()