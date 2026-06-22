import sqlite3 #Allows pyton to interact with an SQLite3 database directly
import os #Allows Python to interact with the OS
basedir = os.path.abspath(os.path.dirname(__file__)) #Builds an absolute path to the DB file allowing it to worl on all OS
DB_PATH = os.path.join(basedir, "instance", "app.db") #The location of the DB file

#Opens and returns a connection to the SQLite3 database.
def get_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok = True) #Creates the instance folder if it doesn't exist
    conn = sqlite3.connect(DB_PATH, timeout = 10) #Connects to the database file. Timeout = 10 makes SQLite wait up to 10 seconds for a lock to clear instead of causing an error.
    conn.row_factory = sqlite3.Row #Allows columns to be accessed by name instead of index
    conn.execute("PRAGMA foreign_keys = ON") #Enforces foreign key constraints
    conn.execute("PRAGMA journal_mode = WAL") #Write-Ahead Logging lets reads and writes happen at the same time, greatly reducing "database is locked" errors
    conn.execute("PRAGMA busy_timeout = 10000") #Backup lock wait of 10 seconds at the SQLIte engine level
    return conn

#Creates all tables if they don't exist. 
def init_db():
    conn = get_db()
    cursor = conn.cursor() #Creates a cursor object from the database connection allowing interaction with data
    
    #Users table stores registered accounts
    cursor.execute("CREATE TABLE IF NOT EXISTS user (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT NOT NULL UNIQUE, password_hash TEXT NOT NULL, role TEXT NOT NULL)") #Text not null makes it so that no empty information is collected. Additionally, "UNIQUE" makes it so tjhat no duplicate information is collected

    #Workouts table stores logged workouts linked to the user
    cursor.execute("CREATE TABLE IF NOT EXISTS workout (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, workout_date TEXT NOT NULL DEFAULT (DATE('now')), exercise TEXT NOT NULL, sets INTEGER NOT NULL, reps INTEGER NOT NULL, weight REAL NOT NULL, FOREIGN KEY (user_id) REFERENCES user(id))") #Foreign Key indicates which table it has a relationship with
 
    #Calorie_Entry table stores tracked meals and calories linked to a user
    cursor.execute("CREATE TABLE IF NOT EXISTS calorie_entry (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, entry_date TEXT NOT NULL DEFAULT (DATETIME('now')), meal TEXT NOT NULL, calories REAL NOT NULL, FOREIGN KEY (user_id) REFERENCES user(id))")

    #Exercise table stores all exercises created by trainers
    cursor.execute("CREATE TABLE IF NOT EXISTS exercise (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, description TEXT NOT NULL, muscle_group TEXT NOT NULL, difficulty TEXT NOT NULL, image_url TEXT, trainer_id INTEGER NOT NULL, FOREIGN KEY (trainer_id) REFERENCES user(id))") #trainer_id links each exercise to the trainer who created it
    
    #Favourite_Exercise table stores the exercises the 
    cursor.execute("CREATE TABLE IF NOT EXISTS favourite_exercise (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, exercise_id INTEGER NOT NULL, FOREIGN KEY (user_id) REFERENCES user(id), FOREIGN KEY (exercise_id) REFERENCES exercise(id), UNIQUE (user_id, exercise_id))") #UNIQUE prevents duplicate favourites for the same user and exercise

    #Review_Exercise table sotres user reviews and ratings for exercises
    cursor.execute("CREATE TABLE IF NOT EXISTS review_exercise (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, exercise_id INTEGER NOT NULL, rating INTEGER NOT NULL, comment TEXT, created_at TEXT NOT NULL DEFAULT (DATETIME('now')), FOREIGN KEY (user_id) REFERENCES user(id), FOREIGN KEY (exercise_id) REFERENCES exercise(id), UNIQUE (user_id, exercise_id))")
    
    #MealPlan Table stores the diets and meal plans created by trainer
    cursor.execute("CREATE TABLE IF NOT EXISTS meal_plan (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, description TEXT NOT NULL, meals TEXT NOT NULL, image_url TEXT, trainer_id INTEGER NOT NULL, FOREIGN KEY (trainer_id) REFERENCES user(id))")

    #Favourite_MealPlan table stores the meal plans a user has favourite
    cursor.execute("CREATE TABLE IF NOT EXISTS favourite_meal_plan (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, meal_plan_id INTEGER NOT NULL, FOREIGN KEY (user_id) REFERENCES user(id), FOREIGN KEY (meal_plan_id) REFERENCES meal_plan(id), UNIQUE (user_id, meal_plan_id))") 

    #Review_MealPlan table stores the user reviews and ratings for meal plans
    cursor.execute("CREATE TABLE IF NOT EXISTS review_meal_plan (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, meal_plan_id INTEGER NOT NULL, rating INTEGER NOT NULL, comment TEXT, created_at TEXT NOT NULL DEFAULT (DATETIME('now')), FOREIGN KEY (user_id) REFERENCES user(id), FOREIGN KEY (meal_plan_id) REFERENCES meal_plan(id), UNIQUE (user_id, meal_plan_id))")

    #Workout_Routine table stores workout outines created by trainers
    cursor.execute("CREATE TABLE IF NOT EXISTS workout_routine (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, description TEXT NOT NULL, difficulty TEXT, exercises_list TEXT NOT NULL, image_url TEXT, trainer_id INTEGER NOT NULL, FOREIGN KEY (trainer_id) REFERENCES user(id))")

    #Favourite_Routine table stores workout routines a user has favourited
    cursor.execute("CREATE TABLE IF NOT EXISTS favourite_routine (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, routine_id INTEGER NOT NULL, FOREIGN KEY (user_id) REFERENCES user(id), FOREIGN KEY (routine_id) REFERENCES workout_routine(id), UNIQUE (user_id, routine_id))")

    #Review_Routine table stores all the user reviews and ratings for workout routins
    cursor.execute("CREATE TABLE IF NOT EXISTS review_routine (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, routine_id INTEGER NOT NULL, rating INTEGER NOT NULL, comment TEXT, created_at TEXT NOT NULL DEFAULT (DATETIME('now')), FOREIGN KEY (user_id) REFERENCES user(id), FOREIGN KEY (routine_id) REFERENCES workout_routine(id), UNIQUE (user_id, routine_id))")

    #Meal table stored individual meals belonging to a meal plan, which is tagged with a category
    cursor.execute("CREATE TABLE IF NOT EXISTS meal (id INTEGER PRIMARY KEY AUTOINCREMENT, meal_plan_id INTEGER NOT NULL, category TEXT NOT NULL, description TEXT NOT NULL, FOREIGN KEY (meal_plan_id) REFERENCES meal_plan(id))")

    conn.commit() #Saves all the table creations
    conn.close() #Closes the connection
