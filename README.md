Welcome to LexPlan, the premier assignment planner!

The purpose of this planner is for the student, inspired by the lack of organization and forgetfullness that could result each night of study.

To compile the web application, use flask.
To configure the program, use CS50 IDE.

LexPlan is a web application that is open for registration that requires additional user information including . Once you have registered,
you will be able to login into the system.

Once the user is logged in, he/she will be able to see a couple of options. First is the add class page. In order to do anything else with
the program, the user must first add a couple of classes along with the default time that an assignment for the class will take.

Next is the add class schedule page, where given the classes that the user has added, they will be able to add scheduling for such classes
each day of the week. The system keeps track of the current datetime, so in order to add assignments for each day, scheduling must be added for
the specific weekday.

Next is the add assignments page, which is also the default page. Here, the user will be able to add assignments and alter their duration time
for each class on the current weekday. Additionally, the program will request an input for priority of assignment, which will be used to generate
a to-do list.

Finally is the todo list page, where the list of assignments for each day will be displayed for that day as well as the option to mark the assignment
as completed. Additionally, the program will display the time that the user should be expected to start their assignments, given their inputed bedtime.
At the end of each day, the todo list is cleared for the next day.

Everything above is what I completed for my final project in CS50. For the current final project, I added a chat application, LexChat, to Lexplan.

All messages and channels are stored in the same LexPlan database, and the user's channels are pre-created for each class that a user has. Also, on the
to-do page, each assignment allows the user to "chat", which directs them to the specific channel that corresponds with an assignment.

And that's it! The purpose of the application is so that each day the user will be able to log in and input assignments for classes that he/she
will have (hopefully!) entered and scheduled beforehand. The purpose of the chat application is for any questions that a user might have for a certain
assignment that his or her peers that have the same class may be able to help with.


How to run batch file on machine:
Start > startflask.cmd


