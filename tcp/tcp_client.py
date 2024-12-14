import socket
import json
import sys

class CarClient:
  def __init__(self, host: str = 'localhost', port: int = 8004):
    self.host = host
    self.port = port
    self.socket = None

  def connect(self):
    try:
      self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
      self.socket.connect((self.host, self.port))
      print(f"Connected to server at {self.host}:{self.port}")
    except Exception as e:
      print(f"Failed to connect: {str(e)}")
      sys.exit(1)

  def send_command(self, command: dict) -> str:
    # sends command to server and gets response
    try:
      self.socket.send(json.dumps(command).encode('utf-8'))
      response = self.socket.recv(4096).decode('utf-8')
      return response
    except Exception as e:
      return f"Error: {str(e)}"

  def write_car(self, car_data: dict):
    command = {
      'action': 'write',
      'data': car_data
    }
    return self.send_command(command)

  def read_cars(self):
    command = {
      'action': 'read'
    }
    return self.send_command(command)

  def close(self):
    if self.socket:
      self.socket.close()

def main():
  client = CarClient()
  client.connect()

  try:
    while True:
      print("\n Commands:")
      print("1. Write car")
      print("2. Read cars")
      print("3. Exit")
      
      choice = input("\nEnter your choice (1-3): ")
      
      if choice == '1':
        car_data = {
          'name': input("Enter car name: "),
          'price': float(input("Enter price: ")),
          'color': input("Enter color: ")
        }
        response = client.write_car(car_data)
        print(f"\nServer response: {response}")
      
      elif choice == '2':
        response = client.read_cars()
        print(f"\nServer response: {response}")
      
      elif choice == '3':
        break
      
      else:
        print("Invalid choice.")

  except KeyboardInterrupt:
    print("\nExiting...")
  finally:
    client.close()

if __name__ == "__main__":
  main()