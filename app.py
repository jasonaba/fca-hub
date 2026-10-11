from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///fca_hub.db"
db = SQLAlchemy(app)

#Database for Prayer Requests
class PrayerRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=True)
    request = db.Column(db.Text, nullable=False)
    prayed_for = db.Column(db.Boolean, default=False, nullable=False)
    submitted_at = db.Column(db.DateTime, default = datetime.utcnow, nullable=False)

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

with app.app_context():
    db.create_all()


#Routes

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



@app.route("/suggestions/review")
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


#Bible inventory
@app.route("/bibles")
def bibles():
    return render_template("bibles.html")

@app.route("/prayer-requests", methods=["GET", "POST"])
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