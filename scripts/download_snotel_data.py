import requests
import pandas as pd
import json
import os
import logging
from datetime import datetime
from time import time
from bs4 import BeautifulSoup
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S'
)

# State name to abbreviation mapping
STATE_ABBREV = {
    'Alaska': 'AK',
    'Arizona': 'AZ',
    'California': 'CA',
    'Colorado': 'CO',
    'Idaho': 'ID',
    'Montana': 'MT',
    'Nevada': 'NV',
    'New Mexico': 'NM',
    'Oregon': 'OR',
    'South Dakota': 'SD',
    'Utah': 'UT',
    'Washington': 'WA',
    'Wyoming': 'WY'
}

def verify_json_url(session, url):
    try:
        response = session.head(url)
        return response.status_code == 200
    except:
        return False

def get_json_availability(session, station_name, state):
    """Check if both PREC and WTEQ JSON files exist for a station"""
    state_code = STATE_ABBREV.get(state, state)
    encoded_name = urllib.parse.quote(station_name)

    prec_url = f"https://nwcc-apps.sc.egov.usda.gov/awdb/site-plots/POR/PREC/{state_code}/{encoded_name}.json"
    wteq_url = f"https://nwcc-apps.sc.egov.usda.gov/awdb/site-plots/POR/WTEQ/{state_code}/{encoded_name}.json"

    prec_exists = verify_json_url(session, prec_url)
    wteq_exists = verify_json_url(session, wteq_url)

    return {
        'station': station_name,
        'state': state_code,
        'prec_exists': prec_exists,
        'wteq_exists': wteq_exists,
        'both_exist': prec_exists and wteq_exists,
        'prec_url': prec_url if prec_exists else None,
        'wteq_url': wteq_url if wteq_exists else None
    }

def download_and_save_json(session, url, output_path):
    """Download and save JSON data"""
    try:
        response = session.get(url, timeout=10)
        response.raise_for_status()
        with open(output_path, 'wb') as f:
            f.write(response.content)
        return True
    except Exception as e:
        logging.error(f"Error downloading {url}: {str(e)}")
        return False

def get_directory_listings(state_code):
    """Get list of available stations from PREC and WTEQ directories"""
    prec_url = f"https://nwcc-apps.sc.egov.usda.gov/awdb/site-plots/POR/PREC/{state_code}/"
    wteq_url = f"https://nwcc-apps.sc.egov.usda.gov/awdb/site-plots/POR/WTEQ/{state_code}/"
    
    prec_response = requests.get(prec_url)
    wteq_response = requests.get(wteq_url)
    
    prec_stations = []
    wteq_stations = []
    
    if prec_response.status_code == 200:
        prec_soup = BeautifulSoup(prec_response.text, 'html.parser')
        prec_stations = [link.text.replace('.json', '') for link in prec_soup.find_all('a') if link.text.endswith('.json')]
        
    if wteq_response.status_code == 200:
        wteq_soup = BeautifulSoup(wteq_response.text, 'html.parser')
        wteq_stations = [link.text.replace('.json', '') for link in wteq_soup.find_all('a') if link.text.endswith('.json')]
        
    return prec_stations, wteq_stations

def main():
    total_start_time = time()
    logging.info("Starting SNOTEL data verification")

    # Read station list for all states
    # Get the project root directory (parent of scripts/)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    base_dir = os.path.dirname(script_dir)
    stations_df = pd.read_csv(os.path.join(base_dir, 'data', 'snotel_station_list.csv'))
    # Filter for states we're interested in
    stations_df = stations_df[stations_df['State'].isin(STATE_ABBREV.keys())]
    station_list = list(zip(stations_df['Name'].str.strip(), stations_df['State']))

    logging.info(f"Processing {len(station_list)} stations across {len(stations_df['State'].unique())} states")

    # Process each state
    all_prec_stations = []
    all_wteq_stations = []
    for state in stations_df['State'].unique():
        state_code = STATE_ABBREV[state]
        prec_stations, wteq_stations = get_directory_listings(state_code)
        all_prec_stations.extend(prec_stations)
        all_wteq_stations.extend(wteq_stations)
    
    logging.info(f"Found {len(all_prec_stations)} total stations in PREC directories")
    logging.info(f"Found {len(all_wteq_stations)} total stations in WTEQ directories")
    
    # Show stations that exist in one directory but not the other
    prec_only = set(all_prec_stations) - set(all_wteq_stations)
    wteq_only = set(all_wteq_stations) - set(all_prec_stations)
    
    if prec_only:
        logging.warning("Stations only in PREC directory:")
        for station in prec_only:
            logging.warning(f"- {station}")
            
    if wteq_only:
        logging.warning("Stations only in WTEQ directory:")
        for station in wteq_only:
            logging.warning(f"- {station}")

    # Verify JSON availability for all stations
    exist_list = []
    dont_exist_list = []

    # Create a session for connection pooling
    session = requests.Session()
    session.headers.update({'User-Agent': 'Mozilla/5.0'})
    
    # Process stations in batches
    batch_size = 5
    for i in range(0, len(station_list), batch_size):
        batch = station_list[i:i + batch_size]
        for station_name, state in batch:
            availability = get_json_availability(session, station_name, state)
            if availability['both_exist']:
                exist_list.append(availability)
                logging.info(f"Found both JSONs for {station_name} ({availability['state']})")
            else:
                dont_exist_list.append(availability)
            if availability['prec_exists']:
                logging.warning(f"Only PREC JSON exists for {station_name} ({availability['state']})")
                logging.warning(f"PREC URL: {availability['prec_url']}")
                logging.warning(f"Missing WTEQ URL: {availability['wteq_url']}")
            elif availability['wteq_exists']:
                logging.warning(f"Only WTEQ JSON exists for {station_name} ({availability['state']})")
                logging.warning(f"WTEQ URL: {availability['wteq_url']}")
                logging.warning(f"Missing PREC URL: {availability['prec_url']}")
            else:
                logging.warning(f"No JSONs found for {station_name} ({availability['state']})")
                logging.warning(f"Attempted PREC URL: {availability['prec_url']}")
                logging.warning(f"Attempted WTEQ URL: {availability['wteq_url']}")

    # Download verified JSONs
    logging.info(f"\nFound {len(exist_list)} stations with both JSONs available")
    logging.info(f"Found {len(dont_exist_list)} stations with missing JSONs")

    # Create directories if they don't exist
    os.makedirs('data/snotel/prec', exist_ok=True)
    os.makedirs('data/snotel/swe', exist_ok=True)

    # Prepare download tasks
    download_tasks = []
    for station in exist_list:
        state_code = station['state']
        station_name = station['station']
        
        # Add PREC and WTEQ download tasks
        prec_output = f"data/snotel/prec/{state_code}_{station_name}.json"
        wteq_output = f"data/snotel/swe/{state_code}_{station_name}.json"
        
        download_tasks.append((station['prec_url'], prec_output, f"PREC for {station_name}"))
        download_tasks.append((station['wteq_url'], wteq_output, f"WTEQ for {station_name}"))

    # Download files concurrently using ThreadPoolExecutor with optimized settings
    successful_downloads = 0
    with ThreadPoolExecutor(max_workers=20) as executor:
        # Process downloads in smaller batches
        batch_size = 10
        for i in range(0, len(download_tasks), batch_size):
            batch = download_tasks[i:i + batch_size]
            futures = [executor.submit(download_and_save_json, session, url, output_path) 
                      for url, output_path, _ in batch]
            
            for future, task in zip(as_completed(futures), batch):
                if future.result():
                    successful_downloads += 1
                    logging.info(f"Downloaded {task[2]}")

    total_elapsed = time() - total_start_time
    logging.info(f"\nVerification and download completed. Total time: {total_elapsed:.2f} seconds")
    logging.info(f"Successfully processed {len(exist_list)} stations")

if __name__ == "__main__":
    main()