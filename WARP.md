# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Project Overview

SNOTEL Snow Drought Dashboard - Real-time tracking and visualization of snow drought conditions across the western United States and Alaska using NRCS SNOTEL data. The dashboard is hosted on GitHub Pages and automatically updated once daily via GitHub Actions.

**Live Dashboard**: https://ajoros.github.io/snowdrought

## Core Architecture

### Deployment Model (Updated January 2026)

The project uses a **two-branch deployment strategy** to minimize repository size and prevent historical bloat:

1. **main branch** - Contains only source code and processed data CSVs (<1MB)
   - Scripts for data processing and plot generation
   - Station list and processed percentile CSVs
   - Configuration files
   - No plot PNG files (excluded via .gitignore)

2. **gh-pages branch** - Contains only deployment artifacts (managed by GitHub Actions)
   - Generated plot PNG files (45MB)
   - index.html dashboard
   - logo and supporting files
   - Updated fresh with each workflow run

**Why this approach?**
- Plots are deployment artifacts, not source code → belong on deployment branch
- Keeps main branch lean and fast (~1.3MB git history vs previous 2.3GB)
- Prevents repository bloat from daily commits
- GitHub Pages served from gh-pages root automatically

### Data Pipeline

The project follows a sequential 5-stage processing pipeline that must be executed in order:

1. **HUC6 Data Download** (`scripts/download_data.py`)
   - Downloads precipitation (PREC) and snow water equivalent (WTEQ) data from NRCS for HUC6 river basins
   - Filters 67 specific HUC6 basins across western states and Alaska
   - Stores raw CSV files in temporary `data/HUC6PREC/` and `data/HUC6WTEQ/`
   - These files are NOT committed (excluded via .gitignore)

2. **SNOTEL Station Download** (`scripts/download_snotel_data.py`)
   - Downloads JSON data for individual SNOTEL stations across 13 states
   - Uses concurrent downloads (ThreadPoolExecutor with 20 workers)
   - Validates that both PREC and WTEQ data exist before downloading
   - Stores station data in temporary `data/snotel/prec/` and `data/snotel/swe/`
   - These files are NOT committed (excluded via .gitignore)

3. **Data Processing** (`scripts/process_snotel_data.py`)
   - Calculates percentiles for precipitation (accumulated from Nov 1) and current SWE
   - Requires ≥20 years of historical data for percentile calculations
   - Generates two output CSVs: `snotel_100day_nov1_precipitation_percentiles.csv` and `snotel_current_swe_percentiles.csv`
   - These CSVs ARE committed to main branch (small, informative)

4. **Phase Diagram Generation** (`scripts/generate_plots.py`)
   - Creates phase diagrams showing daily progression (Nov-May) of SWE vs precipitation percentiles for HUC6 basins
   - Uses 3-day centered window for percentile smoothing
   - Color-codes plots by month with markers showing trajectory
   - Outputs to temporary `plots/phase_diagrams/`
   - These files are NOT committed; deployed to gh-pages branch

5. **State Plot Generation** (`scripts/generate_snow_drought_plots_new.py`)
   - Generates scatter plots classifying SNOTEL stations by snow drought type
   - Three drought classifications: dry (both <30%), warm and dry (SWE <30%, precip 30-50%), warm (SWE <30%, precip >50%)
   - Outputs to temporary `plots/snow_drought_conditions/`
   - These files are NOT committed; deployed to gh-pages branch

### Snow Drought Classifications

- **Dry Snow Drought**: SWE <30th percentile AND precipitation <30th percentile (red)
- **Warm and Dry Snow Drought**: SWE <30th percentile AND precipitation 30-50th percentile (yellow)
- **Warm Snow Drought**: SWE <30th percentile AND precipitation >50th percentile (blue)
- **No Snow Drought**: SWE ≥30th percentile (grey)

### Key Design Patterns

- **Path Resolution**: All scripts use `os.path.dirname(os.path.dirname(os.path.abspath(__file__)))` to determine project root, enabling execution from any directory
- **Water Year Handling**: Water year starts Nov 1 (e.g., WY 2025-26 starts Nov 1, 2025), requiring careful year transitions in data processing
- **Percentile Calculation**: Custom percentile logic using `scipy.stats.rankdata` with 3-day centered windows for phase diagrams
- **Concurrent Downloads**: SNOTEL data uses ThreadPoolExecutor to parallelize network requests while respecting rate limits
- **Two-Branch Deployment**: Plots generated in workflow, deployed to gh-pages via peaceiris/actions-gh-pages, main branch stays clean

## Development Commands

### Setup
```bash
# Install dependencies
pip install -r requirements.txt
```

### Running the Full Pipeline
Execute scripts in this exact order:
```bash
python scripts/download_data.py
python scripts/download_snotel_data.py
python scripts/process_snotel_data.py
python scripts/generate_plots.py
python scripts/generate_snow_drought_plots_new.py
```

### Testing Individual Components
```bash
# Test HUC6 data download only
python scripts/download_data.py

# Test SNOTEL station data download
python scripts/download_snotel_data.py

# Test processing (requires downloaded data)
python scripts/process_snotel_data.py

# Test plot generation (requires processed data)
python scripts/generate_plots.py
python scripts/generate_snow_drought_plots_new.py
```

### Viewing Output
```bash
# Open dashboard locally
open index.html

# View generated plots (in temporary directories)
open plots/phase_diagrams/
open plots/snow_drought_conditions/
```

## GitHub Actions Automation

### Workflow Architecture (Updated January 2026)

The workflow (`.github/workflows/update-dashboard.yml`) runs once daily (6 AM PST / 7 AM PDT) and can be triggered manually:

**Execution steps:**
1. Checkout main branch
2. Set up Python 3.11
3. Install dependencies
4. Download HUC6 data to temporary directory
5. Download SNOTEL station data to temporary directory
6. Process data and generate percentile CSVs
7. Generate phase diagrams and scatter plots to temporary directory
8. Prepare deployment package (copy plots, index.html, logo, data files to deployment/ directory)
9. Deploy deployment/ directory to gh-pages branch using peaceiris/actions-gh-pages
10. Commit only processed CSVs back to main branch
11. Report summary

**Key change from previous setup:**
- Plots are NO LONGER committed to main branch
- Plots are deployed directly to gh-pages branch via GitHub Actions deployment
- This prevents 45MB+ daily additions to git history

### Manual Trigger
Visit: https://github.com/ajoros/snowdrought/actions
Click "Update Snow Drought Dashboard" → "Run workflow"

Dashboard updates 1-2 minutes after workflow completes.

### Workflow Permissions
Requires `contents: write` permission to:
- Commit processed CSVs to main branch
- Deploy to gh-pages branch (via GITHUB_TOKEN)

## Repository Structure (Updated January 2026)

```
snowdrought/
├── .github/
│   └── workflows/
│       └── update-dashboard.yml    # GitHub Actions automation
├── scripts/
│   ├── download_data.py            # Stage 1: HUC6 data
│   ├── download_snotel_data.py     # Stage 2: SNOTEL stations
│   ├── process_snotel_data.py      # Stage 3: Percentile calculation
│   ├── generate_plots.py           # Stage 4: Phase diagrams
│   └── generate_snow_drought_plots_new.py  # Stage 5: State plots
├── data/
│   ├── HUC6PREC/                   # Downloaded HUC6 precip (temporary, excluded)
│   ├── HUC6WTEQ/                   # Downloaded HUC6 SWE (temporary, excluded)
│   ├── snotel/                     # Downloaded station data (temporary, excluded)
│   │   ├── prec/                   # Precipitation JSONs
│   │   └── swe/                    # SWE JSONs
│   ├── snotel_station_list.csv     # Station metadata (in repo)
│   ├── snotel_100day_nov1_precipitation_percentiles.csv  # Processed (in repo)
│   └── snotel_current_swe_percentiles.csv  # Processed (in repo)
├── plots/                          # Generated PNG files (NOT in main branch)
│   ├── phase_diagrams/             # Generated by workflow, deployed to gh-pages
│   └── snow_drought_conditions/    # Generated by workflow, deployed to gh-pages
├── logo/
│   └── official-dri-logo-trans-bkgd.png
├── index.html                      # Dashboard web interface (deployed to gh-pages)
├── requirements.txt                # Python dependencies
├── README.md                       # Public documentation
├── WARP.md                         # This file
├── .gitignore                      # Excludes: plots/, data downloads
└── DEPLOYMENT.md                   # Deployment setup instructions

** Note: plots/ directory is NOT committed to main branch; exists only on gh-pages branch
```

## Data Sources

All data comes from NRCS SNOTEL Network:
- HUC6 Basin Data: `https://nwcc-apps.sc.egov.usda.gov/awdb/basin-plots/`
- Station Data: `https://nwcc-apps.sc.egov.usda.gov/awdb/site-plots/`

Station list maintained in: `data/snotel_station_list.csv`

## Important Constraints

- **Historical Data Requirements**: Stations must have ≥20 years of valid historical data to be included in percentile calculations
- **Water Year Timing**: All accumulation starts Nov 1; scripts are designed for Nov 1 - May 31 water year
- **File Size Validation**: Phase diagram generation checks CSV files are >3KB to ensure valid data
- **State Coverage**: 13 western states: AK, AZ, CA, CO, ID, MT, NV, NM, OR, SD, UT, WA, WY
- **HUC6 Filtering**: Only 67 specific HUC6 basins are processed (defined in `specific_hucs` lists)

## Storage Optimization (January 2026)

**Before Optimization:**
- Repository size: 2.7GB
- Git history: 2.3GB (from daily plot commits)
- Annual growth: ~16.4GB/year

**After Optimization:**
- Repository size: ~100MB
- Git history: ~1.3MB
- Annual growth: 0MB (plots replaced, not accumulated)
- Main branch: <1MB (source code only)
- gh-pages branch: ~45MB (latest plots)

**Why:** Plots are deployment artifacts managed by workflow, not version-controlled source code.

## Modifying the Pipeline

When adding features:
- **New States**: Add to `STATE_ABBREV` dict in `download_snotel_data.py`
- **New HUC6 Basins**: Add codes to `specific_hucs` lists in `download_data.py` and `generate_plots.py`
- **Drought Thresholds**: Modify condition logic in `generate_snow_drought_plots_new.py` conditions dict
- **Plot Styling**: Matplotlib settings configured globally at script tops (e.g., `mpl.rcParams['font.size'] = 24`)

## Dependencies

Core Python packages (see `requirements.txt`):
- `pandas>=2.0.0` - Data manipulation
- `numpy>=1.24.0` - Numerical operations
- `matplotlib>=3.7.0` - Plotting
- `scipy>=1.10.0` - Statistical functions (percentile calculations)
- `requests>=2.31.0` - HTTP downloads
- `beautifulsoup4>=4.12.0` - HTML parsing for directory listings

Python 3.9+ recommended (workflow uses 3.11).

## Deployment

Project is deployed to GitHub Pages from the `gh-pages` branch root directory. The workflow automatically:
1. Generates plots and prepares deployment package
2. Deploys to gh-pages via peaceiris/actions-gh-pages
3. GitHub Pages serves at `https://ajoros.github.io/snowdrought`
4. Updates occur 1-2 minutes after workflow completion

See `DEPLOYMENT.md` for initial setup instructions.

## Contact

Project maintained by Desert Research Institute (DRI)
- Lead: Dan McEvoy (mcevoyd@dri.edu)
- Repository: https://github.com/ajoros/snowdrought

## Reference

Based on methodology from: Hatchett, B. J., Rhoades, A. M., & McEvoy, D. J. (2022). Monitoring the daily evolution and extent of snow drought. *Natural Hazards and Earth System Sciences*, 22(3), 869-890.
