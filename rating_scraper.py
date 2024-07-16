from urllib.request import urlopen
from bs4 import BeautifulSoup
from datetime import datetime
from requests_html import HTMLSession
import json
import os
import logging

# Scraping data
BASE_URL = 'https://www.tradingview.com/symbols/IDX-'
TECHNICAL_ENUM = ['sell', 'neutral', 'buy']
ANALYST_ENUM = ['strong_buy', 'buy', 'hold', 'sell', 'strong_sell']

# Set the logging level for the 'websockets' logger
logging.getLogger('websockets').setLevel(logging.WARNING)

# If you need to configure logging for requests-html as well
logging.getLogger('requests_html').setLevel(logging.WARNING)

def get_url_page(symbol:str) -> str:
    return f"{BASE_URL}{symbol}"

def scrape_technical_page(url: str, frequency : str = "daily") :
    # Frequency = ["hourly", "daily", "weekly", "monthly"] | default = daily
    print(f"[TECHNICAL] = Opening page {url}")
    try:
      session = HTMLSession()
      response = session.get(url)

      if (frequency == "hourly"):
        print(f"[TECHNICAL] = Getting hourly Data")
        script = """
          () => {
            const item = document.getElementById("1h");
            if(item) {
              item.click()
            }
          }
        """
        response.html.render(sleep=1, timeout=10, script=script)
      
      elif (frequency == "weekly"):
        print(f"[TECHNICAL] = Getting weekly Data")
        script = """
          () => {
            const item = document.getElementById("1W");
            if(item) {
              item.click()
            }
          }
        """
        response.html.render(sleep=1, timeout=10, script=script)
      
      elif (frequency == "monthly"):
        print(f"[TECHNICAL] = Getting monthly Data")
        script = """
          () => {
            const item = document.getElementById("1M");
            if(item) {
              item.click()
              return item.innerHTML
            } 
          }
        """
        test = response.html.render(sleep=1, timeout=15, script=script)
        print(test)

      else : #case frequency == daily
        print(f"[TECHNICAL] = Getting daily Data")
        response.html.render(sleep=1, timeout=10)
      
      print(f"[TECHNICAL] = Session for {url} is opened")

      soup = BeautifulSoup(response.html.html, "html.parser")
      if (soup is not None):
        technical_rating_dict = dict()

        # Getting into the data
        speedometer_containers = soup.findAll("div", {"class": "speedometerWrapper-kg4MJrFB"})


        # Get Summary data
        summary_dict = dict()
        summary_technical_data_wrapper = speedometer_containers[1]
        technical_counters_data_wrapper = summary_technical_data_wrapper.findAll("div", {"class": "counterWrapper-kg4MJrFB"})

        technical_number_data = []
        for technical_counter in technical_counters_data_wrapper:
          # Get the number data
          technical_counters_number = technical_counter.find("span", {"class": "counterNumber-kg4MJrFB"})
          technical_number_data.append(technical_counters_number.get_text())
        
        # Insert the data to dictionary
        for idx, enum in enumerate(TECHNICAL_ENUM):
          summary_dict[enum] = int(technical_number_data[idx])
        summary_dict['updated_on'] = (datetime.now()).strftime("%Y-%m-%d %H:%M:%S")
        technical_rating_dict['summary'] = summary_dict


        # Get Oscillator data
        oscillator_dict = dict()
        oscillator_technical_data_wrapper = speedometer_containers[0]
        technical_counters_data_wrapper = oscillator_technical_data_wrapper.findAll("div", {"class": "counterWrapper-kg4MJrFB"})

        technical_number_data = []
        for technical_counter in technical_counters_data_wrapper:
          # Get the number data
          technical_counters_number = technical_counter.find("span", {"class": "counterNumber-kg4MJrFB"})
          technical_number_data.append(technical_counters_number.get_text())
        
        # Insert the data to dictionary
        for idx, enum in enumerate(TECHNICAL_ENUM):
          oscillator_dict[enum] = int(technical_number_data[idx])
        oscillator_dict['updated_on'] = (datetime.now()).strftime("%Y-%m-%d %H:%M:%S")
        technical_rating_dict['oscillator'] = oscillator_dict


        # Get Moving Averages data
        move_avg_dict = dict()
        move_avg_technical_data_wrapper = speedometer_containers[2]
        technical_counters_data_wrapper = move_avg_technical_data_wrapper.findAll("div", {"class": "counterWrapper-kg4MJrFB"})

        technical_number_data = []
        for technical_counter in technical_counters_data_wrapper:
          # Get the number data
          technical_counters_number = technical_counter.find("span", {"class": "counterNumber-kg4MJrFB"})
          technical_number_data.append(technical_counters_number.get_text())
        
        # Insert the data to dictionary
        for idx, enum in enumerate(TECHNICAL_ENUM):
          move_avg_dict[enum] = int(technical_number_data[idx])
        move_avg_dict['updated_on'] = (datetime.now()).strftime("%Y-%m-%d %H:%M:%S")
        technical_rating_dict['moving_average'] = move_avg_dict


        # Get Table data
        table_containers = soup.findAll("div", {"class" : "container-hvDpy38G"})
        oscillator_table = table_containers[0]
        move_avg_table = table_containers[1]

        # Oscillator table
        cells = oscillator_table.findAll("td", {"class" : "cell-hvDpy38G"})
        name_list = list()
        value_list = list()
        action_list = list()
        for i in range (len(cells)):
          if (i % 3 == 0): # Name
            name = cells[i].get_text()
            name_list.append(name)
          elif (i % 3 == 1) : # Value
            value = int(cells[i].get_text().replace(",", "").replace("\u2212", "-"))
            value_list.append(value)
          else: # Action
            action = cells[i].get_text()
            action_list.append(action)
        
        data = list()
        for i in range(len(name_list)): # All list should have the same length
          cell_data = {
            "name" : name_list[i],
            "value" : value_list[i],
            "action" : action_list[i]
          }
          data.append(cell_data)
        technical_rating_dict['oscillator']['data'] = data

        # Moving Average table
        cells = move_avg_table.findAll("td", {"class" : "cell-hvDpy38G"})
        name_list = list()
        value_list = list()
        action_list = list()
        for i in range (len(cells)):
          if (i % 3 == 0): # Name
            name = cells[i].get_text()
            name_list.append(name)
          elif (i % 3 == 1) : # Value
            value = int(cells[i].get_text().replace(",", "").replace("\u2212", "-"))
            value_list.append(value)
          else: # Action
            action = cells[i].get_text()
            action_list.append(action)
        
        data = list()
        for i in range(len(name_list)): # All list should have the same length
          cell_data = {
            "name" : name_list[i],
            "value" : value_list[i],
            "action" : action_list[i]
          }
          data.append(cell_data)
        technical_rating_dict['moving_average']['data'] = data


        print(f"[TECHNICAL] = Successfully scrape from {url}")
        return technical_rating_dict
      else:
        print(f"[TECHNICAL] = None HTML Value for {url}")
        return None
    except Exception as e:
      print(f"[TECHNICAL] = Fail scraping from URL: {url}")
      print(f"[TECHNCIAL] = {e}")
      return None
    finally:
      session.close()
      print(f"[TECHNICAL] = Session for {url} is closed")
    
def scrape_forecast_page(url: str) :
    print(f"[ANALYST] = Opening page {url}")
    try:
      session = HTMLSession()
      response = session.get(url)
      response.html.render(sleep=1, timeout=10)
      print(f"[ANALYST] = Session for {url} is opened")

      soup = BeautifulSoup(response.html.html, "html.parser")
      if (soup is not None):
        analyst_rating_dict = dict()

        # Getting into the data
        analyst_rating_wrap = soup.find("div", {"class" : "wrap-GNeDL9vy"})
        analyst_value_wrap = analyst_rating_wrap.findAll("div", {"class": "value-GNeDL9vy"})

        analyst_number_data = []
        for analyst_rating_elm in analyst_value_wrap:
          analyst_number_data.append(analyst_rating_elm.get_text())
        
        # Insert the data to dictionary
        for idx, enum in enumerate(ANALYST_ENUM):
            analyst_rating_dict[enum] = int(analyst_number_data[idx])

        # Calculate Analyst Rating
        n_analyst = 0
        for number_data in analyst_number_data:
          n_analyst += int(number_data)
        
        analyst_rating_dict['n_analyst'] = n_analyst
        analyst_rating_dict['updated_on'] = (datetime.now()).strftime("%Y-%m-%d %H:%M:%S")

        print(f"[ANALYST] = Successfully scrape from {url}")
        return analyst_rating_dict
      else:
        print(f"[ANALYST] = None HTML Value for {url}")
        return None
    except Exception as e:
      print(f"[ANALYST] = Fail scraping from URL: {url}")
      print(f"[ANALYST] = {e}")
      return None
    finally:
      session.close()
      print(f"[ANALYST] = Session for {url} is closed")
    

def save_to_json(file_path, data):
  with open(file_path, "w") as output_file:
    json.dump(data, output_file, indent=2)

def scrape_technical_rating_data(symbol: str, frequency: str) -> dict:
    url = get_url_page(symbol)
    result_data = dict()
    result_data['symbol'] = symbol
    technical_rating_dict = None

    # Scrape technical page
    technical_url = url+"/technicals/"
    technical_rating_dict = scrape_technical_page(technical_url, frequency)

    # Wrap up
    result_data['technical_rating'] = technical_rating_dict

    return result_data

def scrape_analyst_rating_data(symbol: str) -> dict:
    url = get_url_page(symbol)
    result_data = dict()
    result_data['symbol'] = symbol
    analyst_rating_dict = None

    # Scrape forecast page
    forecast_url = url+"/forecast/"
    analyst_rating_dict = scrape_forecast_page(forecast_url)

    # Wrap up
    result_data['analyst_rating'] = analyst_rating_dict

    return result_data

def scrape_technical_function(symbol_list, process_idx, frequency):
  print(f"==> Start scraping from process P{process_idx}")
  all_data = []
  cwd = os.getcwd()
  start_idx = 0
  count = 0

  # Iterate in symbol list
  for i in range(start_idx, len(symbol_list)):
    symbol = symbol_list[i]
    scrapped_data = scrape_technical_rating_data(symbol, frequency)
    all_data.append(scrapped_data)

    if (i % 10 == 0 and count != 0):
      print(f"CHECKPOINT || P{process_idx} {i} Data")
    count += 1

  # Save last
  filename = f"P{process_idx}_technical_data_{frequency}.json"
  print(f"==> Finished data is exported in {filename}")
  file_path = os.path.join(cwd, "data", filename)
  save_to_json(file_path, all_data)

  return all_data

def scrape_analyst_function(symbol_list, process_idx):
  print(f"==> Start scraping from process P{process_idx}")
  all_data = []
  cwd = os.getcwd()
  start_idx = 0
  count = 0

  # Iterate in symbol list
  for i in range(start_idx, len(symbol_list)):
    symbol = symbol_list[i]
    scrapped_data = scrape_analyst_rating_data(symbol)
    all_data.append(scrapped_data)

    if (i % 10 == 0 and count != 0):
      print(f"CHECKPOINT || P{process_idx} {i} Data")
    count += 1

  # Save last
  filename = f"P{process_idx}_analyst_data.json"
  print(f"==> Finished data is exported in {filename}")
  file_path = os.path.join(cwd, "data", filename)
  save_to_json(file_path, all_data)

  return all_data


# print(scrape_technical_page("https://www.tradingview.com/symbols/IDX-AMMN/technicals/", "hourly"))
# print(scrape_technical_page("https://www.tradingview.com/symbols/IDX-AMMN/technicals/", "daily"))
# print(scrape_technical_page("https://www.tradingview.com/symbols/IDX-AMMN/technicals/", "weekly"))
# print(scrape_technical_page("https://www.tradingview.com/symbols/IDX-AMMN/technicals/", "monthly"))
