# Peter's IA Finance App

A comprehensive Streamlit web application for analyzing Iowa campaign finance data from the Iowa Open Data Portal. This dashboard provides deep insights into campaign contributions and expenditures, with powerful filtering, visualization, and export capabilities.

**Created by Peter Owens**

## Features

### 🔍 Advanced Committee Search
- **Multi-select Committee Type Filter**: Filter by multiple committee types simultaneously (defaults include Governor, Attorney General, Auditor of State, Secretary of Agriculture, Secretary of State, and Treasurer of State)
- **Activity Date Filter**: Filter committees by minimum data publication date
- **Dynamic Filtering**: All filters work together to narrow down results in real-time
- **Latest Data Indicators**: See when each committee's data was last updated

### 📊 Comprehensive Committee Analysis
- **Financial Overview**: 
  - Total Raised
  - Total Spent
  - Cash on Hand (calculated from cash contributions only)
  - Latest Data Available date
- **Cash on Hand Analysis**:
  - Starting and Ending COH calculations
  - Year-over-year COH breakdown table
  - Proper handling of filtered date ranges
- **Interactive Visualizations**:
  - Top 5 States by Number of Donors
  - Top 5 States by Sum of Donations
  - Top 5 Donors by Sum of Donations
  - Donations Over Time (Monthly)
  - Top 5 Expenditure Recipients

### 📥 Data Export
- **PDF Reports**: One-click professional PDF generation with:
  - Committee metadata and financial summary
  - Cash on Hand analysis tables
  - Top 10 Contributions and Expenditures data tables
- **CSV Exports**: Full dataset downloads for both contributions and expenditures
- **Filtered Data**: All exports respect current date/year filters

### 🎨 Modern UI
- Clean, professional interface with green accent theme
- Compact sidebar with efficient use of space
- Responsive layout optimized for data analysis
- Fixed top bar with navigation

## Prerequisites

- Python 3.8 or higher
- pip (Python package installer)

## Installation

1. **Clone or download this repository**

2. **Create a virtual environment (recommended)**:
   ```bash
   python -m venv venv
   ```

3. **Activate the virtual environment**:
   - On Windows:
     ```bash
     venv\Scripts\activate
     ```
   - On macOS/Linux:
     ```bash
     source venv/bin/activate
     ```

4. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

5. **Configure Secrets** (for deployment):
   
   Create a `.streamlit/secrets.toml` file:
   ```toml
   SOCRATA_TOKEN = "your_token_here"
   ```
   
   For local development, you can also set an environment variable:
   ```bash
   export SOCRATA_TOKEN="your_token_here"
   ```

## Running the Application

1. **Start the Streamlit app**:
   ```bash
   streamlit run app.py
   ```

2. **Open your browser**:
   The app will automatically open in your default web browser at `http://localhost:8501`

## Usage

### Searching for Committees

1. **Use the Search Sidebar**:
   - Select one or more Committee Types (multiselect)
   - Choose Party, Office, District, Candidate Name, or Committee Name filters
   - Set "Filter by Activity Since" to show only committees with data after a specific date
   - Click "Clear" to reset all filters to defaults

2. **View Committee Details**:
   - Click on any committee in the search results
   - View financial metrics and latest data date
   - Explore the Analysis tab for detailed breakdowns and visualizations
   - Use the Exports tab to download PDF reports or CSV data

### Analyzing Committee Finances

- **Cash on Hand**: Automatically calculated from cash contributions (transaction type "CON") only
- **Filtering**: Apply year or date range filters to analyze specific time periods
- **Visualizations**: Interactive charts show donor patterns, geographic distribution, and spending trends

### Exporting Data

- **PDF Reports**: Click "Download Report" in the Exports tab for a comprehensive PDF
- **CSV Files**: Download full contribution or expenditure datasets with all columns

## Data Sources

The application connects to the following Iowa Open Data datasets via the Socrata API:

- **Contributions**: Dataset ID `smfg-ds7h`
- **Expenditures**: Dataset ID `3adi-mht4`
- **Committee List**: Dataset ID `5dtu-swbk`

All data is sourced from [data.iowa.gov](https://data.iowa.gov)

## Technical Details

- **Framework**: Streamlit
- **Data Processing**: Pandas
- **API Client**: Socrata (sodapy)
- **Visualizations**: Plotly
- **PDF Generation**: ReportLab
- **Caching**: Aggressive caching for performance (committee lists, metadata, etc.)
- **Rate Limiting**: 60-second timeout for API calls

## Configuration

### Theme Customization

The app uses a green theme defined in `.streamlit/config.toml`. You can customize colors there.

### Secrets Management

For production deployment, use Streamlit's secrets management:
- **Streamlit Cloud**: Add secrets in the app settings
- **Local Development**: Use `.streamlit/secrets.toml` or environment variables

## Troubleshooting

- **No committees showing**: 
  - Check your internet connection
  - Verify the Iowa Open Data Portal is accessible
  - Check if filters are too restrictive
  
- **Slow loading**: 
  - Initial committee list load may take a moment (cached after first load)
  - Large date ranges may take longer to process
  
- **Data not appearing**: 
  - Some committees may have no contributions or expenditures in the selected date range
  - Try adjusting the "Filter by Activity Since" date
  
- **API Timeout Errors**: 
  - The app uses a 60-second timeout
  - Very large queries may still timeout - try narrowing date ranges

## Author

**Peter Owens**

- X (Twitter): [@pcowens_](https://x.com/pcowens_)
- Email: 16petero@gmail.com

## License

This project is provided as-is for educational and analytical purposes.

## Disclaimer

This website is in development. All data is from publicly available sources. There may be errors or technical issues.

Copyright Peter Owens 2026
