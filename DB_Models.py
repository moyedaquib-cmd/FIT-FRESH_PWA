from flask_sqlalchemy import SQLAlchemy #Imports SQLAlchemy which lets Python connect to a database without writing SQL
from flask_login import UserMixin #Imports UserMixin which tracks logged-in users, manages sessions and provides login-related features
db = SQLAlchemy() #Creates a database controller object that creates tables and saves/retrieves data. Connects SQL and Python
class User(db.Model, UserMixin): #This defines a user table. db.Model tells SQLAlchemy that this class is a database table. UserMixin creates a login_system automatically that Flask-Login uses to authenticate and identify users securely.
    id = db.Column(db.Integer, primary_key = True) #Creates a unique ID integer for each user
    username = db.Column(db.String(50), unique = True, nullable = False) #Stores a login name (50 characters) that has to be unique and is required to exist 
    password_hash = db.Column(db.String(255), nullable = False) #Stores the hashed password (255 characters)
    role = db.Column(db.String(20), nullable = False) #Stores the role of the user (gym goer or personal trainer)