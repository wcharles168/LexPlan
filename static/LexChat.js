document.addEventListener('DOMContentLoaded', () => {

    // Adds a channel to the page

    function addChannelHTML(channel){

        // Create new element for drop-down select list
        const button = document.createElement('option');
        button.setAttribute("value", channel);

        // Add channel name to button
        button.innerHTML = channel;

        // Add new element to channel list
        document.querySelector('#channels').append(button);

    }

    // Retrieves messages on channel select

    function retrieveMessage (channel) {

        // Initialize request
        const request = new XMLHttpRequest();
        request.open("POST", "/get_message");

        // Callback function that loads messages in html
        request.onload = () => {

            // Clears any messages in chat box
            document.querySelector('#chat-box').innerHTML = '';

            // Retrieves messages and channel from response
            const data = JSON.parse(request.responseText);

            // Loop through messages and display along with user and timestamp
            for (i = 0; i < data.messages.length; i++){
                // Retrieves a single message
                message = data.messages[i];

                // Gets message attributes
                user = message["user"];
                timestamp = message["date-time"];
                message_text = message["text"];
                id = message["id"];

                addMessage(user, timestamp, message_text, id);
            }

            // Display channel name
            document.querySelector('#current_channel').innerHTML = data.channel;
        };

        const data = new FormData();
        data.append('channel', channel);

        request.send(data);

        return false;
    }

    // Adds message to message table

    function addMessage(user, timestamp, message_text, id) {
        // Initializes new row to store message
        const row = document.createElement('tr');
        const message_box = document.createElement('p');
        const message_col = document.createElement('td'); // First column
        const delete_col = document.createElement('td'); // Second column

        // Checks if message is associated with current user
        if (user == document.querySelector('#current_name').innerHTML) {
            message_box.setAttribute("class", "your-message");

            // Creates a hidden radio button to delete specific message when activated
            const delete_button = document.createElement('input');
            delete_button.setAttribute("class", "delete-select");
            delete_button.setAttribute("type", "radio");
            delete_button.setAttribute("value", id);
            delete_button.setAttribute("hidden", "true");

            // Append form to column
            delete_col.appendChild(delete_button);

        }
        else {
            message_box.setAttribute("class", "other-message");
        }
        // Formats message
        message_box.innerHTML = messageFormat(user, timestamp, message_text);

        // Appends message to column
        message_col.appendChild(message_box);

        // Append two columns to the row
        row.innerHTML += message_col.outerHTML + delete_col.outerHTML;

        document.querySelector('#chat-box').append(row);
    }

    // Formats messages

    function messageFormat (user, timestamp, message) {
        // Re-formats jsonified text
        formattedTime = new Date(timestamp);

        hours = formattedTime.getHours();
        minutes = formattedTime.getMinutes();

        // Formats minute into guarantee two digit
        if (minutes < 10) {
            minutes = '0' + minutes;
        }

        // Check if user is current user, and if so returns different format
        if (user == document.querySelector('#current_name').innerHTML) {
            return ('You' + " (" + hours + ":" + minutes + ")" + ": " + message);
        }
        else
            return (user + " (" + hours + ":" + minutes + ")" + ": " + message);
    }

    // Loads name from local storage

    // If no name on local storage, set to default name
    if (!localStorage.getItem('name')) {

        localStorage.setItem('name', 'Anonymous');

    }

    // Set display name using value stored in local
    const name = localStorage.getItem('name');
    document.querySelector('#current_name').innerHTML = name;

    // Grabs all existing channels and displays them

    window.onload = () => {
        const request = new XMLHttpRequest();
        request.open('GET', '/get_channels');

        // Callback function when request returns
        request.onload = () => {
            const channels = JSON.parse(request.responseText);

            if (channels != null) {
                for(i = 0; i < channels.length; i++) {
                    addChannelHTML(channels[i]);
                }
            }

            // Checks for locally stored channel

            local_channel = localStorage.getItem('channel');

            if (!local_channel) {
                // Displays first channel (general)
                retrieveMessage(channels[0]);
            }
            else {
                // Loads channel from local storage
                retrieveMessage(local_channel);
                // Automatically sets channel as checked
                document.querySelector('#channels').value = local_channel;
            }
        };

        request.send();
    };

    // Sending and receiving messages

    // Connect to websocket
    var socket = io.connect(location.protocol + '//' + document.domain + ':' + location.port);

    // By default disables the submit button
    document.querySelector('#submit_message').disabled = true;

    // Only enables submit button when there is input
    document.querySelector('#message').onkeyup = () => {

        if (document.querySelector('#message').value.length > 0)

            document.querySelector('#submit_message').disabled = false;
        else

            document.querySelector('#submit_message').disabled = true;
    };

        // When connected, look for message submissions
        socket.on('connect', () => {
            document.querySelector('#new_message').onsubmit = () => {

                message = document.querySelector('#message').value;
                channel = document.querySelector('#current_channel').innerHTML;
                user = document.querySelector('#current_name').innerHTML;
                time = new Date();

                socket.emit ('message sent', {'message': message, 'channel': channel, 'user': user, 'time': time});

                // Clears input field and disables submit button after submission
                document.querySelector('#message').value = '';
                document.querySelector('#submit_message').disabled = true;

                return false;
            };
        });

        // When message is stored, add it to html
        socket.on('message received', data => {

            // Will not add message if amount of messages in channel is max
            if (data.message == 'full') {
                alert("Sorry, channel has exceeded maximum (100) amount of messages");
            }
            else {
                // Only append message if user is on the channel
                if (document.querySelector('#current_channel').innerHTML == data.channel){
                    addMessage(data.user, data.time, data.message, data.id);
                }
            }
        });

    // Changes name on user input

    // By default disables the submit button
    document.querySelector('#submit_name').disabled = true;

    // Only enables submit button when there is input
    document.querySelector('#name').onkeyup = () => {

        if (document.querySelector('#name').value.length > 0)

            document.querySelector('#submit_name').disabled = false;
        else

            document.querySelector('#submit_name').disabled = true;

        document.querySelector('#new_name').onsubmit = () => {

            // Remove any current HTML
            document.querySelector('#current_name').innerHTML = '';

            const name = document.querySelector('#name').value;

            // Add new element to HTML and local storage
            document.querySelector('#current_name').innerHTML = name;
            localStorage.setItem('name', name);

            // Clear input field
            document.querySelector('#name').value = '';

            // Disable button again after submit
            document.querySelector('#submit_name').disabled = true;

            return false;
        };
    };

    // Adds a channel to html and channel list based on user input

    // By default disables the submit button
    document.querySelector('#submit_channel').disabled = true;

    // Only enables submit button when there is input
    document.querySelector('#channel').onkeyup = () => {
        if (document.querySelector('#channel').value.length > 0)

            document.querySelector('#submit_channel').disabled = false;
        else

            document.querySelector('#submit_channel').disabled = true;

        document.querySelector('#new_channel').onsubmit = () => {

            channel = document.querySelector('#channel').value;

             // Initialize a new request
            const request = new XMLHttpRequest();
            request.open("POST", "/add_channel");

            // Callback function when request loads that adds channel to html
            request.onload = () => {

                response = JSON.parse(request.responseText);

                // Only adds channel if channel is unique
                if (response == false) {
                     addChannelHTML(channel);
                }
                else {
                    alert("Please enter a unique channel name");
                }
                // Clear input field
                document.querySelector('#channel').value = '';

                // Disable button again after submit
                document.querySelector('#submit_channel').disabled = true;
            };
            // Send channel data to server
            const data = new FormData();
            data.append('channel', channel);
            request.send(data);

            return false;
        };
    };

    // Listens for channel selection

    document.querySelector('#channels').onchange = () => {
        // Retrieves channel name from select list
        var channel = document.querySelector('#channels').value;

        retrieveMessage(channel);

        // Remembers channel that is selected
        localStorage.setItem('channel', channel);
    };

    // Deletes message (client side only)

    document.querySelector('#delete-button').onclick = () => {

        // Show radio buttons and pop up
        document.querySelectorAll('.delete-select').forEach(function(button) {
            button.removeAttribute('hidden');
        });

        document.querySelector('.pop-up').removeAttribute('hidden');

        document.querySelector('#delete-button').disabled = true;

        // Toggle radio buttons
        document.querySelectorAll('delete-select').forEach(function(button) {
            button.click = function() {

                if (button.checked == true) {
                    button.checked = false;
                }
                else {
                    button.checked = true;
                }
            };
        });

        document.querySelector('#delete-confirm').onclick = () => {

            delete_list = document.querySelectorAll('.delete-select');

            for (i = 0; i < delete_list.length; i ++) {
                button = delete_list[i];
                if (button.checked == true) {
                    // Removes parent element of button (row)
                    button.parentElement.parentElement.remove();
                }
            }

            // Restore original settings
            document.querySelector('#delete-button').disabled = false;

            document.querySelectorAll('.delete-select').forEach(function(button) {
                button.setAttribute('hidden', 'true');
            });

            document.querySelector('.pop-up').setAttribute('hidden', 'true');
        };

        // If user clicks cancel, also restore original settings
        document.querySelector('#cancel').onclick = () => {

            // Restore original settings
            document.querySelector('#delete-button').disabled = false;

            document.querySelectorAll('.delete-select').forEach(function(button) {
                button.setAttribute('hidden', 'true');
            });

            document.querySelector('.pop-up').setAttribute('hidden', 'true');
        };
    };
});

