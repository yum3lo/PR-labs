import requests
from bs4 import BeautifulSoup
import re

url = 'https://999.md/ro/list/transport/cars'

def fetch_page(url):
  try:
    headers = {
      # mimic a real browser request
      'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'
    }
    response = requests.get(url, headers=headers)
    # if the response was not successful, raises an http error
    response.raise_for_status()
    return response
  except requests.RequestException as e:
    print(f'Request failed: {e}')
    return None

def extract_product_info(soup):
  products = []
  product_elements = soup.select('li.ads-list-photo-item')

  for element in product_elements:
    name_element = element.select_one('div.ads-list-photo-item-title a')
    name = name_element.text.strip() if name_element else None
    
    price_element = element.select_one('span.ads-list-photo-item-price-wrapper')
    if price_element:
      price_text = price_element.text.strip()
      # remove all non-numeric characters
      price = re.sub(r'[^\d.]', '', price_text)
      price = int(price) if price else None
    else:
      price = None

    link_element = element.select_one('div.ads-list-photo-item-title a')
    link = 'https://999.md' + link_element['href'] if link_element else None

    kilometrage_element = element.select_one('div.is-offer-type span')
    kilometrage = kilometrage_element.text.strip() if kilometrage_element else None

    products.append({
      'name': name,
      'price': price,
      'link': link,
      'kilometrage': kilometrage
    })
  
  return products

response = fetch_page(url)

if response:
  print(f'Successfully fetched page: {url}')
  # parse the HTML content
  soup = BeautifulSoup(response.content, 'html.parser')
  # extract the product information
  products = extract_product_info(soup)
  for product in products:
    print(f"Name: {product['name']}")
    print(f"Price: {product['price']}")
    print(f"Link: {product['link']}")
    print(f"Kilometrage: {product['kilometrage']}")
    print('-----------------------------------')

  print(f"Found {len(products)} products")
else:
  print(f'Failed to fetch page: {url}')