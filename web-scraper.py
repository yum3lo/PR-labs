import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime
from functools import reduce

url = 'https://999.md/ro/list/transport/cars'
eur_to_mdl = 19.286

def fetch_page(url):
  try:
    headers = {
      # mimics a real browser request
      'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'
    }
    response = requests.get(url, headers=headers)
    # if the response was not successful, raises an http error
    response.raise_for_status()
    return response
  except requests.RequestException as e:
    print(f'Request failed: {e}')
    return None

def extract_additional_info(product_url):
  response = fetch_page(product_url)
  if response:
    soup = BeautifulSoup(response.content, 'html.parser')
    color_element = soup.select_one('li.m-value[itemprop="additionalProperty"] span.adPage__content__features__key:-soup-contains("Culoarea") + span.adPage__content__features__value')
    color = color_element.text.strip() if color_element else None
    return color
  return None

def validate_data(product):
  # removing whitespaces from name and color (string fields)
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
    product['kilometrage'] = re.sub(r'[^\d.]', '', product['kilometrage']).strip()
    try:
      product['kilometrage'] = int(product['kilometrage'])
    except ValueError:
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
  # sum up the prices
  total_price = reduce(lambda acc, p: acc + (p['price'] or 0), products_filtered, 0)
  # final data structure
  result = {
    'products_filtered': products_filtered,
    'total_price_eur': total_price,
    'total_price_mdl': total_price * eur_to_mdl,
    'timestamp': datetime.now().isoformat()
  }
  return result

response = fetch_page(url)

if response:
  print(f'Successfully fetched page: {url}')
  soup = BeautifulSoup(response.content, 'html.parser')
  products = extract_product_info(soup)
  # process the products
  processed_data = process_products(products)
  print("Filtered products:")
  for product in processed_data['products_filtered']:
    print(f"Name: {product['name']}")
    print(f"Price (MDL): {product['price_mdl']}")
    print(f"Link: {product['link']}")
    print(f"Kilometrage: {product['kilometrage']}")
    print(f"Color: {product['color']}")
    print('-----------------------------------')

  print(f"Found {len(processed_data['products_filtered'])} products")
  print(f"Total price (MDL): {processed_data['total_price_mdl']}")
  print(f"Timestamp: {processed_data['timestamp']}")
else:
  print(f'Failed to fetch page: {url}')