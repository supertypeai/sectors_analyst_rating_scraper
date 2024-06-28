import os
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
import chromedriver_autoinstaller
from webdriver_manager.chrome import ChromeDriverManager
import json
# from pyvirtualdisplay import Display

# Setup for selenium on Github Action
# Adding display for xvfb
# display = Display(visible=0, size=(800, 800))  
# display.start()

chromedriver_autoinstaller.install()  # Check if the current version of chromedriver exists
                                      # and if it doesn't exist, download it automatically,
                                      # then add chromedriver to path

chrome_options = webdriver.ChromeOptions()    
# Add your options as needed    
options = [
  # Define window size here
   "--window-size=800,800",
    "--headless",
    "--no-sandbox",
    "--disable-dev-shm-usage",
    "--disable-gpu",
    # "--ignore-certificate-errors",
    #"--window-size=1920,1200",
    #"--ignore-certificate-errors",
    #"--disable-extensions",
    #'--remote-debugging-port=9222'
]

for option in options:
    chrome_options.add_argument(option)



# Scraping data
BASE_URL = "https://www.tradingview.com/chart/?symbol=IDX%3A"
TECHNICAL_ENUM = ['sell', 'neutral', 'buy']
ANALYST_ENUM = ['strong_buy', 'buy', 'hold', 'sell', 'strong_sell']



def get_url_page(symbol:str) -> str:
    return f"{BASE_URL}{symbol}"

def scrap_page(url: str) :
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    driver.get(url)
    try:
        _ = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CLASS_NAME, "button-vll9ujXF"))
        )
        print(f"Successfully get element from URL: {url}")
        return driver
    except:
      print(f"Fail scraping from URL: {url}")
      print("Loader did not disappear in time")
      driver.quit()
      return None
    
def scrap_rating_data(symbol: str) -> dict:
    url = get_url_page(symbol)
    driver = scrap_page(url)
    result_data = dict()
    result_data['symbol'] = symbol
    technical_rating_dict = None
    analyst_rating_dict = None

    if (driver is not None):
      items = driver.find_elements(By.CLASS_NAME, "button-vll9ujXF")
      for item in items:
        
        # Getting technical
        if (item.text == "More technicals"):
          technical_rating_dict = dict()

          item.click()
          try:
            _ = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.CLASS_NAME, "speedometerWrapper-kg4MJrFB"))
              )
            technical_data_wrapper = driver.find_elements(By.CLASS_NAME, "speedometerWrapper-kg4MJrFB")
            assert (len(technical_data_wrapper) == 3), "Difference in technical data wrapper detected"

            # Summary should be the middle one
            summary_technical_data_wrapper = technical_data_wrapper[1]
            technical_counters_data_wrapper = summary_technical_data_wrapper.find_element(By.CLASS_NAME, "countersWrapper-kg4MJrFB")
            technical_rating_data = technical_counters_data_wrapper.text.split("\n")

            # Insert the data to dictionary
            start_rating_data_idx = 1
            for enum in TECHNICAL_ENUM:
              technical_rating_dict[enum] = int(technical_rating_data[start_rating_data_idx])
              start_rating_data_idx +=2
          
            technical_rating_dict['updated_on'] = (datetime.now()).strftime("%Y-%m-%d %H:%M:%S")


          except:
            print("Failed to get Technical Data")

        # Getting Analyst Rating
        if (item.text == "See forecast"):
          analyst_rating_dict = dict()
          

          item.click()

          try:
            _ = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "container-zZSa1SHt"))
              )
            analyst_data_wrapper = driver.find_element(By.CLASS_NAME, "container-zZSa1SHt")

            # Get the Value
            analyst_data_values = analyst_data_wrapper.find_elements(By.CLASS_NAME,"value-GNeDL9vy")

            # Insert the data to dictionary
            for idx, enum in enumerate(ANALYST_ENUM):
               analyst_rating_dict[enum] = int((analyst_data_values[idx]).text)

            analyst_rating_dict['updated_on'] = (datetime.now()).strftime("%Y-%m-%d %H:%M:%S")
          except:
            print("Failed to get Analyst Data")

    result_data['technical_rating'] = technical_rating_dict
    result_data['analyst_rating'] = analyst_rating_dict
    if (driver is not None):
      driver.quit()
    return result_data

def save_to_json(file_path, data):
  with open(file_path, "w") as output_file:
    json.dump(data, output_file, indent=2)


def scrap_function(symbol_list, process_idx):
  all_data = []
  cwd = os.getcwd()
  start_idx = 0
  count = 0

  # Iterate in symbol list
  for i in range(start_idx, len(symbol_list)):
    symbol = symbol_list[i]
    scrapped_data = scrap_rating_data(symbol)
    all_data.append(scrapped_data)

    if (i % 10 == 0 and count != 0):
      print(f"CHECKPOINT || P{process_idx} {i} Data")
    
    # if (i % 50 == 0 and count != 0):
    #   filename = f"P{process_idx}_data_{i}.json"
    #   print(f"==> Data is exported in {filename}")
    #   file_path = os.path.join(cwd, "data", filename)
    #   save_to_json(file_path, all_data)
    count += 1

  # Save last
  filename = f"P{process_idx}_data.json"
  print(f"==> Finished data is exported in {filename}")
  file_path = os.path.join(cwd, "data", filename)
  save_to_json(file_path, all_data)

  return all_data

