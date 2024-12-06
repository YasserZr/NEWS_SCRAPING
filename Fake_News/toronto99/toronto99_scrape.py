import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import random
import time

def scrape_article(url):
    """Scrape content from a single article."""
    article_data = {}

    # Send HTTP request to get the article page content
    response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
    response.raise_for_status()  # Raise an HTTPError for bad responses

    soup = BeautifulSoup(response.text, 'html.parser')

    # Extract title
    title_element = soup.find('h1', class_='entry-title')
    title = title_element.get_text(strip=True) if title_element else "No Title"
    
    # Extract body content
    body_element = soup.find('div', class_='entry-content')
    body = body_element.get_text(strip=True) if body_element else "No Content"
    
    # Extract date (use current date if not available)
    date_element = soup.find('time', class_='entry-date')
    date = date_element['datetime'] if date_element and 'datetime' in date_element.attrs else datetime.now().strftime('%Y-%m-%d')
    
    # Randomly assign subject
    subject = random.choice(["News", "Middle-east", "US_News"])
    
    article_data = {
        "title": title,
        "text": body,
        "subject": subject,
        "date": date
    }

    return article_data


def scrape_toronto99_main(url, num_articles=10):
    """Scrape the main page to get article links and then scrape the articles."""
    fake_news = []

    # Send HTTP request to get the main page content
    response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
    response.raise_for_status()  # Raise an HTTPError for bad responses
    
    soup = BeautifulSoup(response.text, 'html.parser')

    # Find all article links (anchors within <h3 class="entry-title h5">)
    article_links = soup.find_all('h3', class_='entry-title h5')

    print(f"Found {len(article_links)} article links.")  # Debugging line

    # Check all found links
    for link in article_links:
        anchor_tag = link.find('a', href=True)  # Find <a> tag with href
        if anchor_tag:
            article_url = anchor_tag['href']
            print(f"Scraping article: {article_url}")  # Debugging line
            try:
                article_data = scrape_article(article_url)
                fake_news.append(article_data)
                time.sleep(2)  # Sleep to avoid overloading the server with requests (politeness)
            except requests.exceptions.RequestException as e:
                print(f"Error fetching the article: {e}")
                continue  # Skip to the next article if there's an error

    return pd.DataFrame(fake_news)

# Example URL to scrape from toronto99.com (you can adjust this URL to get other pages if needed)
main_page_url = 'https://www.toronto99.com/'
fake_news_data = scrape_toronto99_main(main_page_url, num_articles=17)  # Adjust number of articles to scrape

# Print the scraped data
print(fake_news_data)

# Save the data to a CSV file
output_file = 'toronto99_scraped_articles.csv'
fake_news_data.to_csv(output_file, index=False)
print(f"Scraped data saved to '{output_file}'")
