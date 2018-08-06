import os
from cs50 import SQL

import datetime
import calendar
import time
from flask import Flask, flash, redirect, render_template, request, session, jsonify
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

# CHAT APPLICATION #

# Uniquely identifies each message
message_id = 0

# list of all channels
channel_list = {'General': []}

@app.route("/chat", methods=['GET'])
@login_required
def chat():
    # Get username to display
    username = db.execute("SELECT username FROM users WHERE id = :userid", userid = session["user_id"])

    return render_template("chat.html", channels=channel_list, username=username)

@app.route("/get_channels", methods=["GET"])
def get_channel():
    '''Gets channels when window loads'''

    # Returns a list of keys ie. channels
    return jsonify (list(channel_list))

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

    if channelMatch == False:
        db.execute("INSERT INTO channels (name) VALUES (:channel_name)", channel_name = channel_name)

    return jsonify(channelMatch)

@app.route("/get_message", methods=["POST"])
def getMessage():
    '''Retrieves messages'''

    # Gets channel name
    channel = request.form.get("channel")

    # Retrieves messages associated with channel
    messages = channel_list.get(channel)

    return jsonify({ "messages": messages, "channel": channel})


@socketio.on("message sent")
def message(data):

    message_text = data.get("message")
    channel = data.get("channel")
    user = data.get("user")
    time = data.get("time")

    # Check for amount of messages in channel is maxed out
    if (len(channel_list[channel]) > 99):
        emit("message received", {"message": 'full'}, broadcast=True)

    # Create a new message object
    message = {'text': message_text, 'user': user, 'date-time': time, 'id': message_id}

    # Inserts message to corresponding channel
    channel_list[channel].append(message)

    emit("message received", {"message": message_text, "channel": channel, "user": user, "time": time, "id": message_id}, broadcast=True)

    increment()

def increment():
    global message_id
    message_id += 1

#   #   #   #   #   #   #

# PLANNER APPLICATION #

@app.route("/")
@login_required
def index():

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
        return redirect("/")

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

        return redirect("/")

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

        # Information used on html side to display existing classes with respective scheduling
        classSched = db.execute("SELECT start_time, end_time, class_name, class_ID, default_time \
                                FROM class_schedule JOIN class_info ON class_schedule.class_ID = class_info.ID \
                                WHERE DoW = :dow ORDER BY start_Time AND user_ID = :id", \
                                dow = calendar.day_name[datetime.datetime.today().weekday()], id = session["user_id"])

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

        classSched = db.execute("SELECT start_time, end_time, class_name, class_ID, default_time \
                                FROM class_schedule JOIN class_info ON class_schedule.class_ID = class_info.ID \
                                WHERE DoW = :dow ORDER BY start_Time AND user_ID = :id", \
                                dow = calendar.day_name[datetime.datetime.today().weekday()], id = session["user_id"])

        return render_template("add.html", classes = classSched, assignments = assignmentList)

@app.route("/todo", methods=["GET", "POST"])
@login_required
def todoList():
    if request.method == "POST":

        # Get bedtime for user to pass in
        bedtime = db.execute("SELECT Bedtime FROM users WHERE id = :userID", userID =  session["user_id"])

        # Parse bedtime into hr : min
        struct_time = time.strptime(bedtime[0].get("Bedtime"), "%H:%M")

        db.execute("UPDATE assignments SET flag = 'True' WHERE assignment_ID = :id", id = request.form.get("assignment_ID"))

        # Generates an assignment list to be displayed in todo-list
        assignmentList = db.execute("SELECT assignment_name, assignment_ID, duration, assignment_priority, flag \
                                    FROM assignments WHERE date = :date", \
                                    date = datetime.datetime.today())

        return render_template("todo_list.html", assignments = assignmentList, bedtimeHour = struct_time.tm_hour, bedtimeMin = struct_time.tm_min)

    else:
        # Get bedtime for user to pass in
        bedtime = db.execute("SELECT Bedtime FROM users WHERE id = :userID", userID =  session["user_id"])

        # Parse bedtime into hr : min
        struct_time = time.strptime(bedtime[0].get("Bedtime"), "%H:%M")


        assignmentList = db.execute("SELECT assignment_name, assignment_ID, duration, assignment_priority, flag \
                                    FROM assignments WHERE date = :date", \
                                    date = datetime.datetime.today())

        return render_template("todo_list.html", assignments = assignmentList, bedtimeHour = struct_time.tm_hour, bedtimeMin = struct_time.tm_min)

@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")