import sqlite3 #Allows pyton to interact with an SQLite3 database directly
import os #Allows Python to interact with the OS
basedir = os.path.abspath(os.path.dirname(__file__)) #Builds an absolute path to the DB file allowing it to worl on all OS
DB_PATH = os.path.join(basedir, "instance", "app.db") #The location of the DB file

#Opens and returns a connection to the SQLite3 database.
def get_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok = True) #Creates the instance folder if it doesn't exist
    conn = sqlite3.connect(DB_PATH) #Connects to the database file
    conn.row_factory = sqlite3.Row #Allows columns to be accessed by name instead of index
    conn.execute("PRAGMA foreign_keys = ON") #Enforces foreign key constraints
    return conn

#Creates all tables if they don't exist. 
def init_db():
    conn = get_db()
    cursor = conn.cursor() #Creates a cursor object from the database connection allowing interaction with data
    
    #Users table which stores registered accounts
    cursor.execute("CREATE TABLE IF NOT EXISTS user (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT NOT NULL UNIQUE, password_hash TEXT NOT NULL, role TEXT NOT NULL)") #Text not null makes it so that no empty information is collected. Additionally, "UNIQUE" makes it so tjhat no duplicate information is collected

    #Workouts table which stores logged workouts linked to the user
    cursor.execute("CREATE TABLE IF NOT EXISTS workout (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, workout_date TEXT NOT NULL DEFAULT (DATE('now')), exercise TEXT NOT NULL, sets INTEGER NOT NULL, reps INTEGER NOT NULL, weight REAL NOT NULL, FOREIGN KEY (user_id) REFERENCES user(id))") #Foreign Key indicates which table it has a relationship with
 
    #Calorie_Entry table which stores tracked meals and calories linked to a user
    cursor.execute("CREATE TABLE IF NOT EXISTS calorie_entry (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, entry_date TEXT NOT NULL DEFAULT (DATETIME('now')), meal TEXT NOT NULL, calories REAL NOT NULL, FOREIGN KEY (user_id) REFERENCES user(id))")

    #Exercise table which stores all exercises created by trainers
    cursor.execute("CREATE TABLE IF NOT EXISTS exercise (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, description TEXT NOT NULL, muscle_group TEXT NOT NULL, difficulty TEXT NOT NULL, image_url TEXT, trainer_id INTEGER NOT NULL, FOREIGN KEY (trainer_id) REFERENCES user(id))") #trainer_id links each exercise to the trainer who created it
    
    #Favourite_Exercise table which stores the exercises the 
    cursor.execute("CREATE TABLE IF NOT EXISTS favourite_exercise (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, exercise_id INTEGER NOT NULL, FOREIGN KEY (user_id) REFERENCES user(id), FOREIGN KEY (exercise_id) REFERENCES exercise(id), UNIQUE (user_id, exercise_id))") #UNIQUE prevents duplicate favourites for the same user and exercise

    #Review_Exercise table wich sotres user reviews and ratings for exercises
    cursor.execute("CREATE TABLE IF NOT EXISTS review_exercise (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, exercise_id INTEGER NOT NULL, rating INTEGER NOT NULL, comment TEXT, created_at TEXT NOT NULL DEFAULT (DATETIME('now')), FOREIGN KEY (user_id) REFERENCES user(id), FOREIGN KEY (exercise_id) REFERENCES exercise(id), UNIQUE (user_id, exercise_id))")
    
    conn.commit() #Saves all the table creations
    conn.close() #Closes the connection
