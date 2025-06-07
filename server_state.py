from forum_manager import ForumManager

class ServerState:
    def __init__(self):
        self.forum_manager = ForumManager()
        self.processed_requests = {}
        self.mid_auth = False
        self.auth_client = None