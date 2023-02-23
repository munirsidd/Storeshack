import os

from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, pkr

# Configure application
app = Flask(__name__)


# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Custom filter
app.jinja_env.filters["pkr"] = pkr

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///final.db")

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to home
    return redirect("/")

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["password"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["user_id"]
        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")
@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        if not request.form.get("first_name"):
            return apology("must provide your first name", 403)
        if not request.form.get("last_name"):
            return apology("must provide your last name", 403)
        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)
        if not request.form.get("email"):
            return apology("must provide email", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Ensure confirmation was submitted
        elif not request.form.get("confirmation"):
            return apology("please re-enter password", 403)

        # Ensure passwords match
        elif request.form.get("password") != request.form.get("confirmation"):
            return apology("passwords do not match", 403)

        # Ensure username is unique
        if len(db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))) != 0:
            return apology("username already taken", 403)

        db.execute("INSERT INTO users(first_name, last_name, username, email, password) VALUES(:first_name, :last_name, :username, :email, :password)",
                   first_name=request.form.get("first_name"), last_name=request.form.get("last_name"), username=request.form.get("username"), email=request.form.get("email"), password=generate_password_hash(request.form.get("password")))

        # Remember which user has logged in
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))
        session["user_id"] = rows[0]["user_id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")

@app.route("/electronics")
def electronics():
    """Electronics"""

    return render_template("electronics.html")

@app.route("/kids_fashion")
def kids_fashion():
    """Kids' Fashion"""

    return render_template("kids_fashion.html")

@app.route("/cart")
def cart():
    return render_template("cart.html")

@app.route("/item/<product>", methods=["GET", "POST"])
def item(product):
    """Product"""

    if request.method == "POST" and "submit_review" in request.form:

        if not request.form.get("username"):
            return apology("must provide username", 403)

        elif not request.form.get("star"):
            return apology("must provide rating", 403)

        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        if len(rows) != 1:
            return apology("invalid username", 403)


        username = request.form.get("username")
        stars = request.form.get("star")
        review = request.form.get("review")
        recommendation = request.form.get("recommendation")
        db.execute("INSERT INTO review(username, review, stars, recommendation, product) VALUES(:username, :review, :stars, :recommendation, :product)",
                   username=username, review=review, stars=stars, recommendation=recommendation, product=product)

        lines = db.execute("SELECT username, stars, review, recommendation FROM review WHERE product = :product",
                               product=product)

        yes = 0
        total = 0
        yes_percentage = 0

        if len(lines) != 0:
            for i in range(len(lines)):
                if lines[i]["recommendation"] == "Yes":
                    yes = yes + 1
                    total = total + 1
                else:
                    total = total + 1
            yes_percentage = (yes / total * 100)

        details = db.execute("SELECT * From products WHERE name = :name",
                             name=product)

        name = details[0]["name"]
        price = details[0]["price"]
        url = details[0]["image"]
        stock = details[0]["stock"]
        description = details[0]["description"]

        low_stock = False
        out_stock = False

        if stock == 0:
            out_stock = True
        elif stock <= 10:
            low_stock = True
            out_stock = False
        else:
            low_stock = False
            out_stock = False



        return render_template('item.html', total=total, yes=yes, yes_percentage=yes_percentage, lines=lines, rows=rows, product=product, name=name, price=price, url=url, stock=stock, low_stock=low_stock, out_stock=out_stock, description=description)

    elif request.method == "POST" and "add_cart" in request.form:
        flash("Added to cart!")
        return render_template('it')

    else:
        details = db.execute("SELECT * From products WHERE name = :name",
                             name=product)

        name = details[0]["name"]
        price = details[0]["price"]
        url = details[0]["image"]
        stock = details[0]["stock"]
        description = details[0]["description"]

        low_stock = False
        out_stock = False

        if stock == 0:
            out_stock = True
        elif stock <= 10:
            low_stock = True
            out_stock = False
        else:
            low_stock = False
            out_stock = False

        lines = db.execute("SELECT username, stars, review, recommendation FROM review WHERE product = :product",
                           product=product)

        yes = 0
        total = 0
        yes_percentage = 0

        if len(lines) != 0:

            for i in range(len(lines)):
                if lines[i]["recommendation"] == "Yes":
                    yes = yes + 1
                    total = total + 1
                else:
                    total = total + 1
            yes_percentage = (yes / total * 100)


        return render_template('item.html', yes_percentage=yes_percentage, total=total, yes=yes, lines=lines, product=product, name=name, price=price, url=url, stock=stock, low_stock=low_stock, out_stock=out_stock, description=description)


def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)