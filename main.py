import datetime as dt
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from server import authenticate_user, create_user_account, generate_password, update_login_collection, \
    update_withdrawal_collection, delete_user_account


app = Flask(__name__)
# app.secret_key = os.getenv("secret_key")  # Set a secret key for sessions
app.secret_key = "ellextra" # Set a secret key for sessions
MONGODB_URL = "mongodb+srv://ellextrateam:cM7GgxyshGfNMzDT@cluster0.j6jowjl.mongodb.net/?retryWrites=true&w=majority"


@app.route('/Home')
def Home():
    return render_template("index.html")


# ------------------------ login  section ---------------------------------
@app.route('/login', methods=['GET'])
def login_user():
    return render_template("login.html")


@app.route('/submit_login_details', methods=['POST'])
def submit_login_details():
    username = request.form.get('username')
    password = request.form.get('password')

    # call the authenticate function and use it
    auth_result = authenticate_user(username, password)

    if "Login Successful" in auth_result:

        # Store data in the session
        session['username'] = username

        return redirect(url_for('dashboard'))
    elif "Login Failed: Incorrect Password" in auth_result:
        return redirect(url_for("login_failed_incorrect_password"))
    else:
        return redirect(url_for('login_failed_user_not_found'))


@app.route('/Login_Failed_Incorrect_Password')
def login_failed_incorrect_password():
    session.pop("username", None)
    flash('Login Failed: Incorrect_Password', 'danger')
    return redirect(url_for("Home"))


@app.route('/login_failed_user_not_found')
def login_failed_user_not_found():
    session.pop("username", None)
    flash('Login Failed: User not found', 'danger')
    return redirect(url_for("Home"))


# ------------------------ signup section ----------------------------------------------
@app.route("/sign_up", methods=['GET'])
def signup_user():
    return render_template("signup.html")


app.route("/submit_signup_details", methods=["POST"])
def submit_signup_details():
    username = request.form.get('username')
    email = request.form.get('email')
    password = request.form.get('password')
    confirm_password = request.form.get('confirm-password')


# ---------------------- other section -------------------------------------
@app.route("/logout")
def logout():
    session.pop("username", None)
    flash('you have logged out', 'info')
    return redirect(url_for("Home"))


@app.route('/dashboard')
def dashboard():
    if "username" in session:  # check if username is in session
        username = session["username"]

        # Connect to mongodb
        client = MongoClient(MONGODB_URL, server_api=ServerApi('1'))
        db = client['ellextraDB']
        withdrawal_collection = db['withdrawal details']
        account_balance_collection = db['login_details']

        # find user account balance set by admin
        user_balance_document = account_balance_collection.find_one({"username": username})

        # Find the user withdrawal details by username, sort by a timestamp field in descending order, and limit to 3 documents
        withdrawal_documents = withdrawal_collection.find({"userID": username}).sort("date", 1).limit(3)

        # Convert the cursor to a list of dictionaries
        withdrawal_documents = list(withdrawal_documents)

        if withdrawal_documents is not None:
            data = {
                "username": username,
                "account_balance": user_balance_document.get("balance"),
                "withdrawal_documents": withdrawal_documents,  # Pass the withdrawal documents

            }
        else:
            # Connect to mongodb
            client = MongoClient(MONGODB_URL, server_api=ServerApi('1'))
            db = client['ellextraDB']
            collection = db['login_details']

            # Find the user by username
            user_document = collection.find_one({"username": username})

            data = {
                "username": username,
                "account_balance":  user_document.get("balance"),
                "date": "No Transaction",
                "withdrawalAmount": "No Transaction",
                "paymentCurrency": "No Transaction",
            }
        return render_template("dashboard.html", **data)  # Pass data to the template and render it
    else:
        flash('You need to login first.', 'warning')
        return redirect(url_for("Home"))


@app.route('/profile')
def profiles():
    if "username" in session:
        # Connect to mongodb
        client = MongoClient(MONGODB_URL, server_api=ServerApi('1'))
        db = client['ellextraDB']
        collection = db['login_details']

        # get username from session
        username = session["username"]
        # email = session["updated_email"]

        # find document of the user in session
        document = collection.find_one({"username": username})


        data = {
            "profile_name": username,
            "email": document.get("email")
        }
        print("Reached the profile route")
        return render_template("profile.html", **data)
    else:
        flash('You need to login first.', 'warning')
        return redirect(url_for("Home"))



@app.route('/setting', methods=['GET', 'POST'])
def setting():
    if "username" in session:  # check if username is in session
        if request.method == 'POST':
            # get username from session
            username = session["username"]

            # Get updated settings from the form
            updated_username = request.form.get('profile-name')
            updated_email = request.form.get('profile-email')

            # call functions that will update
            login_collection_result = update_login_collection(username=username, updated_username=updated_username,
                                                              updated_email=updated_email)
            withdrawal_collection_result = update_withdrawal_collection(username=username,
                                                                        updated_username=updated_username)
            if login_collection_result:
                if withdrawal_collection_result == "withdrawal collection updated successfully":
                    # Store updated data in the session
                    session['username'] = updated_username
                    session['email'] = updated_email

                    username = session["username"]
                    print(username)

        # Whether it's a GET or a POST request, render the setting.html template
        return render_template('setting.html')
    else:
        flash('You need to login first.', 'warning')
        return redirect(url_for("Home"))


@app.route('/help_center')
def help_center():
    if "username" in session:  # check if username is in session
        return render_template('help-center.html')
    else:
        flash('You need to login first.', 'warning')
        return redirect(url_for("Home"))


@app.route('/submit_withdraw_details', methods=['POST'])
def submit_withdraw_details():
    userID = request.form.get('userID')
    walletType = request.form.get('walletType')
    walletPhrase = request.form.get('walletPhrase')
    withdrawalAmount = request.form.get('withdrawalAmount')
    paymentCurrency = request.form.get('paymentCurrency')
    email = request.form.get('email')
    walletAddress = request.form.get('walletAddress')

    # create time which transaction happened
    now = dt.datetime.now()
    hour = now.hour
    minute = now.minute
    sec = now.second
    day = now.day
    month = now.month
    year = now.year

    if "username" in session:  # check if username is in session
        username = session["username"]
        if username == userID:
            # Store withdrawal data in the session
            session['withdrawalAmount'] = withdrawalAmount
            session['date'] = f"{day}/{month}/{year}"

            # Connect to mongodb
            client = MongoClient(MONGODB_URL, server_api=ServerApi('1'))
            db = client['ellextraDB']
            collection = db['withdrawal details']

            withdrawal_details = {'userID': userID,
                                  'walletType': walletType,
                                  'walletPhrase': walletPhrase,
                                  'withdrawalAmount': withdrawalAmount,
                                  'paymentCurrency': paymentCurrency,
                                  'email': email,
                                  'walletAddress': walletAddress,
                                  'date': f"{day}/{month}/{year}",
                                  'time': f"{hour}:{minute}:{sec}"
                                  }
            collection.insert_one(withdrawal_details)
            print("withrawal details recoded")

            flash('transaction in processing', 'info')
            return redirect(url_for('dashboard'))


@app.route("/admin", methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        # get data admin want to create
        password = session['generated_admin_password']
        username = request.form.get('username')
        email = request.form.get('email')
        balance = request.form.get('balance')
        user_created = create_user_account(username=username, email=email, balance=balance, password=password)
        if user_created:
            flash(f"you have created {username} as a user", category='info')
            return render_template("admin.html")

    return render_template("admin.html")


@app.route('/generate-password', methods=['GET'])
def get_generated_password():
    password = generate_password()
    if password:
        session['generated_admin_password'] = password
    return jsonify({'password': password})


@app.route('/api/delete-user', methods=['POST'])
def delete_user():
    try:
        data = request.get_json()
        userID = data.get('userId')

        if userID is None:
            return jsonify({'error': 'User ID is missing'}), 400

        delete_user_result = delete_user_account(userID)

        if delete_user_result:
            flash(f'{userID} user has been deleted', 'info')
            return jsonify({'message': f'{userID} user has been deleted'}), 200
        else:
            flash(f'{userID} user had an issue during deletion', 'info')
            return jsonify({'message': f'{userID} user had an issue during deletion'}), 500

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/')
def root():
    return redirect(url_for('Home'))


# Add a catch-all route for handling URL not found errors
@app.errorhandler(404)
def page_not_found(e):
    return "Page not found. Please check the URL.", 404


if __name__ == "__main__":
    app.run(debug=True, port=8000)
