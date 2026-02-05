from werkzeug.security import generate_password_hash, check_password_hash  #Werkzeug allows the hashing of passwords. generate_password_hash creates a hash from a password and check_password_hash checks the password with the hashed versions to verify the account
def hash_password(password): #This function generates a password hash from the provided password.
    return generate_password_hash(password) 
def verify_password(password, hashed_password): #This function compares the passwords to the hashed versions to verify if they are the same.
    return check_password_hash(hashed_password, password) 
