# Conservio Hotel Data Scraper

## Overview
This project is a web scraper designed to extract hotel data from the Conservio website. It utilizes Selenium and Requests to gather details such as hotel names, locations, activities, and addresses. The extracted data is saved in an Excel file for further analysis.

## Features
- Extracts hotel details from the Conservio website.
- Implements retries to handle transient errors.
- Uses Selenium WebDriver for dynamic content loading.
- Saves data to an Excel file.
- Logs errors and retry attempts.
- Supports multi-threaded scraping for improved efficiency.

## Technologies Used
- Python
- Selenium
- Requests
- Pandas
- lxml
- WebDriver Manager

## Installation
### Prerequisites
Ensure you have the following installed:
- Python (>=3.7)
- Google Chrome
- ChromeDriver

### Setup
1. Clone the repository:
   ```sh
   git clone https://github.com/Ahmad-1252/Conervio_Hotel_Bot.git
   cd Conervio_Hotel_Bot
   ```
2. Install dependencies:
   ```sh
   pip install -r requirements.txt
   ```

## Usage
To run the scraper, execute:
```sh
python script.py
```

## Functionality
### 1. WebDriver Initialization
Initializes the Chrome WebDriver with options for headless execution, disabled images, and JavaScript enablement.

### 2. Data Extraction
- Fetches hotel details such as:
  - Name
  - Location
  - Activities
  - Address
  - Contact Information
  - Pricing (if available)
- Parses the page using `lxml` and XPath queries.

### 3. Data Storage
Saves extracted data into an Excel file (`conservio_data.xlsx`). If the file exists, it creates a backup before updating.

### 4. Pagination Handling
Clicks the "Next" button to load more results until no further pages are available.

### 5. Multi-threading Support
Uses threading to speed up data extraction by handling multiple pages concurrently.

## Error Handling
- Implements a retry mechanism for handling network and element access errors.
- Logs all warnings and errors for debugging.
- Handles timeouts and dynamically loaded elements.

## Dependencies
The project requires the following Python libraries:
```sh
pip install selenium requests pandas lxml openpyxl webdriver-manager threading
```

## Logging
Logs messages to help track the scraping progress, errors, and retry attempts.

## License
This project is licensed under the MIT License.

## Author
[Ahmad-1252](https://github.com/Ahmad-1252)

