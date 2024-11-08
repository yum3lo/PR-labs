import asyncio
import websockets
import json
from collections import defaultdict
from typing import Set, Dict

class ChatRoom:
  # stores the clients for each room
  def __init__(self):
    self.clients: Dict[str, Set[websockets.WebSocketServerProtocol]] = defaultdict(set)
  
  async def join_room(self, websocket: websockets.WebSocketServerProtocol, room: str):
    self.clients[room].add(websocket)
    await self.broadcast_message(room, f"User joined the room")
  
  async def leave_room(self, websocket: websockets.WebSocketServerProtocol, room: str):
    self.clients[room].remove(websocket)
    await self.broadcast_message(room, f"User left the room")
      
    if not self.clients[room]:
      del self.clients[room]
  
  async def broadcast_message(self, room: str, message: str):
    if room in self.clients:
      disconnected_clients = set()
      for client in self.clients[room]:
        try:
          await client.send(json.dumps({"message": message}))
        except websockets.exceptions.ConnectionClosed:
          disconnected_clients.add(client)
    
      for client in disconnected_clients:
        self.clients[room].remove(client)

chat_room = ChatRoom()

# the main websocket handler for joining, sending, and leaving rooms
async def handle_connection(websocket: websockets.WebSocketServerProtocol, path: str):
  try:
    async for message in websocket:
      try:
        data = json.loads(message)
        action = data.get('action')
        room = data.get('room')
        
        if not room:
          await websocket.send(json.dumps({"error": "Room name is required"}))
          continue
        
        if action == 'join':
          await chat_room.join_room(websocket, room)
          await websocket.send(json.dumps({"message": f"Successfully joined room {room}"}))
        
        elif action == 'send':
          message = data.get('message')
          if message:
            await chat_room.broadcast_message(room, message)
          else:
            await websocket.send(json.dumps({"error": "Message is required"}))
        
        elif action == 'leave':
          await chat_room.leave_room(websocket, room)
          await websocket.send(json.dumps({"message": f"Successfully left room {room}"}))
        
        else:
          await websocket.send(json.dumps({"error": f"Unknown action: {action}"}))
        
      except json.JSONDecodeError:
        await websocket.send(json.dumps({"error": "Invalid JSON format"}))
  
  # removes client from all rooms when connection is closed
  except websockets.exceptions.ConnectionClosed:
    for room, clients in chat_room.clients.items():
      if websocket in clients:
        await chat_room.leave_room(websocket, room)

async def start_server():
  async with websockets.serve(handle_connection, "localhost", 8003) as server:
    print("WebSocket server is running on ws://localhost:8003")
    # runs forever
    await asyncio.Future()

def main():
  try:
    asyncio.run(start_server())
  except KeyboardInterrupt:
    print("Server stopped by user")

if __name__ == "__main__":
  main()