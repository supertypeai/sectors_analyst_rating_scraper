from playwright.sync_api import sync_playwright, Page, Browser, BrowserContext
from bs4 import BeautifulSoup
from datetime import datetime
from requests_html import HTMLSession
import json
import os
import logging
import random

# Scraping data
BASE_URL = 'https://www.tradingview.com/symbols/IDX-'
TECHNICAL_ENUM = ['sell', 'neutral', 'buy']
ANALYST_ENUM = ['strong_buy', 'buy', 'hold', 'sell', 'strong_sell']

# Browser data directory for persistent cookies
BROWSER_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "browser_data")

# Set the logging level for the 'websockets' logger
logging.getLogger('websockets').setLevel(logging.WARNING)

# If you need to configure logging for requests-html as well
logging.getLogger('requests_html').setLevel(logging.WARNING)

# Anti-bot detection settings
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0"
]

def create_stealth_page(browser: Browser) -> Page:
    """Create a page with anti-bot detection settings"""
    context = browser.new_context(
        viewport={"width": 1920, "height": 1080},
        user_agent=random.choice(USER_AGENTS),
        locale="en-US",
        timezone_id="Asia/Jakarta",
        permissions=["geolocation"],
        java_script_enabled=True,
    )
    
    page = context.new_page()
    
    # Add stealth scripts to avoid detection
    page.add_init_script("""
        // Overwrite the 'webdriver' property to hide automation
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
        });
        
        // Overwrite plugins to appear more like a real browser
        Object.defineProperty(navigator, 'plugins', {
            get: () => [1, 2, 3, 4, 5]
        });
        
        // Overwrite languages
        Object.defineProperty(navigator, 'languages', {
            get: () => ['en-US', 'en']
        });
        
        // Add chrome object
        window.chrome = {
            runtime: {}
        };
    """)
    
    return page

def create_persistent_context(playwright, process_idx: int, headless: bool = True) -> BrowserContext:
    """Create a persistent browser context that saves cookies between sessions"""
    # Each process gets its own browser data directory to avoid conflicts
    user_data_dir = os.path.join(BROWSER_DATA_DIR, f"process_{process_idx}")
    
    context = playwright.chromium.launch_persistent_context(
        user_data_dir=user_data_dir,
        headless=headless,
        viewport={"width": 1920, "height": 1080},
        locale="en-US",
        timezone_id="Asia/Jakarta",
        args=[
            '--disable-blink-features=AutomationControlled',
            '--disable-dev-shm-usage',
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-infobars',
        ]
    )
    
    # Add stealth scripts
    context.add_init_script("""
        Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
        Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
        Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });
        window.chrome = { runtime: {} };
    """)
    
    return context

def get_url_page(symbol:str) -> str:
    return f"{BASE_URL}{symbol}"

def scrape_technical_page(page: Page, url: str, frequency : str = "daily") :
    # Frequency = ["daily", "weekly", "monthly"] | default = daily
    print(f"[TECHNICAL] = Opening page {url}")
    try:
      page.goto(url, timeout=60000) # Timeout 60s
      print(f"[TECHNICAL] = Page for {url} is loaded")
      
      html_content = page.content()
      soup = BeautifulSoup(html_content, "html.parser")

      # if (frequency == "weekly"):
      #   print(f"[TECHNICAL] = Getting weekly Data")
      #   script = """
      #     () => {
      #       const items = document.getElementsByClassName("square-tab-button-huvpscfz");
      #       if(items) {
      #         const len = items.length
      #         items[len-1].click()
      #       } 

      #       const popupItems = document.getElementsByClassName("item-jFqVJoPk")
      #       if (popupItems) {
      #         const popupLen = popupItems.length
      #         popupItems[popupLen-2].click()
      #         return
      #       }
      #     }
      #   """
      #   response.html.render(sleep=2, timeout=10, script=script)
      
      # elif (frequency == "monthly"):
      #   print(f"[TECHNICAL] = Getting monthly Data")
      #   script = """
      #     () => {
      #       const items = document.getElementsByClassName("square-tab-button-huvpscfz");
      #       if(items) {
      #         const len = items.length
      #         items[len-1].click()
      #       } 

      #       const popupItems = document.getElementsByClassName("item-jFqVJoPk")
      #       if (popupItems) {
      #         const popupLen = popupItems.length
      #         popupItems[popupLen-1].click()
      #         return
      #       }
      #     }
      #   """
      #   response.html.render(sleep=2, timeout=10, script=script)

      # else : #case frequency == daily

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
            value = cells[i].get_text().replace(",", "").replace("\u2212", "-")
            try:
              value = int(float(value))
            except:
              # Case value is empty (dash (-))
              value = None
            value_list.append(value)
          else: # Action
            action = cells[i].get_text()
            if (len(action) == 1 and action == "—"):
              action = None
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
            value = cells[i].get_text().replace(",", "").replace("\u2212", "-")
            try:
              value = int(float(value))
            except:
              # Case value is empty (dash (-))
              value = None
            value_list.append(value)
          else: # Action
            action = cells[i].get_text()
            if (len(action) == 1 and action == "—"):
              action = None
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
      print(f"[TECHNICAL][FAILED] =  scraping from URL: {url}")
      print(f"[TECHNCIAL][FAILED] = {e}")
      return None

def scrape_forecast_page(page: Page, url: str) :
    print(f"[ANALYST] = Opening page {url}")
    try:
      page.goto(url, timeout=60000) # Timeout 60s
      print(f"[ANALYST] = Page for {url} is loaded")

      # Wait for the page to fully load
      try:
        page.wait_for_load_state("domcontentloaded", timeout=10000)
      except:
        pass
      
      # Scroll down to trigger lazy loading of content
      page.evaluate("window.scrollTo(0, document.body.scrollHeight / 2)")
      page.wait_for_timeout(1000)
      page.evaluate("window.scrollTo(0, 0)")
      page.wait_for_timeout(500)
      
      # Wait for network to be idle (all requests done)
      try:
        page.wait_for_load_state("networkidle", timeout=3000)
      except:
        pass
      
      # Wait specifically for the analyst rating section
      # Try multiple selectors
      analyst_section_found = False
      selectors_to_try = [
        "text=Strong buy",
        "text=Analyst rating", 
        "[class*='value-'][class*='GNeDL9vy']"
      ]
      
      for selector in selectors_to_try:
        try:
          page.wait_for_selector(selector, timeout=5000)
          analyst_section_found = True
          print(f"[ANALYST] = Found element with selector: {selector}")
          break
        except:
          continue
      
      if not analyst_section_found:
        print(f"[ANALYST] = Analyst section not found for {url}, waiting longer...")
        page.wait_for_timeout(3000)
      
      # Additional delay to ensure rendering is complete
      page.wait_for_timeout(1500)

      # Store the HTML content
      html_content = page.content()
      soup = BeautifulSoup(html_content, "html.parser")

      if (soup is not None):
        analyst_rating_dict = dict()

        # # Strategy 1: Find value divs with the specific class pattern
        # analyst_value_wrap = soup.findAll("div", {"class": lambda x: x and "value-" in str(x) and "GNeDL9vy" in str(x)})
        
        # # Strategy 2: If not found, try broader search for value divs
        # if not analyst_value_wrap or len(analyst_value_wrap) < len(ANALYST_ENUM):
        #   # Find all divs, check class as string
        #   all_divs = soup.findAll("div")
        #   analyst_value_wrap = []
        #   for div in all_divs:
        #     class_attr = div.get("class", [])
        #     class_str = " ".join(class_attr) if class_attr else ""
        #     if "value-" in class_str:
        #       # Check if this div contains just a number
        #       text = div.get_text().strip()
        #       if text.isdigit():
        #         analyst_value_wrap.append(div)
        
        # # Strategy 3: Find by parent structure - look for "Strong buy" text
        # if not analyst_value_wrap or len(analyst_value_wrap) < len(ANALYST_ENUM):
        #   strong_buy_elem = soup.find(string=lambda t: t and "Strong buy" in str(t))
        #   if strong_buy_elem:
        #     # Go up to find container
        #     parent = strong_buy_elem.find_parent()
        #     for _ in range(6):
        #       if parent and parent.parent:
        #         parent = parent.parent
        #         # Check if this parent contains all rating labels
        #         text = parent.get_text()
        #         if all(label in text for label in ["Strong buy", "Hold", "Strong sell"]):
        #           # Found the container, now find numeric values
        #           candidate_divs = parent.findAll("div")
        #           analyst_value_wrap = []
        #           for div in candidate_divs:
        #             div_text = div.get_text().strip()
        #             if div_text.isdigit() and len(div.findAll()) == 0:  # Leaf div with number
        #               analyst_value_wrap.append(div)
        #           if len(analyst_value_wrap) >= 5:
        #             # Take only first 5 (the rating numbers)
        #             analyst_value_wrap = analyst_value_wrap[:5]
        #             break
        
        # if not analyst_value_wrap or len(analyst_value_wrap) < len(ANALYST_ENUM):
        #   print(f"[ANALYST] = No analyst data for {url} (found {len(analyst_value_wrap) if analyst_value_wrap else 0} values)")
        #   return None

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
      print(f"[ANALYST][FAILED] = Fail scraping from URL: {url}")
      print(f"[ANALYST][FAILED] = {e}")
      return None    

def save_to_json(file_path, data):
  with open(file_path, "w") as output_file:
    json.dump(data, output_file, indent=2)

def scrape_technical_rating_data(page: Page, symbol: str, frequency: str) -> dict:
    url = get_url_page(symbol)
    technical_url = f"{url}/technicals/"
    
    technical_rating_dict = None
    attempt = 1
    while technical_rating_dict is None and attempt <= 3:
      technical_rating_dict = scrape_technical_page(page, technical_url, frequency)
      if technical_rating_dict is None:
        print(f"Failed to get technical rating data for {symbol} on attempt {attempt}. Retrying...")
      attempt += 1
      
    return {'symbol': symbol, 'technical_rating': technical_rating_dict}

def scrape_analyst_rating_data(page: Page, symbol: str) -> dict:
    url = get_url_page(symbol)
    forecast_url = f"{url}/forecast/"
    
    analyst_rating_dict = scrape_forecast_page(page, forecast_url)
      
    return {'symbol': symbol, 'analyst_rating': analyst_rating_dict}

def scrape_technical_function(symbol_list, process_idx, frequency):
  print(f"==> Start scraping from process P{process_idx}")
  all_data = []
  # Playwright with persistent context (saves cookies)
  with sync_playwright() as p:
    # Use persistent context to maintain cookies across sessions
    context = create_persistent_context(p, process_idx, headless=True)
    page = context.pages[0] if context.pages else context.new_page()

    try:
      # Iterate in symbol list
      for i, symbol in enumerate(symbol_list):
        scrapped_data = scrape_technical_rating_data(page, symbol, frequency)
        all_data.append(scrapped_data)

        if (i > 0 and i % 10 == 0):
          print(f"CHECKPOINT || P{process_idx} {i} Data")
        
        # Random delay to appear more human-like
        page.wait_for_timeout(random.randint(1000, 2500))
    
    finally:
      context.close()
      print(f"==> Browser for P{process_idx} closed.")

  cwd = os.getcwd()
  filename = f"P{process_idx}_technical_data_{frequency}.json"
  print(f"==> Finished data is exported in {filename}")
  file_path = os.path.join(cwd, "data", filename)
  save_to_json(file_path, all_data)
  return all_data

def scrape_analyst_function(symbol_list, process_idx):
  print(f"==> Start scraping from process P{process_idx}")
  all_data = []
  # Playwright with persistent context (saves cookies)
  with sync_playwright() as p:
    # Use persistent context to maintain cookies across sessions
    context = create_persistent_context(p, process_idx, headless=False)
    page = context.pages[0] if context.pages else context.new_page()

    try:
      # Iterate in symbol list
      for i, symbol in enumerate(symbol_list):
        scrapped_data = scrape_analyst_rating_data(page, symbol)
        all_data.append(scrapped_data)

        if (i > 0 and i % 10 == 0):
          print(f"CHECKPOINT || P{process_idx} {i} Data")
        
        # Random delay to appear more human-like
        page.wait_for_timeout(random.randint(1000, 2500))
    
    finally:
      context.close()
      print(f"==> Browser for P{process_idx} closed.")
  
  cwd = os.getcwd()
  filename = f"P{process_idx}_analyst_data.json"
  print(f"==> Finished data is exported in {filename}")
  file_path = os.path.join(cwd, "data", filename)
  save_to_json(file_path, all_data)
  return all_data


