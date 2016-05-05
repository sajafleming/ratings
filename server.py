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

    # Gets all users from user table in database
    users = User.query.all()
    return render_template("user_list.html", users=users)

@app.route('/add_user')
def add_user():
    """Add user form"""

    return render_template("add_user_form.html")

@app.route('/new_user', methods=["POST"])
def new_user_validation():
    """Check if user in db, if not, add!"""

    # Get email and password from the add_user form
    user_email = request.form.get('email')
    user_password = request.form.get('password')

    # Checks if user is already a member, by email and redirects them to login
    if User.query.filter_by(email=user_email).first():
        flash("You are already a member, please log in.") 
    # If new user, adds new user to users table and redirects to login
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

    # Get email and password from the user login page
    user_email = request.form.get('email')
    user_password = request.form.get('password')

    # Check User db for email and password match, if a match add to session and rediredt to homepage
    if User.query.filter_by(email=user_email, password=user_password).first():
        flash("Congrats, you actually remembered your password")
        logged_in_user = User.query.filter_by(email=user_email, password=user_password).first()
        session["user_id"] = logged_in_user.user_id
        return redirect('/')
    # If email and password do not match, prompt user to validate again
    else:
        flash("you idiot, try again and this time GET IT RIGHT.")
        return render_template("login.html")

@app.route('/logout')
def user_logout():
    """Logs out"""

    # Deletes user_id from session when logging out
    del session["user_id"]

    flash("You have chosen to leave us. :( ")

    return redirect('/')

@app.route('/users/<int:user_id>')
def user_details(user_id):
    """Show user details"""

    # Get user from url
    user = User.query.get(user_id)    

    # Get user's age, zipcode and ratings from db
    user_age = user.age
    user_zipcode = user.zipcode 
    user_ratings = user.ratings

    # Iterate through user ratings and get title, rating score, and movie id for each movie rated
    movie_title_rating_list = []
    for rating in user_ratings:
        movie_title_rating_list.append((rating.movie.title, rating.score, rating.movie.movie_id))

    return render_template("user_details.html", 
                           age=user_age,
                           zipcode=user_zipcode,
                           movie_ratings=movie_title_rating_list)

@app.route('/movies')
def movies_list():
    """Show all the movies in alphabetical order"""

    # Get all movies and order by title
    movies = Movie.query.order_by('title').all()

    return render_template("movie_list.html", movies=movies)

@app.route('/movies/<int:movie_id>')
def movie_details(movie_id):
    """Show movie details with ratings"""

    # Get movie by movie_id
    movie = Movie.query.get(movie_id)

    # Get title imdb url, ratings, movie id from db
    movie_title = movie.title
    movie_url = movie.imdb_url
    movie_ratings = movie.ratings
    movie_id = movie.movie_id

    user_id = session.get('user_id')
    # Iterate through movie_ratings and get user_id and score for each rating and append to list
    ratings_list = []
    for rating in movie_ratings:
        ratings_list.append((rating.user_id, rating.score))


    # If logged in, get user's rating if exists and prompt for updated/new rating
    if user_id:
        user_score = (db.session.query(Rating.score)
            .filter(Rating.user_id == user_id, Rating.movie_id==movie_id)
            .first())

        # If rating exists, db.session.query returns as tuple so 
        # taking item out of tuple
        if user_score:
            user_score = user_score[0]

        user_rating = (user_id, user_score)

        # old slow way that looks through every rating
        # for rating in ratings_list:
        #     if user_id == rating[0]:
        #         user_rating = rating
        #     else:
                # user_rating = (user_id, None)
    else:
        user_rating = None

    
    # Find average rating for movie

    # list of all scores for this movie id
    rating_scores = [r.score for r in movie.ratings]
    avg_rating = float(sum(rating_scores)) / len(rating_scores)

    prediction = None

    # Predict code: only predict if the user hasn't rated it yet

    # If user has not yet rated and there is a valid user_id
    if (user_rating[1] == None) and user_id:
        user = User.query.get(user_id)
        if user:
            prediction = user.predict_rating(movie)

    return render_template("movie_details.html",
                           title=movie_title,
                           url=movie_url,
                           movie_id=movie_id,
                           user_rating=user_rating,
                           movie_ratings=ratings_list,
                           average=avg_rating,
                           prediction=prediction)


@app.route("/new-rating", methods=["POST"])
def update_rating():
    """Will update user rating in database given user is logged in"""

    # Get rating from rating form
    new_rating = request.form.get('new_rating')
    # Get movie idea from hidden form
    movie_id = request.form.get('movie_id')

    # If user logged in update rating attribute of particular user
    if session['user_id']: 
        if Rating.query.filter_by(movie_id=movie_id, user_id=session['user_id']).first():
            rating = Rating.query.filter_by(movie_id=movie_id, user_id=session['user_id']).first()
            rating.score = new_rating
        else:
            rating = Rating(movie_id=movie_id, user_id=session['user_id'], score=new_rating) 
            db.session.add(rating)

    db.session.commit()

    return redirect('/movies/%s' %(movie_id))


if __name__ == "__main__":
    # We have to set debug=True here, since it has to be True at the point
    # that we invoke the DebugToolbarExtension
    app.debug = True

    connect_to_db(app)

    # Use the DebugToolbar
    DebugToolbarExtension(app)

    app.run()
