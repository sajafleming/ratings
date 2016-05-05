"""Models and database functions for Ratings project."""

from flask_sqlalchemy import SQLAlchemy

from datetime import datetime

import correlation
# This is the connection to the PostgreSQL database; we're getting this through
# the Flask-SQLAlchemy helper library. On this, we can find the `session`
# object, where we do most of our interactions (like committing, etc.)

db = SQLAlchemy()


##############################################################################
# Model definitions

class User(db.Model):
    """User of ratings website."""

    __tablename__ = "users"

    user_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    email = db.Column(db.String(64), nullable=True)
    password = db.Column(db.String(64), nullable=True)
    age = db.Column(db.Integer, nullable=True)
    zipcode = db.Column(db.String(15), nullable=True)
    

    def __repr__(self):
        """Provide helpful representation when printed."""   
        
        return ("<User user_id=%s email=%s age=%s zipcode=%s>" 
                % (self.user_id, self.email, self.age, self.zipcode)) 

    def similarity(self, other):
        """Return Pearson rating for user compared to other user."""

        u_ratings = {}
        paired_ratings = []

        for r in self.ratings:
            u_ratings[r.movie_id] = r

        for r in other.ratings:
            u_r = u_ratings.get(r.movie_id)
            # only add if they have both rated the movie
            if u_r:
                paired_ratings.append( (u_r.score, r.score) )

        if paired_ratings:
            return correlation.pearson(paired_ratings)
        else:
            return 0.0

    def predict_rating(self, movie):
        """Predict user's rating of a movie."""

        other_ratings = movie.ratings

        # correlation coefficient and rating object tuple
        similarities = [
            (self.similarity(r.user), r)
            for r in other_ratings
        ]

        # sort similarties list in descending order to find best match (highest number)
        similarities.sort(reverse=True)

        # only get similarity coef and rating pair for those with positive coefs
        similarities = [(sim, r) for sim, r in similarities if sim > 0]

        # if there are no positive similarity coefs, return none
        if not similarities:
            return None

        # unpacks sim coef and rating and multiplies the sim coef with that
        # rating's score for numerator
        numerator = sum([r.score * sim for sim, r in similarities])

        # unpacks sim coef and rating and adds up sim coefs as denominator
        denominator = sum([sim for sim, r in similarities])

        # gets an awesomely accurate prediction!
        return numerator / denominator


# Put your Movie and Rating model classes here.
class Movie(db.Model):
    """Movies in ratings website"""

    __tablename__ = "movies"

    movie_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    released_at = db.Column(db.DateTime, nullable=True)
    imdb_url = db.Column(db.String(400), nullable=True)

    def __repr__(self):
        """Provide helpful representation when printed."""

        return ("<Movie movie_id=%s title=%s released_at=%s imdb_url=%s>"
                % (self.movie_id, self.title, self.released_at, self.imdb_url))
               #add in datetime for released_at later

class Rating(db.Model):
    """Ratings of movies by users"""

    __tablename__ = "ratings"

    rating_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    movie_id = db.Column(db.Integer, db.ForeignKey('movies.movie_id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    score = db.Column(db.Integer, nullable=False)

    # Define relationship to user
    user = db.relationship('User', 
                           backref=db.backref('ratings', order_by=rating_id))

    # Define relationship to movie
    movie = db.relationship('Movie',
                            backref=db.backref('ratings', order_by=rating_id))


    def __repr__(self):
        """Provide helpful representation when printed."""

        return ("<Rating rating_id=%s movie_id=%s user_id=%s score=%s>" 
                % (self.rating_id, self.movie_id, self.user_id, self.score))



##############################################################################
# Helper functions

def connect_to_db(app):
    """Connect the database to our Flask app."""

    # Configure to use our PstgreSQL database
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql:///ratings'
    db.app = app
    db.init_app(app)


if __name__ == "__main__":
    # As a convenience, if we run this module interactively, it will leave
    # you in a state of being able to work with the database directly.

    from server import app
    connect_to_db(app)
    print "Connected to DB."
