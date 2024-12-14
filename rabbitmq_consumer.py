# rabbitmq_consumer.py
import pika
import requests
import json

def callback(ch, method, properties, body):
  try:
    message_data = json.loads(body.decode('utf-8'))
    print(f"[x] Received message: {json.dumps(message_data)}")
    
    url = "http://localhost:8001/cars"
    headers = {'Content-Type': 'application/json'}
    cars = message_data.get('products_filtered', [])
    
    for car_data in cars:
      car_payload = {
        "name": car_data.get('name', ''),
        "price_mdl": car_data.get('price_mdl', 0.0),
        "link": car_data.get('link', ''),
        "kilometrage": car_data.get('kilometrage', 0),
        "color": car_data.get('color', '')
      }
      
      response = requests.post(url, json=car_payload, headers=headers)
      
      if response.status_code == 200:
        print(f"[x] Successfully posted car data: {response.json()}")
      else:
        print(f"[x] Failed to post car data, status code: {response.status_code}, response: {response.text}")
  
  except json.JSONDecodeError:
    print(f"[x] Received invalid JSON")
  except Exception as e:
    print(f"[x] An error occurred: {e}")
        
def start_consumer():
  connection = pika.BlockingConnection(
    pika.ConnectionParameters(
        host='localhost', 
        port=5672,
        credentials=pika.PlainCredentials('guest', 'guest')
    )
  )
  channel = connection.channel()
  channel.queue_declare(queue='car_data')
  
  channel.basic_consume(queue='car_data', on_message_callback=callback, auto_ack=True)
  print(' [*] Waiting for messages. To exit press CTRL+C')
  channel.start_consuming()

if __name__ == "__main__":
  start_consumer()