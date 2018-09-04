To create LexPlan, I started off with the general framework from Pset7. Thus, the register and login pages are really the same.

There are four tables to the LexPlan database. First is user information, which corresponds to the register and login pages.
Second is for class schedule information, which stores information corresponding to the class scheduling page. Third is the class
infromation, which corresponds to class setup page. The reason why I kept these two pages, and thus tables separate was because it was
more efficient to consolidate the information in those tables because it makes it more clear which information on which class goes where.

Behind the hood, it is quite simple. I used javascript mainly in the todo list as well as the adding assingment list for a couple reasons.
First, I wanted to improve the user experience by avoiding reloading the page every time a button was clicked on. For this reason, when the
user adds an assignment, the hidden box with the assignment information, using javascript, will be displayed. Furthermore, and the most important,
is the display of time on the todo list, which is generated second by second (imagine if this information would have to be sent back to server-side).

Organization wise, I wanted to keep the user experience as simple as possible. The setup process should be a one and done process, and as a result
I set the default page to the add assignment page because that will be the page that the user uses the most. The entire point of the application is
to make scheduling easier and quick.