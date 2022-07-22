import aiohttp
from aiohttp import web
import time
import json
import yaml
import asyncio

def read_config_file(config_filename):
    with open(config_filename, "r") as config_file:
        return yaml.load(config_file, yaml.FullLoader)

config = read_config_file("config.yaml")

SERVER_URL = config["server"]["url"]
DEVICE_ID = config["device"]["id"]
DEVICE_NAME = config["device"]["name"]
PW = config["bot"]["password"]
USERNAME = config["bot"]["username"]

class MatrixClient:
    async def init(self, server_url):
        self.server_url = server_url
        self.session = aiohttp.ClientSession()
    
    # async def register(self, username, password, device_name = None, device_id = None):
    #     register_request = {
    #         "device_id": device_id,
    #         "initial_device_display_name": device_name,
    #         "password": password,
    #         "refresh_token": True,
    #         "username": username
    #     }

    #     # This should be extracted into a method for handling the user-interactive auth (but perhaps fail on param requirements)
    #     auth_response = await self.session.post(f"{self.server_url}/_matrix/client/v3/register", json.dumps(register_request))
    #     auth_instructions = json.loads(auth_response.text)
    #     register_request["auth"] = {
    #         "type": auth_instructions["flows"][0]["stages"][0],
    #         "session": auth_instructions["session"]
    #     }
    #     register_response = await self.session.post(f"{self.server_url}/_matrix/client/v3/register", json.dumps(register_request))

    #     return json.loads(register_response.text)
    
    async def login(self, username, password):
        login_request = {
            "type": "m.login.password",
            "identifier": {
                "type": "m.id.user",
                "user": username
            },
            "device_id": DEVICE_ID,
            "initial_device_display_name": DEVICE_NAME,
            "password": password
        }
        async with self.session.post(f"{self.server_url}/_matrix/client/v3/login", json=login_request) as response:
            content = json.loads(await response.content.read())

            self.access_token = content["access_token"]
    
    async def send(self, room_id, message):
        return hej
    
    async def join_room(self, room_id):
        await self.post_request(f"/_matrix/client/v3/rooms/{room_id}/join")

    async def sync_loop(self):        
        params = {}
        
        while True:
            response = await self.get_request("/_matrix/client/v3/sync?timeout=20000", params)
            params["since"] = response.json_content["next_batch"]

            # TEST
            print("---")
            print(response.json_content)

            # self.handle_room_events(response.json_content["rooms"])
    
    async def handle_room_events(self, room_events):
        # for event in room_events:
        #     match room_events
        return 4;

    async def get_request(self, path, params):
        headers = self.get_headers()
        
        async with self.session.get(self.get_url(path), headers=headers, params=params) as response:
            json_content = json.loads(await response.content.read())
            response.json_content = json_content

            return response

    async def post_request(self, path, json_body=None):
        headers = self.get_headers();

        async with self.session.post(self.get_url(path), json=json_body, headers=headers) as response:
            json_content = json.loads(await response.content.read())
            response.json_content = json_content

            return response

    def get_url(self, path):
        return f"{self.server_url}{path}";

    def get_headers(self):
        headers = {}

        if self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"

        return headers;

async def main_test():
    client = MatrixClient()

    await client.init(SERVER_URL)
    await client.login(USERNAME, PW)
    await client.sync_loop()

asyncio.run(main_test())