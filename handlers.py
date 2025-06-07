from helper import *
from socket import *

# Checks the credentials file (credentials.txt) for a match of the given username.
# If the username exists, sends a confirmation message to the client.
# If the username does not exist, the user is assumed to be creating a new account,
# and the server sends a message to the client.
def handle_username_login(request, client_address, server_socket, _, user, client_key, state):
    command = request["command"]
    request_id = request.get("request_id")

    print("Client authenticating")
    is_success = False
    if user == None:
        is_success = True
        msg = "New user, enter password: "
    elif user.is_active:
        msg = f"{user.username} has already logged in"
    else:
        is_success = True
        msg = "Enter password: "
    response = format_response(is_success, command, request_id, msg, {})

    state.mid_auth = True
    state.auth_client = client_address
    send_segment(response, server_socket, client_address)
    state.processed_requests[client_key] = response


# Checks for a match with the stored password for this user. Sends a confirmation
# message if the password matches or an error message in the event of a mismatch.
# In case of a mismatch, the client prompts the user to enter a username and
# the login process is repeated. If the user is creating a new account, a new
# username and password entry is added to the credentials file and a confirmation
# is sent to the client. After successful authentication, the client is assumed to be logged in.
def handle_password_login(request, client_address, server_socket, _, user, client_key, state):
    command = request["command"]
    username = request["username"]
    body = request["body"]
    request_id = request.get("request_id")

    if user != None and body != user.password:
        msg = "Incorrect Password"
        print(msg)
        response = format_response(False, command, request_id, msg, {})
        send_segment(response, server_socket, client_address)
        state.processed_requests[client_key] = response
    else:
        if user == None:
            state.forum_manager.add_user(username, request["body"])
            print("New User")
        else:
            user.is_active = True

        state.mid_auth = False
        state.auth_client = client_address
        print(f"{username} successfully logged in")
        response = format_response(True, command, request_id, "Successfully logged in", {})
        send_segment(response, server_socket, client_address)
        state.processed_requests[client_key] = response


# First checks if a thread with the provided title exists. If so, an error message is sent to the client.
# If the thread does not exist, a new file with the provided title is created and a
# confirmation message is sent to the client.
def handle_create_thread(request, client_address, server_socket, _, user, client_key, state):
    command = request["command"]
    request_id = request.get("request_id")
    thread_title = request["body"].get("thread_title")

    is_success = False
    if state.forum_manager.thread_exists(thread_title):
        msg = f"Thread {thread_title} exists"
    else:
        is_success = True
        state.forum_manager.create_thread(thread_title, user)
        msg = f"Thread {thread_title} created"

    print(msg)
    response = format_response(is_success, command, request_id, msg, {})
    send_segment(response, server_socket, client_address)
    state.processed_requests[client_key] = response


# First checks if a thread with this title exists. If so, the message and the username are
# appended at the end of the thread file, along with the message number, and a confirmation
# message is sent to the client. If the thread with this title does not exist,
# an error message is sent to the client.
def handle_post_message(request, client_address, server_socket, _, user, client_key, state):
    command = request["command"]
    request_id = request.get("request_id")
    thread_title = request["body"].get("thread_title")
    thread_message = request["body"].get("message")

    is_success = False
    if not state.forum_manager.thread_exists(thread_title):
        msg = f"Thread {thread_title} does not exist"
        print("Incorrect thread specified")
    else:
        is_success = True
        target_thread = state.forum_manager.get_thread(thread_title)
        target_thread.post_message(thread_message, user)
        msg = f"Message posted to {thread_title} thread"

    response = format_response(is_success, command, request_id, msg, {})
    send_segment(response, server_socket, client_address)
    state.processed_requests[client_key] = response


# A message can only be deleted by the user who originally posted it.
# Verifies if a thread with the given title exists, if the corresponding message number is valid,
# and if this user initially posted the message. If any of these checks fail, an error message is sent to the client.
# If all checks are successful, the server deletes the message, which involves
# removing the line containing it in the corresponding thread file.
# A confirmation is then sent to the client.
def handle_delete_message(request, client_address, server_socket, _, user, client_key, state):
    command = request["command"]
    request_id = request.get("request_id")
    thread_title = request["body"].get("thread_title")
    message_num = request["body"].get("message_number")

    is_success = False
    if not state.forum_manager.thread_exists(thread_title):
        msg = f"Thread {thread_title} does not exist"
    else:
        target_thread = state.forum_manager.get_thread(thread_title)
        if not target_thread.message_exists(message_num):
            msg = f"Message number {message_num} does not exist in thread {thread_title}"
        elif not valid_message_author(target_thread, message_num, user):
            msg = f"The message belongs to another user and cannot be edited"
        else:
            is_success = True
            target_thread.delete_message(message_num)
            msg = f"Message has been deleted from thread {thread_title}"

    if not is_success:
        print("Message cannot be deleted")
    response = format_response(is_success, command, request_id, msg, {})
    send_segment(response, server_socket, client_address)
    state.processed_requests[client_key] = response


# A message can only be edited by the user who originally posted it.
# Checks if a thread with this title exists, if the corresponding message number is
# valid, and if the username has posted this message. If any of these checks are unsuccessful, an
# error message is sent to the client. If all checks pass, the original message
# is replaced in the corresponding thread file with the new message, and
# confirmation is sent to the client.
def handle_edit_message(request, client_address, server_socket, _, user, client_key, state):
    command = request["command"]
    request_id = request.get("request_id")
    thread_title = request["body"].get("thread_title")
    message_num = request["body"].get("message_number")

    is_success = False
    if not state.forum_manager.thread_exists(thread_title):
        msg = f"Thread {thread_title} does not exist"
    else:
        target_thread = state.forum_manager.get_thread(thread_title)
        if not target_thread.message_exists(message_num):
            msg = f"Message number {message_num} does not exist in thread {thread_title}"
        elif not valid_message_author(target_thread, message_num, user):
            msg = f"The message belongs to another user and cannot be edited"
        else:
            is_success = True
            target_thread.edit_message(message_num, request["body"].get("message"))
            msg = f"Message from thread {thread_title} has been edited"

    if not is_success:
        print("Message cannot be edited")
    response = format_response(is_success, command, request_id, msg, {})
    send_segment(response, server_socket, client_address)
    state.processed_requests[client_key] = response


# Fetches all the thread titles and sends them to the client. If there are no
# active threads, a message indicating this is sent instead.
def handle_list_threads(request, client_address, server_socket, _, _2, client_key, state):
    command = request["command"]
    request_id = request.get("request_id")
    thread_list = state.forum_manager.get_thread_list()
    response = format_response(True, command, request_id, None, thread_list)
    send_segment(response, server_socket, client_address)
    state.processed_requests[client_key] = response


# Checks if a thread with this title exists. If so, the server sends the contents
# of the file corresponding to this thread to the client. If the thread with this title does
# not exist, an error message is sent to the client.
def handle_read_thread(request, client_address, server_socket, _, _2, client_key, state):
    command = request["command"]
    request_id = request.get("request_id")
    thread_title = request["body"].get("thread_title")
    is_success = False
    if not state.forum_manager.thread_exists(thread_title):
        msg = f"Thread {thread_title} does not exist"
    else:
        is_success = True
        target_thread = state.forum_manager.get_thread(thread_title)
        thread_posts = target_thread.read_thread()
        response = format_response(is_success, command, request_id, None, thread_posts)

    if not is_success:
        print("Incorrect thread specified")
        response = format_response(is_success, command, request_id, msg, {})

    send_segment(response, server_socket, client_address)
    state.processed_requests[client_key] = response


# Verifies if a thread with this title exists and, if so, whether the user who
# created the thread matches the provided username. If either check fails, an error
# message is sent to the client. Otherwise, the thread will be deleted along with
# the file that stores information about it, any files uploaded to it, and any state
# maintained about the thread on the server. A confirmation message is sent to the client.
def handle_remove_thread(request, client_address, server_socket, _, user, client_key, state):
    command = request["command"]
    request_id = request.get("request_id")
    thread_title = request["body"].get("thread_title")

    is_success = False
    if not state.forum_manager.thread_exists(thread_title):
        msg = f"Thread {thread_title} does not exist"
    else:
        target_thread = state.forum_manager.get_thread(thread_title)
        if user.username != target_thread.author.username:
            msg = f"Thread {thread_title} was created by another user and cannot be removed"
        else:
            is_success = True
            state.forum_manager.delete_thread(thread_title)
            msg = f"Thread {thread_title} has been removed"

    if not is_success:
        print(f"Thread {thread_title} cannot be removed")
    response = format_response(is_success, command, request_id, msg, {})
    send_segment(response, server_socket, client_address)
    state.processed_requests[client_key] = response


# Checks if a thread with this title exists. If it does not, an appropriate error
# message is sent to the client. Also checks if a file with the provided name exists for this thread already.
# If it does, an error message is conveyed to the client. If the thread exists
# and the file has not already been uploaded to the thread, then a confirmation message is sent to the client.
# Following this, the client transfers the file's contents to the server over a TCP connection,
# which is closed immediately after the file transfer is completed. The file is
# stored in the server's current working directory. A record of the file is also noted on the thread.
# Lastly, a final confirmation message is sent to the client.
def handle_upload_file(request, client_address, server_socket, server_port, user, client_key, state):
    command = request["command"]
    request_id = request.get("request_id")
    thread_title = request["body"].get("thread_title")
    filename = request["body"].get("filename")
    is_success = False
    if not state.forum_manager.thread_exists(thread_title):
        msg = f"Thread {thread_title} does not exist"
    else:
        target_thread = state.forum_manager.get_thread(thread_title)
        if target_thread.file_exists(filename):
            msg = f"File {filename} already exists in thread {thread_title}"
        else:
            is_success = True
            msg = "File upload request accepted, awaiting data transfer"

    if not is_success:
        print(f"File {filename} cannot be uploaded")
        response = format_response(is_success, command, request_id, msg, {})
        send_segment(response, server_socket, client_address)
        state.processed_requests[client_key] = response
    else:
        tcp_server_socket = socket(AF_INET, SOCK_STREAM)
        tcp_server_socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        tcp_server_socket.bind(('localhost', server_port))
        tcp_server_socket.listen(1)

        response = format_response(is_success, command, request_id, msg, {"filename": filename})
        send_segment(response, server_socket, client_address)

        tcp_server_socket.settimeout(2.0)

        try:
            connection_socket, _ = tcp_server_socket.accept()
        except:
            tcp_server_socket.close()
            return

        file_path = f"{thread_title}-{filename}"

        with open(file_path, "wb") as upload_file:
            while True:
                data = connection_socket.recv(4096)
                if not data:
                    break
                upload_file.write(data)

        connection_socket.close()
        tcp_server_socket.close()

        target_thread.post_file(user, filename)
        print(f"{user.username} uploaded file {filename} to thread {thread_title}")

        msg = f"{filename} uploaded to {thread_title} thread"
        response = format_response(True, command, request_id, msg, {})
        send_segment(response, server_socket, client_address)
        state.processed_requests[client_key] = response


# Checks if a thread with this title exists and, if so, whether a file with this
# name was previously uploaded to the thread. If either check does not match, an error
# message is sent to the client. If a match is found, the server transfers the file's
# contents to the client over a TCP connections. Once the file transfer is complete, a confirmation message
# is sent to the client.
def handle_download_file(request, client_address, server_socket, server_port, user, client_key, state):
    command = request["command"]
    request_id = request.get("request_id")
    thread_title = request["body"].get("thread_title")
    filename = request["body"].get("filename")
    is_success = False
    if not state.forum_manager.thread_exists(thread_title):
        msg = f"Thread {thread_title} does not exist"
    else:
        target_thread = state.forum_manager.get_thread(thread_title)
        if not target_thread.file_exists(filename):
            msg = f"File {filename} does not exist in thread {thread_title}"
        else:
            is_success = True
            msg = "File download request accepted, awaiting data transfer"

    if not is_success:
        print(f"File {filename} cannot be downloaded")
        response = format_response(is_success, command, request_id, msg, {})
        send_segment(response, server_socket, client_address)
        state.processed_requests[client_key] = response
    else:
        tcp_server_socket = socket(AF_INET, SOCK_STREAM)
        tcp_server_socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        tcp_server_socket.bind(('localhost', server_port))
        tcp_server_socket.listen(1)

        response = format_response(is_success, command, request_id, msg, {"filename": filename})
        send_segment(response, server_socket, client_address)

        tcp_server_socket.settimeout(2.0)

        try:
            connection_socket, _ = tcp_server_socket.accept()
        except:
            tcp_server_socket.close()
            return

        file_path = f"{thread_title}-{filename}"

        with open(file_path, "rb") as dwn_file:
            while True:
                data = dwn_file.read(4096)
                if not data:
                    break
                connection_socket.sendall(data)

        connection_socket.close()
        tcp_server_socket.close()

        print(f"{user.username} downloaded file {filename} from thread {thread_title}")
        msg = f"{filename} successfully downloaded"
        response = format_response(True, command, request_id, msg, {})
        send_segment(response, server_socket, client_address)
        state.processed_requests[client_key] = response


# Logs out user and updates state information about currently logged-in users. Sends
# a confirmation message to the client.
def handle_exit(request, client_address, server_socket, _, user, client_key, state):
    command = request["command"]
    request_id = request.get("request_id")
    msg = "Goodbye"
    state.forum_manager.logout_user(user)
    response = format_response(True, command, request_id, msg, {})
    send_segment(response, server_socket, client_address)
    state.processed_requests[client_key] = response
