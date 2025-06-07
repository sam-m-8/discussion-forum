import json
import uuid
from socket import *

ACK_TIMEOUT = 2
BUFFER_SIZE = 65535
HOST = "localhost"

def format_request(command, username, body):
    return {
        "command": command,
        "username": username,
        "request_id": str(uuid.uuid4()),
        "body": body,
    }


def format_response(is_success, requested_command, request_id, message, body):
    return {
        "success": is_success,
        "requested_command": requested_command,
        "request_id": request_id,
        "message": message,
        "body": body
    }

def send_segment(message, socket, dest_address):
    json_message = json.dumps(message)
    socket.sendto(json_message.encode("utf-8"), dest_address)


def receive_segment(socket):
    data, sender_address = socket.recvfrom(BUFFER_SIZE)
    message = json.loads(data.decode("utf-8"))
    return message, sender_address

# Sends a segment and awaits for a response, if none is received within a timeout
# the segment will be sent again. This process is repeated until a response segment
# is received.
def send_segment_await_response(request, client_socket, server_address):
    client_socket.settimeout(ACK_TIMEOUT)

    while True:
        send_segment(request, client_socket, server_address)
        try:
            response, server_address = receive_segment(client_socket)
            if response.get("request_id") == request["request_id"]:
                return response, server_address
        except timeout:
            continue


def await_response_resend_segment(request, client_socket, server_address):
    client_socket.settimeout(ACK_TIMEOUT)

    while True:
        try:
            response, server_address = receive_segment(client_socket)
            if response.get("request_id") == request["request_id"]:
                return response, server_address
        except timeout:
            send_segment(request, client_socket, server_address)
            continue


# Prompts user for username. Then username is sent to server. Then prompts user
# for password. If the password is invalid it will recurse to repeat the login
# process, otherwise the user will be logged in and can begin inputting commands
def authenticate_user(client_socket, server_port):
    username = input("Enter username: ")
    request = format_request("USR", username, None)
    response, server_address = send_segment_await_response(request, client_socket, (HOST, server_port))

    if response["success"] == True:
        password = input(response["message"])

        request = format_request("PSW", username, password)
        response, server_address = send_segment_await_response(request, client_socket, server_address)

        if response["success"] == False:
            print(response["message"])
            return authenticate_user(client_socket, server_port)
        else:
            print("Welcome to the forum")
            return username, server_address

    else:
        print(response["message"])
        return authenticate_user(client_socket, server_port)


def get_next_command():
    command_input = input("Enter one of the following commands: CRT, MSG, DLT, EDT, LST, RDT, UPD, DWN, RMV, XIT: ")
    args = []
    bad_input = False
    body = {}

    if command_input.strip() == "":
        print("Invalid command")
        return False, "", {}

    command = command_input.strip().split(maxsplit=1)[0]

    match command:
        case "CRT":
            bad_input, args = flag_incorrect_arg_num(command_input, 2, False)
            if not bad_input:
                body = {"thread_title": args[1]}
        case "MSG":
            bad_input, args = flag_incorrect_arg_num(command_input, 3, True)
            if not bad_input:
                body = {"thread_title": args[1], "message": args[2]}
        case "DLT":
            bad_input, args = flag_incorrect_arg_num(command_input, 3, False)
            if not bad_input:
                if not is_int(args[2]):
                    bad_input = True
                else:
                    body = {"thread_title": args[1], "message_number": int(args[2])}
        case "EDT":
            bad_input, args = flag_incorrect_arg_num(command_input, 4, True)
            if not bad_input:
                if not is_int(args[2]):
                    bad_input = True
                else:
                    body = {"thread_title": args[1], "message_number": int(args[2]), "message": args[3]}
        case "LST":
            bad_input, args = flag_incorrect_arg_num(command_input, 1, False)
        case "RDT":
            bad_input, args = flag_incorrect_arg_num(command_input, 2, False)
            if not bad_input:
                body = {"thread_title": args[1]}
        case "UPD":
            bad_input, args = flag_incorrect_arg_num(command_input, 3, False)
            if not bad_input:
                body = {"thread_title": args[1], "filename": args[2]}
        case "DWN":
            bad_input, args = flag_incorrect_arg_num(command_input, 3, False)
            if not bad_input:
                body = {"thread_title": args[1], "filename": args[2]}
        case "RMV":
            bad_input, args = flag_incorrect_arg_num(command_input, 2, False)
            if not bad_input:
                body = {"thread_title": args[1]}
        case "XIT":
            bad_input, args = flag_incorrect_arg_num(command_input, 1, False)
        case _:
            print("Invalid command")
            return False, command, body

    if bad_input:
        print(f"Incorrect syntax for {command}")
        return False, command, body

    return True, command, body


def flag_incorrect_arg_num(command_input, target_num, contains_message):
    maxsplit = target_num - 1

    if contains_message:
        args = command_input.strip().split(maxsplit=maxsplit)
    else:
        args = command_input.strip().split()

    if len(args) != target_num:
        return True, []
    return False, args

def is_int(message_number):
    try:
        int(message_number)
        return True
    except ValueError:
        return False

def valid_message_author(target_thread, message_num, user):
    target_message = target_thread.get_message(message_num)
    if target_message.author.username == user.username:
        return True
    return False