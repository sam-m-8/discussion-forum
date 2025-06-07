import os
from user import User
from thread import Thread


class ForumManager:
    def __init__(self):
        self.users = []
        self.threads = []

    def load_credentials(self):
        with open("credentials.txt", "r") as credentials_file:
            for user in credentials_file:
                if user != '\n':
                    username, password = user.strip().split()
                    self.users.append(User(username, password))

    def find_user(self, target_username):
        for user in self.users:
            if user.username == target_username:
                return user
        return None

    def add_user(self, username, password):
        new_user = User(username, password)
        self.users.append(new_user)
        new_user.is_active = True
        with open("credentials.txt", "a") as credentials_file:
            credentials_file.write(f"{username} {password}\n")
    
    def thread_exists(self, target_title):
        for thread in self.threads:
            if thread.title == target_title:
                return True
        return False
    
    def create_thread(self, thread_title, user):
        new_thread = Thread(thread_title, user)
        self.threads.append(new_thread)
    
    def get_thread(self, target_title):
        for thread in self.threads:
            if thread.title == target_title:
                return thread
            
    def get_thread_list(self):
        return [thread.title for thread in self.threads]

    def delete_thread(self, target_title):
        for thread in self.threads:
            if thread.title == target_title:
                for post in thread.posts:
                    if post.is_file:
                        try:
                            os.remove(f"{target_title}-{post.content}")
                        except FileNotFoundError:
                            pass

                self.threads.remove(thread)
                try:
                    os.remove(target_title)
                except FileNotFoundError:
                    pass
        print(f"Thread {target_title} removed")

    def logout_user(self, target_user):
        for user in self.users:
            if user == target_user:
                user.is_active = False
        print(f"{target_user.username} exited")