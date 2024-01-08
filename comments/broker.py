import asyncio
import json
from typing import AsyncGenerator

from comments.models import Comment


class Broker:
    """
    A async thread pool which publishes messages
    to the database and allows subscribers to receive
    them in real-time.
    """

    def __init__(self) -> None:
        """
        Store connected clients in a set.
        """
        self.connections = set()

    async def publish(self, name: str, url: str, message: str) -> None:
        """
        Take every incoming websocket message and store it in the database.
        Additionally, publish it to connected websocket clients.
        """
        m = Comment(
            name=name,
            message=message,
            url=url
        )
        m.save()
        for connection in self.connections:
            await connection.put(json.dumps({
                'name': m.name,
                'message': m.message,
                'url': m.url,
                'date': str(m.datestamp)
            }))

    async def subscribe(self) -> AsyncGenerator[str, None]:
        """
        Setup thread queue for connected clients.
        """
        connection = asyncio.Queue()
        self.connections.add(connection)

        try:
            while True:
                await connection.put(json.dumps({'connected_clients': len(self.connections)}))
                yield await connection.get()
        finally:
            self.connections.remove(connection)
