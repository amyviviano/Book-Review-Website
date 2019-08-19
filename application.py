import os
import requests

from flask import Flask, session, render_template, request, jsonify
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

# Home page
@app.route("/", methods=["GET", "POST"])
def index():
    return render_template("index.html")

# Register for an account
@app.route("/register", methods=["POST"])
def register():
    # Get form info
    username = request.form.get("username")
    password = request.form.get("password")
    if not request.form.get("username"):
        return render_template("error.html", errormsg="Must enter username")
    elif not request.form.get("password"):
        return render_template("error.html", errormsg="Must enter password")

    # Make sure username is available
    if db.execute("SELECT * FROM users WHERE username = :username", {"username": username}).rowcount > 0:
        return render_template("error.html", errormsg="Username already taken. Please choose another")

    # Insert new user into users database
    db.execute("INSERT INTO users (username, password) VALUES (:username, :password)",
    {"username": username, "password": password})
    db.commit()

    # Save user_id and username in this session
    session["username"] = username
    user_id = db.execute("SELECT id FROM users WHERE username = :username", {"username": username})
    session["user_id"] = user_id
    return render_template("search.html", username=username)

# Login to existing account
@app.route("/login", methods=["POST"])
def login():
    
    # Get form info
    username = request.form.get("username")
    loginPassword = request.form.get("password")
    if not request.form.get("username"):
        return render_template("error.html", errormsg="Must enter username")
    elif not request.form.get("password"):
        return render_template("error.html", errormsg="Must enter password")

    # Check that username and password match
    if db.execute("SELECT * FROM users WHERE username = :username", {"username": username}).rowcount == 0:
        return render_template("error.html", errormsg="Username not found")
    row = db.execute("SELECT * FROM users WHERE username = :username", {"username": username}).fetchone()
    if row.password != loginPassword:
        return render_template("error.html", errormsg="Incorrect password")

    # Save user_id and username in this session
    session["username"] = username
    user_id = row.id
    session["user_id"] = row.id
    return render_template("search.html", username=username)

# Search for a book
@app.route("/search", methods=["GET"])
def search():
    # Make sure a user is logged in to search for books
    if session.get("user_id") != None:
        username = session.get("username")
        return render_template("search.html", username=username)
    else:
        return render_template("error.html", errormsg="Must login on Home Page")

# Display search results
@app.route("/results", methods=["POST"])
def results():
    isbn = None
    title = None
    author = None
    book_rows = None
    isbn = request.form.get("isbn")
    
    # Get form data and check if there are any search results
    # show error page is no results, else show search results
    if request.form.get("isbn"):
        book_rows = db.execute("SELECT * FROM books WHERE isbn iLIKE '%"+isbn+"%'").fetchall()
        if book_rows == None:
            return render_template("error.html", errormsg="ISBN not found")
        else:
            return render_template("book-results.html", book_rows=book_rows)
    title = request.form.get("title")
    if request.form.get("title"):
        book_rows = db.execute("SELECT * FROM books WHERE title iLIKE '%"+title+"%'").fetchall()
        if book_rows == None:
            return render_template("error.html", errormsg="Title not found")
        else:
            return render_template("book-results.html", book_rows=book_rows)
    author = request.form.get("author")
    if request.form.get("author"):
        book_rows = db.execute("SELECT * FROM books WHERE author iLIKE '%"+author+"%'").fetchall()
        if book_rows == None:
            return render_template("error.html", errormsg="Author not found")
        else:
            return render_template("book-results.html", book_rows=book_rows)
    return render_template("error.html", errormsg="Must enter ISBN, Title, or Author")

# Individual book page
@app.route("/books/<int:book_id>")
def book(book_id):
    
    # Get book data from database
    book = db.execute("SELECT * FROM books WHERE id = :book_id", {"book_id": book_id}).fetchone()
    session["book_id"] = book.id
    book_id = session.get("book_id")
    reviews = db.execute("SELECT * FROM reviews WHERE book_id = :book_id", {"book_id": book_id}).fetchall()
    isbn = book.isbn
    
    # Get ratings data on book from Goodreads.com
    if isbn[0] != '#':
        res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": "pgdQAyyOr87lB4ZpAnnfbA", "isbns": isbn})
        if res.status_code != 200:
            raise Exception("ERROR: API request unsuccessful.")
        data = res.json()
        avg_rating = data["books"][0]["average_rating"]
        num_rating = data["books"][0]["work_ratings_count"]
    else:
        avg_rating = "No ratings available"
        num_rating = "No ratings available"
    return render_template("book.html", book=book, reviews=reviews, avg_rating=avg_rating, num_rating=num_rating)

@app.route("/newreview", methods=["POST", "GET"])
def newreview():
    
    # Get review data from form
    rating = request.form.get("rating")
    if not request.form.get("rating"):
        return render_template("error.html", errormsg="Must enter rating")
    review = request.form.get("review")
    if not request.form.get("review"):
        return render_template("error.html", errormsg="Must enter review")

    # Insert data into reviews database
    user_id = session.get("user_id")
    book_id = session.get("book_id")
    if db.execute("SELECT * FROM reviews WHERE book_id = :book_id AND user_id = :user_id", {"book_id": book_id, "user_id": user_id}).rowcount != 0:
        return render_template("error.html", errormsg="Only 1 review per book can be submitted")
    db.execute("INSERT INTO reviews (user_id, book_id, rating, review) VALUES (:user_id, :book_id, :rating, :review)", {"user_id": user_id, "book_id": book_id, "rating": rating, "review": review})
    db.commit()
    book = db.execute("SELECT * FROM books WHERE id = :book_id", {"book_id": book_id}).fetchone()
    reviews = db.execute("SELECT * FROM reviews WHERE book_id = :book_id", {"book_id": book_id}).fetchall()
    return render_template("book.html", book=book, reviews=reviews)

# API access
@app.route("/api/<isbn>", methods=["POST", "GET"])
def api(isbn):
# Return details on a single books

    # Make sure books exists
    book = db.execute("SELECT * FROM books WHERE isbn = :isbn", {"isbn": isbn}).fetchone()
    if book is None:
        return jsonify({"error": "Invalid isbn"}), 404
        
    # Get rating data from Goodreads.com
    if isbn[0] != '#':
        res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": "pgdQAyyOr87lB4ZpAnnfbA", "isbns": isbn})
        if res.status_code != 200:
            raise Exception("ERROR: API request unsuccessful.")
        data = res.json()
        avg_rating = data["books"][0]["average_rating"]
        num_rating = data["books"][0]["work_ratings_count"]
    else:
        avg_rating = "No ratings available"
        num_rating = "No ratings available"

    # Get book information
    return jsonify({
                   "title": book.title,
                   "author": book.author,
                   "year": book.year,
                   "isbn": book.isbn,
                   "review_count": num_rating,
                   "average_score": avg_rating
                   })

# Logout
@app.route("/logout")
def logout():
    session.clear()
    return render_template("index.html")





