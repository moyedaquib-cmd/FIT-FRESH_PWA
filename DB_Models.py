from flask_sqlalchemy import SQLAlchemy #Allows communication with a SQL database through Python code
from flask_login import UserMixin #Allows the user to log in and saves their data
from datetime import date, datetime # #Datetime allows date and time to be viewed by the user
db = SQLAlchemy() #Creates a database controller object that creates tables and saves/retrieves data. 
class User(db.Model, UserMixin): #This defines a user table. db.Model tells SQLAlchemy that this class is a database table. UserMixin creates a login_system automatically that Flask-Login uses to authenticate and identify users securely.
    id = db.Column(db.Integer, primary_key = True) #Creates a unique ID integer for each user
    username = db.Column(db.String(50), unique = True, nullable = False) #Stores a login name (50 characters) that has to be unique and is required to exist 
    password_hash = db.Column(db.String(255), nullable = False) #Stores the hashed password (255 characters)
    role = db.Column(db.String(20), nullable = False) #Stores the role of the user (gym goer or personal trainer)
class Workout(db.Model): #This defines a workouts table to log exercises.
    id = db.Column(db.Integer, primary_key = True) #Creates a unique ID integer for each user
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable = False) #Links workout to the logged-in user
    workout_date = db.Column(db.Date, default = date.today, nullable = False) #The date the workout occured, defaults to the day the user is logging the workout
    exercise = db.Column(db.String(100), nullable = False) #What type of exercise it is
    sets = db.Column(db.Integer, nullable = False) #How many sets the user performed
    reps = db.Column(db.Integer, nullable = False) #How many reps of each exercise the user performed
    weight = db.Column(db.Float, nullable = False) #The weight that they exercised with
class CalorieEntry(db.Model): #A table that stores the calories tracked by the user for each meal.
    id = db.Column(db.Integer, primary_key = True)  #Creates a unique ID integer for each user
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable = False) #Links calories to the logged-in user 
    entry_date = db.Column(db.DateTime, default = datetime.utcnow, nullable = False) #The date and time the user tracked the calories
    meal = db.Column(db.String(50), nullable = False) #Meal
    calories = db.Column(db.Float, nullable = False) #Calories of the meal
class Exercise(db.Model): #A table that stores the exercise added by the trainer.
    id = db.Column(db.Integer, primary_key = True)  #Creates a unique ID integer for each user
    name = db.Column(db.String(100), nullable = False) #Name of the exercise
    description = db.Column(db.String(50), nullable = False) #Description of the exercise
    muscle_group = db.Column(db.String(50), nullable = False) #What muscle group it affects
    difficulty = db.Column(db.String(20), nullable = False) #How difficult it's to perform
    image_url = db.Column(db.String(255)) #The image of the exercise
    trainer_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable = False) #Links Exercise to the logged-in user 
class Favourite(db.Model): #A table that stores the user's favourite exercises
    id = db.Column(db.Integer, primary_key = True) #Creates a unique ID integer for each user
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable = False) #Links favourite to the logged-in user 
    exercise_id = db.Column(db.Integer, db.ForeignKey("exercise.id"), nullable = False) #Links the exercise to its id
    __table_args__ = (db.UniqueConstraint("user_id", "exercise_id"), ) #Database blocks duplicate favourites from being added.