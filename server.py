from socket import *
import sys
from helper import *
import threading
import queue
import handlers
from server_state import ServerState

request_queue = queue.Queue()
state = ServerState()

def main():
    if len(sys.argv) != 2:
        print("Usage: python3 server.py server_port")
        exit(0)

    state.forum_manager.load_credentials()

    server_port = int(sys.argv[1])
    # Initialise UDP socket
    server_socket = socket(AF_INET, SOCK_DGRAM)
    server_socket.bind(('localhost', server_port))
    print("Server ready, waiting for clients")

    # Initialise worker thread that processes the requests
    threading.Thread(target=handle_requests, args=(server_socket, server_port), daemon=True).start()

    # Listener loop, always listening for new requests and pushing them to queue
    while True:
        request, client_address = receive_segment(server_socket)
        request_queue.put((request, client_address))

def handle_requests(server_socket, server_port):
    skipped_requests = []

    while True:
        request, client_address = request_queue.get()

        if state.mid_auth and client_address != state.auth_client:
            skipped_requests.append((request, client_address))
            continue

        process_request(request, client_address, server_socket, server_port)

        if not state.mid_auth:
            for req in skipped_requests:
                request_queue.put(req)
            skipped_requests.clear()

def process_request(request, client_address, server_socket, server_port):
    command = request["command"]
    user = state.forum_manager.find_user(request["username"])
    username = request["username"]
    request_id = request.get("request_id")

    client_key = (client_address, request_id)
    if client_key in state.processed_requests:
        cached_response = state.processed_requests[client_key]
        send_segment(cached_response, server_socket, client_address)
        return


    if command != "USR" and command != "PSW":
        print(f"{username} issued {command} command")

    handler_map = {
        "USR": handlers.handle_username_login,
        "PSW": handlers.handle_password_login,
        "CRT": handlers.handle_create_thread,
        "MSG": handlers.handle_post_message,
        "DLT": handlers.handle_delete_message,
        "EDT": handlers.handle_edit_message,
        "LST": handlers.handle_list_threads,
        "RDT": handlers.handle_read_thread,
        "RMV": handlers.handle_remove_thread,
        "UPD": handlers.handle_upload_file,
        "DWN": handlers.handle_download_file,
        "XIT": handlers.handle_exit,
    }

    handler = handler_map.get(command)
    if handler:
        handler(request, client_address, server_socket, server_port, user, client_key, state)


if __name__ == "__main__":
    main()