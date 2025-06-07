from post import Post

class Thread:
    def __init__(self, title, author):
        self.title = title
        self.author = author
        self.posts = []
        self.num_messages = 0

        self.create_thread_file()

    def create_thread_file(self):
        with open(self.title, "w") as new_file:
            new_file.write(f"{self.author.username}\n")

    def post_message(self, message_content, author):
        self.num_messages += 1
        with open(self.title, "a") as thread_file:
            thread_file.write(f"{self.num_messages} {author.username}: {message_content}\n")

        new_post = Post(self.num_messages, author, message_content, False)
        self.posts.append(new_post)
        print(f"{author.username} posted to {self.title} thread")

    def message_exists(self, target_num):
        for post in self.posts:
            if post.message_number == target_num:
                return True
        return False

    def get_message(self, target_num):
        for post in self.posts:
            if post.message_number == target_num:
                return post
    
    def delete_message(self, target_num):
        self.posts = [post for post in self.posts if post.message_number != target_num]
        self.num_messages -= 1
        self.create_thread_file()
        with open(self.title, "a") as thread_file:
            for post in self.posts:
                if post.message_number != None and post.message_number > target_num:
                    post.message_number -= 1

                if post.is_file:
                    thread_file.write(f"{post.author.username} uploaded {post.content}\n")
                else:
                    thread_file.write(f"{post.message_number} {post.author.username}: {post.content}\n")
        print("Message has been deleted")
    
    def edit_message(self, target_num, new_message):
        self.create_thread_file()
        with open(self.title, "a") as thread_file:
            for post in self.posts:
                if post.message_number == target_num:
                    post.content = new_message

                if post.is_file:
                    thread_file.write(f"{post.author.username} uploaded {post.content}\n")
                else:
                    thread_file.write(f"{post.message_number} {post.author.username}: {post.content}\n")
        print("Message has been edited")
    
    def read_thread(self):
        thread_posts = []
        for post in self.posts:
            thread_posts.append({
                "message_number": post.message_number,
                "author": post.author.username,
                "content": post.content,
                "is_file": post.is_file
            })
        return thread_posts
    
    def file_exists(self, target_filename):
        for post in self.posts:
            if post.is_file and post.content == target_filename:
                return True
        return False
    
    def post_file(self, author, filename):
        with open(self.title, "a") as thread_file:
            thread_file.write(f"{author.username} uploaded {filename}\n")
        new_post = Post(None, author, filename, True)
        self.posts.append(new_post)