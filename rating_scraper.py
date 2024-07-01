from urllib.request import urlopen
from bs4 import BeautifulSoup
from datetime import datetime
from requests_html import HTMLSession
import json
import os


# Scraping data
BASE_URL = 'https://www.tradingview.com/symbols/IDX-'
TECHNICAL_ENUM = ['sell', 'neutral', 'buy']
ANALYST_ENUM = ['strong_buy', 'buy', 'hold', 'sell', 'strong_sell']

def get_url_page(symbol:str) -> str:
    return f"{BASE_URL}{symbol}"

def scrap_page(url: str) :
    try:
      session = HTMLSession()
      response = session.get(url)
      response.html.render()

      soup = BeautifulSoup(response.html.html, "html.parser")
      return soup
    except Exception as e:
      print(f"Fail scraping from URL: {url}")
      print(e)
      return None
    

def save_to_json(file_path, data):
  with open(file_path, "w") as output_file:
    json.dump(data, output_file, indent=2)

def scrap_rating_data(symbol: str) -> dict:
    url = get_url_page(symbol)
    result_data = dict()
    result_data['symbol'] = symbol
    technical_rating_dict = None
    analyst_rating_dict = None

    # Scrap technical page
    technical_url = url+"/technicals/"
    soup_tpage = scrap_page(technical_url)
    if (soup_tpage is not None):
      technical_rating_dict = dict()

      # Getting into the data
      speedometer_containers = soup_tpage.findAll("div", {"class": "speedometerWrapper-kg4MJrFB"})
      summary_technical_data_wrapper = speedometer_containers[1]
      technical_counters_data_wrapper = summary_technical_data_wrapper.findAll("div", {"class": "counterWrapper-kg4MJrFB"})

      technical_number_data = []
      for technical_counter in technical_counters_data_wrapper:
        # Get the number data
        technical_counters_number = technical_counter.find("span", {"class": "counterNumber-kg4MJrFB"})
        technical_number_data.append(technical_counters_number.get_text())
      
      # Insert the data to dictionary
      for idx, enum in enumerate(TECHNICAL_ENUM):
        technical_rating_dict[enum] = int(technical_number_data[idx])
      technical_rating_dict['updated_on'] = (datetime.now()).strftime("%Y-%m-%d %H:%M:%S")
    
    # Scrap technical page
    forecast_url = url+"/forecast/"
    soup_fpage = scrap_page(forecast_url)
    if (soup_fpage is not None):
      analyst_rating_dict = dict()
      # Getting into the data
      analyst_rating_wrap = soup_fpage.find("div", {"class" : "wrap-GNeDL9vy"})
      analyst_value_wrap = analyst_rating_wrap.findAll("div", {"class": "value-GNeDL9vy"})

      analyst_number_data = []
      for analyst_rating_elm in analyst_value_wrap:
        analyst_number_data.append(analyst_rating_elm.get_text())
      
      # Insert the data to dictionary
      for idx, enum in enumerate(ANALYST_ENUM):
          analyst_rating_dict[enum] = int(analyst_number_data[idx])
      analyst_rating_dict['updated_on'] = (datetime.now()).strftime("%Y-%m-%d %H:%M:%S")

    # Wrap up
    result_data['technical_rating'] = technical_rating_dict
    result_data['analyst_rating'] = analyst_rating_dict
    print(result_data)
    return result_data

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

test = ["BBCA", "AMMN", "GOTO"]
for i in test:
  scrap_rating_data(i)