import random
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from bson import ObjectId
from dotenv import load_dotenv
import os

load_dotenv()
MONGODB_URL = os.getenv("MONGODB_URL")

# Connect to mongodb
client = MongoClient(MONGODB_URL)
db = client['meyleDB']


def authenticate_user(email, password):
    try:
        # Chose collection
        collection = db['login_details']

        # Define the criteria for the username and password
        input_email = email
        input_password = password

        # Find the user by username
        user_login_document = collection.find_one({"email": input_email})

        if user_login_document:
            stored_password = user_login_document["password"]

            # Check if the provided password matches the stored hash
            if stored_password == input_password:
                return "Login Successful"
            else:
                return "Login Failed: Incorrect Password"
        else:
            return "Login Failed: User not found"
    except Exception as e:
        return "An error occurred: " + str(e)



def generate_password():
    letters = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u',
               'v', 'w', 'x', 'y', 'z', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P',
               'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z']
    numbers = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']
    symbols = ['!', '#', '$', '%', '&', '(', ')', '*', '+']

    nr_letters = random.randint(8, 10)
    nr_symbols = random.randint(2, 4)
    nr_numbers = random.randint(2, 4)

    password_letter = [random.choice(letters) for _ in range(nr_letters)]
    password_symbols = [random.choice(symbols) for _ in range(nr_symbols)]
    password_char = [random.choice(numbers) for _ in range(nr_numbers)]

    password_list = password_letter + password_symbols + password_char
    random.shuffle(password_list)

    password = "".join(password_list)

    return password


def create_user_account(username, email, password):
    try:
        collection = db['login_details']

        # Check if the username already exists in the database
        existing_user = collection.find_one({'email': email})
        if existing_user:
            print("Username already exists. Please choose a different username.")
            return "user exist"

        submission = {'username': username,
                      'email': email,
                      'password': password
                      }
        collection.insert_one(submission)
        print(f"data has been recoreded")
        return "Signup Successful"

    except Exception as e:
        return "An error occurred: " + str(e)


def delete_user_account(userID):
    try:
        # Connect to MongoDB
        client = MongoClient(MONGODB_URL, server_api=ServerApi('1'))
        db = client['ellextraDB']
        collection = db['login_details']

        target_object_id = ObjectId(userID)
        # Filter for the document to delete
        doc_to_delete = {'_id': target_object_id}
        result = collection.delete_one(doc_to_delete)

        if result.deleted_count == 1:
            print(f"{userID} data has been deleted")
            return True
        else:
            print(f"{userID} Document not found or not deleted")
            return False

    except Exception as e:
        print("An error occurred: " + str(e))
        return False



# delete_user_account("64fc845673e3dc28a3cdb44d")
def update_login_collection(username, updated_username, updated_email):
    try:
        # Connect to mongodb
        client = MongoClient(MONGODB_URL, server_api=ServerApi('1'))
        db = client['ellextraDB']

        # define document of the user in session you want to update

        query = {"username": username}

        # insert the updated details
        updated_doc = {"updated_username": updated_username,
                       "updated_email": updated_email
                       }

        # Use `Aggregation` to find the user, add the updated details and save to a new collection
        db.login_details.aggregate([
            {"$match": query}, {"$project": {"email": 1, "password": 1, "_id": 0}},
            {"$set": updated_doc}, {"$out": {"db": "ellextraDB", "coll": "updated_login_details"}}

        ])

        return True
    except Exception as e:
        return "An error occurred: " + str(e)


def update_withdrawal_collection(username, updated_username):
    try:
        # Connect to mongodb
        client = MongoClient(MONGODB_URL, server_api=ServerApi('1'))
        db = client['ellextraDB']
        withdrawal_collection = db['withdrawal details']

        # Define a filter to identify the document you want to update
        filter = {"userID": username}

        # Define the update operation
        update = {"$set": {"userID": updated_username}}

        # Update a single document
        result = withdrawal_collection.update_one(filter, update)

        # Check if the update was successful
        if result.modified_count > 0:
            return "withdrawal collection updated successfully"
        else:
            return "withdrawal collection not updated"
    except Exception as e:
        return "An error occurred: " + str(e)
