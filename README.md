# Iowa Campaign Finance Dashboard

A comprehensive Streamlit web application for analyzing Iowa campaign finance data from the Iowa Open Data Portal. This dashboard allows users to explore campaign contributions and expenditures by committee, visualize fundraising trends, and export complete datasets.

## Features

- **Committee Selection**: Browse and select from all available campaign committees
- **Date Range Filtering**: Filter contributions and expenditures by custom date ranges
- **Interactive Visualizations**:
  - Top 10 Donors bar chart
  - Fundraising Over Time line chart (monthly aggregation)
- **Data Export**: Download full datasets as CSV files with all columns including address and state information
- **Real-time Data**: Connects directly to Iowa's Socrata Open Data API

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

## Running the Application

1. **Start the Streamlit app**:
   ```bash
   streamlit run app.py
   ```

2. **Open your browser**:
   The app will automatically open in your default web browser at `http://localhost:8501`

## Usage

1. **Select a Committee**: Use the dropdown in the sidebar to choose a campaign committee
2. **Filter by Date** (optional): Check "Filter by Date Range" and select your desired date range
3. **Explore Visualizations**: View the "Visuals" tab for charts and graphs
4. **Export Data**: Use the "Contributions Export" and "Expenditures Export" tabs to download full CSV files

## Data Sources

The application connects to the following Iowa Open Data datasets:
- **Contributions**: Dataset ID `smfg-ds7h`
- **Expenditures**: Dataset ID `3adi-mht4`
- **Committee List**: Dataset ID `5dtu-swbk`

All data is sourced from [data.iowa.gov](https://data.iowa.gov)

## Optional: Using an App Token

By default, the app uses anonymous access to the Socrata API. For higher rate limits and better performance, you can obtain a free app token from [Socrata](https://dev.socrata.com/register) and update the `app_token` parameter in `app.py`:

```python
client = Socrata("data.iowa.gov", app_token="YOUR_TOKEN_HERE")
```

## Troubleshooting

- **No committees showing**: Check your internet connection and verify that the Iowa Open Data Portal is accessible
- **Slow loading**: The initial committee list load may take a moment. Subsequent loads are cached
- **Data not appearing**: Some committees may have no contributions or expenditures in the selected date range

## License

This project is provided as-is for educational and analytical purposes.

