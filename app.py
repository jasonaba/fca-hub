from flask import Flask, render_template, request
app = Flask(__name__)

#Routes

#Home Page
@app.route("/")
def home():#The "/" route is associated with the home function
    return render_template("index.html")#Flask automatically looks in a folder named "templates" if not otherwise specified

#Prayer Page
@app.route("/prayer", methods=["GET", "POST"])
def prayer():
    if request.method == "POST":
        prayer_request = request.form.get("prayer_request") #getting the value of "prayer_request" from the form
        print(prayer_request)
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