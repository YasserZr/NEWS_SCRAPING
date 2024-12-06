from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import pandas as pd
import os
import time
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import random
import re

# Function to calculate date difference or generate random past date
def calculate_date_difference(time_string):
    try:
        # Check if the time_string is in relative format like 'X hrs ago', 'X mins ago'
        if "hr" in time_string or "hour" in time_string:  # Handle hours
            hours_ago = int(re.search(r'\d+', time_string).group())
            calculated_date = datetime.now() - timedelta(hours=hours_ago)
        elif "min" in time_string:  # Handle minutes
            minutes_ago = int(re.search(r'\d+', time_string).group())
            calculated_date = datetime.now() - timedelta(minutes=minutes_ago)
        elif "day" in time_string:  # Handle days
            days_ago = int(re.search(r'\d+', time_string).group())
            calculated_date = datetime.now() - timedelta(days=days_ago)
        elif "month" in time_string:  # Handle months (use pandas for month offset)
            months_ago = int(re.search(r'\d+', time_string).group())
            calculated_date = datetime.now() - pd.DateOffset(months=months_ago)
        else:
            # If the string is in the format "X Nov 2024" or similar
            calculated_date = datetime.strptime(time_string, "%d %b %Y")
        
        return calculated_date.strftime("%Y-%m-%d")
    
    except Exception:
        # Generate a random date in the past for "N/A" values or errors
        days_in_past = random.randint(1, 365)  # Random number of days within the past year
        random_date = datetime.now() - timedelta(days=days_in_past)
        return random_date.strftime("%Y-%m-%d")

# Settings
MAX_PAGES = 30  # Maximum number of pages to scrape
progress_file = "progress.txt"
html_file = "News.html"
output_csv = "Data.csv"

# Resume progress if available
page_number = 1
if os.path.exists(progress_file):
    with open(progress_file, "r") as f:
        page_number = int(f.read().strip())

# Data Scraping
driver = webdriver.Chrome()

try:
    driver.get("https://www.bbc.com/")
    
    # Interact with search elements
    search_button = driver.find_element(By.XPATH, '//button[@aria-label="Search BBC"]')
    search_button.click()
    
    search_box = driver.find_element(By.XPATH, '//*[@id="__next"]/div/div[6]/div/div[1]/div/input')
    search_box.send_keys("Technology")
    search_box.send_keys(Keys.RETURN)
    
    # Clear old HTML data if starting from page 1
    if os.path.exists(html_file) and page_number == 1:
        os.remove(html_file)
    
    # Start scraping
    while page_number <= MAX_PAGES:
        print(f"Scraping page {page_number}...")
        try:
            tech_element = driver.find_element(By.XPATH, '//*[@id="main-content"]/div[1]/div/div[2]/div')
            data = tech_element.get_attribute("outerHTML")
            
            # Save the current page's data to the file
            with open(html_file, "a", encoding="utf-8") as f:
                f.write(data)
            
            # Save progress
            with open(progress_file, "w") as f:
                f.write(str(page_number))
            
            # Move to the next page
            next_page = driver.find_element(By.XPATH, '//button[@aria-label="Next Page"]')
            next_page.click()
            page_number += 1
            time.sleep(2)
        
        except Exception as e:
            print(f"Reached the end or encountered an error: {e}")
            break

except Exception as e:
    print(f"Error occurred during scraping: {e}")

finally:
    driver.quit()
    print(f"Scraping stopped at page {page_number}. Progress saved.")

# Data Extraction with Debugging
data_dict = {
    "titles": [],
    "text": [],
    "subject": [],
    "date": []
}

# Get current date for calculations
current_date = datetime.now()

try:
    with open(html_file, 'r', encoding="utf-8") as f:
        html_doc = f.read()
        soup = BeautifulSoup(html_doc, "html.parser")
        
        # Extract time_ago, titles, subtitles, and location
        time_ago = soup.find_all("span", attrs={'class': 'sc-6fba5bd4-1 bCFJJn'})
        titles = soup.find_all("h2")
        subtitles = soup.find_all("p")
        location = soup.find_all("span", attrs={'class': 'sc-6fba5bd4-2 bHkTZK'})

        # Debug: Check how many elements are found
        print(f"Found {len(time_ago)} time_ago elements")
        print(f"Found {len(titles)} titles")
        print(f"Found {len(subtitles)} subtitles")
        print(f"Found {len(location)} location elements")
        
        # Ensure all lists have the same length by filling with "N/A" if necessary
        max_len = max(len(time_ago), len(titles), len(subtitles), len(location))
        
        # Extend lists with "N/A" to make all lists the same length
        time_ago.extend(["N/A"] * (max_len - len(time_ago)))
        titles.extend(["N/A"] * (max_len - len(titles)))
        subtitles.extend(["N/A"] * (max_len - len(subtitles)))
        location.extend(["N/A"] * (max_len - len(location)))

        # Populate the data dictionary
        for ta, title, subtitle, loc in zip(time_ago, titles, subtitles, location):
            data_dict["titles"].append(title.get_text().strip() if hasattr(title, 'get_text') else title.strip())
            data_dict["text"].append(subtitle.get_text().strip() if hasattr(subtitle, 'get_text') else subtitle.strip())
            data_dict["subject"].append(loc.get_text().strip() if hasattr(loc, 'get_text') else loc.strip())
            data_dict["date"].append(calculate_date_difference(ta.get_text().strip() if hasattr(ta, 'get_text') else ta.strip()))

    # Create DataFrame and save to CSV
    df = pd.DataFrame(data_dict)
    
    # Clean up whitespace in all columns
    for col in df.columns:
        df[col] = df[col].apply(lambda x: ' '.join(str(x).split()) if isinstance(x, str) else x)
    
    # Save to CSV
    if not df.empty:
        df.to_csv(output_csv, encoding="utf-8", index=False)
        print(f"Data saved successfully to {output_csv}")
    else:
        print("No data to save. Check your selectors and extracted content.")

except Exception as e:
    print(f"Error occurred during data extraction: {e}")
