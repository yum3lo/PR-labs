# web-scraper.py
import socket
import ssl
from bs4 import BeautifulSoup
import re
from datetime import datetime
from functools import reduce
from json_serializer import to_json
from xml_serializer import to_xml
from compact_serializer import CompactSerialize
import pika 
import json

url = 'https://999.md/ro/list/transport/cars'
eur_to_mdl = 19.286

# because of 301 Moved Permanently redirect, redirect following is needed, HTTP to HTTPS, SSL for secure connection
def fetch_page_socket(url, max_redirects=5): # no infinite loops
  for _ in range(max_redirects):
    try:
      parts = url.split('/')
      if len(parts) >= 3:
        protocol, _, host = parts[:3]
        path = '/' + '/'.join(parts[3:])
      else:
        raise ValueError('Invalid URL format')
      
      context = ssl.create_default_context()
      with socket.create_connection((host, 443)) as sock:
        with context.wrap_socket(sock, server_hostname=host) as secure_sock:
          # encode the request to bytes
          # close server after sending the response
          # \r\n\r\n - end of the headers
          secure_sock.sendall(f"GET {path} HTTP/1.1\r\nHost: {host}\r\nUser-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36\r\nConnection: close\r\n\r\n".encode())
          response = b""
          while True:
            data = secure_sock.recv(4096)
            if not data:
              break
            response += data

      # # AF_INET = IPv4, SOCK_STREAM = TCP
      # s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
      # s.connect((host, 80))

      # split the response into headers and body
      headers, _, body = response.partition(b'\r\n\r\n')
      # decodes the headers from bytes to string
      headers = headers.decode('utf-8')

      # check if the response is a redirect
      if 'HTTP/1.1 301' in headers or 'HTTP/1.1 302' in headers:
        location = re.search(r'Location: (.*)\r\n', headers)
        if location:
          # get the new url
          url = location.group(1)
          if not url.startswith('http'):
            url = f'{protocol}//{host}{url}'
          print(f'Redirecting to: {url}')
          continue
      
      return body.decode('utf-8')

    except Exception as e:
      print(f'Request failed: {e}')
      return None

  print("Max redirects reached")
  return None

def extract_additional_info(product_url):
  html_content = fetch_page_socket(product_url)
  if html_content:
    soup = BeautifulSoup(html_content, 'html.parser')
    color_element = soup.select_one('li.m-value[itemprop="additionalProperty"] span.adPage__content__features__key:-soup-contains("Culoarea") + span.adPage__content__features__value')
    color = color_element.text.strip() if color_element else None
    return color
  return None

def validate_data(product):
  product['name'] = product['name'].strip() if product['name'] else None
  product['color'] = product['color'].strip() if product['color'] else None

  if product['price']:
    # removing the currency (euro) string
    product['price'] = re.sub(r'[^\d.]', '', product['price']).strip()
    try:
      product['price'] = float(product['price'])
    except ValueError:
      product['price'] = None

  if product['kilometrage']:
    # removing "km" string
    if product['kilometrage']:
      product['kilometrage'] = re.sub(r'[^\d.]', '', product['kilometrage']).strip()
      try:
        product['kilometrage'] = int(product['kilometrage'])
      except ValueError:
        product['kilometrage'] = None
    else:
      product['kilometrage'] = None
    
  return product

def extract_product_info(soup):
  products = []
  product_elements = soup.select('li.ads-list-photo-item')

  for element in product_elements:
    name_element = element.select_one('div.ads-list-photo-item-title a')
    name = name_element.text if name_element else None
    
    price_element = element.select_one('span.ads-list-photo-item-price-wrapper')
    price = price_element.text if price_element else None

    link_element = element.select_one('div.ads-list-photo-item-title a')
    link = 'https://999.md' + link_element['href'] if link_element else None

    kilometrage_element = element.select_one('div.is-offer-type span')
    kilometrage = kilometrage_element.text if kilometrage_element else None

    color = extract_additional_info(link) if link else None

    product = {
      'name': name,
      'price': price,
      'link': link,
      'kilometrage': kilometrage,
      'color': color
    }
  
    validated_product = validate_data(product)
    products.append(validated_product)

  return products

def process_products(products):
  # convert eur to mdl
  products_mdl = list(map(lambda p: {**p, 'price_mdl': p['price'] * eur_to_mdl if p['price'] else None}, products))
  # filter products by price
  products_filtered = list(filter(lambda p: p['price'] and 5000<= p['price'] <= 10000, products_mdl))
  for product in products_filtered:
    # Ensure all required fields are not None
    product['name'] = product.get('name', '').strip()
    product['price_mdl'] = product.get('price_mdl', 0)
    product['link'] = product.get('link', '')
    product['kilometrage'] = product.get('kilometrage', 0)
    product['color'] = (product.get('color') or '').strip()  
  # sum up the prices
  total_price = reduce(lambda acc, p: acc + (p['price_mdl'] or 0), products_filtered, 0)
  # final data structure
  result = {
    'products_filtered': products_filtered,
    'total_price_mdl': total_price,
    'timestamp': datetime.now().isoformat()
  }
  return result

def publish_to_rabbitmq(data):
  try:
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()
    channel.queue_declare(queue='car_data')
    message = json.dumps(data, default=str)
    channel.basic_publish(
      exchange='', 
      routing_key='car_data', 
      body=message)
    
    print(f"Published message to RabbitMQ: {message}")
    connection.close()
  except Exception as e:
    print(f"Error publishing to RabbitMQ: {e}")

html_content = fetch_page_socket(url)

if html_content:
  print(f'Successfully fetched page: {url}')
  soup = BeautifulSoup(html_content, 'html.parser')
  products = extract_product_info(soup)
  # process the products
  processed_data = process_products(products)
  
  publish_to_rabbitmq(processed_data) 
  print(f"Published data to RabbitMQ")
else:
  print(f'Failed to fetch page: {url}')
  
#   print("Filtered products:")
#   for product in processed_data['products_filtered']:
#     print(f"Name: {product['name']}")
#     print(f"Price (MDL): {product['price_mdl']}")
#     print(f"Link: {product['link']}")
#     print(f"Kilometrage: {product['kilometrage']}")
#     print(f"Color: {product['color']}")
#     print('-----------------------------------')

#   print(f"Found {len(processed_data['products_filtered'])} products")
#   print(f"Total price (MDL): {processed_data['total_price_mdl']}")
#   print(f"Timestamp: {processed_data['timestamp']}")
# else:
#   print(f'Failed to fetch page: {url}')

# if processed_data:
#   json_data = to_json(processed_data)
#   xml_data = to_xml(processed_data, 'processed_data')
#   print("\nJSON Data:")
#   print(json_data)
#   print("\nXML Data:")
#   print(xml_data)
#   compact_output = CompactSerialize.serialize(processed_data)
#   print("\nCompact Data:")
#   print(compact_output)

#   deserialize_data = CompactSerialize.deserialize(compact_output)
#   print("\nDeserialized data mathes original:", processed_data == deserialize_data)