import requests
from bs4 import BeautifulSoup
from datetime import datetime
import csv

def scrape_article(url):
    """Scrape content from a single article."""
    article_data = {}

    # Send HTTP request to get the article page content
    response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
    response.raise_for_status()  # Raise an HTTPError for bad responses

    soup = BeautifulSoup(response.text, 'html.parser')

    # Extract title from h1 with class="entry-title"
    title_element = soup.find('h1', class_='entry-title')
    title = title_element.get_text(strip=True) if title_element else "No Title"
    
    # Extract body content from div with id="article_content"
    body_element = soup.find('div', id='article_content')
    body = body_element.get_text(strip=True) if body_element else "No Content"
    
    # Extract date from div with id="ch-postdate"
    date_element = soup.find('div', id='ch-postdate')
    date = date_element.get_text(strip=True) if date_element else datetime.now().strftime('%Y-%m-%d')
    
    # Extract subject from div with id="bc-share"
    subject_element = soup.find('div', id='bc-share')
    subject = subject_element.get_text(strip=True) if subject_element else "No Subject"
    
    # Compile the article data
    article_data = {
        "title": title,
        "text": body,
        "subject": subject,
        "date": date
    }
    return article_data

def scrape_page(url):
    """Scrape all articles on the current page."""
    response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
    response.raise_for_status()

    soup = BeautifulSoup(response.text, 'html.parser')

    # Find all article links within divs with id="ch-ls-box"
    article_links = []
    article_divs = soup.find_all('div', id='ch-ls-box')
    
    for article_div in article_divs:
        link_element = article_div.find('a', href=True)
        if link_element:
            article_links.append(link_element['href'])

    # Scrape each article
    articles = []
    for link in article_links:
        article_data = scrape_article(link)
        articles.append(article_data)

    return articles

def save_to_csv(articles, filename):
    """Save scraped articles to a CSV file."""
    with open(filename, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=["title", "text", "subject", "date"])
        writer.writeheader()
        writer.writerows(articles)
    print(f"Data saved to {filename}")

def scrape_all_pages(base_url, start_page=1, max_pages=5):
    """Scrape articles from multiple pages, incrementing the page number."""
    all_articles = []
    page_number = start_page

    while page_number <= max_pages:
        url = f"{base_url}/page/{page_number}"
        print(f"Scraping {url}...")

        # Scrape articles from the current page
        articles = scrape_page(url)
        all_articles.extend(articles)

        # Increment the page number
        page_number += 1

    return all_articles

# Example usage
if __name__ == "__main__":
    base_url = 'https://globalnation.inquirer.net/category/latest-stories'  # Base URL without page number
    all_articles = scrape_all_pages(base_url, start_page=1, max_pages=5)  # Scrape first 5 pages
    
    print(f"Total articles scraped: {len(all_articles)}")
    
    # Save the data to a CSV file
    save_to_csv(all_articles, 'newsinfo_scraped_articles.csv')
