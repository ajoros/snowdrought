import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl
import logging
import os
from datetime import datetime
from zoneinfo import ZoneInfo

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)



def plot_state_conditions(df, state_name, output_dir):  # ← Added parameter
    """Generate snow drought plot for a state"""
    fig, ax = plt.subplots(figsize=(10, 8))

    # Define conditions and colors
    conditions = {
        'no SD': ('lightgrey', lambda df: df[df['swe_percentile'] >= 0.30]),
        'dry SD': ('tab:red', lambda df: df[(df['swe_percentile'] < 0.30) & (df['prec_percentile'] < 0.30)]),
        'warm and dry SD': ('lightyellow', lambda df: df[(df['swe_percentile'] < 0.30) & (df['prec_percentile'].between(0.30, 0.50))]),
        'warm SD': ('tab:blue', lambda df: df[(df['swe_percentile'] < 0.30) & (df['prec_percentile'] > 0.50)])
    }

    # Plot points for each condition
    for condition, (color, filter_func) in conditions.items():
        condition_df = filter_func(df)
        ax.scatter(condition_df['prec_percentile'], condition_df['swe_percentile'],
                  label=condition, color=color, edgecolor='k', s=200, zorder=3)

    # Add reference lines
    ax.axhline(0.30, color='gold', label='30th percentile SWE', linewidth=2, zorder=2)
    ax.axhline(0.50, color='k', linewidth=1, zorder=2)
    ax.axvline(0.50, color='k', linewidth=1, zorder=2)

    current_date = datetime.now(ZoneInfo("America/Los_Angeles")).strftime('%Y-%m-%d')
    
    # Labels and formatting
    ax.set_title(f'{state_name} SNOTEL Stations on {current_date}', fontsize=16)
    ax.set_xlabel('Accumulated Precipitation Percentile')
    ax.set_ylabel('Snow Water Equivalent Percentile')

    ax.set_xlim(-0.02, 1.02)
    ax.set_ylim(-0.02, 1.02)

    # Set ticks as percentages
    ax.set_xticks(np.arange(0, 1.1, 0.1))
    ax.set_yticks(np.arange(0, 1.1, 0.1))
    ax.set_xticklabels([f'{int(x*100)}' for x in ax.get_xticks()])
    ax.set_yticklabels([f'{int(x*100)}' for x in ax.get_yticks()])

    ax.legend(loc='best')

    plt.savefig(os.path.join(output_dir, f'{state_name}_snow_drought_conditions.png'),
                dpi=300, bbox_inches='tight')
    plt.close()

def main():
    # Get the project root directory (parent of scripts/)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    base_dir = os.path.dirname(script_dir)
    
    # Create output directory
    output_dir = os.path.join(base_dir, 'plots/snow_drought_conditions')
    os.makedirs(output_dir, exist_ok=True)
    
    # Load the percentile data files
    prec_df = pd.read_csv(os.path.join(base_dir, 'data/snotel_100day_nov1_precipitation_percentiles.csv'))
    swe_df = pd.read_csv(os.path.join(base_dir, 'data/snotel_current_swe_percentiles.csv'))

    # Merge the dataframes
    merged = pd.merge(prec_df, swe_df, on=['Name', 'State'], suffixes=('_prec', '_swe'))

    # Convert percentiles to decimals
    merged['prec_percentile'] = merged['Percentile_POR_prec'] / 100
    merged['swe_percentile'] = merged['Percentile_POR_swe'] / 100

    # Process each state
    for state in merged['State'].unique():
        state_df = merged[merged['State'] == state].copy()
        if len(state_df) > 0:
            logging.info(f"Generating plot for {state}")
            plot_state_conditions(state_df, state, output_dir)  # ← Pass output_dir
            logging.info(f"Completed plot for {state} with {len(state_df)} stations")

if __name__ == "__main__":
    main()