import pandas as pd
import numpy as np
import json
import os
from datetime import datetime, timedelta
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def process_precipitation_data(prec_dir):
    """Process precipitation data from Nov 1 through current date"""
    data = []
    current_year = "2025"  # Water year starts Nov 1, 2025
    next_year = "2026"    # Continues into 2026

    for filename in os.listdir(prec_dir):
        if not filename.endswith('.json'):
            continue

        state_code = filename.split('_')[0]
        station_name = filename.replace('.json', '').replace(f"{state_code}_", '')

        try:
            with open(os.path.join(prec_dir, filename), 'r') as f:
                json_data = json.load(f)

            # Get the Nov 1 value from current water year
            nov1_value = None
            latest_value = None
            latest_date = None

            # First find latest value with valid data
            for entry in reversed(json_data):
                if next_year in entry and entry[next_year] is not None:
                    try:
                        value = float(entry[next_year])
                        if not np.isnan(value):
                            latest_value = value
                            latest_date = entry['date']
                            # Now find the Nov 1 value
                            for e in json_data:
                                if e['date'] == "11-01" and current_year in e and e[current_year] is not None:
                                    try:
                                        nov1_value = float(e[current_year])
                                        break
                                    except (ValueError, TypeError):
                                        continue
                            break
                    except (ValueError, TypeError):
                        continue

            if latest_value is not None and nov1_value is not None:
                # Calculate current accumulation
                current_accum = latest_value - nov1_value

                # Calculate historical accumulations for this time period
                historical_accums = []
                valid_years = set()

                # Get all available years from the data
                available_years = sorted([int(year) for year in json_data[0].keys() 
                                       if year.isdigit() and year not in [current_year, next_year]])
                
                for year in available_years:
                    year_str = str(year)
                    next_year_str = str(year + 1)
                    
                    # Get Nov 1 value for this historical year
                    hist_nov1 = None
                    hist_current_date = None
                    
                    for entry in json_data:
                        if entry['date'] == "11-01" and year_str in entry and entry[year_str] is not None:
                            try:
                                hist_nov1 = float(entry[year_str])
                            except (ValueError, TypeError):
                                continue
                            
                        if entry['date'] == latest_date and next_year_str in entry and entry[next_year_str] is not None:
                            try:
                                hist_current_date = float(entry[next_year_str])
                            except (ValueError, TypeError):
                                continue
                                
                    if hist_nov1 is not None and hist_current_date is not None:
                        hist_accum = hist_current_date - hist_nov1
                        if not np.isnan(hist_accum):
                            historical_accums.append(hist_accum)
                            valid_years.add(year_str)

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

    for filename in os.listdir(swe_dir):
        if not filename.endswith('.json'):
            continue

        state_code = filename.split('_')[0]
        station_name = filename.replace('.json', '').replace(f"{state_code}_", '')

        try:
            with open(os.path.join(swe_dir, filename), 'r') as f:
                json_data = json.load(f)

            # Get current water year (2026 - includes data from Nov 1, 2025 onwards)
            current_year = "2025"  # Water year starts Nov 1, 2025
            next_year = "2026"    # Continues into 2026
            historical_years = []

            # Find latest date with valid data
            latest_valid_date = None
            latest_value = None

            # Check both current and next year for valid data
            for entry in reversed(json_data):
                if (next_year in entry and entry[next_year] is not None) or \
                   (current_year in entry and entry[current_year] is not None):
                    try:
                        value = float(entry[next_year] if next_year in entry else entry[current_year])
                        if not np.isnan(value):
                            latest_valid_date = entry['date']
                            latest_value = value
                            break
                    except (ValueError, TypeError):
                        continue

            if latest_valid_date:
                # Get historical values for percentile calculation
                historical_values = []
                valid_years = set()

                # Find entry for latest valid date
                for entry in json_data:
                    if entry['date'] == latest_valid_date:
                        for year in entry:
                            if year.isdigit() and year != next_year and year != current_year and entry[year] is not None:
                                try:
                                    hist_val = float(entry[year])
                                    if not np.isnan(hist_val):
                                        valid_years.add(year)
                                        historical_values.append(hist_val)
                                except (ValueError, TypeError):
                                    continue

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