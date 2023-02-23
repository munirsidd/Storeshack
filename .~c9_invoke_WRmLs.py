import os

from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session, make_response
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
from flask_mail import Mail, Message
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

ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///final.db")

@app.route("/", methods=["GET", "POST"])
@login_required
def index():
    if request.method == "POST":
        search = request.form.get("search")
        return search_results(search)
    else:
        return render_template("index.html")
@app.route("/search")
@login_required
def search_results(search):
    rows = db.execute("SELECT * FROM products WHERE name LIKE ?",
                      '%' + search + '%')

    not_found = False

    if len(rows) == 0:
        not_found = True

    return render_template("search.html", not_found=not_found, rows=rows)

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
        session["username"] = rows[0]["username"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")
app.config["IMAGE_UPLOADS"] = "/final/pictures"
@app.route("/upload-image", methods=["GET", "POST"])
def upload_image():

    if request.method == "POST":

        if request.files:

            image = request.files["image"]

            image.save(os.path.join(app.config["IMAGE_UPLOADS"], image.filename))

            flash("Image saved")

            return render_template("add_products.html")
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

@app.route("/all_categories", methods=["GET", "POST"])
@login_required
def all_categories():
    """All categories"""

    if request.method == "POST":
        search = request.form.get("search")
        return search_results(search)
    else:
        return render_template("all_categories.html")

@app.route("/electronics", methods=["GET", "POST"])
@login_required
def electronics():
    """Electronics"""

    if request.method == "POST":
        search = request.form.get("search")
        return search_results(search)

    else:
        return render_template("electronics.html")

@app.route("/kids_fashion", methods=["GET", "POST"])
@login_required
def kids_fashion():
    """Kids' Fashion"""

    if request.method == "POST":
        search = request.form.get("search")
        return search_results(search)

    else:
        return render_template("kids_fashion.html")

@app.route("/cart", methods=["GET", "POST"])
@login_required
def cart():


        if request.method == "POST" and "search" in request.form:
            search = request.form.get("search")
            return search_results(search)

        else:

            lines = db.execute("SELECT * FROM user_cart WHERE username = :username",
                               username=session["username"])
            for i in range(len(lines)):

                if request.method == "POST" and lines[i]["item"] in request.form:
                    db.execute("DELETE FROM user_cart WHERE item = :item AND username = :username",
                               item=lines[i]["item"], username=session["username"])
                    db.execute("UPDATE products SET stock = stock + :quantity WHERE name = :name",
                               quantity=lines[0]["quantity"], name=lines[i]["item"])
                    items = db.execute("SELECT * FROM user_cart WHERE username = :username",
                                       username=session["username"])
                    total = 0
                    no_items = False
                    for i in range(len(items)):
                        total = total + (items[i]["quantity"] * items[i]["price"])

                    if len(items) == 0:
                        no_items = True
                    return render_template("cart.html", no_items=no_items, items=items, total=total)

            if request.method == "POST" and "checkout" in request.form:
                return redirect("/checkout")

            total = 0
            no_items = False

            items = db.execute("SELECT * FROM user_cart WHERE username = :username",
                               username=session["username"])
            for i in range(len(items)):
                total = total + (items[i]["quantity"] * items[i]["price"])

            if len(items) == 0:
                no_items = True

            return render_template("cart.html", no_items=no_items, items=items, total=total)

@app.route("/checkout", methods=["GET", "POST"])
@login_required
def checkout():
    """Checkout"""

    if request.method == "POST" and "search" in request.form:
        search = request.form.get("search")
        return search_results(search)

    else:

        if request.method == "POST" and "confirm_order" in request.form:
            if not request.form.get("full_name"):
                return apology("must provide your full name", 403)
            if not request.form.get("email"):
                return apology("must provide your email", 403)
            if not request.form.get("phone_number"):
                return apology("must provide phone number", 403)
            if not request.form.get("address"):
                return apology("must provide address", 403)
            full_name = request.form.get("full_name")
            email = request.form.get("email")
            phone_number = request.form.get("phone_number")
            address = request.form.get("address")
            province = request.form.get("province")
            zip_code = request.form.get("zip_code")
            payment_method = request.form.get("payment_method")

            db.execute("INSERT INTO checkout(user_id, full_name, email, phone_number, address, province, zip_code, payment_method) VALUES(:user_id, :full_name, :email, :phone_number, :address, :province, :zip_code, :payment_method)",
                       user_id=session["user_id"], full_name=full_name, email=email, phone_number=phone_number, address=address, province=province, zip_code=zip_code, payment_method=payment_method)
            rows = db.execute("SELECT item, price, quantity FROM user_cart WHERE user_id = :user_id", user_id = session["user_id"])
            for i in range(len(rows)):
                db.execute("INSERT INTO transactions(user_id, name, price, quantity) VALUES(:user_id, :name, :price, :quantity)",
                           user_id = session["user_id"], name = rows[i]["item"], price = rows[i]["price"], quantity = rows[i]["quantity"])

            db.execute("DELETE FROM user_cart WHERE user_id = :user_id",
                       user_id=session["user_id"])
            return redirect("/confirm_order")


        else:
            items = db.execute("SELECT * FROM user_cart WHERE username = :username",
                               username=session["username"])
            total = 0
            for i in range(len(items)):
                total = total + (items[i]["quantity"] * items[i]["price"])
            return render_template("checkout.html", total=total, items=items)
@app.route("/my_profile", methods=["GET", "POST"])
@login_required
def my_profile():

    if request.method == "POST":
        search = request.form.get("search")
        return search_results(search)

    else:
        rows = db.execute("SELECT * FROM users WHERE user_id = :user_id", user_id = session["user_id"])
        first_name = rows[0]["first_name"]
        last_name = rows[0]["last_name"]
        email = rows[0]["email"]
        orders = db.execute("SELECT * FROM transactions WHERE user_id = :user_id", user_id = session["user_id"])
        return render_template("my_profile.html", rows = rows, orders = orders, first_name = first_name, last_name = last_name, email = email)

@app.route("/confirm_order")
@login_required
def confirm_order():
    """Confirm Order"""

    if request.method == "POST":
        search = request.form.get("search")
        return search_results(search)

    else:
        items = db.execute("SELECT * FROM transactions WHERE user_id = :user_id",
                           user_id=session["user_id"])
        total = 0
        for i in range(len(items)):
            total = total + (items[i]["quantity"] * items[i]["price"])

        return render_template("confirm_order.html", total=total, items=items)



@app.route("/item/<product>", methods=["GET", "POST"])
@login_required
def item(product):
    """Product"""

    if request.method == "POST" and "search" in request.form:
        search = request.form.get("search")
        return search_results(search)

    else:
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
            stars_count = 0
            count = 0
            avg_stars = 0

            if len(lines) != 0:
                for i in range(len(lines)):
                    if lines[i]["recommendation"] == "Yes":
                        yes = yes + 1
                        total = total + 1
                    else:
                        total = total + 1
                    stars_count = stars_count + int(lines[i]["stars"])
                    count = count + 1
                yes_percentage = int((yes / total * 100))
                avg_stars = int(stars_count / count)


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

            return render_template('item.html', avg_stars=avg_stars, rows=rows, total=total, yes=yes, yes_percentage=yes_percentage, lines=lines, product=product, name=name, price=price, url=url, stock=stock, low_stock=low_stock, out_stock=out_stock, description=description)

        elif request.method == "POST" and "add_cart" in request.form and not "submit_review":
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
            count = 0
            avg_stars = 0
            stars_count = 0

            if len(lines) != 0:

                for i in range(len(lines)):
                    if lines[i]["recommendation"] == "Yes":
                        yes = yes + 1
                        total = total + 1
                    else:
                        total = total + 1
                    stars_count = stars_count + int(lines[i]["stars"])
                    count = count + 1
                yes_percentage = int((yes / total * 100))
                avg_stars = int(stars_count / count)
            user_id = session["user_id"]
            username = session["username"]


            if db.execute("SELECT stock FROM products WHERE name = :name",
                                      name=product)[0]["stock"] > 0:

                carts = db.execute("SELECT item, quantity FROM user_cart WHERE username = :username AND item = :name",
                                   username=username, name=product)
                if len(carts) != 0:
                    for i in range(len(carts)):
                        if carts[i]["item"] == product:
                            db.execute("UPDATE user_cart SET quantity = quantity + 1 WHERE item = :name",
                                       name=product)

                            db.execute("UPDATE products SET stock = stock - 1 WHERE name = :name", name=product)

                else:

                    db.execute("INSERT INTO user_cart(user_id, item, price, image, username) VALUES(:user_id, :item, :price, :image, :username)",
                                   user_id=user_id, item=product, price=price, image=url, username = username)
                    db.execute("UPDATE products SET stock = stock - 1 WHERE name = :name", name=product)

                flash("Added to cart!")

            else:
                flash("Out of stock!")
            return render_template('item.html', avg_stars=avg_stars, total=total, yes=yes, yes_percentage=yes_percentage, lines=lines, product=product, name=name, price=price, url=url, stock=stock, low_stock=low_stock, out_stock=out_stock, description=description)

        elif request.method == "POST" and "add_cart" in request.form and "submit_review" in request.form:

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
            count = 0
            avg_stars = 0
            stars_count = 0

            if len(lines) != 0:
                for i in range(len(lines)):
                    if lines[i]["recommendation"] == "Yes":
                        yes = yes + 1
                        total = total + 1
                    else:
                        total = total + 1
                    stars_count = stars_count + int(lines[i]["stars"])
                    count = count + 1
                yes_percentage = int((yes / total * 100))
                avg_stars = int(stars_count / count)

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

            return render_template('item.html', avg_stars=avg_stars, rows=rows, total=total, yes=yes, yes_percentage=yes_percentage, lines=lines, product=product, name=name, price=price, url=url, stock=stock, low_stock=low_stock, out_stock=out_stock, description=description)

        elif request.method == "POST" and "add_cart" in request.form and not "submit_review" in request.form:
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
            count = 0
            avg_stars = 0
            stars_count = 0

            if len(lines) != 0:

                for i in range(len(lines)):
                    if lines[i]["recommendation"] == "Yes":
                        yes = yes + 1
                        total = total + 1
                    else:
                        total = total + 1
                    stars_count = stars_count + int(lines[i]["stars"])
                    count = count + 1
                yes_percentage = int((yes / total * 100))
                avg_stars = int(stars_count / count)
            user_id = session["user_id"]
            username = session["username"]

            if db.execute("SELECT stock FROM products WHERE name = :name",
                                      name=product)[0]["stock"] > 0:

                carts = db.execute("SELECT item, quantity FROM user_cart WHERE username = :username AND item=:name",
                                  username=username, name=product)

                if len(carts) != 0:
                    for i in range(len(carts)):
                        if carts[i]["item"] == product:
                            db.execute("UPDATE user_cart SET quantity = quantity + 1 WHERE item = :name",
                                       name=product)
                            db.execute("UPDATE products SET stock = stock - 1 WHERE name = :name", name=product)

                else:
                    db.execute("INSERT INTO user_cart(user_id, username, item, price, image) VALUES(:user_id, :username, :item, :price, :image)",
                               user_id=user_id, username=username, item=product, price=price, image=url)
                    db.execute("UPDATE products SET stock = stock - 1 WHERE name = :name", name=product)
                flash("Added to cart!")

            else:
                flash("Out of stock!")

            return render_template('item.html', total=total, yes=yes, yes_percentage=yes_percentage, lines=lines, product=product, name=name, price=price, url=url, stock=stock, low_stock=low_stock, out_stock=out_stock, description=description)

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
            count = 0
            avg_stars = 0
            stars_count = 0

            if len(lines) != 0:

                for i in range(len(lines)):
                    if lines[i]["recommendation"] == "Yes":
                        yes = yes + 1
                        total = total + 1
                    else:
                        total = total + 1
                    stars_count = stars_count + int(lines[i]["stars"])
                    count = count + 1
                yes_percentage = int((yes / total * 100))
                avg_stars = int(stars_count / count)


            return render_template('item.html', avg_stars=avg_stars, yes_percentage=yes_percentage, total=total, yes=yes, lines=lines, product=product, name=name, price=price, url=url, stock=stock, low_stock=low_stock, out_stock=out_stock, description=description)

def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)