import warnings
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os
from scipy import stats
import datetime as dt
import matplotlib as mpl
import logging
from time import time

# Setup logging to include timestamps
logging.basicConfig(
    format='%(asctime)s - %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Suppress specific warnings from matplotlib about missing fonts
with warnings.catch_warnings():
    warnings.simplefilter("ignore", category=UserWarning)
    mpl.rcParams['font.size'] = 24

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

# Get base directory (project root)
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Set directories - updated for GitHub Actions
prec_directory = os.path.join(base_dir, 'data', 'HUC6PREC')
wteq_directory = os.path.join(base_dir, 'data', 'HUC6WTEQ')
output_directory = os.path.join(base_dir, 'plots', 'phase_diagrams')
os.makedirs(output_directory, exist_ok=True)
threshold_size = 3 * 1024  # 3KB

# Function to check if the file size is above the threshold
def check_csv_file_size(file_path):
    return os.path.getsize(file_path) > threshold_size

# Function to generate plot
def generate_plot(wteq_file_path, prec_file_path, output_path):
    logging.info(f"Starting plot generation for {output_path}")
    start_time = time()

    # Read data
    swedata = pd.read_csv(wteq_file_path)
    pdata = pd.read_csv(prec_file_path)

    # Dropping unnecessary columns
    def filter_columns(df):
        cols_to_keep = [col for col in df.columns if col.isdigit() or col in ['Min', '10%', '30%', '70%', '90%', 'Max']]
        return df[cols_to_keep]

    swedata = filter_columns(swedata)
    pdata = filter_columns(pdata)

    # Find common years between the two dataframes
    swe_years = set(swedata.columns).intersection([str(year) for year in range(1900, 2100)])  # Assuming years are between 1900 and 2100
    p_years = set(pdata.columns).intersection([str(year) for year in range(1900, 2100)])
    common_years = sorted(swe_years.intersection(p_years), key=int)

    # Ensure presence of necessary columns and keep only the common years
    swe_cols_to_keep = ['Min', '10%', '30%', '70%', '90%', 'Max'] + common_years
    swe_cols_to_keep = [col for col in swe_cols_to_keep if col in swedata.columns]
    pdata_cols_to_keep = ['Min', '10%', '30%', '70%', '90%', 'Max'] + common_years
    pdata_cols_to_keep = [col for col in pdata_cols_to_keep if col in pdata.columns]

    swedata = swedata[swe_cols_to_keep]
    pdata = pdata[pdata_cols_to_keep]

    # Start ppt accumulation from Nov 1
    nov_1_row = 31
    pdata.iloc[:nov_1_row] = np.nan

    # Adjust precipitation data by subtracting value at row 31
    cols = pdata.columns
    for col in cols:
        pdata[col] = pdata[col] - pdata[col].iloc[nov_1_row]

    # Create daily percentile arrays but use a 3-day centered window
    swe_ptile = np.full(swedata.shape, np.nan)
    p_ptile = np.full(pdata.shape, np.nan)

    for idx in range(len(pdata) - 2):
        swe_data = swedata.iloc[idx:idx+3].values.astype(float)
        swe_ravel = swe_data.ravel()
        swe_locs = np.argwhere(~np.isnan(swe_ravel)).flatten()
        swe_ranks = stats.rankdata(swe_ravel[swe_locs], 'min') / len(swe_ravel[swe_locs])
        swe_ranks_all = np.full(swe_ravel.shape, np.nan)
        swe_ranks_all[swe_locs] = swe_ranks
        swe_ptile[idx+1, :] = swe_ranks_all.reshape(swe_data.shape)[1, :]

        p_data = pdata.iloc[idx:idx+3].values.astype(float)
        p_ravel = p_data.ravel()
        p_locs = np.argwhere(~np.isnan(p_ravel)).flatten()
        p_ranks = stats.rankdata(p_ravel[p_locs], 'min') / len(p_ravel[p_locs])
        p_ranks_all = np.full(p_ravel.shape, np.nan)
        p_ranks_all[p_locs] = p_ranks
        p_ptile[idx+1, :] = p_ranks_all.reshape(p_data.shape)[1, :]

    # Determine the latest year column based on numeric column names
    latest_year_column = common_years[-1]
    yearidx = pdata.columns.get_loc(latest_year_column)

    # Define current date
    today = dt.date.today()
    end_date = today

    # Calculate the number of days from Nov 1 to the end date
    nov_1_date = dt.date(today.year - 1, 11, 1)
    days_from_nov_1 = (end_date - nov_1_date).days

    # Define the end row while ensuring it doesn't exceed data length
    start_row = nov_1_row
    end_row = min(nov_1_row + days_from_nov_1, len(swe_ptile))

    # Find last valid data point
    last_valid_idx = min(end_row-1, len(swe_ptile)-1)
    while last_valid_idx >= start_row and (np.isnan(p_ptile[last_valid_idx, yearidx]) or np.isnan(swe_ptile[last_valid_idx, yearidx])):
        last_valid_idx -= 1

    # Calculate the date and percentiles for the last valid point
    last_date = nov_1_date + dt.timedelta(days=last_valid_idx-nov_1_row)
    last_date_str = last_date.strftime('%Y-%m-%d')
    last_swe_ptile = swe_ptile[last_valid_idx, yearidx] * 100
    last_p_ptile = p_ptile[last_valid_idx, yearidx] * 100

    # Create text string for the annotation
    text_str = f'Last Date: {last_date_str}\\nSWE: {last_swe_ptile:.1f}%\\nPrecip: {last_p_ptile:.1f}%'

    # Plotting section
    fig = plt.figure(figsize=(16, 16))
    ax = fig.add_subplot(111)

    ax.set_title(f'{base_name} Water Year 25/26\n{last_date_str}  SWE: {last_swe_ptile:.1f}%  Precip: {last_p_ptile:.1f}%', fontsize=25)
    ax.set_ylim(0, 1)
    ax.set_xlim(0, 1)
    ax.axvline(x=0.50, color='k')
    ax.axhline(y=0.30, color='gold', linewidth=6, label='D0')
    ax.axhline(y=0.20, color='peru', linewidth=6, label='D1')
    ax.axhline(y=0.10, color='orange', linewidth=6, label='D2')
    ax.axhline(y=0.05, color='tab:red', linewidth=6, label='D3')
    ax.axhline(y=0.02, color='darkred', linewidth=6, label='D4')
    ax.axhline(y=0.50, color='k')

    # Define the plotting range from Nov 1 to the end date
    start_row = nov_1_row
    end_row = nov_1_row + days_from_nov_1

    # Color palette for months
    color_palette = ['#6B8FAE', '#CF9652', '#9BBB5A', '#D2ADC1', '#DBDB9B', '#A1C9F4', '#FF9F9B']

    # Month names and corresponding end rows
    month_names = ['Nov', 'Dec', 'Jan', 'Feb', 'Mar', 'Apr', 'May']
    month_end_rows = [61, 92, 123, 152, 183, 213, 244]

    # Get current month index (0-based, where 0 is November)
    current_month = last_date.month
    if current_month >= 11:  # November or December
        month_index = current_month - 11  # 0 for Nov, 1 for Dec
    else:  # January through May
        month_index = current_month + 1  # 2 for Jan, 3 for Feb, etc.
    
    # Ensure we don't exceed May (index 6)
    month_index = min(month_index, 6)

    # Plot only up to current month
    marker_size = 15
    line_width = 1.5
    for i, (month, color) in enumerate(zip(month_names[:month_index + 1], color_palette[:month_index + 1])):
        if i == 0:
            start = start_row + 1  # Start at day 1 instead of day 0
        else:
            start = month_end_rows[i-1]
        end = month_end_rows[i]
        if start < end_row <= end:
            end = end_row
        ax.plot(p_ptile[start:end, yearidx], swe_ptile[start:end, yearidx], '-o', color='black', mfc=color, label=month, markersize=marker_size, linewidth=line_width, markeredgecolor='k')

        # Add this line to connect between months
        if i > 0 and start < end_row:
            ax.plot([p_ptile[start-1, yearidx], p_ptile[start, yearidx]],
                    [swe_ptile[start-1, yearidx], swe_ptile[start, yearidx]], '-k', linewidth=line_width)

    # Plot start point and end point - start at day 1 instead of day 0
    ax.plot(p_ptile[start_row + 1, yearidx], swe_ptile[start_row + 1, yearidx], 'X', color='black', mfc='white', label='Start', markersize=marker_size * 1.5, linewidth=line_width, markeredgecolor='k')
    # Always plot the end point star at the last valid data point
    last_valid_idx = min(end_row-1, len(p_ptile)-1)  # Ensure we don't go beyond array bounds
    while last_valid_idx >= start_row and (np.isnan(p_ptile[last_valid_idx, yearidx]) or np.isnan(swe_ptile[last_valid_idx, yearidx])):
        last_valid_idx -= 1
    if last_valid_idx >= start_row:
        ax.plot(p_ptile[last_valid_idx, yearidx], swe_ptile[last_valid_idx, yearidx], '*', color='black', mfc='white', label='End', markersize=marker_size * 2, linewidth=line_width, markeredgecolor='k')
    

    # Add text box with date and percentiles
    # text_str = f'Last Date: {last_date_str}\\nSWE: {last_swe_ptile:.1f}%\\nPrecip: {last_p_ptile:.1f}%'
    # ax.text(0.02, 0.98, text_str, transform=ax.transAxes, 
    #         bbox=dict(facecolor='white', alpha=0.8, edgecolor='none'),
    #         verticalalignment='top', fontsize=20)
    
    # Place the legend in the top right and make it three columns
    ax.legend(loc='best', ncol=3)
    ax.set_xlim(0, 0.95)
    ax.set_ylim(0, 0.95)

    ax.set_ylabel('Snow Water Equivalent Percentile')
    ax.set_xlabel('Accumulated Precipitation Percentile')
    ax.set_yticks(np.arange(0, 101, 10) / 100)  # Divide by 100 for 0-1 scale
    ax.set_yticklabels(np.arange(0, 101, 10).astype(int))  # Show 0, 10, 20, ..., 100

    ax.set_xticks(np.arange(0, 101, 10) / 100)  # Divide by 100 for 0-1 scale
    ax.set_xticklabels(np.arange(0, 101, 10).astype(int))  # Show 0, 10, 20, ..., 100

    # Save the plot
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close(fig)  # Close figure to free memory

    # Log time taken for the plot generation
    end_time = time()
    logging.info(f"Plot saved at {output_path}. Time taken: {end_time - start_time:.2f} seconds")

# Iterate through each file in the PREC directory and match with the WTEQ directory
for file_name in os.listdir(prec_directory):
    if file_name.endswith('_p.csv'):
        # Extract the HUC number and Basin name (the part before "_p.csv")
        base_name = file_name.replace('_p.csv', '')  # Keep the HUC number and Basin name

        # Extract the HUC number (first part of the base_name before the first underscore)
        huc_number = file_name.split('_')[0]

        # Check if the HUC number is in the specific_hucs list
        if huc_number in specific_hucs:
            logging.info(f"Processing {file_name} for HUC {huc_number}")
            prec_file_path = os.path.join(prec_directory, file_name)
            wteq_file_name = f"{base_name}_swe.csv"  # Match with the WTEQ file name
            wteq_file_path = os.path.join(wteq_directory, wteq_file_name)

            if os.path.exists(wteq_file_path) and check_csv_file_size(prec_file_path) and check_csv_file_size(wteq_file_path):
                # Use the full base_name (HUC number + Basin name) for the output file
                output_file_name = f"{base_name}_phase_diagram.png"
                output_path = os.path.join(output_directory, output_file_name)
                generate_plot(wteq_file_path, prec_file_path, output_path)
                logging.info(f"Finished processing {file_name}")
            else:
                logging.warning(f"Missing or too small files for {file_name}. Skipping.")
