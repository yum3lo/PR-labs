import requests
from bs4 import BeautifulSoup
import re

url = 'https://999.md/ro/list/transport/cars'

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

def extract_product_info(soup, limit=10):
  products = []
  product_elements = soup.select('li.ads-list-photo-item')

  for element in product_elements[:limit]:
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

response = fetch_page(url)

if response:
  print(f'Successfully fetched page: {url}')
  soup = BeautifulSoup(response.content, 'html.parser')
  products = extract_product_info(soup)
  for product in products:
    print(f"Name: {product['name']}")
    print(f"Price: {product['price']}")
    print(f"Link: {product['link']}")
    print(f"Kilometrage: {product['kilometrage']}")
    print(f"Color: {product['color']}")
    print('-----------------------------------')

  print(f"Found {len(products)} products")
else:
  print(f'Failed to fetch page: {url}')