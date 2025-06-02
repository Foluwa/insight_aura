class BaseMigration:
    async def up(self, connection):
        raise NotImplementedError("Each migration must implement the 'up' method.")

    async def down(self, connection):
        raise NotImplementedError("Each migration should optionally implement the 'down' method.")
