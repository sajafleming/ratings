"""Movie Ratings."""

from jinja2 import StrictUndefined

from flask import Flask, render_template, redirect, request, flash, session
from flask_debugtoolbar import DebugToolbarExtension

from model import connect_to_db, db, User, Rating, Movie

from flask_sqlalchemy import SQLAlchemy


app = Flask(__name__)

# Required to use Flask sessions and the debug toolbar
app.secret_key = "ABC"

# Normally, if you use an undefined variable in Jinja2, it fails silently.
# This is horrible. Fix this so that, instead, it raises an error.
app.jinja_env.undefined = StrictUndefined


@app.route('/')
def index():
    """Homepage."""

    return render_template("homepage.html")

@app.route("/users")
def user_list():
    """Show list of users"""

    users = User.query.all()
    return render_template("user_list.html", users=users)

@app.route('/add_user')
def add_user():
    """Add user form"""

    return render_template("add_user_form.html")

@app.route('/form_submit', methods=["POST"])
def submit_form():
    """Check if user in db, if not, add!"""

    user_email = request.form.get('email')
    user_password = request.form.get('password')

    if User.query.filter_by(email=user_email).first():
        flash("You are already a member, please log in.") 
    else:
        user = User(email=user_email, password=user_password)

        # add user to database
        db.session.add(user)

        # commit user to database
        db.session.commit()

        flash("Thank you for registering, please log in.") 

    return render_template("login.html")

@app.route('/login', methods=["POST"])
def user_login():
    """Check if email and password are correct and log in"""

    user_email = request.form.get('email')
    user_password = request.form.get('password')

    if User.query.filter_by(email=user_email, password=user_password).first():
        flash("Congrats, you actually remembered your password")
        logged_in_user = User.query.filter_by(email=user_email, password=user_password).first()
        session["user_id"] = logged_in_user.user_id

        return redirect('/')
    else:
        flash("you idiot, try again and this time GET IT RIGHT.")
        return render_template("login.html")

@app.route('/logout')
def user_logout():
    """Logs out"""

    del session["user_id"]

    return redirect('/')

@app.route('/users/<int:user_id>')
def user_details(user_id):
    """Show user details"""

    user = User.query.get(user_id)    

    user_age = user.age
    user_zipcode = user.zipcode 
    user_ratings = user.ratings

    movie_title_rating_list = []
    for rating in user_ratings:
        movie_title_rating_list.append((rating.movie.title, rating.score))

    return render_template("user_details.html", age=user_age,
                           zipcode=user_zipcode,
                           movie_ratings=movie_title_rating_list)



if __name__ == "__main__":
    # We have to set debug=True here, since it has to be True at the point
    # that we invoke the DebugToolbarExtension
    app.debug = True

    connect_to_db(app)

    # Use the DebugToolbar
    DebugToolbarExtension(app)

    app.run()
