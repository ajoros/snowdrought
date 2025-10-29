import requests
from bs4 import BeautifulSoup
import os
import logging
from datetime import datetime

# Setup logging to include timestamps
logging.basicConfig(
    format='%(asctime)s - %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Define the list of specific locations (HUCs) to filter the CSV files
specific_hucs = [
    "170102", "160300", "170501", "170402", "171100", "140100", "100200", "170200", "180102",
    "140600", "101800", "180201", "180400", "100800", "140401", "160202", "170800", "101900",
    "160201", "170900", "160401", "170701", "170401", "100700", "140500", "170602", "170703",
    "130100", "160600", "160501", "170300", "160102", "130201", "170603", "140200", "170601",
    "190803", "180300", "140801", "170101", "150100", "170702", "171003", "140700", "100301",
    "160502", "160101", "140300", "180200", "190203", "150200", "171200", "110200", "150601",
    "170103", "150602", "170502", "180901", "150400", "160503", "160203", "100902", "130202",
    "100901", "110800", "160402", "190204", "190205", "190201", "100401", "100302", "190202"
]


# Function to download and save CSV files with a specific suffix
def download_csv_files(base_url, download_directory, suffix):
    logging.info(f"Starting download from {base_url}")

    response = requests.get(base_url)
    if response.status_code != 200:
        logging.error(f"Failed to access {base_url}: Status code {response.status_code}")
        return

    html_content = response.text
    soup = BeautifulSoup(html_content, 'html.parser')
    csv_links = [a['href'] for a in soup.find_all('a', href=True) if a['href'].endswith('.csv')]

    # Log the number of CSV links found
    logging.info(f"Found {len(csv_links)} CSV files on the page.")

    # Create the directory if it doesn't exist
    os.makedirs(download_directory, exist_ok=True)

    downloaded_count = 0
    for link in csv_links:
        # Filter based on specific HUCs
        if any(huc in link for huc in specific_hucs):
            huc_number = link.split('/')[-1].split('_')[0]
            logging.info(f"Downloading file for HUC: {huc_number}")

            full_url = os.path.join(base_url, link)
            file_name = link.split('/')[-1].replace('.csv', f'{suffix}.csv')
            output_path = os.path.join(download_directory, file_name)

            # Download the file and log the progress
            try:
                # Fetch the file content
                file_response = requests.get(full_url, stream=True)
                if file_response.status_code == 200:
                    with open(output_path, 'wb') as f:
                        for chunk in file_response.iter_content(chunk_size=1024):
                            f.write(chunk)
                    logging.info(f"Downloaded and overwrote {file_name} in {download_directory}")
                else:
                    logging.error(f"Failed to download {file_name}: Status code {file_response.status_code}")
                downloaded_count += 1
            except Exception as e:
                logging.error(f"Failed to download {file_name}: {str(e)}")

    logging.info(f"Downloaded {downloaded_count} files to {download_directory}")


def main():
    # Get the directory where this script is located
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Download PREC data
    prec_url = "https://nwcc-apps.sc.egov.usda.gov/awdb/basin-plots/POR/PREC/assocHUC6/"
    prec_directory = os.path.join(base_dir, 'data', 'HUC6PREC')
    logging.info("Starting PREC data download.")
    download_csv_files(prec_url, prec_directory, '_p')

    # Download WTEQ data
    wteq_url = "https://nwcc-apps.sc.egov.usda.gov/awdb/basin-plots/POR/WTEQ/assocHUC6/"
    wteq_directory = os.path.join(base_dir, 'data', 'HUC6WTEQ')
    logging.info("Starting WTEQ data download.")
    download_csv_files(wteq_url, wteq_directory, '_swe')

    logging.info("Download completed.")


if __name__ == "__main__":
    main()
