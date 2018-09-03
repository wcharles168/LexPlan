import os
from cs50 import SQL

import datetime
import time
from flask import Flask, flash, redirect, render_template, request, session, jsonify, send_from_directory
import requests
import json
from flask_session import Session
from flask_wtf.csrf import CSRFProtect
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions
from werkzeug.security import check_password_hash, generate_password_hash

from flask_socketio import SocketIO, emit

from helpers import apology, login_required

app = Flask(__name__)
app.config["JSONIFY_PRETTYPRINT_REGULAR"] = False

# csrf = CSRFProtect(app)

app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
socketio = SocketIO(app)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///LexPlan.db")


@app.route("/resume/<path:filename>", methods=['GET'])
def resume(filename):
    '''Main page for charleswang.info'''

    return send_from_directory("resume", filename)

@app.route("/", methods=['GET'])
def mainpage():

    return redirect("/resume/index.html")

# CHAT APPLICATION #

@app.route("/chat", methods=['GET', 'POST'])
@login_required
def chat():
    # Get username to display
    username = db.execute("SELECT * FROM users WHERE id = :userid", userid = session["user_id"])

    # User is requesting from to-do page (with specific channel id)
    if request.method == "POST":

        channel_id = request.form.get("channel_id")
        channel_name = request.form.get("channel_name")

        return render_template("chat.html", username = username, channel_id = channel_id, channel_name = channel_name)

    else:

        return render_template("chat.html", username = username)

@app.route("/get_channels", methods=["GET"])
def get_channel():
    '''Gets channels when window loads'''

    # Pre-create channels of the classes a user has

    channels = db.execute("SELECT * FROM channels")

    # Returns a list of dictionaries ie. channels
    return jsonify (channels)

@app.route("/add_channel", methods=["POST"])
def addChannel():
    '''Remembers channels'''

    # Gets channel name
    channel_name = request.form.get("channel")

    # Checks for channel uniqueness
    channelMatch = False

    rows = db.execute("SELECT * FROM channels WHERE name=:channel_name", channel_name = channel_name)

    if len(rows) > 0:
        channelMatch = True
        channels = None

    if channelMatch == False:
        db.execute("INSERT INTO channels (name) VALUES (:channel_name)", channel_name = channel_name)
        channels = db.execute("SELECT * FROM channels WHERE name=:channel_name", channel_name = channel_name)

    return jsonify({"status": channelMatch, "channel": channels})

@app.route("/get_message", methods=["POST"])
def getMessage():
    '''Retrieves messages'''

    # Gets channel id
    channel = request.form.get("channel")

    # Retrieves messages associated with channel
    messages = db.execute("SELECT * FROM messages JOIN channels ON messages.channel_id = channels.id JOIN users ON messages.user_id = users.id \
                            WHERE channels.id = :channel_id", channel_id = channel)

    return jsonify({"messages": messages})

@app.route("/delete_message", methods=["POST"])
def deleteMessage():
    '''Deletes messages from database'''
    messages = json.loads(request.form.get("messages"))

    # Loop through message ids
    for message in messages:
        db.execute("DELETE FROM messages WHERE message_id=:message_id", message_id = message)

    return jsonify(True)

@app.route("/delete_channel", methods=["POST"])
def deleteChannel():
    '''Deletes channel from database'''
    channel_id = request.form.get("channel_id")

    # Deletes messages associated with channel
    db.execute("DELETE FROM messages WHERE channel_id=:channel_id", channel_id = channel_id)
    # Delete channel
    db.execute("DELETE FROM channels WHERE id=:channel_id", channel_id = channel_id)

    return jsonify(True)

@app.route("/chuck_norris", methods=["GET"])
def chuckNorris():
    '''Gets a Chuck Norris joke'''

    response = requests.get("https://api.chucknorris.io/jokes/random?category=dev")

    return jsonify(response.json())

@socketio.on("message sent")
def message(data):

    message_text = data.get("message")
    channel_id = data.get("channel_id")
    user_id = data.get("user")
    time = data.get("time")

    # Insert new message into database
    db.execute("INSERT INTO messages (channel_id, user_id, message, timestamp) VALUES (:channel, :user_id, :message, :time)" \
                , channel = channel_id, user_id = user_id, message = message_text, time = time)

    # Retrieve username
    username = db.execute("SELECT username FROM users WHERE id=:userid", userid = user_id)
    # Retrieve message ID of message just inserted
    message = db.execute("SELECT message_id FROM messages WHERE channel_id=:channel AND user_id=:user_id AND message=:message AND timestamp=:time" \
                        , channel = channel_id, user_id = user_id, message = message_text, time = time)

    emit("message received", {"message": message_text, "channel_id": channel_id, "username": username, "user": user_id, "time": time, "id": message}, broadcast=True)

#   #   #   #   #   #   #

# PLANNER APPLICATION #

@app.route("/index")
@login_required
def index():
    # Get all classes for a user and make them channels if they do not already exist
    classes = db.execute("SELECT * FROM class_info WHERE user_id=:userID", userID = session["user_id"])

    # Get all current channels
    channels = db.execute("SELECT * FROM channels")

    channelMatch = False

    # Loop through all channels and classes
    for course in classes:
        for channel in channels:
            # If there is a channel with course name, do not insert into database
            if course["class_name"] == channel["name"]:
                channelMatch = True

        # If course name does not match channel name, create a new channel
        if channelMatch == False:
            db.execute("INSERT INTO channels (name) VALUES (:channel_name)", channel_name = course["class_name"])
            channelMatch = False
        else:
            channelMatch = False

    return redirect("/addAssignment")

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/index")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")

@app.route("/register_check", methods=["POST"])
def registerCheck():
    # Query database for username
    result = db.execute("SELECT * FROM users WHERE username = :username",
                      username=request.form.get("username"))

    # Ensure username does not exist
    if len(result) > 0:
        return jsonify({"status": False, "user": request.form.get("username")})

    else:
        return jsonify({"status": True})


@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        # Encrypt password
        hash = generate_password_hash(request.form.get("password"))

        # Insert username and password into database
        db.execute("INSERT INTO users (username, hash, bedtime) VALUES (:username, :hash, :bedtime)", username = request.form.get("username"), hash=hash, bedtime = request.form.get("bedtime"))

        # Remembers user
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        session["user_id"] = rows[0]["id"]

        return redirect("/index")

    else:
        return render_template("register.html")

@app.route("/class_check", methods=["POST"])
def checkClass():
     # Ensures that class is not entered twice
    rows = db.execute("SELECT * FROM class_info WHERE class_name = :classname",
                      classname=request.form.get("class_name"))

    if len(rows) > 0:
        return jsonify({"status": False, "class": request.form.get("class_name")})
    else:
        return jsonify({"status": True})

@app.route("/classSet", methods=["GET", "POST"])
@login_required
def classSet():
    """ Class information set up """
    if request.method == "POST":

        # Code for deleting assignments
        if request.form.get("class_id"):
            db.execute("DELETE FROM assignments WHERE class_ID = :classID", classID = request.form.get("class_id"))
            db.execute("DELETE FROM class_schedule WHERE class_ID = :classID", classID = request.form.get("class_id"))
            db.execute("DELETE FROM class_info WHERE ID = :classID", classID = request.form.get("class_id"))
            return redirect("/classSet")

        # Ensures a default time is inserted despite lack of user input
        submitTime = request.form.get("default_time")

        if not submitTime:
            submitTime = 30

        # Inputs class information into the class_info table
        db.execute("INSERT INTO class_info (default_time, class_name, user_ID) VALUES (:time, :name, :id)", time = submitTime, name = request.form.get("class_name"), id = session["user_id"])

        # Generates list of classes to be passed in to html form
        classes = db.execute("SELECT class_name, ID FROM class_info WHERE user_ID = :userID", userID = session["user_id"])

        return render_template("class_setup.html", classes = classes)

    else:
        # Generates list of classes to be passed in to html form
        classes = db.execute("SELECT class_name, ID FROM class_info WHERE user_ID = :userID", userID = session["user_id"])

        return render_template("class_setup.html", classes = classes)

@app.route("/check_overlap", methods=["POST"])
def checkOverlap():
    rows = db.execute("SELECT start_time, end_time, class_name FROM class_schedule JOIN class_info ON class_schedule.class_ID = class_info.ID \
                        WHERE class_info.user_ID = :userID AND DoW = :dow", userID = session["user_id"], dow = request.form.get("DoW"))

    print(request.form.get('start_time'), request.form.get('end_time'))

    for row in rows:
        print(row.get("class_name"), row.get("start_time"), row.get("end_time"))
        # Time ranges overlap
        if ((request.form.get("start_time") <= row.get("end_time")) and (row.get("start_time") <= request.form.get("end_time"))):
            return jsonify ({"status": False, "overlap": row.get("class_name")})

    return jsonify ({"status": True})

@app.route("/ScheduleSet", methods=["GET", "POST"])
@login_required
def scheduleSet():
    """ Class schedule set up """
    if request.method == "POST":

        # Code for deleting scheduling
        if request.form.get("schedule_id"):
            db.execute("DELETE FROM class_schedule WHERE schedule_ID = :schedID", schedID = request.form.get("schedule_id"))
            return redirect("/ScheduleSet")

        # Insert scheduling information into class_schedule table
        db.execute("INSERT INTO class_schedule (DoW, start_Time, end_Time, class_ID) VALUES (:day, :stime, :etime, :id)", day = request.form.get("DoW"), stime = request.form.get("start_time"), etime = request.form.get("end_time"), id = request.form.get("class"))

        # Information used on html page for the drop down menu of classes
        classes = db.execute("SELECT class_name, ID FROM class_info WHERE user_ID = :userID", userID = session["user_id"])
        classSched = db.execute("SELECT DoW, start_time, end_time, class_name, schedule_ID FROM class_schedule JOIN class_info, users ON class_schedule.class_ID = class_info.ID AND class_info.user_ID = users.ID WHERE user_ID = :userId ORDER BY DoW, start_Time", userId = session["user_id"])

        return render_template("scheduling_setup.html", classes = classes, classSchedules = classSched)

    else:
        classes = db.execute("SELECT class_name, ID FROM class_info WHERE user_ID = :userID", userID = session["user_id"])
        classSched = db.execute("SELECT DoW, start_time, end_time, class_name, schedule_ID FROM class_schedule JOIN class_info, users ON class_schedule.class_ID = class_info.ID AND class_info.user_ID = users.ID WHERE user_ID = :userId ORDER BY DoW, start_Time", userId = session["user_id"])

        return render_template("scheduling_setup.html", classes = classes, classSchedules = classSched)

@app.route("/addAssignment", methods=["GET", "POST"])
@login_required
def addAssignment():
    """ Adding assignments """

   # Information used on html side to display existing classes with respective scheduling
    classSched = db.execute("SELECT start_time, end_time, class_name, class_ID, default_time \
                            FROM class_schedule JOIN class_info ON class_schedule.class_ID = class_info.ID \
                            WHERE DoW = :dow AND user_ID = :userid ORDER BY start_Time", \
                            dow = datetime.datetime.today().strftime('%A'), userid = session["user_id"])

    if request.method == "POST":

        # Code for deleting assignments
        if request.form.get("assignment_id"):

            db.execute("DELETE FROM assignments WHERE assignment_ID = :assignmentID", assignmentID = request.form.get("assignment_id"))
            return redirect("/addAssignment")

        # Insert assignment information into assignment table
        db.execute("INSERT INTO assignments (class_ID, duration, assignment_priority, assignment_name, date) \
                    VALUES (:classID, :time, :priority, :name, :date)", \
                            classID = request.form.get("assignment_Class_ID"), \
                            time = request.form.get("assignment_time"), \
                            priority = request.form.get("priority"), \
                            name = request.form.get("assignment_name"), \
                            date = datetime.datetime.today())

        assignmentList = db.execute("SELECT assignment_name, duration, assignment_priority, assignment_ID \
                                FROM assignments  \
                                WHERE date = :date ORDER BY assignment_priority desc, assignment_name", \
                                date = datetime.datetime.today() )

        return render_template("add.html", classes = classSched, assignments = assignmentList)

    else:


        assignmentList = db.execute("SELECT assignment_name, duration, assignment_priority, assignment_ID \
                                FROM assignments  \
                                WHERE date = :date ORDER BY assignment_priority desc, assignment_name", \
                                date = datetime.datetime.today() )

        return render_template("add.html", classes = classSched, assignments = assignmentList)

@app.route("/todo", methods=["GET", "POST"])
@login_required
def todoList():
    # Generates an assignment list to be displayed in todo-list
    assignmentList = db.execute("SELECT channels.id, channels.name, assignment_name, assignment_ID, duration, assignment_priority, flag \
                                FROM assignments JOIN class_info ON assignments.class_id=class_info.ID JOIN channels ON class_info.class_name=channels.name \
                                WHERE date = :date", date = datetime.datetime.today())

    if request.method == "POST":

        # Get bedtime for user to pass in
        bedtime = db.execute("SELECT Bedtime FROM users WHERE id = :userID", userID =  session["user_id"])

        # Parse bedtime into hr : min
        struct_time = time.strptime(bedtime[0].get("Bedtime"), "%H:%M")

        db.execute("UPDATE assignments SET flag = 'True' WHERE assignment_ID = :id", id = request.form.get("assignment_ID"))

        return render_template("todo_list.html", assignments = assignmentList, bedtimeHour = struct_time.tm_hour, bedtimeMin = struct_time.tm_min)

    else:
        # Get bedtime for user to pass in
        bedtime = db.execute("SELECT Bedtime FROM users WHERE id = :userID", userID =  session["user_id"])

        # Parse bedtime into hr : min
        struct_time = time.strptime(bedtime[0].get("Bedtime"), "%H:%M")

        return render_template("todo_list.html", assignments = assignmentList, bedtimeHour = struct_time.tm_hour, bedtimeMin = struct_time.tm_min)

@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/index")