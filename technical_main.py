import os
from dotenv import load_dotenv
import pandas as pd
import numpy as np
import sys
from supabase import create_client
from multiprocessing import Process
import time
from rating_scraper import scrape_technical_function
from rating_combiner import combine_technical_data
import logging
from imp import reload
import datetime

load_dotenv()

# Connection to Supabase
url_supabase = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
supabase = create_client(url_supabase, key)

# Get the table
db_data = supabase.table("idx_key_stats").select("").execute()
df_db_data = pd.DataFrame(db_data.data)

cols = df_db_data.columns.tolist()

# Get symbol data
symbol_list = df_db_data['symbol'].tolist()
symbol_list

# Remove the .JK
for i in range (len(symbol_list)):
  symbol_list[i] = symbol_list[i].replace(".JK", "")

def initiate_logging(LOG_FILENAME):
    reload(logging)

    formatLOG = '%(asctime)s - %(levelname)s: %(message)s'
    logging.basicConfig(filename=LOG_FILENAME,level=logging.INFO, format=formatLOG)
    logging.info('The technical rating scraper program started')
       

if __name__ == "__main__":
    
  # Start time
  start = time.time()
  print("==> START TECHNICAL DATA SCRAPING ")

  # Read running argument
  if (len(sys.argv) == 1 or sys.argv[1] == None):
    frequency = "daily"
  else:
    frequency = sys.argv[1]
    # Should be inputed with [daily, weekly, monthly]

  # length_list = len(symbol_list)
  length_list = 8
  i1 = int(length_list // 4)
  i2 = 2 * i1
  i3 = 3 * i1

  LOG_FILENAME = 'scrapper.log'
  initiate_logging(LOG_FILENAME)

  p1 = Process(target=scrape_technical_function, args=(symbol_list[:i1], 1, frequency))
  # p2 = Process(target=scrape_technical_function, args=(symbol_list[i1:i2], 2, frequency))
  # p3 = Process(target=scrape_technical_function, args=(symbol_list[i2:i3], 3, frequency))
  # p4 = Process(target=scrape_technical_function, args=(symbol_list[i3:], 4, frequency))

  p1.start()
  # p2.start()
  # p3.start()
  # p4.start()

  p1.join()
  # p2.join()
  # p3.join()
  # p4.join()

  # Merge and upsert to db
  df_merge = combine_technical_data(df_db_data, frequency)

  # Convert to json. Remove the index in dataframe
  records = df_merge.to_dict(orient="records")

  # # Upsert to db
  # try:
  #   supabase.table("idx_key_stats").upsert(
  #       records
  #   ).execute()
  #   print(
  #       f"Successfully upserted {len(records)} data to database"
  #   )
  # except Exception as e:
  #   raise Exception(f"Error upserting to database: {e}")
  
  # End time
  end = time.time()
  duration = int(end-start)

  print(f"The execution time: {time.strftime('%H:%M:%S', time.gmtime(duration))}")
  print("==> FINISHED TECHNICAL DATA SCRAPING")

  logging.info(f"{datetime.datetime.now().strftime('%Y-%m-%d')} the {frequency} technical rating data has been scrapped. Execution time: {time.strftime('%H:%M:%S', time.gmtime(duration))}")




