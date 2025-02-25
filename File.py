import os
import time
import logging
import requests
from lxml import etree
import pandas as pd
from functools import wraps
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException, NoSuchElementException, StaleElementReferenceException
from webdriver_manager.chrome import ChromeDriverManager

# Retry decorator for handling transient errors
def retries(max_retries=3, delay=2, exceptions=(Exception,)):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            attempts = 0
            while attempts < max_retries:
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    attempts += 1
                    logging.warning(f"Attempt {attempts}/{max_retries} failed for '{func.__name__}': {e}")
                    if attempts < max_retries:
                        logging.info(f"Retrying '{func.__name__}' after {delay} seconds...")
                        time.sleep(delay)
                    else:
                        logging.error(f"'{func.__name__}' failed after {max_retries} retries.")
                        raise
        return wrapper
    return decorator

# Initialize the Chrome WebDriver
@retries(max_retries=3, delay=1, exceptions=(NoSuchElementException,))
def get_chromedriver(headless=False):
    logging.info("Initializing Chrome WebDriver...")
    
    options = Options()
    options.add_experimental_option("prefs", {
        "download.default_directory": os.getcwd(),
        "download.prompt_for_download": False,
        "safebrowsing.enabled": True,
        "profile.managed_default_content_settings.images": 2,  # Disable images
        "profile.managed_default_content_settings.javascript": 1,  # Enable JS
    })
    options.add_argument("--disable-logging")
    options.add_argument("--start-maximized")
    if headless:
        options.add_argument("--headless")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.set_page_load_timeout(300)  # Set timeout to 30 seconds
    pid = driver.service.process.pid
    logging.info(f"Chrome WebDriver initialized with PID: {pid}")
    return driver, pid


def extract_data_from_page(url):
    try:
        # Send a GET request to fetch the page content
        response = requests.get(url, timeout=60)
        response.raise_for_status()  # Raise an exception for HTTP errors

        # Parse the HTML content using lxml
        tree = etree.HTML(response.text)
        
        # Extract the hotel name
        hotel_name = tree.xpath('//h1[@id="title"]/text()')
        hotel_name = hotel_name[0].strip() if hotel_name else "N/A"
        
        # Extract the category
        addresses = tree.xpath('//div[@class="flex flex-row items-center"]/a')
        addresses = ' '.join(address.text.strip() for address in addresses).strip() if addresses else "N/A"
        
        # Extract the referral link
        activities = tree.xpath('//h3[@class=" uppercase text-sm font-bold"]')
        activities = ', '.join(activity.text.strip() for activity in activities) if activities else "N/A"
        
        # Extract the rent per night
        location = tree.xpath('//p[@class="map_address mb-4"]/text()')
        location = location[0].strip() if location else "N/A"
        
        # Create a dictionary with the extracted data
        data = [
            hotel_name,
            addresses,
            activities,
            location
        ]
        print(data)
        return data

    except requests.exceptions.RequestException as e:
        print(f"HTTP request failed: {e}")
        return []
    except Exception as e:
        print(f"Error extracting data: {e}")
        return []

def write_to_excel(file_name, data_list):
    # Validate file extension
    if not file_name.endswith(".xlsx"):
        raise ValueError("File must have a '.xlsx' extension.")
    
    # Initialize variables
    old_data = None
    if os.path.exists(file_name):
        try:
            old_data = pd.read_excel(file_name)
        except Exception as e:
            print(f"Error reading existing file: {e}")
            return

    # Handle empty data_list
    if not data_list:
        print("No data provided to write.")
        return

    try:
        # Convert data_list to a DataFrame
        if isinstance(data_list[0], dict):  # List of dictionaries
            df = pd.DataFrame(data_list)
        else:  # List of lists/tuples
            # Specify column names explicitly
            df = pd.DataFrame(data_list, columns=['Name', 'Location', 'Activities', 'Address'])

        # Append to old data if it exists
        if old_data is not None:
            df = pd.concat([old_data, df], ignore_index=True)

        # Write the final DataFrame to the Excel file
        df.to_excel(file_name, index=False, engine="openpyxl", columns=['Name', 'Location', 'Activities', 'Address'])
        print(f"Data successfully written to {file_name}")
    except Exception as e:
        print(f"Error writing to Excel file: {e}")


@retries(max_retries=3, delay=2, exceptions=(TimeoutException,))
def get_href_attributes(driver, element_xpath, base_url):
    logging.info("Starting to collect href attributes...")
    hrefs = set()
    try:
        # Wait for elements to load
        WebDriverWait(driver, 50).until(
            EC.presence_of_all_elements_located((By.XPATH, element_xpath))
        )
        
        # Collect hrefs
        elements = driver.find_elements(By.XPATH, element_xpath)
        for element in elements:
            try:
                
                href = element.get_attribute("href")
                if href and href not in hrefs:
                    href = f"{base_url}{href}" if href.startswith("/") else href
                    hrefs.add(href)
                    logging.info(f"Added href: {href}") 
            except StaleElementReferenceException:
                continue

        logging.info(f"Collected {len(hrefs)} unique hrefs so far.")

    except TimeoutException:
        logging.warning("Timeout occurred while waiting for elements.")
        return list(hrefs)

    logging.info(f"Final collection: {len(hrefs)} unique hrefs.")
    return list(hrefs)


def main():

    # checking the file
    file = 'conservio_data.xlsx'
    backup_file = 'conservio_data_backup.xlsx'
    if os.path.exists(file):
        if os.path.exists(backup_file):
            os.remove(backup_file)
        # Backup the existing file
        os.rename(file, backup_file)
        logging.info(f"Backup created: {backup_file}")

    driver = None
    pid = None
    try:
        # Initialize WebDriver
        base_url = 'https://conservio.com'
        driver, pid = get_chromedriver(headless=True)
        driver.get("https://conservio.com/places-to-stay/")
        logging.info(f"Page Title: {driver.title}")
        
        try:
            # Wait for the search results to load
            next_btn =  WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, '//button[@id="nextBtn"]'))
            )
        except:
            logging.warning("Search results not loaded. Exiting.")
            return
        
        while True:
            hrefs = get_href_attributes(driver, '//div[@class="swiper-slide swiper-slide-next"]/a[@id="location-card-mp"]' , base_url)
            logging.info("hrefs: {}".format(len(hrefs)))
            if not hrefs:
                logging.warning("No hrefs collected. Exiting.")
                return
            logging.info(f"Collected {len(hrefs)} unique hrefs.")
            print("hrefs:", len(hrefs))

            # Extract data from each href
            data = []

            for href in hrefs:
                data.append(extract_data_from_page(href))

            # writting to excel format
            write_to_excel('conservio_data.xlsx', data)

            next_btn =  WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, '//button[@id="nextBtn"]'))
            )
            if next_btn.get_attribute('disabled'):
                logging.info("No more results to load. Exiting.")
                break
            # Click the "Next" button
            next_btn.click()

    except Exception as e:
        logging.error(f"An error occurred: {e}")
        return
    finally:
        if driver:
            driver.quit()
            logging.info(f"Chrome WebDriver stopped. Process ID: {pid}")

    logging.info("Starting to extract data...")

if __name__ == "__main__":
    main()
