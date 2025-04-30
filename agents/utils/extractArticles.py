import requests
from bs4 import BeautifulSoup

def extract(url):
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an error for bad responses
        soup = BeautifulSoup(response.content, 'html.parser')

        # Extract the content
        paragraphs = soup.find_all('p')
        content = '\n\n'.join(p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True))

        return content, None  # Return content and no error

    except Exception as e:
        print(f"Error extracting article from {url}: {e}")
        return None, str(e)  # Return no content and the error message