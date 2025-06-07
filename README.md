# Discussion Forum

## Overview
The application is based on a client-server model consisting of one server and multiple clients communicating sequentially (i.e., one 
at a time) or concurrently. The client and server communicate using both UDP and TCP.
The application supports various functions typically found on discussion forums, including 
authentication, creating and deleting threads and messages, reading threads, and uploading and 
downloading files. However, unlike typical online forums accessed through HTTP, a custom application protocol was used.

The goal of this project was to gain a deeper understanding of different network layer protocals. Most of the
forum commands are implemented UDP segments, however, uploading and downloading of files is handled with TCP connections. The application has multiple features
including handling of packet loss and concurrent users.

## How to start the application
The server should be started before the client(s) and can be started using:
```python3 server.py server_port```

The client can then be started on a seperate terminal and accepts one argument, the server_port, which
should be the same port number used to start the server:
```python3 client.py server_port```

There can be multiple active clients at any time

## Forum Commands
**Create Thread**

```CRT thread_title```

Creates a new thread with the provided title.

**Post Message**

```MSG thread_title message```

Posts a message to the thread with the name *thread_title* and with the content *message*.

**Delete Message**

```DLT thread_title message_number```

Deletes the message with a message number of *message_number* on thread *thread_title*.

**Edit Message**

```EDT thread_title message_number message```

Given the thread title and message number, the corresponding message in that thread
will be edited to have the contents *message*.

**List Threads**

```LST```

Lists the titles of all the threads that exist.

**Read Thread**

```RDT thread_title```

Displays the contents of a thread with the name *thread_title*.

**Upload File**

```UPD thread_title filename```

Uploads a file with name *filename* to thread *thread_title*.

**Download File**

```DWN thread_title filename```

Downloads file *filename* from *thread_title* from the server onto the client's directory.

**Remove Thread**

```RMV thread_title```

Deletes the thread with title *thread_title*, along with all corresponding messages
and files that have been uploaded to this thread.

**Exit**

```XIT```

Logs the user out.


## State Design
Maintaining the state of the forum largely takes advantage of an object-oriented style of programming. My design consists of four classes: ForumManager, User, Thread, and Post.
The ForumManager is responsible for maintaining all the objects in the state and contains a list of all User objects, and a list of all Thread objects. As such all main state manipulation happens here through creating new users, creating new threads, deleting threads, fetching all current threads. The User class is simply a data store, containing no methods but instead important login information and the current active state of the user. The Thread class contains data about a thread including its title, author (held as a User object), a list of posts, and the number of messages. The thread object contains methods to update and read its post's state. Finally, the Post class just acts as a data class for threads, containing information about a certain post and whether it is a file or not.

Within these classes, the management of updating files is also handled such that when any change is made on the forum manager, the file state of the server is updated, and the forum manager state is updated. Although this could lead to differing states between the files and contents of the forum manager, it was vital to me that I could easily access and query any part of the forum at a given time and not have to read through the files of the server. For example, rather than having to read through a file and return its messages, I can simply iterate through the thread object’s list of posts. This also gives me the ability to not have to extract variables out of files like message numbers and whether the line in the file matches a file upload or a message upload. Instead, I can simply store all information in the respective objects and pass these around as the source of truth.

This greatly helped with encapsulating my state logic and I believe saved me a lot of time not having to deal with different files in the server directory.

## Application Layer
My application layer follows a simple structure. Any request sent by the client will contain a json object containing the command requested by the client, the username of the client, the unique id of the request, and the body of the request. Using a json structure was beneficial in saving me from having to manually use regex to get different variables from the request, making my code much cleaner. Although not every request will use every part of this structure, ie sometimes the body will be empty, and sometimes the username isn’t needed like for reading threads, I thought that it was more important that my system follows a consistent request format so that the server always knows what the structure of the request is. Furthermore, this also increases the ability to expand the program as although for example a request might not need to send the username now, it acts as somewhat of a token to the server as only one user can be logged in to one account at a time. So if the server needs to log that a user read a thread or something in the future, it already has the client’s username token.

My response format follows a similar structure. It contains whether a request was a success or not, the command that was requested by the client, the request id, a message to give to the client, and a body. As such, the client is able to check whether a response was successful, and for which command, and is able to print meaningful messages to the client terminal.

A note on what my server vs client handles is that I wanted my server to just be responsible for sending data to the client and not responsible for formatting this data. As such, my server will respond with meaningful messages, but when it needs to return data it will do so in a json format through the body of the response. For example, reading a thread will provide a list of json objects containing the message number, a bool for whether its a file, and the message content. It will then be the client’s responsibility to format this and print it out. I did this to better separate the responsibilities of the client and the server, as the server should merely be performing requests, not formatting client side responses. This also means if something were to change or the client wants to change the way it prints these responses it is able to do this without changing how the response from the server is sent.

## Segment Handling
The client will receive a command from the user and then parse this as a request object. This request object will assign a random unique request id to the request. The request is then sent to the server.
If the client doesn’t receive a response from the server within a timeout limit (2 seconds) it will resend the same request (it will have the same request id) and wait again. This is repeated until the client receives a response that has the same request id as the request it sent.

On the server side, when a request is processed, it will first check if a response for the current client key has already been performed ie a response has already been sent to this client address with this same request id. If so it will send back this cached request rather than performing the request again. If not it will perform the request and when it sends the response to the client it will also cache this client key in the dictionary.

This process ensures that if any packets are lost, that requests aren’t performed multiple times. Although my approach means that there is no immediate ACK from the server, this method is more efficient as requests are very quick to process anyway. I previously had a request and then an immediate ACK and then the response but this was unnecessary and resulted in all three packets having to constantly be sent again if any one of them was lost.

## Concurrent Users
My system uses a listener loop and worker thread to process requests. When the server receives a request it will immediately be added to the request queue and the loop will go back to listening for requests. This ensures that every request is received and not lost while the server is busy. Then on a separate thread, the worker thread pulls a request from the queue and processes the request. Once the request is processed it will repeat again, pulling from the queue and performing the request.

I believe this is a very elegant and simple solution that ensures every request is captured but also that only one request is being processed at a time.

