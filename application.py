import os

from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from gutenberg.acquire import load_etext
from gutenberg.cleanup import strip_headers
# from werkzeug.security import check_password_hash, generate_password_hash

from helpers import *

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached

# Global variable to store number of words outputted as per TA suggestion
global number


@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///storage.db")


@app.route("/")
def index():
    """Show home page"""
    return render_template("homepage.html")


@app.route("/input", methods=["GET", "POST"])
def collectTextInput():
    """Gets words from form and installs to database then sends user to home in POST, displays input.html in GET"""
    if request.method == "POST":
        words = request.form.get("word")
        installText(words)
        return render_template("homepage.html")
    else:
        return render_template("input.html")


@app.route("/numInput", methods=["GET", "POST"])
def collectNumInput():
    """Takes in an input of words to generate in POST, renders numInput.html in GET"""
    if request.method == "POST":
        # Global variable number
        global number
        number = request.form.get("number")

        if not number:
            return apology("You didn't input anything. Do that next time.")
        return redirect("/output")
    else:
        return render_template("numInput.html")


@app.route("/bookInput", methods=["GET", "POST"])
def downloadBook():
    """If posting, takes in a book number from getty.html, installs the book into
    the database. Otherwise displays getty.html"""
    if request.method == "POST":
        bookNum = int(request.form.get("bookNum"))
        words = strip_headers(load_etext(bookNum)).strip()
        installText(words)
        return render_template("homepage.html")
    else:
        return render_template("getty.html")


@app.route("/output", methods=["GET"])
def output():
    """Generates text, passes it into output.html"""
    if request.method == "GET":
        return render_template("output.html", generatedText=randomWords(int(number), "time"))

    else:
        return apology("something bad happened")


def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
