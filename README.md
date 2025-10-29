# SNOTEL Snow Drought Dashboard

Real-time tracking and visualization of snow drought conditions across the western United States and Alaska using NRCS SNOTEL data.

🌐 **Live Dashboard**: [https://ajoros.github.io/snowdrought](https://ajoros.github.io/snowdrought)

## Overview

This automated dashboard provides:
- **Phase Diagrams**: Daily progression (November-May) of accumulated precipitation and SWE percentiles for HUC6 river basins
- **State-wide Snow Drought Plots**: Real-time snow drought classifications for individual SNOTEL stations
- **Automatic Updates**: Data refreshed twice daily via GitHub Actions (midnight and noon UTC)

## Snow Drought Classifications

- **Dry Snow Drought**: Both SWE and precipitation below 30th percentile
- **Warm Snow Drought**: SWE below 30th percentile, precipitation above 50th percentile
- **Warm and Dry Snow Drought**: SWE below 30th percentile, precipitation between 30th-50th percentile

## Project Structure

```
snowdrought/
├── .github/
│   └── workflows/
│       └── update-dashboard.yml    # GitHub Actions automation
├── scripts/
│   ├── download_data.py            # Download HUC6 PREC/WTEQ data
│   ├── download_snotel_data.py     # Download SNOTEL station data
│   ├── process_snotel_data.py      # Process and calculate percentiles
│   ├── generate_plots.py           # Generate phase diagrams
│   └── generate_snow_drought_plots_new.py  # Generate state plots
├── data/
│   ├── HUC6PREC/                   # HUC6 precipitation data
│   ├── HUC6WTEQ/                   # HUC6 SWE data
│   ├── snotel/                     # SNOTEL station data
│   └── snotel_station_list.csv     # List of SNOTEL stations
├── plots/
│   ├── phase_diagrams/             # Generated phase diagrams
│   └── snow_drought_conditions/    # Generated state plots
├── logo/                           # DRI logo
├── index.html                      # Dashboard web interface
├── requirements.txt                # Python dependencies
└── README.md                       # This file
```

## Data Sources

- **NRCS SNOTEL Network**: Snow water equivalent and precipitation data
  - HUC6 Basin Data: https://nwcc-apps.sc.egov.usda.gov/awdb/basin-plots/
  - Station Data: https://nwcc-apps.sc.egov.usda.gov/awdb/site-plots/

## Automation

The dashboard updates automatically via GitHub Actions:
- **Schedule**: Every 12 hours (0:00 and 12:00 UTC)
- **Process**:
  1. Download latest NRCS data
  2. Process and calculate percentiles
  3. Generate phase diagrams and state plots
  4. Commit changes to repository
  5. GitHub Pages automatically serves the updated site

## Local Development

### Prerequisites

- Python 3.9 or higher
- pip

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/ajoros/snowdrought.git
   cd snowdrought
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run individual scripts:
   ```bash
   # Download data
   python scripts/download_data.py
   python scripts/download_snotel_data.py
   
   # Process data
   python scripts/process_snotel_data.py
   
   # Generate plots
   python scripts/generate_plots.py
   python scripts/generate_snow_drought_plots_new.py
   ```

4. View the dashboard:
   - Open `index.html` in a web browser

## GitHub Pages Deployment

### Initial Setup

1. Create a new GitHub repository named `snowdrought`

2. Push your local repository:
   ```bash
   cd ~/Dropbox/Snowdrought
   git remote add origin https://github.com/ajoros/snowdrought.git
   git branch -M main
   git push -u origin main
   ```

3. Configure GitHub Pages:
   - Go to repository Settings → Pages
   - Source: Deploy from a branch
   - Branch: `main`
   - Folder: `/ (root)`
   - Save

4. Enable GitHub Actions:
   - The workflow will run automatically on schedule
   - Manual runs: Go to Actions → Update Snow Drought Dashboard → Run workflow

### First Run

After pushing to GitHub, manually trigger the first workflow run to populate initial data:
1. Go to Actions tab
2. Select "Update Snow Drought Dashboard"
3. Click "Run workflow"

The dashboard will be live at: **https://ajoros.github.io/snowdrought**

## Cron Schedule (Original EC2 Setup)

For reference, the original cron schedule was:
```cron
# Run every 12 hours at midnight and noon
1 0,12 * * * python3 download_snotel_data.py
11 0,12 * * * python3 process_snotel_data.py
15 0,12 * * * python3 generate_snow_drought_plots_new.py
20 0,12 * * * python3 download_data.py
40 0,12 * * * python3 generate_plots.py
```

This has been replaced by the GitHub Actions workflow.

## References

- **Hatchett, B. J., Rhoades, A. M., & McEvoy, D. J. (2022)**. Monitoring the daily evolution and extent of snow drought. *Natural Hazards and Earth System Sciences*, 22(3), 869-890.
  - [https://nhess.copernicus.org/articles/22/869/2022/](https://nhess.copernicus.org/articles/22/869/2022/nhess-22-869-2022.html)

- **NRCS SNOTEL Network**
  - [https://nwcc-apps.sc.egov.usda.gov/imap](https://nwcc-apps.sc.egov.usda.gov/imap)

## Contact

For questions or comments, please contact Dan McEvoy at the Desert Research Institute:
- Email: mcevoyd@dri.edu
- Website: [https://www.dri.edu](https://www.dri.edu)

## License

This project is developed at the Desert Research Institute (DRI).

---

**Maintained by**: Desert Research Institute  
**GitHub**: [https://github.com/ajoros/snowdrought](https://github.com/ajoros/snowdrought)  
**Last Updated**: 2025
