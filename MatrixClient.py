import aiohttp
import json
from enum import Enum
from MatrixClientPgStorage import MatrixClientPgStorage

class RoomStatus(Enum):
        JOINED = 1
        INVITED = 2
        KNOCKED = 3
        LEFT = 4

class MatrixClient:
    auto_join = True
    
    @classmethod
    async def create(cls, server_url, storage):
        session = aiohttp.ClientSession()
        instance = cls(server_url, session, storage)

        return instance
    
    def __init__(self, server_url, http_client_session, storage: MatrixClientPgStorage):
        self.server_url = server_url
        self.session = http_client_session
        self.storage = storage
        self.callbacks = {}

    def add_callback(self, event_type, callback):
        if event_type not in self.callbacks:
            self.callbacks[event_type] = []

        self.callbacks[event_type].append(callback)
    
    async def login(self, username, password, device_id, device_name):
        login_request = {
            "type": "m.login.password",
            "identifier": {
                "type": "m.id.user",
                "user": username
            },
            "device_id": device_id,
            "initial_device_display_name": device_name,
            "password": password
        }
        async with self.session.post(f"{self.server_url}/_matrix/client/v3/login", json=login_request) as response:
            content = json.loads(await response.content.read())

            self.access_token = content["access_token"]
    
    async def send(self, room_id, message):
        return hej
    
    async def join_room(self, room_id):
        await self.__post_request(f"/_matrix/client/v3/rooms/{room_id}/join")

    async def sync_loop(self):
        params = {}
        
        while True:
            params["timeout"] = 20000

            if self.storage.config["since"]:
                params["since"] = self.storage.config["since"]
            
            response = await self.__get_request("/_matrix/client/v3/sync", params)
            await self.__update_since(response.json_content["next_batch"])

            if "rooms" in response.json_content:
                await self.__handle_sync_events(response.json_content["rooms"])
    
    async def __update_since(self, batch_id):
        self.storage.config["since"] = batch_id
        self.storage.store()
    
    async def __handle_sync_events(self, room_events):
        if "join" in room_events:
            # TODO: Reconsider using this method and the RoomStatus to streamline handling events
            # It might be useless if the other structures are different (as with invitations)
            await self.__handle_room_events(room_events["join"], RoomStatus.JOINED)

        if "invite" in room_events:
            await self.__handle_room_invites(room_events["invite"])
    
    async def __handle_room_events(self, room_events, room_status):
        # The following is not that pretty
        for room_name in room_events:
            room = room_events[room_name]
            
            for event in room["timeline"]["events"]:
                type = event["type"]

                if type in self.callbacks:
                    for callback in self.callbacks[type]:
                        callback(event, room_status)
    
    async def __handle_room_invites(self, invites):
        if self.auto_join:
            for room_id in invites:
                await self.join_room(room_id)

    async def __get_request(self, path, params):
        headers = self.__get_headers()
        
        async with self.session.get(self.__get_url(path), headers=headers, params=params) as response:
            json_content = json.loads(await response.content.read())
            response.json_content = json_content

            return response

    async def __post_request(self, path, json_body=None):
        headers = self.__get_headers();

        async with self.session.post(self.__get_url(path), json=json_body, headers=headers) as response:
            json_content = json.loads(await response.content.read())
            response.json_content = json_content

            return response

    def __get_url(self, path):
        return f"{self.server_url}{path}";

    def __get_headers(self):
        headers = {}

        if self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"

        return headers;