from socket import *
from helper import *
import sys

def main():
    if len(sys.argv) != 2:
        print("Usage: python3 client.py server_port")
        exit(0)

    server_port = int(sys.argv[1])
    # Initialise client socket
    client_socket = socket(AF_INET, SOCK_DGRAM)
    username, server_address = authenticate_user(client_socket, server_port)

    # Waits for user to input command, processes command and then repeats
    while True:
        is_valid, operation, body = get_next_command()
        if not is_valid:
            continue

        request = format_request(operation, username, body)
        response, server_address = send_segment_await_response(request, client_socket, server_address)

        match response["requested_command"]:
            case "LST":
                if not response["body"]:
                    print("No threads to list")
                else:
                    print("The list of active threads:")
                    for thread in response["body"]:
                        print(thread)

            case "RDT":
                if not response["success"]:
                    print(response["message"])
                elif not response["body"] and response["success"]:
                    print(f"Thread {body['thread_title']} is empty")
                elif response["success"]:
                    res_body = response["body"]
                    for post in res_body:
                        if post["is_file"]:
                            print(f"{post['author']} uploaded {post['content']}")
                        else:
                            print(f"{post['message_number']} {post['author']}: {post['content']}")

            case "UPD":
                if response["success"]:
                    tcp_client_socket = socket(AF_INET, SOCK_STREAM)
                    tcp_client_socket.connect(('localhost', server_port))

                    filename = response["body"].get("filename")
                    with open(filename, "rb") as upload_file:
                        while True:
                            data = upload_file.read(4096)
                            if not data:
                                break
                            tcp_client_socket.sendall(data)
                    tcp_client_socket.close()

                    response, server_address = await_response_resend_segment(request, client_socket, server_address)
                    print(response["message"])
                else:
                    print(response["message"])

            case "DWN":
                if response["success"]:
                    tcp_client_socket = socket(AF_INET, SOCK_STREAM)
                    tcp_client_socket.connect(('localhost', server_port))

                    filename = response["body"].get("filename")
                    with open(filename, "wb") as dwn_file:
                        while True:
                            data = tcp_client_socket.recv(4096)
                            if not data:
                                break
                            dwn_file.write(data)
                    tcp_client_socket.close()

                    response, server_address = receive_segment(client_socket)
                    print(response["message"])
                else:
                    print(response["message"])

            case "XIT":
                print(response["message"])
                client_socket.close()
                sys.exit()

            case _:
                if response["message"] != None:
                    print(response["message"])


if __name__ == "__main__":
    main()