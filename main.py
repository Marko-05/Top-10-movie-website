from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Float
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
import requests

class Base(DeclarativeBase):
    pass

# Creates the page forms

class EditForm(FlaskForm):
    rating = StringField('Your rating out of 10 e.g. 7.2', validators=[DataRequired()])
    review = StringField('Your review')
    submit = SubmitField('Done')

class AddForm(FlaskForm):
    title = StringField('Movie Title', validators=[DataRequired()])
    submit = SubmitField('Add movie')


app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///movies.db"
# Change if needed
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
Bootstrap5(app)


# CREATE DB
db = SQLAlchemy(model_class=Base)
db.init_app(app)

# CREATE TABLE
class Movie(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    rating: Mapped[float] = mapped_column(Float, nullable=True)
    ranking: Mapped[int] = mapped_column(Integer, nullable=True)
    review: Mapped[str] = mapped_column(String(250), nullable=True)
    img_url: Mapped[str] = mapped_column(String(250), nullable=False)

with app.app_context():
    db.create_all()

# EXAMPLE MOVIES
# with app.app_context():
#     new_movie = Movie(
#         title="Phone Booth",
#         year=2002,
#         description="Publicist Stuart Shepard finds himself trapped in a phone booth, pinned down by an extortionist's sniper rifle. Unable to leave or receive outside help, Stuart's negotiation with the caller leads to a jaw-dropping climax.",
#         rating=7.3,
#         ranking=10,
#         review="My favourite character was the caller.",
#         img_url="https://image.tmdb.org/t/p/w500/tjrX2oWRCM3Tvarz38zlZM7Uc10.jpg"
#     )
#     db.session.add(new_movie)
#     db.session.commit()

# with app.app_context():
#     second_movie = Movie(
#         title="Avatar The Way of Water",
#         year=2022,
#         description="Set more than a decade after the events of the first film, learn the story of the Sully family (Jake, Neytiri, and their kids), the trouble that follows them, the lengths they go to keep each other safe, the battles they fight to stay alive, and the tragedies they endure.",
#         rating=7.3,
#         ranking=9,
#         review="I liked the water.",
#         img_url="https://image.tmdb.org/t/p/w500/t6HIqrRAclMCA60NsSmeqe9RmNV.jpg"
#     )
#     db.session.add(second_movie)
#     db.session.commit()


@app.route("/")
def home():

    # queries all of the movies and assigns them their rank based on user rating
    result = db.session.execute(db.select(Movie).order_by(Movie.rating))
    all_movies = result.scalars().all()  # convert ScalarResult to Python List

    for i in range(len(all_movies)):
        all_movies[i].ranking = len(all_movies) - i
    db.session.commit()

    return render_template("index.html", movies=all_movies)

@app.route("/edit", methods=["GET", "POST"])
def edit():
    # gets the movie id from the index.html file
    form = EditForm()
    movie_id = request.args.get("id")
    movie = db.get_or_404(Movie, movie_id)
    if form.validate_on_submit():
        movie.rating = float(form.rating.data)
        movie.review = form.review.data
        db.session.commit()
        return redirect(url_for('home'))
    return render_template("edit.html",movie=movie, form=form)

@app.route("/delete", methods=["GET", "POST"])
def delete():
    movie = db.get_or_404(Movie,request.args.get("id"))
    db.session.delete(movie)
    db.session.commit()
    return redirect(url_for('home'))

@app.route("/add", methods=["GET", "POST"])
def add_movie():
    form = AddForm()
    if form.validate_on_submit():

        # add your API token here
        headers = {
            "accept": "application/json",
            "Authorization": "Bearer API_TOKEN"
        }
        # finds all movies with a similar or same title and renders them as anchor tags
        response = requests.get("https://api.themoviedb.org/3/search/movie?include_adult=false&language=en-US&page=1", headers=headers, params={"query": request.form["title"]})
        return render_template("select.html",data=response.json())
    return render_template("add.html", form=form)



@app.route("/find", methods=["GET", "POST"])
def find_movie():

    # add your API token here
    headers = {
        "accept": "application/json",
        "Authorization": "Bearer Token"
    }

    # returns the data for the requested movie
    response = requests.get(f"https://api.themoviedb.org/3/movie/{request.args.get("id")}?language=en-US", headers=headers)
    print(response.text)
    data = response.json()
    new_movie = Movie(title=data["title"], year=int(data["release_date"][:4]), img_url=f"https://image.tmdb.org/t/p/w500/{data["poster_path"]}",description=data["overview"])

    db.session.add(new_movie)
    db.session.commit()
    return redirect(url_for('edit', id=new_movie.id))


if __name__ == '__main__':
    app.run(debug=True)
