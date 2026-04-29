# all routes, auth, upload, API
import json
import os
import hashlib
from datetime import datetime
from functools import wraps # @login required decorator
from flask import (Flask, render_template, request, jsonify, redirect, url_for, session)
from models import Property, User
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Secret key for session cookies and 
# it is the same for the flask app and all users
app.secret_key = "aqar-misr-secret-2026"

# File paths
DATA_FILE = "data/properties.json"
USERS_FILE  = "data/users.json"
CONTACTS_FILE = "data/contacts.json"
UPLOAD_FOLDER = "static/uploads"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# this function is used to hash password to avoid hard coding
def hash_password(plain):
    return hashlib.sha256(plain.encode()).hexdigest() 

# make sure that the uploaded file is safe and one of allowed extentions 
# and here I mean (the images in add property page)
def allowed_file(filename):
    return "." in filename and \
           filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

# READ FROM FILE
# convert from text to proprty
def load_properties():
    with open(DATA_FILE, "r") as f:
        raw_list = json.load(f) # convert it to list of dicts

    properties = []
    for item in raw_list:
        prop = Property(
            prop_id = item["prop_id"],
            title = item["title"],
            price = item["price"],
            area = item["area"],
            prop_type = item["prop_type"],
            bedrooms= item["bedrooms"],
            bathrooms= item["bathrooms"],
            image_url= item["image_url"],
            description = item.get("description", ""), # we use get to make it optional, because in some cases we can uplad a property without description or why choose. if it is empty replace it with " "
            why_choose= item.get("why_choose", ""),
        )
        prop.listed_at = item["listed_at"] #i didn't put it in the constructor because it is generated automatically when we create a new property, but when we read from the file we need to set it to the value in the file
        properties.append(prop)
    return properties

# WRITE TO FILE
# write that objects came from load_properties to the json file again(but convert it to dict first)
def save_properties(properties):
    list_of_dicts = []
    for p in properties:
        list_of_dicts.append(p.to_dict())
    with open(DATA_FILE, "w") as f:
        json.dump(list_of_dicts, f, indent=4)


#Reads all users from users.json
def load_users():
    if not os.path.exists(USERS_FILE):
        return []
    with open(USERS_FILE, "r") as f:
        raw = json.load(f)
    users = []
    for item in raw:
        u = User(item["user_id"], item["name"], item["email"], item["password_hash"])
        u.favorites = item.get("favorites", [])
        u.joined_at = item["joined_at"]
        users.append(u)
    return users

#Writes the list of User objects to users.json.
def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump([u.to_dict() for u in users], f, indent=4)

# Reads user_id from the Flask session cookie.
def get_current_user():
    user_id = session.get("user_id")
    if not user_id:
        return None
    for u in load_users():
        if u.user_id == user_id:
            return u
    return None

#Decorator redirects to /login.
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs): # what ever parameter type is
        if not get_current_user():
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated

# Routes 
#Sign-up page. 
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        name = request.form.get("name","").strip()
        email= request.form.get("email","").strip().lower()
        password= request.form.get("password","")
        confirm = request.form.get("confirm","")

        # Validate no crash on unvaild input
        if not name or not email or not password:
            return render_template("signup.html", user=None,
                                   error="All fields are required.")
        if password != confirm:
            return render_template("signup.html", user=None,
                                   error="Passwords do not match.")
        if len(password) < 6:
            return render_template("signup.html", user=None,
                                   error="Password must be at least 6 characters.")

        users = load_users()

        for u in users:
            if u.email == email:
                return render_template("signup.html", user=None,
                                       error="An account with this email already exists.")

        # Calculate the next user ID by finding the highest current ID then adding 1
        highest_id = 0
        for u in users:
            if u.user_id > highest_id:
                highest_id = u.user_id
        new_id = highest_id + 1

        new_user = User(new_id, name, email, hash_password(password))
        users.append(new_user)
        save_users(users)

        # Log in immediately after sign-up
        session["user_id"] = new_user.user_id
        return redirect(url_for("home"))

    return render_template("signup.html", user=None)

#Login page. Validates email and hashed password
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email= request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not email or not password:
            return render_template("login.html", user=None,
                                   error="Please enter your email and password.")

        for u in load_users():
            if u.email == email and u.password_hash == hash_password(password):
                session["user_id"] = u.user_id
                return redirect(url_for("home"))

        return render_template("login.html", user=None,
                               error="Incorrect email or password.")

    return render_template("login.html", user=None)

# clear session and redirect to home page
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))

#shows user info and their favorited properties
@app.route("/profile")
@login_required
def profile():
    user = get_current_user()
    all_props = load_properties()
    fav_props= [p for p in all_props if p.prop_id in user.favorites]
    return render_template("profile.html", user=user, favorites=fav_props)

#toggle a fav prop
@app.route("/api/favorite/<int:prop_id>", methods=["POST"])
@login_required
def toggle_favorite(prop_id):
    users = load_users()
    current_id = session["user_id"]

    for u in users:
        if u.user_id == current_id:
            is_now_fav = u.toggle_favorite(prop_id)
            save_users(users)
            return jsonify({"favorited": is_now_fav})


# Home route
@app.route("/")
def home():
    properties = load_properties()
    featured = properties[:6]
    user = get_current_user()

    return render_template(
        "index.html",
        properties=featured,
        user=user,
    )

# search route
@app.route("/search")
def search():
    area = request.args.get("area", "").strip()
    prop_type = request.args.get("type", "").strip()
    max_price_str = request.args.get("max_price", "").strip()

    max_price = None
    if max_price_str:
        try:
            max_price = int(max_price_str)
        except ValueError:
            max_price = None

    all_props = load_properties()
    results= []

    for prop in all_props:
        if prop.matches_filter(area=area, prop_type=prop_type, max_price=max_price):
            results.append(prop)

    user = get_current_user()

    return render_template(
        "search.html",
        properties = results,
        selected_area = area,
        selected_type = prop_type,
        selected_price = max_price_str,
        user= user,
    )

# each property detail
@app.route("/property/<int:prop_id>")
def property_detail(prop_id):
    all_props = load_properties()
    found = None

    for prop in all_props:
        if prop.prop_id == prop_id:
            found = prop
            break

    user = get_current_user()
    is_fav = (user is not None and prop_id in user.favorites)
    contact_ok = request.args.get("contact_ok")
    contact_error = request.args.get("contact_error")

    return render_template(
        "property.html",
        property = found,
        user = user,
        is_fav = is_fav,
        contact_ok = contact_ok,
        contact_error = contact_error,
    )

# buy route
@app.route("/buy/<int:prop_id>")
@login_required
def buy_now(prop_id):
    all_props = load_properties()
    prop = None

    for p in all_props:
        if p.prop_id == prop_id:
            prop = p
            break

    return render_template("thankyou.html", property=prop, user=get_current_user())

# aadd new property route
@app.route("/add-property", methods=["GET", "POST"])
@login_required
def add_property():
    user = get_current_user()

    if request.method == "POST":
        title= request.form.get("title","").strip()
        area= request.form.get("area","").strip()
        prop_type= request.form.get("prop_type","").strip()
        description= request.form.get("description", "").strip()
        why_choose= request.form.get("why_choose","").strip()

        try:
            price= int(request.form.get("price",0))
            bedrooms= int(request.form.get("bedrooms",1))
            bathrooms = int(request.form.get("bathrooms",1))
        except ValueError:
            return render_template("add_property.html", user=user,
                error="Please enter valid numbers for price, bedrooms, bathrooms, and coordinates.")

        if not title or not area or not prop_type:
            return render_template("add_property.html", user=user,
                error="Title, area, and type are required.")

        # Handle image upload
        image_url = "https://images.unsplash.com/photo-1560448204-e02f11c3d0e2?w=600"
        file = request.files.get("image")
        if file and file.filename and allowed_file(file.filename):
            filename  = secure_filename(file.filename)
            save_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            file.save(save_path)
            image_url = f"/static/uploads/{filename}"

        all_props = load_properties()
        # Calculate the next property ID
        highest_prop_id = 0
        for p in all_props:
            if p.prop_id > highest_prop_id:
                highest_prop_id = p.prop_id
        new_id = highest_prop_id + 1

        new_prop = Property(
            prop_id = new_id,
            title  = title,
            price  = price,
            area  = area,
            prop_type = prop_type,
            bedrooms= bedrooms,
            bathrooms = bathrooms,
            image_url= image_url,
            description = description,
            why_choose= why_choose,
            
        )

        summary = new_prop.get_summary()
        all_props.append(new_prop)
        save_properties(all_props)

        return render_template("add_property.html", user=user,
            success=f"Property listed successfully! {summary}")

    return render_template("add_property.html", user=user)

# favorites page route for a specific user
@app.route("/favorites")
def favorites():
    user = get_current_user()
    fav_props = []

    if user:
        all_props = load_properties()
        for prop in all_props:
            if prop.prop_id in user.favorites:
                fav_props.append(prop)

    return render_template("favorites.html", user=user, favorites=fav_props)

# run the app
if __name__ == "__main__":
    app.run(debug=True)