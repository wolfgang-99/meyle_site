import asyncio
import datetime as dt
import os

from dotenv import load_dotenv
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, make_response, Response
from server import authenticate_user, create_user_account, generate_password, update_login_collection, \
    update_withdrawal_collection, delete_user_account, get_product, retrieve_image, validate_product_image, save_cart, \
    get_cart, delete_from_cart, save_order, get_order_list, get_product_list, get_order_by_id
from translate import Translator
import json
from email_module import email_admin, email_user
import logging
import sys
from aiocache import cached, Cache  # Use aiocache for async caching
from datetime import timedelta

load_dotenv()
app = Flask(__name__)

app.secret_key = os.getenv("secret_key")  # Set a secret key for sessions
app.permanent_session_lifetime = timedelta(hours=3)

# # Configure Flask-Caching
# cache = Cache(app, config={'CACHE_TYPE': 'SimpleCache'})  # Use in-memory caching

# mongodb setup
MONGODB_URL = os.getenv("MONGODB_URL")
# Establish a connection to MongoDB
client = MongoClient(MONGODB_URL)
db = client['meyleDB']

# Configure logging
logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)
logger = logging.getLogger(__name__)


# ---------------- test mongodb connection ----------------------------------------
@app.route('/test-mongodb')
def test_mongodb():
    try:
        client = MongoClient(MONGODB_URL, server_api=ServerApi('1'))
        db = client['meyleDB']
        collection = db['login_details']
        result = collection.find_one()

        if result:
            return jsonify({"status": "success"})
    except Exception as e:
        logger.error(f"MongoDB connection error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


#  ------------------- language handling ------------------------------------------
# Function to translate text with caching
@cached(ttl=10800)  # Cache for 3 hour
async def translate_text(text, dest_language):
    try:
        if dest_language == 'en':  # No translation needed for English
            return text

        translator = Translator(to_lang=dest_language)
        translated = await asyncio.to_thread(translator.translate, text)
        return translated
    except Exception as e:
        print(f"Translation error: {e}")
        return text  # Return original text if translation fails


async def clear_cache():
    # Clear the entire cache
    await Cache().clear()
    return "Cache cleared successfully!", 200


@app.route('/set_language/<language>')
def set_language(language):
    response = make_response(redirect(url_for("Home")))
    response.set_cookie('user_lang', language)
    return response


@app.route('/')
async def Home():
    # Get user's selected language from cookies (default to English)
    user_lang = request.cookies.get('user_lang', 'en')

    # Load the JSON file
    with open('translate/index_translate.json', 'r', encoding='utf-8') as json_file:
        text_to_translate = json.load(json_file)
    # Translate the text
    translated_text = {key: await translate_text(value, user_lang) for key, value in text_to_translate.items()}

    # Use asyncio.to_thread to run render_template in a separate thread
    rendered_template = await asyncio.to_thread(render_template, 'index.html', user_lang=user_lang, **translated_text)
    return rendered_template


# ------------------------ login  section ---------------------------------
@app.route('/login', methods=['GET'])
async def login_user():
    # Get user's selected language from cookies (default to English)
    user_lang = request.cookies.get('user_lang', 'en')

    # Load the JSON file
    with open('translate/login_translate.json', 'r', encoding='utf-8') as json_file:
        text_to_translate = json.load(json_file)
    # Translate the text
    translated_text = {key: await translate_text(value, user_lang) for key, value in text_to_translate.items()}

    # Use asyncio.to_thread to run render_template in a separate thread
    rendered_template = await asyncio.to_thread(render_template, 'login.html', user_lang=user_lang, **translated_text)
    return rendered_template


@app.route('/submit_login_details', methods=['POST'])
def submit_login_details():
    email = request.form.get('email')
    password = request.form.get('password')

    # call the authenticate function and use it
    auth_result = authenticate_user(email, password)

    if "Login Successful" in auth_result:

        # Store data in the session
        session['email'] = email

        return redirect(url_for('show_products'))
    elif "Login Failed: Incorrect Password" in auth_result:
        return redirect(url_for("login_failed_incorrect_password"))
    else:
        return redirect(url_for('login_failed_user_not_found'))


@app.route('/Login_Failed_Incorrect_Password')
def login_failed_incorrect_password():
    session.pop("email", None)
    flash('Login Failed: Incorrect_Password', 'error')
    return redirect(url_for("login_user"))


@app.route('/login_failed_user_not_found')
def login_failed_user_not_found():
    session.pop("email", None)
    flash('Login Failed: User not found', 'error')
    return redirect(url_for("login_user"))


# ------------------------ signup section ----------------------------------------------
@app.route("/sign_up", methods=['GET'])
async def signup_user():
    # Get user's selected language from cookies (default to English)
    user_lang = request.cookies.get('user_lang', 'en')

    # Define the text to be translated
    # Load the JSON file
    with open('translate/signup_translate.json', 'r', encoding='utf-8') as json_file:
        text_to_translate = json.load(json_file)
    # Translate the text
    translated_text = {key: await translate_text(value, user_lang) for key, value in text_to_translate.items()}

    # Use asyncio.to_thread to run render_template in a separate thread
    rendered_template = await asyncio.to_thread(render_template, 'signup.html', user_lang=user_lang, **translated_text)
    return rendered_template


async def send_email_notification_singup(email, username):
    # Put your email sending code here
    email_user(register_email=email, register_name=username, file_path='Email-text/signup_Email_text.txt')


@app.route('/submit_signup_details', methods=['POST'])
async def submit_signup_details():
    username = request.form.get('username')
    email = request.form.get('email')
    password = request.form.get('password')
    confirm_password = request.form.get('confirm-password')
    terms = request.form.get('terms')

    if password != confirm_password:
        return "Passwords do not match", 400

    # create a new user
    signup_result = create_user_account(username=username, email=email, password=password)

    if "Signup Successful" in signup_result:
        # Store data in the session
        session['email'] = email

        # send a registration email
        asyncio.create_task(send_email_notification_singup(email, username))

        flash("signup successful", 'success')
        return redirect(url_for('login_user'))  # Redirect to login page after successful signup

    elif "user exist" in signup_result:
        flash("user already existed. choose another email", 'error')
        return redirect(url_for("signup_user"))

    else:
        return "Signup Failed", 400


@app.route("/logout")
def logout():
    session.pop("username", None)
    flash('you have logged out', 'info')
    return redirect(url_for("Home"))


# ---------------------- cart  section -------------------------------------
@app.route('/cart')
def view_cart():
    if "email" in session:  # check if email is in session
        email = session["email"]
        DB_cart = get_cart(email)

        # initialize cart in session when user is signed in
        session['cart'] = [id for id in DB_cart['products']]

        product_in_cart = [get_product(product_id=id) for id in DB_cart['products']]
        total_price = sum(
            int(product['product_details']['product_price'].replace('$', '').strip())
            for product in product_in_cart
        )
        return render_template('cart.html', products=product_in_cart, total_price=total_price)

    else:
        cart = session.get('cart', [])  # Use get() to handle the case when 'cart' is not in the session
        product_in_cart = [get_product(product_id=id) for id in cart]
        total_price = sum(
            int(product['product_details']['product_price'].replace('$', '').strip())
            for product in product_in_cart
        )
        return render_template('cart.html', products=product_in_cart, total_price=total_price)


@app.route('/add_to_cart/<product_id>')
def add_to_cart(product_id):
    if "email" in session:  # check if email is in session
        email = session["email"]
        cart = session.get('cart', [])  # use get to handle when cart is not in season

        saved_cart = save_cart(product_id, email)
        if saved_cart:
            if product_id not in cart:
                cart.append(product_id)
                session['cart'] = cart
                return redirect(url_for('show_products'))

            elif product_id in cart:
                return redirect(url_for('show_products'))

        else:
            return "error saving cart to db"

    else:
        cart = session.get('cart', [])  # use get to handle when cart is not in season
        if product_id not in cart:
            cart.append(product_id)
            session['cart'] = cart
        return redirect(url_for('show_products'))


@app.route('/remove_from_cart/<product_id>', methods=['POST'])
def remove_from_cart(product_id):
    if "email" in session:  # check if email is in session
        email = session["email"]
        cart = session.get('cart')  # Use get() to handle the case when 'cart' is not in the session

        for item in cart:
            if item == product_id:
                result = delete_from_cart(email, product_id)
                if result:
                    cart.remove(item)
                    session['cart'] = cart
                    break
        return redirect(url_for('view_cart'))

    else:
        cart = session.get('cart', [])  # Use get() to handle the case when 'cart' is not in the session

        for item in cart:
            if item == product_id:
                cart.remove(item)
                session['cart'] = cart
                break
        return redirect(url_for('view_cart'))


# ---------------------- checkout section ------------------------------
@app.route("/checkout")
def check_out():
    return render_template("checkout.html")


# ---------------------- order section ------------------------------
@app.route("/order")
def place_order():
    order_id = "#12345"
    customer_details = {"name": "John Doe",
                        "email": "example@gmail.com",
                        "contact": "+2349023232"}
    order_list = [{"product_id": "glass",
                   "quantity": 1,
                   "price": 50,
                   }]
    order_price = 50
    status = "Pending"
    shipping_address = "nill"
    shipping_logistic = "nill"
    pick_up_branch = "enugu"
    branch_logistic = 50
    total_price = 100
    time = dt.datetime.now()

    order = {"order_id": order_id,
             "customer_details": customer_details,
             "order_list": order_list,
             "order_price": order_price,
             "status": status,
             "shipping_address": shipping_address,
             "shipping_logistic": shipping_logistic,
             "pick_up_branch": pick_up_branch,
             "branch_logistic": branch_logistic,
             "total_price": total_price,
             "order_time": time
             }

    saved_order = save_order(order)
    if saved_order:
        return "your order have been placed"


# ---------------------- product  section -------------------------------------
@app.route('/image/<filename>')
def get_image(filename):
    get_image = retrieve_image(filename)

    if get_image:
        # Return the image data as a binary response
        return Response(get_image['retrieved_image'], content_type=get_image['format'])


@app.route('/products')
def show_products():
    product_list = get_product_list()

    return render_template('products.html', products=product_list)


# ------------- admin section -------------------------------
@app.route("/admin/dashboard")
def admin_dashboard():
    orders = get_order_list()
    return render_template("admin-dashboard.html", orders=orders)

@app.route("/admin/all-orders")
def all_order_and_users():
    orders = get_order_list()
    return render_template("all_orders.html", orders=orders)

@app.route('/admin/order_details/<order_id>')
def order_details(order_id):
    order = get_order_by_id(order_id)
    if not order:
        return "Order not found", 404
    return render_template('order_details.html', order=order)


@app.route("/admin/upload")
def admin_upload():
    return render_template("upload_product.html")


@app.route('/admin/upload_product', methods=['POST'])
def upload_product():
    if request.method == 'POST':
        if 'product_image' in request.files:
            product_name = request.form.get('product_name')
            product_id = request.form.get('product_id')
            product_price = request.form.get('product_price')
            product_description = request.form.get('product_description')
            uploaded_image = request.files['product_image']

            product_details = {'product_id': product_id,
                               'product_name': product_name,
                               'product_price': product_price,
                               'product_description': product_description
                               }

            result = validate_product_image(uploaded_image, product_details=product_details)
            if result == True:
                return f'Product ({product_id}) Uploaded and Processed Successfully.'
            else:
                return 'Invalid Image Format. Allowed formats are: jpg, jpeg, png'
        else:
            return 'No Image Uploaded'


# -------------------------------  unused ---------------------------------------------
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


@app.route("/admin", methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        # get data admin want to create
        password = session['generated_admin_password']
        username = request.form.get('username')
        email = request.form.get('email')
        balance = request.form.get('balance')
        user_created = create_user_account(username=username, email=email, password=password)
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


@app.errorhandler(Exception)
def handle_exception(e):
    logger.error(f"An error occurred: {e}", exc_info=True)
    return "Internal Server Error", 500


if __name__ == "__main__":
    app.run(debug=True, port=8000)
