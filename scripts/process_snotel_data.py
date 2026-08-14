import pandas as pd
import numpy as np
import json
import os
import sys
import logging

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from water_year import (
    today_pacific,
    water_year_start_end,
    year_column_for_mmdd,
    entry_num,
    latest_in_water_year,
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


def process_precipitation_data(prec_dir):
    """Process precipitation data from Nov 1 through current date"""
    data = []
    today = today_pacific()
    start_year, end_year = water_year_start_end(today)
    start_s, end_s = str(start_year), str(end_year)
    logging.info(f"Water year {start_year}/{end_year} (precip)")

    for filename in os.listdir(prec_dir):
        if not filename.endswith('.json'):
            continue

        state_code = filename.split('_')[0]
        station_name = filename.replace('.json', '').replace(f"{state_code}_", '')

        try:
            with open(os.path.join(prec_dir, filename), 'r') as f:
                json_data = json.load(f)

            latest_date, latest_value = latest_in_water_year(
                json_data, start_year, end_year, today
            )
            nov1_value = None
            for entry in json_data:
                if entry.get("date") == "11-01":
                    nov1_value = entry_num(entry, start_s)
                    if nov1_value is not None:
                        break

            if latest_value is not None and nov1_value is not None:
                current_accum = latest_value - nov1_value
                historical_accums = []
                valid_years = set()
                wy_years = {start_s, end_s}
                available_years = sorted(
                    int(year) for year in json_data[0].keys()
                    if year.isdigit() and year not in wy_years
                )

                for year in available_years:
                    hist_col = year_column_for_mmdd(latest_date, year, year + 1)
                    hist_nov1 = None
                    hist_current_date = None
                    for entry in json_data:
                        if entry.get("date") == "11-01":
                            hist_nov1 = entry_num(entry, str(year))
                        if entry.get("date") == latest_date:
                            hist_current_date = entry_num(entry, hist_col)

                    if hist_nov1 is not None and hist_current_date is not None:
                        hist_accum = hist_current_date - hist_nov1
                        if not np.isnan(hist_accum):
                            historical_accums.append(hist_accum)
                            valid_years.add(str(year))

                if historical_accums and len(valid_years) >= 20:
                    percentile = len([x for x in historical_accums if x <= current_accum]) / len(historical_accums)
                    data.append({
                        'Name': station_name,
                        'State': state_code,
                        'Value': current_accum,
                        'Number_of_Observations_POR': len(valid_years),
                        'Percentile_POR': percentile * 100
                    })

        except Exception as e:
            logging.error(f"Error processing {filename}: {str(e)}")

    return pd.DataFrame(data)


def process_swe_data(swe_dir):
    """Process current SWE data"""
    data = []
    today = today_pacific()
    start_year, end_year = water_year_start_end(today)
    start_s, end_s = str(start_year), str(end_year)
    logging.info(f"Water year {start_year}/{end_year} (SWE)")

    for filename in os.listdir(swe_dir):
        if not filename.endswith('.json'):
            continue

        state_code = filename.split('_')[0]
        station_name = filename.replace('.json', '').replace(f"{state_code}_", '')

        try:
            with open(os.path.join(swe_dir, filename), 'r') as f:
                json_data = json.load(f)

            latest_valid_date, latest_value = latest_in_water_year(
                json_data, start_year, end_year, today
            )

            if latest_valid_date:
                historical_values = []
                valid_years = set()
                wy_years = {start_s, end_s}

                for entry in json_data:
                    if entry.get("date") != latest_valid_date:
                        continue
                    for year in entry:
                        if year.isdigit() and year not in wy_years:
                            hist_val = entry_num(entry, year)
                            if hist_val is not None:
                                valid_years.add(year)
                                historical_values.append(hist_val)

                if historical_values and len(valid_years) >= 20:
                    percentile = len([x for x in historical_values if x <= latest_value]) / len(historical_values)
                    data.append({
                        'Name': station_name,
                        'State': state_code,
                        'Value': latest_value,
                        'Number_of_Observations_POR': len(valid_years),
                        'Percentile_POR': percentile * 100
                    })

        except Exception as e:
            logging.error(f"Error processing {filename}: {str(e)}")

    return pd.DataFrame(data)

def main():
    # Define paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    base_dir = os.path.dirname(script_dir)
    prec_dir = os.path.join(base_dir, 'data', 'snotel', 'prec')
    swe_dir = os.path.join(base_dir, 'data', 'snotel', 'swe')

    # Process data
    logging.info("Processing precipitation data...")
    prec_df = process_precipitation_data(prec_dir)

    logging.info("Processing SWE data...")
    swe_df = process_swe_data(swe_dir)

    # Save processed data
    output_dir = os.path.join(base_dir, 'data')

    prec_df.to_csv(os.path.join(output_dir, 'snotel_100day_nov1_precipitation_percentiles.csv'), index=False)
    swe_df.to_csv(os.path.join(output_dir, 'snotel_current_swe_percentiles.csv'), index=False)

    logging.info("Data processing complete!")
    logging.info(f"Processed {len(prec_df)} precipitation records")
    logging.info(f"Processed {len(swe_df)} SWE records")

if __name__ == "__main__":
    main()