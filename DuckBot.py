import psycopg2
from MatrixClient import MatrixClient
from MatrixClientPgStorage import MatrixClientPgStorage
from CommandProcessor import CommandProcessor

class DuckBot:
    @classmethod
    async def create(cls, config):
        db_host = config["storage"]["host"]
        db_name = config["storage"]["db_name"]
        db_username = config["storage"]["username"]
        db_password = config["storage"]["password"]
        server_url = config["server"]["url"]
        
        pg_connection = psycopg2.connect(host=db_host, database=db_name, user=db_username, password=db_password)
        matrix_client_storage = MatrixClientPgStorage.create(pg_connection)
        command_processor = await CommandProcessor.create(config)
        matrix_client = await MatrixClient.create(server_url, matrix_client_storage)

        return cls(matrix_client, command_processor)

    def __init__(self, matrix_client, command_processor):
        self.matrix_client = matrix_client
        self.command_processor = command_processor

        matrix_client.add_callback("m.room.message", self.text_callback)
    
    async def run(self, username, password, device_id, device_name):
        print(f"Logging in {username}...")
        await self.matrix_client.login(username, password, device_id, device_name)
        print("Logged in")
        print("Running sync loop")
        await self.matrix_client.sync_loop()
    
    async def text_callback(self, event, room_status):
        message = event["content"]["body"]
        await self.command_processor.parse_command(message)
