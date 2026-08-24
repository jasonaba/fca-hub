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
    if request.method == "POST":
        prayer_request = request.form.get("prayer_request").strip() #getting the value of "prayer_request" from the form
        #Invalid submissions:
        # Empty
        # Only white spaces
        if len(prayer_request)>0: #or could say "if prayer_request" because an empty string is False while a non-empty string is True in Python (called "truthiness" in Python)
            print(prayer_request)
        else:
            print("Prayer request submission is invalid! Enter your prayer request.")
    return render_template("prayer.html")


#Attendance Page
@app.route("/attendance")
def attendance():
    return render_template("attendance.html")

#Bible inventory
@app.route("/bibles")
def bibles():
    return render_template("bibles.html")

#Run the web server
if __name__ == "__main__":
    app.run(debug=True)