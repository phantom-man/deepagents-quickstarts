# Environmental Monitoring Analytics & Metrics Specification

**Version:** 1.0  
**Date:** February 5, 2026  
**Purpose:** Feature Requirements Document for Environmental Data Analytics Platform

---

## Table of Contents

1. [Air Quality Metrics](#1-air-quality-metrics)
2. [Water Quality Metrics](#2-water-quality-metrics)
3. [Climate/Weather Metrics](#3-climateweather-metrics)
4. [Marine Metrics](#4-marine-metrics)
5. [Biodiversity Metrics](#5-biodiversity-metrics)
6. [Cross-Domain Analysis](#6-cross-domain-analysis)
7. [Report Types](#7-report-types)
8. [Statistical Methods](#8-statistical-methods)
9. [Data Quality Indicators](#9-data-quality-indicators)
10. [Implementation Priority](#10-implementation-priority)

---

## 1. Air Quality Metrics

### 1.1 Core Pollutant Measurements

| Pollutant | Unit | Averaging Periods | Health Standard Reference |
|-----------|------|-------------------|---------------------------|
| PM2.5 (Fine Particulate Matter) | µg/m³ | 1-hr, 24-hr, Annual | WHO: 15 µg/m³ (24-hr), 5 µg/m³ (annual) |
| PM10 (Coarse Particulate Matter) | µg/m³ | 1-hr, 24-hr, Annual | WHO: 45 µg/m³ (24-hr), 15 µg/m³ (annual) |
| Ozone (O₃) | ppb/µg/m³ | 1-hr, 8-hr | EPA: 70 ppb (8-hr) |
| Nitrogen Dioxide (NO₂) | ppb/µg/m³ | 1-hr, Annual | WHO: 25 µg/m³ (24-hr) |
| Sulfur Dioxide (SO₂) | ppb/µg/m³ | 1-hr, 24-hr | WHO: 40 µg/m³ (24-hr) |
| Carbon Monoxide (CO) | ppm | 1-hr, 8-hr | EPA: 9 ppm (8-hr) |
| Lead (Pb) | µg/m³ | Rolling 3-month, Annual | EPA: 0.15 µg/m³ |
| Ammonia (NH₃) | µg/m³ | 24-hr | Regional standards |

### 1.2 Air Quality Index Calculations

#### US EPA AQI Breakpoints
```
AQI Range    | Category                    | Color   | Health Implications
0-50         | Good                        | Green   | Satisfactory, minimal risk
51-100       | Moderate                    | Yellow  | Acceptable, sensitive groups risk
101-150      | Unhealthy for Sensitive     | Orange  | Sensitive groups affected
151-200      | Unhealthy                   | Red     | General public may experience effects
201-300      | Very Unhealthy              | Purple  | Health alert: everyone at risk
301-500      | Hazardous                   | Maroon  | Emergency conditions
```

#### AQI Calculation Formula
```
AQI = ((IHi - ILo) / (BPHi - BPLo)) × (Cp - BPLo) + ILo

Where:
- Cp = Truncated concentration of pollutant
- BPHi = Concentration breakpoint ≥ Cp
- BPLo = Concentration breakpoint ≤ Cp
- IHi = AQI value corresponding to BPHi
- ILo = AQI value corresponding to BPLo
```

### 1.3 Derived Air Quality Analytics

| Metric | Description | Formula/Method |
|--------|-------------|----------------|
| **NowCast** | Real-time weighted average | Weight recent hours more heavily for rapidly changing conditions |
| **Daily Max AQI** | Highest AQI of day | max(AQI_hourly) |
| **Exceedance Days** | Days above standard | count(AQI > threshold) |
| **Pollutant Dominance** | Primary pollutant frequency | mode(dominant_pollutant) per period |
| **Diurnal Variation** | Day/night patterns | hourly_avg by time_of_day |
| **Weekend Effect** | Weekday vs weekend comparison | avg(weekday) vs avg(weekend) |
| **Seasonal Trend** | Seasonal patterns | monthly_avg grouped by season |
| **Year-over-Year Change** | Annual comparison | (current_year - prev_year) / prev_year × 100 |

### 1.4 Health Impact Indices

| Index | Description | Components |
|-------|-------------|------------|
| **AQHI (Air Quality Health Index)** | Canadian health-focused index | NO₂, O₃, PM2.5 combined |
| **Respiratory Risk Index** | Lung health impact | PM2.5, O₃, NO₂ weighted |
| **Cardiovascular Risk Index** | Heart health impact | PM2.5, CO, SO₂ weighted |
| **Sensitive Population Index** | Elderly/children focus | Lower thresholds applied |

### 1.5 Pollutant Correlation Metrics

- **PM2.5/PM10 Ratio**: Indicates fine vs coarse particle sources
- **NO₂/NOx Ratio**: Traffic vs industrial source indicator
- **O₃/NOx Relationship**: Photochemical smog indicator
- **CO/NO₂ Correlation**: Vehicle emission signature
- **Source Apportionment Index**: Multi-pollutant source identification

---

## 2. Water Quality Metrics

### 2.1 Physical Indicators

| Parameter | Unit | Typical Range | Significance |
|-----------|------|---------------|--------------|
| **Temperature** | °C/°F | Varies seasonally | Affects dissolved oxygen, organism metabolism |
| **Turbidity** | NTU/FNU | 0-1000+ | Suspended particles, light penetration |
| **Total Dissolved Solids (TDS)** | mg/L | 0-500 (fresh) | Mineral content |
| **Total Suspended Solids (TSS)** | mg/L | Variable | Sediment load |
| **Conductivity** | µS/cm | 50-1500 | Ion concentration |
| **Secchi Depth** | meters | 0.1-40+ | Water clarity |
| **Color** | Pt/Co units | 0-500+ | Organic matter indicator |
| **Odor** | TON | 0-200+ | Contamination indicator |

### 2.2 Chemical Indicators

| Parameter | Unit | Safe Limit | Health Impact |
|-----------|------|------------|---------------|
| **pH** | pH units | 6.5-8.5 | Acidity/alkalinity |
| **Dissolved Oxygen (DO)** | mg/L | >5 mg/L | Aquatic life support |
| **Biochemical Oxygen Demand (BOD)** | mg/L | <5 mg/L | Organic pollution |
| **Chemical Oxygen Demand (COD)** | mg/L | <25 mg/L | Total oxidizable matter |
| **Nitrate (NO₃⁻)** | mg/L | <10 mg/L | Agricultural runoff |
| **Nitrite (NO₂⁻)** | mg/L | <1 mg/L | Intermediate nitrogen |
| **Phosphate (PO₄³⁻)** | mg/L | <0.1 mg/L | Eutrophication risk |
| **Ammonia (NH₃)** | mg/L | <0.5 mg/L | Toxicity to fish |
| **Chloride** | mg/L | <250 mg/L | Salinity indicator |
| **Sulfate** | mg/L | <250 mg/L | Industrial pollution |
| **Alkalinity** | mg/L CaCO₃ | 20-200 | Buffering capacity |
| **Hardness** | mg/L CaCO₃ | 0-500+ | Calcium/magnesium content |

### 2.3 Heavy Metals & Contaminants

| Metal | Maximum Safe (mg/L) | Primary Sources |
|-------|---------------------|-----------------|
| Lead (Pb) | 0.015 | Pipes, industrial |
| Mercury (Hg) | 0.002 | Mining, industrial |
| Arsenic (As) | 0.010 | Natural, industrial |
| Cadmium (Cd) | 0.005 | Industrial, batteries |
| Chromium (Cr) | 0.100 | Industrial |
| Copper (Cu) | 1.300 | Pipes, agricultural |
| Iron (Fe) | 0.300 | Natural, industrial |
| Manganese (Mn) | 0.050 | Natural, industrial |
| Zinc (Zn) | 5.000 | Industrial, agricultural |

### 2.4 Biological Indicators

| Indicator | Description | Healthy Range |
|-----------|-------------|---------------|
| **Fecal Coliform** | E. coli indicator | <200 CFU/100mL |
| **Enterococci** | Intestinal bacteria | <35 CFU/100mL |
| **Chlorophyll-a** | Algae biomass | <10 µg/L |
| **Cyanobacteria** | Blue-green algae | <20,000 cells/mL |
| **EPT Index** | Mayflies, stoneflies, caddisflies | Higher = healthier |
| **Biotic Index** | Organism diversity score | Site-specific |

### 2.5 Water Quality Index (WQI)

#### NSF Water Quality Index Components
```
WQI = Σ(Wi × Qi)

Parameters and Weights:
- Dissolved Oxygen: 0.17
- Fecal Coliform: 0.15
- pH: 0.12
- BOD: 0.10
- Temperature Change: 0.10
- Total Phosphate: 0.10
- Nitrates: 0.10
- Turbidity: 0.08
- Total Solids: 0.08
```

#### WQI Classification
| Score | Classification | Description |
|-------|---------------|-------------|
| 90-100 | Excellent | Pristine water |
| 70-89 | Good | Minor impairment |
| 50-69 | Medium | Moderate impairment |
| 25-49 | Bad | Significant pollution |
| 0-24 | Very Bad | Severe pollution |

### 2.6 Derived Water Analytics

| Metric | Description | Application |
|--------|-------------|-------------|
| **Trophic State Index (TSI)** | Eutrophication level | Lake/reservoir health |
| **Sodium Adsorption Ratio (SAR)** | Irrigation suitability | Agricultural water |
| **Langelier Saturation Index** | Corrosion potential | Distribution systems |
| **Pollution Load Index** | Cumulative contamination | Watershed assessment |
| **Flow-Weighted Concentration** | Mass flux calculation | Watershed loading |

---

## 3. Climate/Weather Metrics

### 3.1 Temperature Metrics

| Metric | Description | Calculation |
|--------|-------------|-------------|
| **Daily Mean Temperature** | Average of day | (Tmax + Tmin) / 2 |
| **Temperature Anomaly** | Deviation from normal | Tobserved - Tnormal |
| **Heating Degree Days (HDD)** | Heating energy demand | max(0, 65°F - Tavg) |
| **Cooling Degree Days (CDD)** | Cooling energy demand | max(0, Tavg - 65°F) |
| **Growing Degree Days (GDD)** | Agricultural index | max(0, Tavg - Tbase) |
| **Heat Index** | Felt temperature | f(T, Humidity) |
| **Wind Chill** | Felt cold temperature | f(T, Wind Speed) |
| **Frost Days** | Days with Tmin < 0°C | count(Tmin < 0) |
| **Tropical Nights** | Nights with Tmin > 20°C | count(Tmin > 20) |
| **Heat Wave Duration** | Consecutive hot days | count(consecutive Tmax > threshold) |

### 3.2 Precipitation Metrics

| Metric | Unit | Description |
|--------|------|-------------|
| **Total Precipitation** | mm/inches | Sum over period |
| **Precipitation Anomaly** | % of normal | (Observed / Normal) × 100 |
| **Wet Days** | count | Days with precip > 1mm |
| **Heavy Precipitation Days** | count | Days with precip > 10mm |
| **Extreme Precipitation Days** | count | Days with precip > 20mm |
| **Maximum 1-Day Precipitation** | mm | max(daily_precip) |
| **Maximum 5-Day Precipitation** | mm | max(5-day rolling sum) |
| **Consecutive Dry Days (CDD)** | count | Longest dry spell |
| **Consecutive Wet Days (CWD)** | count | Longest wet spell |
| **Precipitation Intensity** | mm/day | Total / Wet Days |
| **Simple Daily Intensity** | mm/day | avg(precip on wet days) |

### 3.3 Climate Normals & Comparisons

| Reference Period | Description |
|------------------|-------------|
| **1991-2020 Normal** | Current WMO standard baseline |
| **1981-2010 Normal** | Previous baseline (transition) |
| **Pre-Industrial (1850-1900)** | Climate change reference |
| **Station Record** | Historical extremes comparison |

### 3.4 Drought Indices

| Index | Range | Description |
|-------|-------|-------------|
| **Palmer Drought Severity Index (PDSI)** | -10 to +10 | Soil moisture anomaly |
| **Standardized Precipitation Index (SPI)** | -3 to +3 | Precipitation anomaly |
| **Standardized Precipitation-Evapotranspiration Index (SPEI)** | -3 to +3 | Water balance anomaly |
| **Keetch-Byram Drought Index (KBDI)** | 0-800 | Fire risk indicator |
| **Evaporative Demand Drought Index (EDDI)** | Percentiles | Atmospheric demand |
| **US Drought Monitor Categories** | D0-D4 | Composite classification |

### 3.5 Climate Extremes Indices (ETCCDI)

| Index | Description | Category |
|-------|-------------|----------|
| **TXx** | Max of daily max temperature | Temperature |
| **TNn** | Min of daily min temperature | Temperature |
| **TX90p** | Warm days (% above 90th percentile) | Temperature |
| **TN10p** | Cold nights (% below 10th percentile) | Temperature |
| **WSDI** | Warm spell duration index | Temperature |
| **CSDI** | Cold spell duration index | Temperature |
| **R10mm** | Days with precip ≥ 10mm | Precipitation |
| **R20mm** | Days with precip ≥ 20mm | Precipitation |
| **RX1day** | Max 1-day precipitation | Precipitation |
| **RX5day** | Max 5-day precipitation | Precipitation |
| **SDII** | Simple daily intensity index | Precipitation |
| **PRCPTOT** | Annual total wet-day precipitation | Precipitation |

---

## 4. Marine Metrics

### 4.1 Physical Oceanographic Parameters

| Parameter | Unit | Typical Range | Significance |
|-----------|------|---------------|--------------|
| **Sea Surface Temperature (SST)** | °C | -2 to 35 | Climate indicator |
| **Subsurface Temperature** | °C | -2 to 30 | Thermocline structure |
| **Salinity** | PSU | 30-40 | Water mass identification |
| **Significant Wave Height** | meters | 0-20+ | Sea state |
| **Wave Period** | seconds | 1-25 | Wave energy |
| **Wave Direction** | degrees | 0-360 | Swell origin |
| **Sea Level** | meters | Variable | Tidal/climate signal |
| **Current Speed** | m/s | 0-5 | Transport patterns |
| **Current Direction** | degrees | 0-360 | Circulation patterns |
| **Mixed Layer Depth** | meters | 10-300 | Stratification |

### 4.2 Ocean Chemistry

| Parameter | Unit | Typical Range | Concern Level |
|-----------|------|---------------|---------------|
| **pH** | pH units | 7.8-8.3 | <8.0 (acidification) |
| **Dissolved Oxygen** | mg/L or % saturation | 4-8 mg/L | <2 mg/L (hypoxia) |
| **pCO₂** | µatm | 300-500 | >400 (high absorption) |
| **Total Alkalinity** | µmol/kg | 2200-2500 | Buffering capacity |
| **Dissolved Inorganic Carbon (DIC)** | µmol/kg | 1900-2200 | Carbon storage |
| **Aragonite Saturation (Ωa)** | dimensionless | 1-5 | <1 (shell dissolution) |
| **Calcite Saturation (Ωc)** | dimensionless | 1-6 | <1 (shell dissolution) |
| **Nutrients (N, P, Si)** | µmol/L | Variable | Productivity indicators |

### 4.3 Marine Biological Metrics

| Metric | Description | Application |
|--------|-------------|-------------|
| **Chlorophyll-a** | Phytoplankton biomass | Primary productivity |
| **Primary Productivity** | Carbon fixation rate | Ecosystem health |
| **Zooplankton Biomass** | Secondary producers | Food web indicator |
| **Fish Stock Index** | Population estimates | Fisheries management |
| **Coral Cover (%)** | Live coral extent | Reef health |
| **Coral Bleaching Index** | Thermal stress response | Climate impact |
| **Seagrass Extent** | Area of coverage | Habitat health |
| **Harmful Algal Bloom (HAB) Index** | Toxic algae presence | Public health |

### 4.4 Ocean Climate Indices

| Index | Description | Influence |
|-------|-------------|-----------|
| **ENSO (ONI)** | El Niño/La Niña | Global weather patterns |
| **PDO** | Pacific Decadal Oscillation | Long-term Pacific climate |
| **AMO** | Atlantic Multidecadal Oscillation | Atlantic climate |
| **NAO** | North Atlantic Oscillation | European/Atlantic weather |
| **IOD** | Indian Ocean Dipole | Indian Ocean/Australia |
| **Arctic Oscillation** | Polar vortex strength | Northern Hemisphere weather |

### 4.5 Derived Marine Analytics

| Metric | Description | Calculation |
|--------|-------------|-------------|
| **Marine Heat Wave (MHW)** | Anomalously warm periods | SST > 90th percentile for 5+ days |
| **Ocean Heat Content** | Integrated temperature | ∫ρCpTdz |
| **Thermal Stratification Index** | Vertical temperature gradient | ΔT/Δz |
| **Upwelling Index** | Nutrient-rich water movement | Wind stress derived |
| **Sea Ice Extent** | Area with >15% ice coverage | Satellite derived |
| **Degree Heating Weeks (DHW)** | Coral bleaching risk | Accumulated thermal stress |

---

## 5. Biodiversity Metrics

### 5.1 Species Diversity Indices

| Index | Formula | Description | Range |
|-------|---------|-------------|-------|
| **Species Richness (S)** | Count of species | Simple count | 0 to ∞ |
| **Shannon Diversity (H')** | H' = -Σ(pi × ln(pi)) | Combines richness & evenness | 0 to ~4.5 |
| **Simpson's Diversity (D)** | D = 1 - Σ(pi²) | Probability of different species | 0 to 1 |
| **Inverse Simpson (1/D)** | 1 / Σ(pi²) | Effective number of species | 1 to S |
| **Pielou's Evenness (J')** | J' = H' / ln(S) | Distribution uniformity | 0 to 1 |
| **Margalef's Richness** | DMg = (S-1) / ln(N) | Richness relative to sample size | 0 to ∞ |
| **Menhinick's Index** | DMn = S / √N | Simple richness standardization | 0 to ∞ |

### 5.2 Community Composition Metrics

| Metric | Description | Application |
|--------|-------------|-------------|
| **Relative Abundance** | Proportion of each species | Community structure |
| **Species Accumulation Curve** | New species vs sampling effort | Sampling adequacy |
| **Rank-Abundance (Whittaker) Plot** | Species ranked by abundance | Dominance patterns |
| **Beta Diversity (β)** | Turnover between sites | Habitat heterogeneity |
| **Jaccard Similarity** | Species overlap | Site comparison |
| **Bray-Curtis Dissimilarity** | Abundance-weighted difference | Community comparison |
| **Indicator Species Analysis** | Characteristic species | Habitat classification |

### 5.3 Population Metrics

| Metric | Description | Application |
|--------|-------------|-------------|
| **Population Size (N)** | Total count | Baseline assessment |
| **Population Density** | Individuals per area | Carrying capacity |
| **Population Trend** | Rate of change | Conservation status |
| **Age Structure** | Distribution by age class | Population viability |
| **Sex Ratio** | Male:Female ratio | Reproductive potential |
| **Recruitment Rate** | New individuals entering | Population dynamics |
| **Mortality Rate** | Death rate | Threat assessment |
| **Minimum Viable Population (MVP)** | Threshold for persistence | Conservation planning |

### 5.4 Habitat & Ecosystem Metrics

| Metric | Description | Measurement |
|--------|-------------|-------------|
| **Habitat Area** | Total extent | km² or hectares |
| **Habitat Fragmentation** | Patch connectivity | Edge:area ratio, connectivity index |
| **Habitat Quality Index** | Suitability score | Multi-factor composite |
| **Vegetation Cover** | % of area vegetated | Remote sensing |
| **Canopy Cover** | Forest structure | LiDAR or field measurement |
| **Biomass** | Living matter | kg/m² or tons/ha |
| **Net Primary Productivity (NPP)** | Carbon fixation | gC/m²/year |
| **Ecosystem Intactness** | Departure from natural | Biodiversity Intactness Index |

### 5.5 Conservation Status Metrics

| Framework | Categories | Application |
|-----------|------------|-------------|
| **IUCN Red List** | LC, NT, VU, EN, CR, EW, EX | Species threat status |
| **Living Planet Index (LPI)** | Percentage change from baseline | Population trends |
| **Red List Index (RLI)** | 0 (all extinct) to 1 (all LC) | Regional/taxonomic trends |
| **Species Status Score** | Composite threat level | Multi-criteria assessment |
| **Protected Area Coverage** | % of habitat protected | Conservation progress |
| **Key Biodiversity Areas (KBA)** | Sites of global importance | Priority identification |

### 5.6 Migration & Movement Metrics

| Metric | Description | Data Source |
|--------|-------------|-------------|
| **Migration Timing** | Arrival/departure dates | Phenological records |
| **Flyway Population Estimate** | Regional abundance | Survey counts |
| **Stopover Duration** | Time at staging sites | Tracking data |
| **Movement Distance** | Total travel | Telemetry |
| **Home Range Size** | Area used | GPS tracking |
| **Connectivity Index** | Habitat network function | Landscape modeling |

---

## 6. Cross-Domain Analysis

### 6.1 Air-Water Correlations

| Relationship | Metrics | Analysis Type |
|--------------|---------|---------------|
| **Acid Deposition Impact** | SO₂, NO₂ → Water pH, Alkalinity | Regression, lag analysis |
| **Particulate Settling** | PM → TSS, Turbidity | Deposition modeling |
| **Atmospheric Nitrogen** | NOx → Water Nitrate | Mass balance |
| **Mercury Deposition** | Air Hg → Water/Fish Hg | Bioaccumulation modeling |
| **Dust Transport** | PM10 → Surface water nutrients | Source tracking |

### 6.2 Climate-Biodiversity Links

| Relationship | Metrics | Analysis Type |
|--------------|---------|---------------|
| **Temperature-Range Shift** | Temperature anomaly → Species distribution | SDM, trend analysis |
| **Phenology Shifts** | Degree days → Migration/flowering timing | Time series correlation |
| **Drought-Fire-Habitat** | PDSI → Fire → Habitat loss | Cascade modeling |
| **Sea Level-Coastal Habitat** | Sea level → Wetland area | Inundation modeling |
| **Thermal Stress-Coral** | SST anomaly, DHW → Coral bleaching | Threshold analysis |
| **Ocean Acidification-Calcifiers** | pH, Ω → Shell-forming organisms | Impact assessment |

### 6.3 Pollution Source Tracing

| Method | Data Required | Output |
|--------|---------------|--------|
| **Chemical Fingerprinting** | Multi-pollutant ratios | Source identification |
| **Isotope Analysis** | Stable isotope signatures | Origin determination |
| **Back-Trajectory Analysis** | Wind patterns + pollutant data | Atmospheric source regions |
| **Watershed Loading Model** | Land use + runoff + concentration | Nonpoint source quantification |
| **Receptor Modeling** | Multi-pollutant time series | Source apportionment % |

### 6.4 Multi-Variate Analysis Methods

| Method | Application | Output |
|--------|-------------|--------|
| **Principal Component Analysis (PCA)** | Dimensionality reduction | Major drivers identification |
| **Cluster Analysis** | Site/sample grouping | Pattern discovery |
| **Discriminant Analysis** | Classification | Category prediction |
| **Canonical Correspondence Analysis (CCA)** | Species-environment relationships | Ecological gradients |
| **Structural Equation Modeling (SEM)** | Causal pathways | Direct/indirect effects |
| **Machine Learning Classification** | Pattern recognition | Automated categorization |

### 6.5 Anomaly Detection Algorithms

| Algorithm | Use Case | Parameters |
|-----------|----------|------------|
| **Z-Score** | Simple outlier detection | Threshold (typically ±2-3σ) |
| **IQR Method** | Robust outlier detection | 1.5× or 3× IQR |
| **Moving Average Deviation** | Time series anomalies | Window size, threshold |
| **CUSUM** | Change point detection | Sensitivity parameter |
| **Isolation Forest** | Multi-dimensional anomalies | Contamination rate |
| **LSTM Autoencoder** | Complex temporal patterns | Architecture, threshold |

### 6.6 Trend Forecasting Methods

| Method | Data Type | Forecast Horizon |
|--------|-----------|------------------|
| **Linear Regression** | Trend estimation | Long-term |
| **ARIMA/SARIMA** | Seasonal time series | Short to medium |
| **Exponential Smoothing** | Level/trend/seasonal | Short to medium |
| **Prophet** | Multiple seasonality | Medium to long |
| **LSTM Neural Networks** | Complex patterns | Short to medium |
| **Ensemble Methods** | Combined forecasts | All horizons |

---

## 7. Report Types

### 7.1 Temporal Summary Reports

| Report Type | Frequency | Content |
|-------------|-----------|---------|
| **Real-Time Dashboard** | Continuous | Current conditions, alerts |
| **Daily Summary** | Daily | 24-hr statistics, max/min/mean |
| **Weekly Report** | Weekly | 7-day trends, week-over-week comparison |
| **Monthly Report** | Monthly | Monthly statistics, comparison to normal |
| **Seasonal Report** | Quarterly | Seasonal patterns, trends |
| **Annual Report** | Yearly | Year summary, annual trends, year-over-year |
| **Decadal Assessment** | 10 years | Long-term trends, climate signals |

### 7.2 Alert & Exceedance Reports

| Alert Type | Trigger Condition | Response Time |
|------------|-------------------|---------------|
| **Threshold Exceedance** | Value > standard | Immediate |
| **Rapid Change Alert** | Rate of change > limit | Immediate |
| **Trend Alert** | Projected exceedance | Hours to days |
| **Multi-Parameter Alert** | Combined conditions | Immediate |
| **Forecast Alert** | Predicted conditions | 24-72 hours |
| **Health Advisory** | AQI/WQI levels | Immediate to daily |
| **Emergency Notification** | Hazardous conditions | Immediate |

### 7.3 Comparative Analysis Reports

| Comparison Type | Description | Use Case |
|-----------------|-------------|----------|
| **Year-over-Year** | Same period, different years | Trend identification |
| **Location-to-Location** | Same period, different sites | Spatial patterns |
| **Baseline Comparison** | Current vs reference period | Change detection |
| **Standard Comparison** | Measured vs regulatory limit | Compliance |
| **Percentile Ranking** | Position in historical distribution | Context |
| **Peer Comparison** | Similar sites/regions | Benchmarking |

### 7.4 Regulatory Compliance Reports

| Report Type | Framework | Content |
|-------------|-----------|---------|
| **NAAQS Compliance** | Clean Air Act | Criteria pollutant attainment |
| **CWA 303(d)** | Clean Water Act | Impaired waters listing |
| **CWA 305(b)** | Clean Water Act | Water quality inventory |
| **NPDES DMR** | Discharge permits | Effluent monitoring data |
| **ESA Monitoring** | Endangered Species Act | Species status reports |
| **EU WFD Status** | Water Framework Directive | Ecological/chemical status |
| **Paris Agreement NDC** | Climate treaty | Emissions tracking |

### 7.5 Public Health Advisories

| Advisory Type | Trigger | Audience |
|---------------|---------|----------|
| **Air Quality Health Advisory** | AQI > 100 | General public, sensitive groups |
| **Heat Advisory/Warning** | Extreme temperatures | General public |
| **Beach/Swimming Advisory** | Bacteria levels | Recreational users |
| **Harmful Algal Bloom Alert** | Toxin detection | Water users |
| **Fish Consumption Advisory** | Contaminant levels | Anglers, communities |
| **Wildfire Smoke Advisory** | PM2.5 from fires | General public |

### 7.6 Research Export Formats

| Format | Description | Use Case |
|--------|-------------|----------|
| **CSV** | Comma-separated values | General analysis |
| **JSON** | JavaScript Object Notation | Web applications, APIs |
| **NetCDF** | Network Common Data Form | Climate/ocean science |
| **GeoTIFF** | Georeferenced imagery | Spatial analysis |
| **GeoJSON** | Geographic JSON | Web mapping |
| **HDF5** | Hierarchical Data Format | Large datasets |
| **Parquet** | Columnar storage | Big data analytics |
| **Shapefile** | GIS vector data | Traditional GIS |
| **KML/KMZ** | Google Earth format | Visualization |

---

## 8. Statistical Methods

### 8.1 Descriptive Statistics

| Statistic | Formula | Application |
|-----------|---------|-------------|
| **Mean** | x̄ = Σxi / n | Central tendency |
| **Median** | Middle value when sorted | Robust central tendency |
| **Mode** | Most frequent value | Categorical data |
| **Standard Deviation** | σ = √(Σ(xi - x̄)² / n) | Spread |
| **Variance** | σ² = Σ(xi - x̄)² / n | Spread (squared) |
| **Coefficient of Variation** | CV = σ / x̄ × 100 | Relative variability |
| **Skewness** | Third moment | Distribution asymmetry |
| **Kurtosis** | Fourth moment | Distribution tails |
| **Range** | max - min | Data spread |
| **Interquartile Range** | Q3 - Q1 | Robust spread |

### 8.2 Percentile Calculations

| Percentile | Description | Application |
|------------|-------------|-------------|
| **P0 (Min)** | Minimum value | Lower bound |
| **P10** | 10th percentile | Low extreme |
| **P25 (Q1)** | First quartile | Lower spread |
| **P50 (Median)** | Second quartile | Central tendency |
| **P75 (Q3)** | Third quartile | Upper spread |
| **P90** | 90th percentile | High extreme |
| **P95** | 95th percentile | Regulatory standard (some pollutants) |
| **P98** | 98th percentile | Regulatory standard (EU) |
| **P99** | 99th percentile | Extreme events |
| **P100 (Max)** | Maximum value | Upper bound |

### 8.3 Moving Averages & Smoothing

| Method | Formula | Use Case |
|--------|---------|----------|
| **Simple Moving Average (SMA)** | Σ(xi) / n over window | Basic smoothing |
| **Weighted Moving Average (WMA)** | Σ(wi × xi) / Σwi | Weighted recent values |
| **Exponential Moving Average (EMA)** | α × xt + (1-α) × EMAt-1 | Responsive smoothing |
| **NowCast Algorithm** | EPA-specific weighting | Real-time AQI |
| **LOESS/LOWESS** | Local regression | Trend extraction |
| **Savitzky-Golay Filter** | Polynomial smoothing | Signal processing |

### 8.4 Trend Analysis Methods

| Method | Description | Output |
|--------|-------------|--------|
| **Linear Regression** | y = mx + b | Slope, intercept, R² |
| **Mann-Kendall Test** | Non-parametric trend | Tau, p-value |
| **Sen's Slope** | Median of pairwise slopes | Robust trend estimate |
| **Theil-Sen Estimator** | Robust regression | Slope estimate |
| **Pettitt Test** | Change point detection | Change point location |
| **CUSUM Analysis** | Cumulative sum | Shift detection |
| **Seasonal Kendall Test** | Seasonal trend | Seasonally-adjusted trend |

### 8.5 Correlation Analysis

| Method | Use Case | Range |
|--------|----------|-------|
| **Pearson Correlation** | Linear relationships | -1 to +1 |
| **Spearman Correlation** | Monotonic relationships | -1 to +1 |
| **Kendall's Tau** | Ordinal association | -1 to +1 |
| **Cross-Correlation** | Lagged relationships | -1 to +1 per lag |
| **Partial Correlation** | Controlled relationships | -1 to +1 |
| **Correlation Matrix** | Multi-variable relationships | Matrix of coefficients |

### 8.6 Time Series Decomposition

| Component | Description | Method |
|-----------|-------------|--------|
| **Trend** | Long-term direction | Moving average, regression |
| **Seasonal** | Regular periodic pattern | Seasonal indices |
| **Cyclical** | Irregular multi-year patterns | Filtering |
| **Residual** | Random variation | Remainder after decomposition |

#### Decomposition Models
- **Additive**: Y = T + S + C + R
- **Multiplicative**: Y = T × S × C × R
- **STL (Seasonal-Trend-LOESS)**: Robust decomposition

### 8.7 Regression Analysis

| Type | Use Case | Requirements |
|------|----------|--------------|
| **Simple Linear** | One predictor | Linear relationship |
| **Multiple Linear** | Multiple predictors | Linear, independence |
| **Polynomial** | Curvilinear | Higher-order terms |
| **Logistic** | Binary outcome | Categorical response |
| **Poisson** | Count data | Non-negative integers |
| **Quantile** | Percentile modeling | Non-normal distributions |
| **Ridge/Lasso** | Regularized | Multicollinearity, feature selection |

---

## 9. Data Quality Indicators

### 9.1 Completeness Metrics

| Metric | Calculation | Acceptable Level |
|--------|-------------|------------------|
| **Data Capture Rate** | (Valid records / Expected) × 100 | >75-90% |
| **Uptime** | (Operational time / Total time) × 100 | >95% |
| **Missing Data Percentage** | (Missing / Total) × 100 | <10% |
| **Consecutive Missing** | Longest gap in records | Site-specific |

### 9.2 Accuracy Metrics

| Metric | Description | Assessment |
|--------|-------------|------------|
| **Precision** | Reproducibility of measurements | Replicate analysis |
| **Accuracy** | Closeness to true value | Reference standards |
| **Bias** | Systematic deviation | Calibration checks |
| **Detection Limit** | Minimum detectable amount | Method-specific |
| **Measurement Uncertainty** | Combined error | Error propagation |

### 9.3 Quality Flags

| Flag | Description | Action |
|------|-------------|--------|
| **Valid** | Passed all QC checks | Use as-is |
| **Suspect** | Potential issue detected | Review/investigate |
| **Invalid** | Failed QC checks | Exclude from analysis |
| **Estimated** | Gap-filled or interpolated | Use with caution |
| **Preliminary** | Not yet validated | Subject to revision |
| **Final** | Fully validated | Archival quality |

---

## 10. Implementation Priority

### Phase 1: Core Metrics (Months 1-3)

**Air Quality**
- [ ] AQI calculation for all criteria pollutants
- [ ] Hourly/daily/monthly aggregations
- [ ] Threshold exceedance alerts
- [ ] Basic trend visualization

**Water Quality**
- [ ] WQI calculation
- [ ] Parameter trend tracking
- [ ] Exceedance reporting
- [ ] Basic alerts

**Climate**
- [ ] Temperature/precipitation anomalies
- [ ] Degree day calculations
- [ ] Comparison to normals
- [ ] Extreme event tracking

### Phase 2: Advanced Analytics (Months 4-6)

**Cross-Domain**
- [ ] Correlation matrices
- [ ] Multi-parameter anomaly detection
- [ ] Basic forecasting (ARIMA)
- [ ] Source apportionment (preliminary)

**Biodiversity**
- [ ] Species richness calculations
- [ ] Diversity indices
- [ ] Population trend tracking
- [ ] Habitat metrics

**Marine**
- [ ] SST anomalies
- [ ] Ocean chemistry indices
- [ ] Marine heat wave detection
- [ ] Climate index correlations

### Phase 3: Reporting & Export (Months 7-9)

**Reports**
- [ ] Automated daily/weekly/monthly reports
- [ ] Compliance report templates
- [ ] Public health advisory system
- [ ] Custom report builder

**Export**
- [ ] CSV/JSON export API
- [ ] NetCDF support
- [ ] GeoJSON spatial export
- [ ] Report PDF generation

### Phase 4: Machine Learning & Forecasting (Months 10-12)

**Advanced Analytics**
- [ ] ML anomaly detection
- [ ] Ensemble forecasting
- [ ] Pattern recognition
- [ ] Causal inference models

**Integration**
- [ ] Cross-domain dashboard
- [ ] Real-time streaming analytics
- [ ] Mobile alerts
- [ ] API documentation

---

## Appendix A: Reference Standards

### US EPA Standards
- National Ambient Air Quality Standards (NAAQS)
- Safe Drinking Water Act Standards
- Clean Water Act Section 304(a) Criteria

### WHO Guidelines
- Air Quality Guidelines (2021)
- Drinking Water Quality Guidelines (2017)

### EU Directives
- Air Quality Directive 2008/50/EC
- Water Framework Directive 2000/60/EC

### International Standards
- WMO Climate Normals (1991-2020)
- IPCC Climate Assessment Reports
- CBD Biodiversity Indicators

---

## Appendix B: Glossary

| Term | Definition |
|------|------------|
| **Anomaly** | Deviation from a reference value (usually long-term average) |
| **AQI** | Air Quality Index - standardized pollutant reporting scale |
| **Breakpoint** | Concentration threshold defining AQI category boundaries |
| **Criteria Pollutant** | Six pollutants regulated under US Clean Air Act |
| **Exceedance** | Measurement above regulatory or advisory threshold |
| **Normal** | Long-term average (typically 30-year period) |
| **Percentile** | Value below which a percentage of data falls |
| **WQI** | Water Quality Index - composite water quality score |

---

*Document maintained by Environmental Monitoring Analytics Team*  
*Last updated: February 5, 2026*
