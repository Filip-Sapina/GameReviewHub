"""
Main Application Program, starts flask site.
"""

import secrets
import re
from datetime import datetime
from werkzeug import security

from flask import Flask, g, redirect, url_for, render_template, request, flash, session, jsonify

from database_connection.user_connection import (
    add_user,
    get_user_by_id,
    get_user_by_username,
    get_user_session,
)
from database_connection.game_tag_connection import (
    get_game_tag_by_name,
    get_game_tags,
)
from database_connection.platform_connection import (
    get_platform_by_id,
    get_platform_by_name,
    get_platforms_by_game_name,
)
from database_connection.game_connection import (
    get_game_by_id,
    get_avg_rating,
    get_games,
    get_games_by_closest_match,
    get_games_by_game_tag_ids,
)
from database_connection.review_connection import (
    add_review,
    get_reviews_by_game_id,
    get_review_by_game_and_user,
    update_review,
    Review,
)


# App Setup

app = Flask(__name__)
app.config["SECRET_KEY"] = secrets.token_urlsafe(32)


# Web App Logic
@app.teardown_appcontext
def close_database_connection(exception):
    """closes database when app has been closed"""
    db = g.pop("db", None)
    if db is not None:
        db.close()
    if exception is not None:
        print(f"ERROR: {exception} RAISED ON CLOSING APP")


@app.route("/home")
def home():
    """
    returns a webpage from template "home.html", called when user goes to /home.
    """

    return render_template("home.html", user=get_user_session())

# used for both login and register. only allows letters, numbers and some special characters
PATTERN_USERNAME = r'[a-zA-Z0-9_\/\-]{3, 20}' # min 3 characters max 20
PATTERN_PASSWORD = r'[a-zA-Z0-9_@?/\\-]{5, 30}' # min 5 characters max 30
regex_username = re.compile(PATTERN_USERNAME)
regex_password = re.compile(PATTERN_PASSWORD)

@app.route("/login", methods=["GET", "POST"])
def login_page():
    """
    login page for site.
    sets session's user id to user's user id if they login successfuly.
    """

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        if not regex_username.fullmatch(username):
            flash("Invalid username format")
            return render_template("login.html", user=get_user_session())
        if not regex_password.fullmatch(password):
            flash("Invalid password format")
            return render_template("login.html", user=get_user_session())


        user = get_user_by_username(username)

        if user:

            if security.check_password_hash(user.password_hash, password):
                session["user_id"] = user.user_id
                flash("Login Accepted")
                return redirect(url_for("home"))
            else:
                flash("Password incorrect")
        else:
            flash("USER NOT FOUND")
    return render_template("login.html", user=get_user_session())


@app.route("/register", methods=["GET", "POST"])
def register_page():
    """Regisar Page for new users to create account."""
    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]
        if not regex_username.fullmatch(username):
            flash("Invalid username format")
            return render_template("register.html", user=get_user_session())
        if not regex_password.fullmatch(password):
            flash("Invalid password format")
            return render_template("register.html", user=get_user_session())

        if get_user_by_username(username):
            flash("Username is Already Taken!")
            return render_template("register.html", user=get_user_session())
        
        add_user(username, password)
        session["user_id"] = get_user_by_username(username).user_id
        return redirect(url_for("home"))
    return render_template("register.html", user=get_user_session())


@app.route("/logout")
def logout():
    """removes user's user_id in the session and sends to home"""
    session["user_id"] = None
    return redirect(url_for("login_page"))


@app.route("/search", methods=["GET"])
def search_page():
    search_term = ""
    filters = []
    tag_ids = []
    games = []

    if request.method == "GET":
        search_term = request.args.get("search_term", "")

        # Get Game Tags that are on.
        for key, value in request.form.items():
            if value == "on":
                filters.append(key)

        # If game tags have been set as filters, manage it.
        if filters:
            for tag_filter in filters:
                tag = get_game_tag_by_name(tag_filter)
                if tag:
                    tag_ids.append(tag.id)
            games = get_games_by_game_tag_ids(tag_ids)

        elif search_term:
            games = get_games_by_closest_match(search_term)
        else:
            games = get_games()

        for game in games:
            # Format each game's release date
            release_date = datetime.fromtimestamp(game.release_date)
            date = release_date.date().strftime("%d/%m/%Y")
            time_passed = datetime.now() - release_date

            years_passed = time_passed.days / 365.25
            if years_passed < 1:
                months_passed = time_passed.days // 30  # approximate months
                game.date_str = f"{date} ({months_passed} month(s) ago)"
            else:
                game.date_str = f"{date} ({round(years_passed, 1)} year(s) ago)"

            # Get Average Rating for each Game
            game.rating = get_avg_rating(game.id)

            # Review managing
            reviews = get_reviews_by_game_id(game.id)

            # Get Review Count
            game.review_count = len(reviews)

            # get amount of reviews with each accessibilty setting.
            if game.review_count > 0:
                MAJORITY_RATIO = 0.6
                game.has_colourblind_support = 0
                game.has_difficulty_options = 0
                game.has_subtitles = 0
                for review in reviews:
                    if review.accessibility.has_colourblind_support:
                        game.has_colourblind_support += 1
                    if review.accessibility.has_difficulty_options:
                        game.has_difficulty_options += 1
                    if review.accessibility.has_subtitles:
                        game.has_subtitles += 1
                game.has_colourblind_support = (
                    game.has_colourblind_support / game.review_count
                ) > MAJORITY_RATIO
                game.has_colourblind_support = (
                    game.has_difficulty_options / game.review_count
                ) > MAJORITY_RATIO
                game.has_colourblind_support = (
                    game.has_subtitles / game.review_count
                ) > MAJORITY_RATIO

    return render_template(
        "search.html",
        user=get_user_session(),
        search=search_term,
        games=games,
        game_tags=get_game_tags(),
        filters=filters,
    )


@app.route("/game/<int:game_id>", methods=["GET", "POST"])
def game_page(game_id: int):
    user = get_user_session()

    real_method = request.form.get("_method")
    method = request.method if not real_method else real_method.upper()

    # Logic for add/updating review.
    if method in ("POST, PUT"):

        # Shared Logic
        data = request.form.to_dict(flat=True)
        data["user_id"] = get_user_session().user_id
        data["game_id"] = game_id
        data["platform_id"] = get_platform_by_name(data["user_platform"]).id
        data["review_date"] = datetime.now().timestamp()

        data["has_subtitles"] = True if data.get("has_subtitles") else False
        data["has_difficulty_options"] = (
            True if data.get("has_difficulty_options") else False
        )
        data["has_colourblind_support"] = (
            True if data.get("has_colourblind_support") else False
        )

        review = Review(**data)

        if method == "POST":
            # writing review logic
            add_review(review)
            flash("Review Submitted!")
        else:  # method must be PUT
            # editing review logic
            old_review = get_review_by_game_and_user(data["game_id"], data["user_id"])
            new_review = Review(**data)
            update_review(new_review, old_review.review_id)
            flash("Review Updated!")

        return redirect(url_for("game_page", game_id=game_id))

    # For GET method

    game = get_game_by_id(game_id)
    if game is None:
        flash("Game Not Found")
        return redirect(url_for("home"))

    reviews = get_reviews_by_game_id(game_id)
    user_review = None

    for review in reviews:
        review.platform = get_platform_by_id(review.platform_id)
        review.user = get_user_by_id(review.user_id)
        if user.user_id == review.user.user_id:
            user_review = review

    return render_template(
        "game.html",
        game=game,
        user=user,
        platforms=get_platforms_by_game_name(game.title),
        reviews=reviews,
        user_review=user_review,
    )

@app.route("/filter_reviews", methods=["GET"])
def filter_reviews():
    filter_type = request.args.get("filter", "mixed")
    game_id = request.args.get("game_id")

    reviews = get_reviews_by_game_id(game_id)

    for review in reviews:
        review.user = get_user_by_id(review.user_id).__dict__
        review.platform = get_platform_by_id(review.platform_id)


    if filter_type == "positive":
        filtered = [r.__dict__ for r in reviews if r.rating > 7]
    elif filter_type == "negative":
        filtered = [r.__dict__ for r in reviews if r.rating < 5]
    else:
        filtered = [r.__dict__ for r in reviews]

    return jsonify(filtered)

        
    

@app.route("/")
def index():
    """simple redirect from home, only should be called when first going to website."""
    return redirect(url_for("home"))


if __name__ == "__main__":
    app.run(debug=True)
