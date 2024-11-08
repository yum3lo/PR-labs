import socket
import threading
import json
import time
import random
from typing import Dict
from datetime import datetime

class FileServer:
  def __init__(self, host: str = 'localhost', port: int = 8004):
    self.host = host
    self.port = port
    self.file_lock = threading.Lock()  # mutex (mutually exclusive flag) for file operations
    self.car_data_file = "car_data.json"
    self.initialize_file()
        
  def initialize_file(self):
    try:
      with open(self.car_data_file, 'r') as f:
        json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
      with open(self.car_data_file, 'w') as f:
        json.dump([], f)

  def write_car(self, car_data: Dict) -> str:
    time.sleep(random.randint(1, 7))
    
    with self.file_lock:
      try:
        with open(self.car_data_file, 'r') as f:
          cars = json.load(f)
        car_data['timestamp'] = datetime.now().isoformat()
        cars.append(car_data)
        
        with open(self.car_data_file, 'w') as f:
          json.dump(cars, f, indent=2)
        
        return f"Successfully wrote car: {car_data['name']}"
      except Exception as e:
        return f"Error writing to file: {str(e)}"

  def read_cars(self) -> str:
    time.sleep(random.randint(1, 7))
    with self.file_lock:
      try:
        with open(self.car_data_file, 'r') as f:
          cars = json.load(f)
        return json.dumps(cars, indent=2)
      except Exception as e:
        return f"Error reading from file: {str(e)}"

  def handle_client(self, client_socket: socket.socket):
    client_address = client_socket.getpeername()
    print(f"New connection from {client_address}")
    
    try:
      while True:
        data = client_socket.recv(1024).decode('utf-8')
        if not data:
          break
        
        try:
          command = json.loads(data)
          action = command.get('action')
          
          if action == 'write':
            car_data = command.get('data')
            if car_data:
              response = self.write_car(car_data)
            else:
              response = "Error: No car data provided"
          
          elif action == 'read':
            response = self.read_cars()
          
          else:
            response = f"Unknown action: {action}"
          
          client_socket.send(response.encode('utf-8'))
        
        except json.JSONDecodeError:
          error_msg = "Invalid JSON format"
          client_socket.send(error_msg.encode('utf-8'))
    
    except Exception as e:
      print(f"Error handling client {client_address}: {str(e)}")
    finally:
      client_socket.close()
      print(f"Connection closed for {client_address}")

  def start(self):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((self.host, self.port))
    server_socket.listen(5) # max 5 connections
    
    print(f"Server listening on {self.host}:{self.port}")
    
    try:
      while True:
        client_socket, _ = server_socket.accept()
        # starts a new thread for client
        client_thread = threading.Thread(
          target=self.handle_client,
          args=(client_socket,)
        )
        client_thread.start()
    
    except KeyboardInterrupt:
      print("\nShutting down server...")
    finally:
      server_socket.close()

if __name__ == "__main__":
  server = FileServer()
  server.start()