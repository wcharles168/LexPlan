document.addEventListener('DOMContentLoaded', () => {

    // Adds a channel to the page

    function addChannelHTML(channel_id, channel_name){

        // Create new element for drop-down select list
        const button = document.createElement('option');
        button.setAttribute("value", channel_id);

        // Add channel name to button
        button.innerHTML = channel_name;

        // Add new element to channel list
        document.querySelector('#channels').append(button);

    }

    // Retrieves messages on channel select

    function retrieveMessage (channel_id, channel) {

        channel_list = document.querySelector('#channels');
        // Loops through all options in channel list
         for (i = 0; i < channel_list.options.length; i++) {
            //  If option matches channel, mark that option as selected
             if (channel_list[i].innerHTML == channel) {
                 channel_list.selectedIndex = i;
             }
         }

        // Initialize request
        const request = new XMLHttpRequest();
        request.open("POST", "/get_message");

        // Callback function that loads messages in html
        request.onload = () => {

            // Clears any messages in chat box
            document.querySelector('#chat-box').innerHTML = '';

            // Display channel name
            document.querySelector('#current_channel').innerHTML = channel;
            document.querySelector('#current_channel_id').setAttribute("value", channel_id);

            // Reveals delete channel button if channel is not the general channel
            if (document.querySelector('#current_channel').innerHTML != 'General') {
                document.querySelector('#current_channel_id').removeAttribute('hidden');
            }
            // If user is requesting General channel, hide delete button
            else if (document.querySelector('#current_channel').innerHTML == 'General') {
                document.querySelector('#current_channel_id').setAttribute('hidden', true);
            }

            // Retrieves messages and channel from response
            const data = JSON.parse(request.responseText);

            // Loop through messages and display along with user and timestamp
            for (i = 0; i < data.messages.length; i++){

                // Retrieves a single message
                message = data.messages[i];

                // Gets message attributes
                user = message["user_id"];
                username = message["username"];
                timestamp = message["timestamp"];
                message_text = message["message"];
                id = message["message_id"];

                addMessage(user, username, timestamp, message_text, id);
            }
        };

        const data = new FormData();
        data.append('channel', channel_id);

        request.send(data);

        return false;
    }

    // Adds message to message table

    function addMessage(user, username, timestamp, message_text, message_id) {
        // Initializes new row to store message
        const row = document.createElement('tr');
        const message_box = document.createElement('p');
        const message_col = document.createElement('td'); // First column
        const delete_col = document.createElement('td'); // Second column

        // Checks if message is associated with current user
        if (user == document.querySelector('#user_id').innerHTML) {
            message_box.setAttribute("class", "your-message");

            // Creates a hidden radio button to delete specific message when activated
            const delete_button = document.createElement('input');
            delete_button.setAttribute("class", "delete-select");
            delete_button.setAttribute("type", "radio");
            delete_button.setAttribute("value", message_id);
            delete_button.setAttribute("hidden", "true");

            // Append form to column
            delete_col.appendChild(delete_button);

        }
        else {
            message_box.setAttribute("class", "other-message");
        }

        // Formats message
        message_box.innerHTML = messageFormat(username, timestamp, message_text);

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

    window.onload = getChannels();

    // Grabs all existing channels and displays them
    function getChannels() {
        const request = new XMLHttpRequest();
        request.open('GET', '/get_channels');

        // Callback function when request returns
        request.onload = () => {
            const channels = JSON.parse(request.responseText);

            if (channels != null) {
                for(i = 0; i < channels.length; i++) {
                    addChannelHTML(channels[i]["id"], channels[i]["name"]);
                }
            }

            channel_id = document.querySelector('#requested_channel_id');
            channel_name = document.querySelector('#requested_channel');

            // Check for requested channel
            if (channel_id.innerHTML && channel_name.innerHTML) {
                retrieveMessage(channel_id.innerHTML, channel_name.innerHTML);

                // Clear hidden divs for new channels to be requested
                channel_id.innerHTML = '';
                channel_name.innerHTML = '';
            }
            else {
                // Checks for locally stored channel
                local_channel_id = localStorage.getItem('channel_id');
                local_channel = localStorage.getItem('channel');

                if (!local_channel) {
                    // Displays first channel
                    retrieveMessage(channels[0]["id"], channels[0]["name"]);
                }
                else {
                    // Loads channel from local storage
                    retrieveMessage(local_channel_id, local_channel);
                }
            }
        };

        request.send();
    }

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
                channel_id = document.querySelector('#current_channel_id').value;
                user = document.querySelector('#user_id').innerHTML;
                time = new Date();

                socket.emit ('message sent', {'message': message, 'channel_id': channel_id, 'user': user, 'time': time});

                // Clears input field and disables submit button after submission
                document.querySelector('#message').value = '';
                document.querySelector('#submit_message').disabled = true;

                return false;
            };
        });

        // When message is stored, add it to html
        socket.on('message received', data => {

            // // Only append message if user is on the channel
            if (document.querySelector('#current_channel_id').value == data.channel_id) {
                for (i = 0; i < data.id.length; i++) {
                    addMessage(data.user, data.username[i]["username"], data.time, data.message, data.id[i]["id"]);
                }
            }
        });

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
                if (response["status"] == false) {
                    for (i=0; i < response.channel.length; i++) {
                        addChannelHTML(response.channel[i]["id"], response.channel[i]["name"]);
                    }
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

        input =  document.querySelector('#channels');

        // Retrieves channel name from select list
        var channel_id = input.value;
        var channel = input.options[input.selectedIndex].innerHTML;

        retrieveMessage(channel_id, channel);

        // Remembers channel that is selected
        localStorage.setItem('channel_id', channel_id);
        localStorage.setItem('channel', channel);

    };

    // Deletes messages

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

            const request = new XMLHttpRequest();
            request.open("POST", "/delete_message");

            delete_list = document.querySelectorAll('.delete-select');

            // List of message ids to be deleted
            message_ids = [];

            for (i = 0; i < delete_list.length; i ++) {
                button = delete_list[i];
                if (button.checked == true) {
                    // Removes parent element of button (row)
                    button.parentElement.parentElement.remove();
                    // Add message id to list
                    message_ids.push(button.value);
                }
            }

            request.onload = () => {
                response = JSON.parse(request.responseText);

                if (response == true) {
                     // Restore original settings
                    document.querySelector('#delete-button').disabled = false;

                    document.querySelectorAll('.delete-select').forEach(function(button) {
                        button.setAttribute('hidden', 'true');
                    });

                    document.querySelector('.pop-up').setAttribute('hidden', 'true');
                }
            };
            // Add list of messages to request
            const data = new FormData();
            data.append("messages", JSON.stringify(message_ids));

            request.send(data);
            return false;
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

    // Deletes channel
    document.querySelector('#current_channel_id').onclick = () => {
        // Retrieves channel id
        var channel_id = document.querySelector('#current_channel_id').value;

        // Highlights channel
        document.querySelector('#current_channel').style.color = 'red';

        // Hide delete button and reveals confirm and cancel buttons
        document.querySelector('#current_channel_id').setAttribute('hidden', true);
        document.querySelector('#delete_channel').removeAttribute('hidden');
        document.querySelector('#cancel_channel').removeAttribute('hidden');

        // If user confirms deletion, delete from database and re-get channels
        document.querySelector('#delete_channel').onclick = () => {
            const request = new XMLHttpRequest();
            request.open("POST", "/delete_channel");

            request.onload = () => {
                response = JSON.parse(request.responseText);

                if (response == true) {
                    // Restore original settings
                    document.querySelector('#delete_channel').setAttribute('hidden', true);
                    document.querySelector('#cancel_channel').setAttribute('hidden', true);
                    document.querySelector('#current_channel_id').removeAttribute('hidden');
                    document.querySelector('#current_channel').innerHTML = '';
                    document.querySelector('#current_channel').style.color = 'black';

                    // Remove channel from local storage
                    localStorage.removeItem('channel_id');
                    localStorage.removeItem('channel');

                    // Remove all channel options in channel list
                    document.querySelector('#channels').options.length = 0;

                    // Get new set of channels
                    getChannels();
                }
            };
            const data = new FormData();
            data.append("channel_id", channel_id);

            request.send(data);
            return false;
        };
        // If user clicks cancel, also restore original settings
        document.querySelector('#cancel_channel').onclick = () => {

            document.querySelector('#delete_channel').setAttribute('hidden', true);
            document.querySelector('#cancel_channel').setAttribute('hidden', true);
            document.querySelector('#current_channel_id').removeAttribute('hidden');
            document.querySelector('#current_channel').style.color = 'black';
        };
    };
});


