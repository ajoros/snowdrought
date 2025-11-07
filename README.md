# SNOTEL Snow Drought Dashboard

Real-time tracking and visualization of snow drought conditions across the western United States and Alaska using NRCS SNOTEL data.

🌐 **Live Dashboard**: [https://ajoros.github.io/snowdrought](https://ajoros.github.io/snowdrought)

## Overview

This website provides real-time tracking and summaries of snow drought conditions across the western United States and Alaska using data from the Natural Resources Conservation Service SNOw TELemetry network (NRCS SNOTEL). The dashboard automatically updates daily at 6:00 AM PST / 7:00 AM PDT with the latest snow water equivalent (SWE) and precipitation data.

The dashboard provides two types of visualizations:

### Phase Diagrams
Phase diagrams show the daily progression (November-May) of accumulated precipitation and SWE percentiles for Hydrologic Unit Code 6 (HUC 6) river basins. These diagrams are described in detail in Hatchett et al. (2022) and use basin-mean precipitation and SWE obtained from NRCS SNOTEL stations. The trajectory through the season helps identify the type and severity of snow drought conditions.

### State-wide Scatter Plots
Scatter plots show snow drought classifications for individual SNOTEL stations within each state at a single point in time (the most recent day). For both visualization types, the SWE value represents the most recent day, while the precipitation value is the accumulation from November 1 through the current day.

## Snow Drought Science

Snow drought occurs when snow water equivalent falls below expected levels, which can happen through different mechanisms:

- **Dry Snow Drought**: Both SWE and precipitation are below the 30th percentile. This occurs when there is insufficient precipitation falling as snow.

- **Warm Snow Drought**: SWE is below the 30th percentile while precipitation is above the 50th percentile. This occurs when temperatures are warm enough that precipitation falls as rain instead of snow, or existing snowpack melts prematurely.

- **Warm and Dry Snow Drought**: SWE is below the 30th percentile while precipitation is between the 30th and 50th percentile. This represents a combination of reduced precipitation and warmer temperatures.

These classifications help water resource managers, researchers, and the public understand both the severity and the physical mechanisms driving snow drought conditions.

## Data Sources

- **NRCS SNOTEL Network**: Snow water equivalent and precipitation data
  - HUC6 Basin Data: [https://nwcc-apps.sc.egov.usda.gov/awdb/basin-plots/](https://nwcc-apps.sc.egov.usda.gov/awdb/basin-plots/)
  - Station Data: [https://nwcc-apps.sc.egov.usda.gov/awdb/site-plots/](https://nwcc-apps.sc.egov.usda.gov/awdb/site-plots/)
  - Interactive Map: [https://nwcc-apps.sc.egov.usda.gov/imap](https://nwcc-apps.sc.egov.usda.gov/imap)

## References

Hatchett, B. J., Rhoades, A. M., & McEvoy, D. J. (2022). Monitoring the daily evolution and extent of snow drought. *Natural Hazards and Earth System Sciences*, 22(3), 869-890. [https://nhess.copernicus.org/articles/22/869/2022/nhess-22-869-2022.html](https://nhess.copernicus.org/articles/22/869/2022/nhess-22-869-2022.html)

## Contact

For questions or comments, please contact:

**Andrew Joros**  
Assistant Research Scientist  
Desert Research Institute  
Email: [andrew.joros@dri.edu](mailto:andrew.joros@dri.edu)

**Dan McEvoy, Ph.D.**  
Research Professor  
Desert Research Institute  
Email: [mcevoyd@dri.edu](mailto:mcevoyd@dri.edu)

**Desert Research Institute**  
Website: [https://www.dri.edu](https://www.dri.edu)

---

**Maintained by**: Desert Research Institute  
**Dashboard**: [https://ajoros.github.io/snowdrought](https://ajoros.github.io/snowdrought)  
**Repository**: [https://github.com/ajoros/snowdrought](https://github.com/ajoros/snowdrought)
