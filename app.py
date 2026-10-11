
import os
from datetime import datetime
from functools import wraps
from hmac import compare_digest

from dotenv import load_dotenv
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
)
from flask_sqlalchemy import SQLAlchemy

load_dotenv()

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("FLASK_SECRET_KEY")

if not app.config["SECRET_KEY"] or not os.environ.get("FCA_ADMIN_PASSWORD"):
    raise RuntimeError(
        "Missing FLASK_SECRET_KEY or FCA_ADMIN_PASSWORD in .env"
    )

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///fca_hub.db"
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

db = SQLAlchemy(app)


#Database for Prayer Requests
class PrayerRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=True)
    request = db.Column(db.Text, nullable=False)
    prayed_for = db.Column(db.Boolean, default=False, nullable=False)
    submitted_at = db.Column(db.DateTime, default = datetime.utcnow, nullable=False)

#Database for Study Suggestions
class StudySuggestion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    suggested_by = db.Column(db.String, nullable=True)
    topic = db.Column(db.String(200), nullable=False)
    details = db.Column(db.Text, nullable=True)
    submitted_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False
    )

#Database for Bible Requests
class BibleRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    needs_bible = db.Column(
        db.Boolean,
        default=True,
        nullable=False
    )
    submitted_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False
    )


with app.app_context():
    db.create_all()

def leader_required(view_function):
    @wraps(view_function)
    def wrapped_view(*args, **kwargs):
        if not session.get("is_leader"):
            return redirect(url_for("login"))
        return view_function(*args, **kwargs)

    return wrapped_view



#Routes

#Login Page (Leaders Only)

@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("is_leader"):
        return redirect(url_for("study_suggestions"))

    error = False

    if request.method == "POST":
        password = request.form.get("password") or ""
        admin_password = os.environ["FCA_ADMIN_PASSWORD"]

        if compare_digest(password, admin_password):
            session.clear()
            session["is_leader"] = True
            return redirect(url_for("study_suggestions"))

        error = True

    return render_template("login.html", error=error)

#Logout route (to log leaders out)

@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return redirect(url_for("login"))


#Home Page
@app.route("/")
def home():#The "/" route is associated with the home function
    return render_template("index.html")#Flask automatically looks in a folder named "templates" if not otherwise specified

#Prayer Page
@app.route("/prayer", methods=["GET", "POST"])
def prayer():
    submitted = False
    invalid = False
    if request.method == "POST":
        prayer_request = request.form.get("prayer_request").strip() #getting the value of "prayer_request" from the form
        name = request.form.get("name").strip()
        
        #Invalid submissions:
        # Empty
        # Only white spaces
        if len(prayer_request)>0: #or could say "if prayer_request" because an empty string is False while a non-empty string is True in Python (called "truthiness" in Python)
            prayer = PrayerRequest(request = prayer_request, name = name)
            db.session.add(prayer)
            db.session.commit()
            submitted = True
            invalid = False
        else:
            invalid = True
    return render_template("prayer.html", submitted=submitted, invalid = invalid)


#Study Suggestions Page
@app.route("/suggestions", methods=["GET", "POST"])
def suggestions():
    submitted = False
    invalid = False

    if request.method == "POST":
        topic = (request.form.get("topic") or "").strip()
        suggested_by = (request.form.get("suggested_by") or "").strip()
        details = (request.form.get("details") or "").strip()

        if topic:
            suggestion = StudySuggestion(
                topic=topic,
                suggested_by=suggested_by or None,
                details=details or None
            )

            db.session.add(suggestion)
            db.session.commit()

            submitted = True
        else:
            invalid = True

    return render_template(
        "suggestions.html",
        submitted=submitted,
        invalid=invalid
    )


#Suggestions Review Page
@app.route("/suggestions/review")
@leader_required #makes it so only logged-in leaders can access
def study_suggestions():
    suggestions = db.session.execute(
        db.select(StudySuggestion).order_by(
            StudySuggestion.submitted_at.desc()
        )
    ).scalars().all()

    return render_template(
        "study-suggestions.html",
        suggestions=suggestions
    )


#Bible Request Page
@app.route("/needbible", methods=["GET", "POST"])
def needbibles():
    submitted = False
    invalid = False

    if request.method == "POST":
        name = (request.form.get("name") or "").strip()
        wants_bible = request.form.get("needs_bible") == "yes"
        print(wants_bible)
        if name and wants_bible:
            bible_request = BibleRequest(name=name)
            db.session.add(bible_request)
            db.session.commit()
            submitted = True
        else:
            invalid = True

    return render_template(
        "needbible.html",
        submitted=submitted,
        invalid=invalid
    )


#Bible Requests Review Page
@app.route("/needbible/review", methods=["GET", "POST"])
@leader_required
def bible_requests():
    if request.method == "POST":
        request_id = request.form.get("id", type=int)
        action = request.form.get("action")

        bible_request = db.session.get(BibleRequest, request_id)

        if bible_request is not None:
            if action == "toggle":
                bible_request.needs_bible = not bible_request.needs_bible
                db.session.commit()

            elif action == "delete":
                db.session.delete(bible_request)
                db.session.commit()

        return redirect(url_for("bible_requests"))

    bible_requests = db.session.execute(
        db.select(BibleRequest).order_by(
            BibleRequest.submitted_at.desc()
        )
    ).scalars().all()

    return render_template(
        "bible-requests.html",
        bible_requests=bible_requests
    )

@app.route("/prayer-requests", methods=["GET", "POST"])
@leader_required
def prayer_requests():
    if request.method=="POST":
        #if someone selects "Mark as prayed for"
        prayer_id = request.form.get("id")
        prayer = db.session.execute(
            db.select(PrayerRequest).where(PrayerRequest.id == prayer_id)
            ).scalars().first()
        prayer.prayed_for = not prayer.prayed_for
        db.session.commit()

    return render_template( #passes the whole database of Prayer Requests into the html
        "prayer-requests.html", 
        prayer_requests = db.session.execute(
            db.select(PrayerRequest)
            ).scalars().all())

#Run the web server
if __name__ == "__main__":
    app.run(debug=True)