import asyncio
import websockets
import json
import aioconsole  

async def receive_messages(websocket):
  try:
    while True:
      message = await websocket.recv()
      data = json.loads(message)
      print(f"\nReceived: {data['message']}")
      print("Enter message (or 'quit' to exit): ", end='', flush=True)
  except websockets.exceptions.ConnectionClosed:
    print("\nConnection closed")

async def connect_to_chat():
  try:
    async with websockets.connect('ws://localhost:8002') as websocket:
      room_name = input("Enter room name to join: ")
      await websocket.send(json.dumps({
        "action": "join",
        "room": room_name
      }))

      receive_task = asyncio.create_task(receive_messages(websocket))

      print("\nStart chatting (type 'quit' to exit)")
      
      try:
        while True:
          message = await aioconsole.ainput("Enter message: ")
          
          if message.lower() == 'quit':
            break

          await websocket.send(json.dumps({
            "action": "send",
            "room": room_name,
            "message": message
          }))

      except Exception as e:
        print(f"Error sending message: {str(e)}")
      
      finally:
        await websocket.send(json.dumps({
          "action": "leave",
          "room": room_name
        }))
        receive_task.cancel()

  except Exception as e:
    print(f"Connection error: {str(e)}")

if __name__ == "__main__":
  asyncio.run(connect_to_chat())