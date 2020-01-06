// Navigate to chat application and specific channel
function goToChannel(button) {
    // Gets channel id
    channel_id = button.value;

    // Redirects to chat application
    window.location.href = "http://ide50-llei168.cs50.io:8080/chat";

    // Set channel to channel that user specified
    document.querySelector('#channels').setAttribute('value', channel_id);
}

function show_Error_Message(message) {
    // Reveal hidden div
    document.querySelector('.error-message').removeAttribute('hidden');

    // Set error message
    document.querySelector('.error-message').innerHTML = message;

}

// Checks if username already exists
function checkUsername() {

    // Initialize request
    const request = new XMLHttpRequest();
    request.open("POST", "/register_check");

    // var csrf_token = document.querySelector('#csrf_token').value;

    // request.setRequestHeader("X-CSRFToken", csrf_token);

    request.setRequestHeader("X-Requested-With", XMLHttpRequest);

    request.onload = () => {
        response = JSON.parse(request.responseText);

        // If username matches, throw error
        if (response["status"] == false) {
            show_Error_Message("Username '"  + response["user"] + "' taken");
        }
        // Else, submit form
        else if (response["status"] == true) {
            document.querySelector('#register').submit();
        }
    };

    const data = new FormData();
    data.append("username", document.querySelector('#username').value);

    request.send(data);
}

// Check if class already exists
function checkClass() {

    // Initialize request
    const request = new XMLHttpRequest();
    request.open("POST", "/class_check");

    request.onload =() => {
        response = JSON.parse(request.responseText);

        // If class matches, throw error
        if (response["status"] == false) {
            show_Error_Message("Class '"  + response["class"] + "' already created");
        }
        // Else, submit form
        else if (response["status"] == true) {
            document.querySelector('#create_class').submit();
        }
    };
    const data = new FormData();
    data.append("class_name", document.querySelector('#class_name'));

    request.send(data);

}

// Form validation
function validateForm(form) {

    // Validates registration and login forms
    if (form == (document.querySelector('#register_form') || document.querySelector('#login_form'))) {

        if (!document.querySelector('#username').value) {
            show_Error_Message('Must provide a username');
            return false;
        }
        else if (!document.querySelector('#password').value) {
            show_Error_Message('Must provide a password');
            return false;
        }

        if (form == document.querySelector('#register_form')) {

            if (!document.querySelector('#confirmation').value) {
                show_Error_Message('Must confirm password');
                return false;
            }
            else if (document.querySelector('#password').value.length < 8) {
                show_Error_Message('Password length must be greater than 8');
                return false;
            }
            else if (document.querySelector('#password').value != document.querySelector('#confirmation').value) {
                show_Error_Message('Passwords do not match');
                return false;
            }
            else if (!document.querySelector('#bedtime').value) {
                show_Error_Message('Must provide bedtime');
                return false;
            }

            checkUsername();
        }
    }

    // Validates class input form
    else if (form == (document.querySelector('#class_form'))) {

        if (!document.querySelector('#class_name').value) {
            show_Error_Message('Please specify a class');
            return false;
        }

        else if (!document.querySelector('#default_time').value) {
            show_Error_Message('Please enter a default assignment time');
            return false;
        }

        else if (!validateInt(document.querySelector('#default_time'))) {
            return false;
        }

        checkClass();
    }
}

// Return true if value of field is an integer
function validateInt(inputField)
{
    let isValid = /^[1-9][0-9]*$/.test(inputField.value);
    if (isValid)
    {
        inputField.style.color = 'black';
    }
    else
    {
        inputField.style.color = 'red';
        show_Error_Message('Please enter valid time');
    }

    return isValid;
}

// When default time field is empty, revert to black text
function blackText(input) {
    if (!input.value) {
        input.style.color = 'black';
    }
}

// Return true if value of field is Hh:Mm
function validateHhMm(inputFields)
{
    var allCorrect = true;

    for(i = 0; i < inputFields.length; i++)
    {
        // regular expression to determine validity of input
        var isValid = /^([0-1]?[0-9]|2[0-4]):([0-5][0-9])?$/.test(inputFields[i].value);
        if (!isValid)
        {
            inputFields[i].style.color = 'red';
            allCorrect = false;
        }
        else
        {
            inputFields[i].style.color = 'black';
        }
    }

    return allCorrect;
}

// Checks if time range overlaps with other time ranges
function checkOverlap(start, end, current_class, dow) {

    // alert(start, end, current_class);

    const request = new XMLHttpRequest();
    request.open("POST", "/check_overlap");

    request.onload = () => {
        response = JSON.parse(request.responseText);

        if (response["status"] == false) {
            alert("Alert! Classes " + current_class + " and " + response["overlap"] + " overlap in time ranges.");
        }
    };
    const data = new FormData();
    data.append("start_time", start);
    data.append("end_time", end);
    data.append("DoW", dow);

    request.send(data);
}
// Used to hide a field
function hideElement(elementID)
{
    document.getElementById(elementID).style.display = 'none';

}

function getAssignment(className, classID, defaultTime)
{
    //display (or redisplays) block used for adding assignments
    document.getElementById("assignmentForm").style.display = 'block';

    var assignmentName = document.getElementsByName("assignment_name");
    var assignmentTime = document.getElementsByName("assignment_time");
    var assignmentClassID = document.getElementsByName("assignment_Class_ID");

    assignmentName[0].value = className;
    assignmentTime[0].value = defaultTime;
    assignmentClassID[0].value = classID;

}
// Returns remaining time for to-do list
function getRemainingTime(){

	var hour = document.getElementById("bedtimeHour");
	var min = document.getElementById("bedtimeMin");
    var durationList = document.getElementsByName("duration");

	timeNeeded=0;

	for (i=0; i<durationList.length; i++){
		timeNeeded+=parseInt(durationList[i].innerText);
	}

	now=new Date();
	bedTime=new Date(now.getFullYear(), now.getMonth(), now.getDate(), hour.defaultValue, min.defaultValue, 0);
	var diff = bedTime-now;

	//Dividing the result by 1000 gives you the number of seconds. Dividing that by 60 gives you the number of minutes. To round to whole minutes, use Math.floor or Math.ceil:
	return Math.floor((diff/1000)) - timeNeeded*60;
}

function writeRemainingTime(){
	time = getRemainingTime();
    var thecolor;
    var hours, mins, seconds;
    var isLate = false;
    var durationList = document.getElementsByName("duration");

    if(durationList.length == 0)
    {
        element=document.getElementById("timeRemaining");
    	element.style="color:green";
    	element.innerHTML = "Congratulations! You are done for today.";
    	return;
    }

    if (time >= 0)
    {
        thecolor='green';
        hours = Math.floor(time / 3600);
        time %= 3600;
        mins = Math.floor(time / 60);
        seconds = time % 60;
    }
    if (time < 0)
    {
        isLate = true;

        time = -time;
        thecolor='red';
        hours = Math.ceil(time / 3600);
        time %= 3600;
        mins = Math.ceil(time / 60);
        seconds = time % 60;
    }

	element=document.getElementById("timeRemaining");
	element.style="color:"+thecolor;

	if(isLate)
	{
	    element.innerHTML = "Should have started " + hours + ":" + mins + ":" + seconds + " ago!";
	}
	else
	{
	    element.innerHTML = "Must Start in " + hours + ":" + mins + ":" + seconds;
	}

}

// Adds an additional form for time