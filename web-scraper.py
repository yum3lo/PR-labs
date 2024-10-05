import requests

url = 'https://carturesti.md/'

def fetch_page(url):
  try:
    response = requests.get(url)
    # if the response was not successful, raises an http error
    response.raise_for_status()
    return response
  except requests.RequestException as e:
    print(f'Request failed: {e}')
    return None

response = fetch_page(url)

if response:
  print(f'Successfully fetched page: {url}')
  print(f'Status code: {response.status_code}')
  print(f'Content type: {response.headers["content-type"]}')
  print(f'Content length: {response.headers["content-length"]}')
  print(f'Content encoding: {response.encoding}')
  print(f'Content: {response.text[:1000]}')

  with open('carturesti.html', "w", encoding='utf-8') as file:
    file.write(response.text)
  print("Page saved to 'carturesti.html'")
else:
  print(f'Failed to fetch page: {url}')