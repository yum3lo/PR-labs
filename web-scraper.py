# web-scraper.py
import socket
import ssl
from bs4 import BeautifulSoup
import re
from datetime import datetime
from functools import reduce
import pika 
import json
import os
from ftp_processor import FTPProcessor

url = 'https://999.md/ro/list/transport/cars'
eur_to_mdl = 19.286

def fetch_page_socket(url, max_redirects=5):
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
          secure_sock.sendall(f"GET {path} HTTP/1.1\r\nHost: {host}\r\nUser-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36\r\nConnection: close\r\n\r\n".encode())
          response = b""
          while True:
            data = secure_sock.recv(4096)
            if not data:
              break
            response += data

      headers, _, body = response.partition(b'\r\n\r\n')
      headers = headers.decode('utf-8')

      if 'HTTP/1.1 301' in headers or 'HTTP/1.1 302' in headers:
        location = re.search(r'Location: (.*)\r\n', headers)
        if location:
          url = location.group(1)
          if not url.startswith('http'):
            url = f'{protocol}//{host}{url}'
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
    product['price'] = re.sub(r'[^\d.]', '', product['price']).strip()
    try:
      product['price'] = float(product['price'])
    except ValueError:
      product['price'] = None

  if product['kilometrage']:
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
  products_mdl = list(map(lambda p: {**p, 'price_mdl': p['price'] * eur_to_mdl if p['price'] else None}, products))
  products_filtered = list(filter(lambda p: p['price'] and 5000<= p['price'] <= 10000, products_mdl))
  for product in products_filtered:
    product['name'] = product.get('name', '').strip()
    product['price_mdl'] = product.get('price_mdl', 0)
    product['link'] = product.get('link', '')
    product['kilometrage'] = product.get('kilometrage', 0)
    product['color'] = (product.get('color') or '').strip()
  total_price = reduce(lambda acc, p: acc + (p['price_mdl'] or 0), products_filtered, 0)
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
    
    print(f"[x] Published message to RabbitMQ: {message}")
    connection.close()
  except Exception as e:
    print(f"[x] Error publishing to RabbitMQ: {e}")

html_content = fetch_page_socket(url)

if html_content:
  print(f'Successfully fetched page: {url}')
  soup = BeautifulSoup(html_content, 'html.parser')
  products = extract_product_info(soup)
  processed_data = process_products(products)
  ftp_processor = FTPProcessor()
  publish_to_rabbitmq(processed_data) 
  print(f"Published data to RabbitMQ")
  saved_file = ftp_processor.save_processed_data(processed_data)
  if saved_file:
    ftp_processor.upload_file_to_ftp(saved_file)
else:
  print(f'Failed to fetch page: {url}')