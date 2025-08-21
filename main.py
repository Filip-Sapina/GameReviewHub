"""
Main Application Program, starts flask site.
"""

import secrets
import re
import time
from datetime import datetime
from werkzeug import security

from flask import (
    Flask,
    g,
    redirect,
    url_for,
    render_template,
    request,
    flash,
    session,
    jsonify,
    abort,
)

from database_connection.user_connection import UserConnector
from database_connection.game_tag_connection import GameTagConnector
from database_connection.platform_connection import PlatformConnector
from database_connection.game_connection import GameConnector
from database_connection.review_connection import ReviewConnector, Review


# App Setup

UserConnection = UserConnector()
GameTagConnection = GameTagConnector()
PlatformConnection = PlatformConnector()
GameConnection = GameConnector()
ReviewConnection = ReviewConnector()

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
    returns a webpage from template "home.html", called when user goes to /home. Base page for the website.
    """
    games = GameConnection.get_games()
    for game in games:
        game.rating = GameConnection.get_avg_rating(game.game_id)

        game.review_count = len(ReviewConnection.get_reviews_by_game_id(game.game_id))

        accessibilty_ratios = ReviewConnection.get_accessibilty_ratios(game.game_id)
        game.has_colourblind_support = accessibilty_ratios[0]
        game.has_subtitles = accessibilty_ratios[1]
        game.has_difficulty_options = accessibilty_ratios[2]

        game.date_str = GameConnection.get_date_str(game.game_id)
    # sort games by when they released.
    recent_games = sorted(games, key=lambda g: g.release_date, reverse=True)
    # sort by game rating.
    best_games = sorted(games, key=lambda g: g.rating, reverse=True)

    current_year = datetime.now().year
    # Jan 1st of current year.
    start_current_year = datetime(current_year, 1, 1)
    # Jan 1st as timestamp for comparing to current year.
    timestamp_current_year = int(time.mktime(start_current_year.timetuple()))

    # 3 most recent games.
    most_recent = recent_games[:3]
    # 3 rated games.
    best_all_time = best_games[:3]

    # gets the 3 rated games from current year.
    best_recent = []
    for game in best_games:
        if game.release_date > timestamp_current_year:
            best_recent.append(game)
        if len(best_recent) > 3:
            break

    return render_template(
        "home.html",
        user=UserConnection.get_user_session(),
        current_year=current_year,
        most_recent=most_recent,
        best_recent=best_recent,
        best_all_time=best_all_time,
    )


# used for both login and register. only allows letters, numbers and some special characters
PATTERN_USERNAME = r"[a-zA-Z0-9_/\-]{3,20}"  # min 3 characters max 20
PATTERN_PASSWORD = r"[a-zA-Z0-9_@?\-]{5,30}"  # min 5 characters max 30
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
            return render_template("login.html", user=UserConnection.get_user_session())
        if not regex_password.fullmatch(password):
            flash("Invalid password format")
            return render_template("login.html", user=UserConnection.get_user_session())
        user = UserConnection.get_user_by_username(username)
        if user:
            if security.check_password_hash(user.password_hash, password):
                session["user_id"] = user.user_id
                flash("Login Accepted")
                return redirect(url_for("home"))
            flash("Password incorrect")
        else:
            flash("USER NOT FOUND")
    return render_template("login.html", user=UserConnection.get_user_session())


@app.route("/register", methods=["GET", "POST"])
def register_page():
    """Regisar Page for new users to create account."""
    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]
        if not regex_username.fullmatch(username):

            flash("Invalid username format")
            return render_template(
                "register.html", user=UserConnection.get_user_session()
            )
        if not regex_password.fullmatch(password):
            flash("Invalid password format")
            return render_template(
                "register.html", user=UserConnection.get_user_session()
            )

        if UserConnection.get_user_by_username(username):
            flash("Username is Already Taken!")
            return render_template(
                "register.html", user=UserConnection.get_user_session()
            )

        UserConnection.add_user(username, password)
        session["user_id"] = UserConnection.get_user_by_username(username).user_id
        return redirect(url_for("home"))
    return render_template("register.html", user=UserConnection.get_user_session())


@app.route("/logout")
def logout():
    """removes user's user_id in the session and sends to home"""
    session["user_id"] = None
    return redirect(url_for("login_page"))


@app.route("/search", methods=["GET"])
def search_page():
    """the search page of the website, appears when search bar is used."""
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
                tag = GameTagConnection.get_game_tag_by_name(tag_filter)
                if tag:
                    tag_ids.append(tag.tag_id)
            games = GameConnection.get_games_by_game_tag_ids(tag_ids)

        elif search_term:
            games = GameConnection.get_games_by_closest_match(search_term)
        else:
            games = GameConnection.get_games()

        for game in games:
            # Format each game's release date
            game.date_str = GameConnection.get_date_str(game.game_id)

            # Get Average Rating for each Game
            game.rating = GameConnection.get_avg_rating(game.game_id)

            game.review_count = len(
                ReviewConnection.get_reviews_by_game_id(game.game_id)
            )

            accessibilty_ratios = ReviewConnection.get_accessibilty_ratios(game.game_id)
            game.has_colourblind_support = accessibilty_ratios[0]
            game.has_subtitles = accessibilty_ratios[1]
            game.has_difficulty_options = accessibilty_ratios[2]

    return render_template(
        "search.html",
        user=UserConnection.get_user_session(),
        search=search_term,
        games=games,
        game_tags=GameTagConnection.get_game_tags(),
        filters=filters,
    )


@app.route("/game/<int:game_id>", methods=["GET", "POST"])
def game_page(game_id: int):
    user = UserConnection.get_user_session()

    real_method = request.form.get("_method")
    method = request.method if not real_method else real_method.upper()

    # Logic for add/updating review.
    if method in ("POST, PUT"):

        # Shared Logic
        data = request.form.to_dict(flat=True)
        data["user_id"] = UserConnection.get_user_session().user_id
        data["game_id"] = game_id
        data["platform_id"] = PlatformConnection.get_platform_by_name(
            data["user_platform"]
        ).platform_id
        data["review_date"] = datetime.now().timestamp()

        data["has_subtitles"] = bool(data.get("has_subtitles"))
        data["has_difficulty_options"] = bool(data.get("has_difficulty_options"))
        data["has_colourblind_support"] = bool(data.get("has_colourblind_support"))

        review = Review.from_dict(data)

        if method == "POST":
            # writing review logic + security checks

            if len(review.review_text) > 1000 or PlatformConnection.get_platform_by_id(
                review.platform_id
            ):
                flash("Invalid Review!")
            else:
                ReviewConnection.add_review(review)
                flash("Review Submitted!")
        else:  # method must be PUT
            # editing review logic
            old_review = ReviewConnection.get_review_by_game_and_user(
                data["game_id"], data["user_id"]
            )
            new_review = Review.from_dict(data)
            ReviewConnection.update_review(new_review, old_review.review_id)
            flash("Review Updated!")

        return redirect(url_for("game_page", game_id=game_id))

    # For GET method

    game = GameConnection.get_game_by_id(game_id)
    if game is None:
        flash("Game Not Found")
        return redirect(url_for("home"))

    reviews = ReviewConnection.get_reviews_by_game_id(game_id)
    user_review = None

    accessibilty_ratios = ReviewConnection.get_accessibilty_ratios(game.game_id)
    game.has_colourblind_support = accessibilty_ratios[0]
    game.has_subtitles = accessibilty_ratios[1]
    game.has_difficulty_options = accessibilty_ratios[2]


    for review in reviews:
        review.platform = PlatformConnection.get_platform_by_id(review.platform_id)
        review.user = UserConnection.get_user_by_id(review.user_id)
        if user.user_id == review.user.user_id:
            user_review = review

    return render_template(
        "game.html",
        game=game,
        user=user,
        platforms=PlatformConnection.get_platforms_by_game_name(game.title),
        reviews=reviews,
        user_review=user_review,
    )


@app.route("/filter_reviews", methods=["GET"])
def filter_reviews():
    filter_type = request.args.get("filter", "mixed")
    game_id = request.args.get("game_id")

    reviews = ReviewConnection.get_reviews_by_game_id(game_id)

    if filter_type == "positive":
        filtered = [
            (
                r,
                UserConnection.get_user_by_id(r.user_id),
                PlatformConnection.get_platform_by_id(r.platform_id),
            )
            for r in reviews
            if r.rating > 7
        ]
    elif filter_type == "negative":
        filtered = [
            (
                r,
                UserConnection.get_user_by_id(r.user_id),
                PlatformConnection.get_platform_by_id(r.platform_id),
            )
            for r in reviews
            if r.rating < 5
        ]
    else:
        filtered = [
            (
                r,
                UserConnection.get_user_by_id(r.user_id),
                PlatformConnection.get_platform_by_id(r.platform_id),
            )
            for r in reviews
        ]

    return jsonify(filtered)


@app.route("/")
def index():
    """simple redirect from home, only should be called when first going to website."""
    return redirect(url_for("home"))


@app.errorhandler(404)
def page_not_found(error):
    flash(error)
    return render_template("404.html", user=UserConnection.get_user_session())


@app.errorhandler(505)
def page_not_found(error):
    flash(error)
    return render_template("505.html", user=UserConnection.get_user_session())


@app.route("/trigger505")
def trigger_505():
    abort(505)


if __name__ == "__main__":
    app.run(debug=True)
