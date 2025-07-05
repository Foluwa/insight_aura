import asyncpg

class BaseService:
    def __init__(self, connection: asyncpg.Connection):
        self.connection = connection
