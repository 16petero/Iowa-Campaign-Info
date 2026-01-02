import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
from sodapy import Socrata
from datetime import datetime, date
import plotly.express as px
import plotly.graph_objects as go
import requests
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from io import BytesIO
import os

# Constants
DEFAULT_START_DATE = date(2024, 1, 1)

# Committee Categories Mapping
COMMITTEE_CATEGORIES = {
    "Statewide": ["Governor", "Attorney General", "Auditor of State", "Secretary of State", "Secretary of Agriculture", "Treasurer of State"],
    "Legislature": ["State House", "State Senate"],
    "City": ["City Candidate - City Council", "City Candidate - Mayor"],
    "County": ["County Candidate - Attorney", "County Candidate - Auditor", "County Candidate - Recorder", "County Candidate - Sheriff", "County Candidate - Supervisor", "County Candidate - Treasurer"],
    "PAC": ["City PAC", "Iowa PAC", "County PAC"],
    "Other": ["Other Political Subdivision Candidate", "School Board Candidate", "School Board or Other Political Subdivision PAC", "State Central Committee", "Local Ballot Issue"]
}

# Theme colors (matching .streamlit/config.toml)
THEME_PRIMARY_COLOR = "#2E8B57"  # SeaGreen
THEME_PRIMARY_DARK = "#1F5F3F"   # Darker green for gradients/borders

# Page configuration
st.set_page_config(
    page_title="Peter's IA $ App",
    page_icon="💲",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better aesthetics - using theme colors
# Use THEME_PRIMARY_COLOR defined above
THEME_COLOR_DARK = "#3CB371"  # Lighter green for gradient end

st.markdown(f"""
<style>
    /* --- RESET & BASIC SETUP --- */
    .main .block-container {{
        padding-top: 0.5rem !important;
        padding-bottom: 1.5rem !important;
        max-width: 95%;
    }}
    
    /* Remove extra padding from first element */
    .main .block-container > div:first-child {{
        padding-top: 0 !important;
        margin-top: 0 !important;
    }}

    /* --- SIDEBAR FIXES --- */
    /* Restore default sidebar behavior (collapsible) */
    section[data-testid="stSidebar"] {{
        top: 0 !important; /* Reset top to avoid gaps */
        padding-top: 70px !important; /* Push content down to match top bar */
        background-color: #f8f9fa;
        z-index: 998;
    }}

    /* Reduce padding at the very top of the sidebar content */
    section[data-testid="stSidebar"] .block-container {{
        padding-top: 1rem !important;
        padding-bottom: 0rem !important;
    }}
    
    /* Tighten space between sidebar widgets */
    section[data-testid="stSidebar"] .stElementContainer {{
        margin-bottom: -0.5rem !important;
    }}
    
    /* Remove padding around the 'Search' header */
    div[data-testid="stSidebarHeader"] {{
        padding-bottom: 0rem !important;
    }}
    
    /* Reduce Sidebar Header/Content Padding */
    div[data-testid="stSidebarContent"] {{
        padding-top: 0rem !important;
    }}
    
    /* --- HEADER & NAVIGATION FIXES (MOBILE) --- */
    /* Make header transparent but clickable (restores Hamburger Menu) */
    header[data-testid="stHeader"] {{
        background: transparent !important;
        z-index: 1001 !important; /* Above custom top bar */
        height: 70px !important;
    }}
    
    /* Hide the red/orange decoration line */
    header[data-testid="stHeader"] .decoration {{
        display: none;
    }}

    /* Hide the 3-dots menu if desired, but KEEP the hamburger */
    #MainMenu {{
        visibility: hidden;
    }}
    
    /* --- CUSTOM TOP BAR --- */
    .top-bar {{
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        width: 100%;
        height: 70px;
        background: linear-gradient(135deg, {THEME_PRIMARY_COLOR} 0%, {THEME_COLOR_DARK} 100%); /* Green Theme */
        color: white;
        padding: 0 1rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        border-bottom: 2px solid #228B22;
        z-index: 1000;
        display: flex;
        align-items: center;
    }}
    
    .top-bar-content {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        width: 100%;
        height: 100%;
    }}
    
    .top-bar-title {{
        font-size: 1.5rem;
        font-weight: 700;
        margin: 0;
        white-space: nowrap;
        margin-left: 3.5rem; /* Space for Hamburger Menu */
    }}
    
    .top-bar-center {{
        flex: 1;
        display: flex;
        justify-content: center;
        align-items: center;
    }}
    
    .top-bar-info {{
        display: flex;
        gap: 2rem;
        align-items: center;
        font-size: 0.9rem;
    }}
    
    .top-bar-page {{
        background-color: rgba(255,255,255,0.2);
        padding: 0.4rem 0.8rem;
        border-radius: 4px;
        font-weight: 500;
        white-space: nowrap;
    }}
    
    .top-bar-update {{
        color: rgba(255,255,255,0.9);
    }}

    /* --- RESPONSIVE / MOBILE TWEAKS --- */
    @media (max-width: 640px) {{
        .top-bar-title {{
            font-size: 1.1rem;
            margin-left: 3rem; 
        }}
        .top-bar-update {{
            display: none; /* Hide update time on mobile */
        }}
        .top-bar-page {{
            font-size: 0.8rem;
            padding: 0.2rem 0.5rem;
        }}
        /* Ensure main content isn't covered */
        .main .block-container {{
            padding-top: 80px !important;
        }}
    }}

    /* --- GENERAL STYLING --- */
    [data-testid="stMetricValue"] {{
        font-size: 1.8rem;
        font-weight: 600;
    }}
    
    footer[data-testid="stFooter"] {{
        display: none !important;
    }}
    
    /* Better button styling - Green theme for all buttons */
    .stButton > button {{
        border-radius: 6px;
        transition: all 0.2s ease;
        border: 1px solid {THEME_PRIMARY_COLOR};
        background-color: {THEME_PRIMARY_COLOR};
        color: white !important;
    }}
    
    .stButton > button:hover {{
        transform: translateY(-1px);
        box-shadow: 0 2px 6px rgba(0,0,0,0.1);
        background-color: {THEME_COLOR_DARK};
        border-color: {THEME_COLOR_DARK};
        color: white !important;
    }}
    
    /* Ensure primary buttons also use green */
    button[kind="primary"] {{
        background-color: {THEME_PRIMARY_COLOR} !important;
        color: white !important;
        border-color: {THEME_PRIMARY_COLOR} !important;
    }}
    
    button[kind="primary"]:hover {{
        background-color: {THEME_COLOR_DARK} !important;
        border-color: {THEME_COLOR_DARK} !important;
        color: white !important;
    }}
    
    /* Secondary buttons also use green */
    button[kind="secondary"] {{
        background-color: {THEME_PRIMARY_COLOR} !important;
        color: white !important;
        border-color: {THEME_PRIMARY_COLOR} !important;
    }}
    
    button[kind="secondary"]:hover {{
        background-color: {THEME_COLOR_DARK} !important;
        border-color: {THEME_COLOR_DARK} !important;
        color: white !important;
    }}
    
    /* Better card appearance for committees */
    .committee-card {{
        border-left: 3px solid {THEME_PRIMARY_COLOR};
        padding-left: 12px;
    }}
    
    /* Remove extra spacing in tabs */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 8px;
        margin-top: 0 !important;
        padding-top: 0 !important;
    }}
    
    /* Remove grey bar/divider above tabs */
    .stTabs > div:first-child {{
        border-top: none !important;
        margin-top: 0 !important;
        padding-top: 0 !important;
    }}
    
    /* Remove any horizontal rules before tabs */
    hr {{
        display: none !important;
    }}
    
    /* Reduce spacing between search results and metrics */
    [data-testid="stMetricContainer"] {{
        margin-bottom: 0.5rem !important;
    }}
    
    /* Adjust main content to account for fixed top bar */
    .main .block-container {{
        padding-top: calc(0.5rem + 70px) !important;
    }}
</style>
""", unsafe_allow_html=True)

# Initialize Socrata client with secrets management
try:
    # Try to get token from Streamlit secrets (for deployment)
    socrata_token = st.secrets.get("SOCRATA_TOKEN", None)
    if socrata_token is None:
        # Fallback to environment variable (for local development)
        socrata_token = os.getenv("SOCRATA_TOKEN", None)
    if socrata_token is None:
        # Final fallback - show warning but don't crash
        st.warning("⚠️ Socrata token not found. Please set SOCRATA_TOKEN in secrets or environment variables.")
        socrata_token = None
except Exception as e:
    # If secrets don't exist (local run without secrets file), try environment variable
    socrata_token = os.getenv("SOCRATA_TOKEN", None)
    if socrata_token is None:
        st.warning("⚠️ Socrata token not found. Please set SOCRATA_TOKEN in secrets or environment variables.")

client = Socrata("data.iowa.gov", app_token=socrata_token, timeout=60)

# Initialize session state
if 'selected_committee' not in st.session_state:
    st.session_state.selected_committee = None
if 'filter_reset_counter' not in st.session_state:
    st.session_state.filter_reset_counter = 0

# Function to get dataset metadata (last updated time)
@st.cache_data(ttl=3600)  # Cache for 1 hour
def get_dataset_metadata():
    """Get metadata for the main datasets to find last update time."""
    try:
        # Try to get metadata from the committee dataset
        metadata_url = "https://data.iowa.gov/api/views/5dtu-swbk.json"
        response = requests.get(metadata_url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            # Try to find updatedAt or similar field
            if 'rowsUpdatedAt' in data:
                return data['rowsUpdatedAt']
            elif 'updatedAt' in data:
                return data['updatedAt']
            elif 'viewLastModified' in data:
                return data['viewLastModified']
    except Exception as e:
        # If metadata fetch fails, return None
        pass
    return None

# Step 1: Load full committee dataset (cached indefinitely)
@st.cache_data(show_spinner=False)  # Disable default spinner to show custom message
def load_committee_dataset():
    """Fetch all committee data for filtering."""
    try:
        results = client.get("5dtu-swbk", select="*", limit=500000)
        df = pd.DataFrame.from_records(results)
        return df
    except Exception as e:
        st.error(f"Error loading committee dataset: {str(e)}")
        return pd.DataFrame()

# Server-side filtering: Get committees with data since a given date
@st.cache_data(ttl=3600)
def get_committees_with_data_since(min_date):
    """Get list of committees that have published data since the given date."""
    try:
        # Format date for Socrata query
        date_str = min_date.strftime('%Y-%m-%dT00:00:00')
        # Query for distinct committee names with date >= min_date
        results = client.get(
            "smfg-ds7h",
            select="DISTINCT committee_nm",
            where=f"date >= '{date_str}'",
            limit=200000
        )
        # Extract committee names from results
        committee_names = set()
        for record in results:
            if 'committee_nm' in record and record['committee_nm']:
                committee_names.add(record['committee_nm'])
        return list(committee_names)
    except Exception as e:
        st.warning(f"Could not fetch committees: {str(e)}")
        return []

# Helper function to get latest data date for a committee
@st.cache_data(ttl=3600)
def get_committee_latest_date(committee_name):
    """Get the latest data date for a committee (cached)."""
    try:
        escaped_name = committee_name.replace("'", "''")
        # Get latest contribution date
        contrib_query = f"committee_nm='{escaped_name}'"
        contrib_dates = client.get("smfg-ds7h", 
                                   where=contrib_query,
                                   select="date, contribution_date, transaction_date",
                                   limit=1,
                                   order="date DESC NULL LAST")
        # Get latest expenditure date  
        expend_query = f"committee_nm='{escaped_name}'"
        expend_dates = client.get("3adi-mht4",
                                  where=expend_query,
                                  select="date, expenditure_date, transaction_date",
                                  limit=1,
                                  order="date DESC NULL LAST")
        
        latest_date = None
        for record in contrib_dates:
            for col in ['date', 'contribution_date', 'transaction_date']:
                if col in record and record[col]:
                    try:
                        date_val = pd.to_datetime(record[col])
                        if latest_date is None or date_val > latest_date:
                            latest_date = date_val
                    except:
                        pass
        
        for record in expend_dates:
            for col in ['date', 'expenditure_date', 'transaction_date']:
                if col in record and record[col]:
                    try:
                        date_val = pd.to_datetime(record[col])
                        if latest_date is None or date_val > latest_date:
                            latest_date = date_val
                    except:
                        pass
        
        return latest_date
    except:
        return None

# Step 2: Load committee-specific data
@st.cache_data(ttl=3600, show_spinner=False)  # Cache for 1 hour, disable default spinner
def load_committee_data(committee_name):
    """Fetch all contributions and expenditures for a specific committee."""
    try:
        # Escape single quotes in committee name for SoQL query
        escaped_name = committee_name.replace("'", "''")
        
        # Fetch contributions
        contributions_query = f"committee_nm='{escaped_name}'"
        contributions = client.get("smfg-ds7h", 
                                   where=contributions_query, 
                                   select="*",
                                   limit=500000)
        df_contributions = pd.DataFrame.from_records(contributions)
        
        # Fetch expenditures
        expenditures_query = f"committee_nm='{escaped_name}'"
        expenditures = client.get("3adi-mht4", 
                                  where=expenditures_query, 
                                  select="*",
                                  limit=500000)
        df_expenditures = pd.DataFrame.from_records(expenditures)
        
        return df_contributions, df_expenditures
    except Exception as e:
        st.error(f"Error loading committee data: {str(e)}")
        return pd.DataFrame(), pd.DataFrame()

def process_contributions(df):
    """Process contributions dataframe."""
    if df.empty:
        return df
    
    df = df.copy()
    
    # Create contributor_final column
    if 'organization_nm' in df.columns and 'first_nm' in df.columns and 'last_nm' in df.columns:
        df['contributor_final'] = df.apply(
            lambda row: row['organization_nm'] if pd.notna(row['organization_nm']) and str(row['organization_nm']).strip() != '' 
            else f"{row.get('first_nm', '')} {row.get('last_nm', '')}".strip(),
            axis=1
        )
    
    # Convert date column to datetime
    date_columns = ['date', 'contribution_date', 'transaction_date']
    for col in date_columns:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce')
    
    # Convert amount to float
    amount_columns = ['amount', 'contribution_amount', 'transaction_amount']
    for col in amount_columns:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    return df

def process_expenditures(df):
    """Process expenditures dataframe."""
    if df.empty:
        return df
    
    df = df.copy()
    
    # Convert date column to datetime
    date_columns = ['date', 'expenditure_date', 'transaction_date']
    for col in date_columns:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce')
    
    # Convert amount to float
    amount_columns = ['amount', 'expenditure_amount', 'transaction_amount']
    for col in amount_columns:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    return df

def generate_pdf_report(committee_name, committee_info, total_raised, total_spent, cash_on_hand, 
                        latest_data_date, df_contributions_filtered, df_expenditures_filtered,
                        df_coh, starting_coh, ending_coh, amount_col_contrib, amount_col_expend,
                        candidate_name=None, earliest_date=None, latest_date=None):
    """Generate a comprehensive PDF report for the committee."""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
    story = []
    styles = getSampleStyleSheet()
    
    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor(THEME_PRIMARY_COLOR),
        spaceAfter=30,
        alignment=TA_CENTER
    )
    story.append(Paragraph(f"Campaign Finance Report: {committee_name}", title_style))
    story.append(Spacer(1, 0.2*inch))
    
    # Metadata Block
    info_text = ""
    
    # Candidate Name
    if candidate_name:
        info_text += f"<b>Candidate Name:</b> {candidate_name}<br/>"
    else:
        info_text += f"<b>Candidate Name:</b> N/A<br/>"
    
    # Committee Info
    if committee_info is not None:
        # Handle both Series and dict
        if isinstance(committee_info, pd.Series):
            committee_info_dict = committee_info.to_dict()
        else:
            committee_info_dict = committee_info
        
        # Committee Type
        committee_type = "N/A"
        for c in ['committee_type', 'type', 'type_nm', 'committee_type_nm']:
            if c in committee_info_dict:
                val_check = committee_info_dict[c]
                if isinstance(val_check, pd.Series):
                    if not val_check.empty:
                        val_check = val_check.iloc[0] if len(val_check) > 0 else None
                    else:
                        val_check = None
                if val_check is not None:
                    val_str = str(val_check).strip()
                    if val_str and val_str.lower() not in ['nan', 'none', '']:
                        committee_type = val_str
                        break
        
        # Party
        party = "N/A"
        for c in ['party', 'party_nm', 'party_name', 'political_party']:
            if c in committee_info_dict:
                val_check = committee_info_dict[c]
                if isinstance(val_check, pd.Series):
                    if not val_check.empty:
                        val_check = val_check.iloc[0] if len(val_check) > 0 else None
                    else:
                        val_check = None
                if val_check is not None:
                    val_str = str(val_check).strip()
                    if val_str and val_str.lower() not in ['nan', 'none', '']:
                        party = val_str
                        break
        
        # District
        district = "N/A"
        for c in ['district', 'district_nbr', 'district_number', 'district_num']:
            if c in committee_info_dict:
                val_check = committee_info_dict[c]
                if isinstance(val_check, pd.Series):
                    if not val_check.empty:
                        val_check = val_check.iloc[0] if len(val_check) > 0 else None
                    else:
                        val_check = None
                if val_check is not None:
                    val_str = str(val_check).strip()
                    if val_str and val_str.lower() not in ['nan', 'none', '']:
                        district = val_str
                        break
        
        info_text += f"<b>Committee Type:</b> {committee_type}<br/>"
        info_text += f"<b>Party:</b> {party}<br/>"
        info_text += f"<b>District:</b> {district}<br/>"
    else:
        info_text += f"<b>Committee Type:</b> N/A<br/>"
        info_text += f"<b>Party:</b> N/A<br/>"
        info_text += f"<b>District:</b> N/A<br/>"
    
    # Dates
    if earliest_date and latest_date:
        if hasattr(earliest_date, 'strftime'):
            earliest_str = earliest_date.strftime('%Y-%m-%d')
        else:
            earliest_str = str(earliest_date)
        if hasattr(latest_date, 'strftime'):
            latest_str = latest_date.strftime('%Y-%m-%d')
        else:
            latest_str = str(latest_date)
        info_text += f"<b>Data Range:</b> {earliest_str} to {latest_str}<br/>"
    else:
        info_text += f"<b>Data Range:</b> N/A<br/>"
    
    if latest_data_date:
        info_text += f"<b>Latest Data:</b> {latest_data_date}<br/>"
    else:
        info_text += f"<b>Latest Data:</b> N/A<br/>"
    
    story.append(Paragraph(info_text, styles['Normal']))
    story.append(Spacer(1, 0.3*inch))
    
    # Financial Summary
    story.append(Paragraph("<b>Financial Summary</b>", styles['Heading2']))
    summary_data = [
        ['Metric', 'Amount'],
        ['Total Raised', f"${total_raised:,.2f}"],
        ['Total Spent', f"${total_spent:,.2f}"],
        ['Cash on Hand', f"${cash_on_hand:,.2f}"]
    ]
    summary_table = Table(summary_data, colWidths=[3*inch, 2*inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(THEME_PRIMARY_COLOR)),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 0.3*inch))
    
    # Cash on Hand Analysis
    story.append(Paragraph("<b>Cash on Hand Analysis</b>", styles['Heading2']))
    coh_text = f"<b>Starting COH:</b> ${starting_coh:,.2f}  |  <b>Ending COH:</b> ${ending_coh:,.2f}"
    story.append(Paragraph(coh_text, styles['Normal']))
    story.append(Spacer(1, 0.2*inch))
    
    if df_coh is not None and isinstance(df_coh, pd.DataFrame) and not df_coh.empty:
        # COH by Year table
        coh_headers = ['Year', 'Contributions', 'Expenditures', 'Net', 'Ending COH']
        coh_data = [coh_headers]
        for _, row in df_coh.iterrows():
            coh_data.append([
                str(int(row['Year'])),
                f"${row['Contributions']:,.2f}",
                f"${row['Expenditures']:,.2f}",
                f"${row['Net']:,.2f}",
                f"${row['Ending COH']:,.2f}"
            ])
        coh_table = Table(coh_data, colWidths=[0.8*inch, 1.5*inch, 1.5*inch, 1.2*inch, 1.5*inch])
        coh_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(THEME_PRIMARY_COLOR)),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 1), (-1, -1), 9)
        ]))
        story.append(coh_table)
    
    story.append(PageBreak())
    
    # Data Summary
    story.append(Paragraph("<b>Data Summary</b>", styles['Heading2']))
    story.append(Paragraph(f"<b>Total Contribution Records:</b> {len(df_contributions_filtered)}", styles['Normal']))
    story.append(Paragraph(f"<b>Total Expenditure Records:</b> {len(df_expenditures_filtered)}", styles['Normal']))
    
    # Build PDF
    doc.build(story)
    buffer.seek(0)
    return buffer

def get_committee_types_from_categories(categories):
    """Convert category selections to list of committee types.
    Handles 'Other' category specially to include catch-all types."""
    if not categories:
        return []
    
    if not isinstance(categories, list):
        categories = [categories] if categories else []
    
    committee_types = []
    all_known_types = set()
    
    # Collect all known types from defined categories
    for cat_types in COMMITTEE_CATEGORIES.values():
        all_known_types.update(cat_types)
    
    for category in categories:
        if category == "Other":
            # Include the explicit "Other" types
            committee_types.extend(COMMITTEE_CATEGORIES["Other"])
            # Also need to find types not in other categories (handled in filtering)
        else:
            # Add types from this category
            if category in COMMITTEE_CATEGORIES:
                committee_types.extend(COMMITTEE_CATEGORIES[category])
    
    return list(set(committee_types))  # Remove duplicates

def get_filter_options(df_committees, current_filters, exclude_filter=None):
    """Get available filter options based on current selections.
    exclude_filter: name of filter to exclude from filtering (so it shows all options)"""
    filtered_df = df_committees.copy()
    
    # Apply existing filters progressively, but exclude the filter we're getting options for
    if current_filters.get('category') and exclude_filter != 'category':
        # Convert categories to committee types
        selected_categories = current_filters['category']
        if not isinstance(selected_categories, list):
            selected_categories = [selected_categories] if selected_categories else []
        
        if selected_categories:
            # Get committee types from selected categories
            committee_types = get_committee_types_from_categories(selected_categories)
            
            # Handle "Other" category - include types not in other categories
            if "Other" in selected_categories:
                # Get all known types from defined categories
                all_known_types = set()
                for cat_types in COMMITTEE_CATEGORIES.values():
                    all_known_types.update(cat_types)
                
                # Find committee type column
                type_col = None
                for col in ['committee_type', 'type', 'type_nm', 'committee_type_nm']:
                    if col in filtered_df.columns:
                        type_col = col
                        break
                
                if type_col:
                    # Add types that are not in any defined category
                    all_types_in_data = set(filtered_df[type_col].dropna().astype(str).unique())
                    other_types = all_types_in_data - all_known_types
                    committee_types.extend(list(other_types))
            
            if committee_types:
                for col in ['committee_type', 'type', 'type_nm', 'committee_type_nm']:
                    if col in filtered_df.columns:
                        filtered_df = filtered_df[filtered_df[col].astype(str).isin([str(ct) for ct in committee_types])]
                        break
    
    if current_filters.get('election_year') and exclude_filter != 'election_year':
        # Try different possible column names
        for col in ['election_year', 'election_yr', 'year', 'election_year_text']:
            if col in filtered_df.columns:
                filtered_df = filtered_df[filtered_df[col].astype(str) == str(current_filters['election_year'])]
                break
    
    if current_filters.get('party') and exclude_filter != 'party':
        for col in ['party', 'party_nm', 'party_name', 'political_party']:
            if col in filtered_df.columns:
                filtered_df = filtered_df[filtered_df[col].astype(str) == str(current_filters['party'])]
                break
    
    if current_filters.get('office') and exclude_filter != 'office':
        for col in ['office', 'office_sought', 'office_nm', 'office_name']:
            if col in filtered_df.columns:
                filtered_df = filtered_df[filtered_df[col].astype(str) == str(current_filters['office'])]
                break
    
    if current_filters.get('district') and exclude_filter != 'district':
        for col in ['district', 'district_nbr', 'district_number', 'district_num']:
            if col in filtered_df.columns:
                filtered_df = filtered_df[filtered_df[col].astype(str) == str(current_filters['district'])]
                break
    
    if current_filters.get('candidate_name') and exclude_filter != 'candidate_name':
        for col in ['candidate_name', 'candidate_nm', 'candidate', 'name']:
            if col in filtered_df.columns:
                # Use contains for candidate name
                filtered_df = filtered_df[filtered_df[col].astype(str).str.contains(str(current_filters['candidate_name']), case=False, na=False)]
                break
    
    if current_filters.get('committee_name') and exclude_filter != 'committee_name':
        for col in ['committee_name', 'committee_nm', 'committee']:
            if col in filtered_df.columns:
                filtered_df = filtered_df[filtered_df[col].astype(str) == str(current_filters['committee_name'])]
                break
    
    # Get unique values for each filter
    options = {}
    
    # Committee Type
    for col in ['committee_type', 'type', 'type_nm', 'committee_type_nm']:
        if col in filtered_df.columns:
            types = sorted(filtered_df[col].dropna().unique())
            options['committee_type'] = [str(t) for t in types if str(t).strip() != '']
            break
    
    # Election Year
    for col in ['election_year', 'election_yr', 'year', 'election_year_text']:
        if col in filtered_df.columns:
            years = sorted(filtered_df[col].dropna().unique(), reverse=True)
            options['election_year'] = [str(y) for y in years]
            break
    
    # Party
    for col in ['party', 'party_nm', 'party_name', 'political_party']:
        if col in filtered_df.columns:
            parties = sorted(filtered_df[col].dropna().unique())
            options['party'] = [str(p) for p in parties if str(p).strip() != '']
            break
    
    # Office
    for col in ['office', 'office_sought', 'office_nm', 'office_name']:
        if col in filtered_df.columns:
            offices = sorted(filtered_df[col].dropna().unique())
            options['office'] = [str(o) for o in offices if str(o).strip() != '']
            break
    
    # District
    for col in ['district', 'district_nbr', 'district_number', 'district_num']:
        if col in filtered_df.columns:
            districts = sorted(filtered_df[col].dropna().unique())
            options['district'] = [str(d) for d in districts if str(d).strip() != '']
            break
    
    # Candidate Name (for search)
    for col in ['candidate_name', 'candidate_nm', 'candidate', 'name']:
        if col in filtered_df.columns:
            candidates = sorted(filtered_df[col].dropna().unique())
            options['candidate_name'] = [str(c) for c in candidates if str(c).strip() != '']
            break
    
    # Committee Name
    for col in ['committee_name', 'committee_nm', 'committee']:
        if col in filtered_df.columns:
            committees = sorted(filtered_df[col].dropna().unique())
            options['committee_name'] = [str(c) for c in committees if str(c).strip() != '']
            break
    
    return options, filtered_df

# Load committee dataset
with st.spinner("Fetching committee index..."):
    df_committees = load_committee_dataset()

if df_committees.empty:
    st.error("Unable to load committee data. Please check your connection.")
    st.stop()

# Get dataset metadata
dataset_update_time = get_dataset_metadata()
update_time_str = None
if dataset_update_time:
    try:
        # Parse timestamp (could be Unix timestamp or ISO string)
        if isinstance(dataset_update_time, (int, float)):
            update_time = datetime.fromtimestamp(dataset_update_time / 1000 if dataset_update_time > 1e10 else dataset_update_time)
        else:
            update_time = pd.to_datetime(dataset_update_time)
        update_time_str = update_time.strftime("%B %d, %Y at %I:%M %p")
    except:
        update_time_str = None

# Determine current page
current_page = "Committee View" if st.session_state.selected_committee else "Committee Search"

# Top bar component - simplified, no interactive elements
top_bar_html = f"""
<div class="top-bar">
    <div class="top-bar-content">
        <div class="top-bar-title"><a href="?home=true" target="_self" style="text-decoration: none; color: white;">Peter's IA Finance App</a></div>
        <div class="top-bar-center">
            <div class="top-bar-page">{current_page}</div>
        </div>
        <div class="top-bar-info">
            {f'<div class="top-bar-update">Last IECDB Update: {update_time_str}</div>' if update_time_str else ''}
        </div>
    </div>
</div>
"""
# Render top bar
st.markdown(top_bar_html, unsafe_allow_html=True)


# Check for home navigation via query params
if st.query_params.get("home") == "true":
    st.session_state.selected_committee = None
    st.query_params.clear()
    st.rerun()

# Page transition logic - show search or detail page
if st.session_state.selected_committee is None:
    # SEARCH PAGE
    # Title removed - using top bar instead
    
    # Initialize filters in session state
    if 'filters' not in st.session_state:
        st.session_state.filters = {
            'category': ["Statewide"],  # Default to Statewide category
            'election_year': None,
            'party': None,
            'office': None,
            'district': None,
            'candidate_name': None,
            'committee_name': None
        }
    
    # Helper function to get index for selectbox
    def get_index_for_value(options, current_value):
        """Get the index of current_value in options, or 0 if not found."""
        if current_value is None:
            return 0
        try:
            return options.index(current_value)
        except ValueError:
            return 0
    
    # Sidebar for filters
    with st.sidebar:
        # Header with inline Clear button
        header_col1, header_col2 = st.columns([2.5, 1.5])
        with header_col1:
            st.header("Search")
        with header_col2:
            st.write("")  # Spacer
            if st.button("Clear", use_container_width=True, key="clear_filters_btn_inline"):
                # Reset all filters
                st.session_state.filters = {
                    'category': ["Statewide"],
                    'election_year': None,
                    'party': None,
                    'office': None,
                    'district': None,
                    'candidate_name': None,
                    'committee_name': None
                }
                # Reset date filter to default
                st.session_state.date_filter_value = DEFAULT_START_DATE
                st.session_state.filter_reset_counter += 1
                st.rerun()
        
        # Filter by Activity Since date input - using dynamic key for reset capability
        # Initialize default if not set
        if 'date_filter_value' not in st.session_state:
            st.session_state.date_filter_value = DEFAULT_START_DATE
        
        # Use dynamic key so we can reset it
        filter_min_date = st.date_input(
            "Filter by Activity Since",
            value=st.session_state.date_filter_value,
            min_value=datetime(2000, 1, 1).date(),
            key=f"date_filter_{st.session_state.filter_reset_counter}"
        )
        # Store the current value in our own variable (not the widget's key)
        st.session_state.date_filter_value = filter_min_date
        
        st.markdown("---")
        
        # Get committees with data since the selected date
        committees_with_data = set()
        if st.session_state.date_filter_value:
            committees_with_data = set(get_committees_with_data_since(st.session_state.date_filter_value))
        
        # Filter df_committees by minimum date if filter is enabled
        df_committees_filtered = df_committees.copy()
        if st.session_state.date_filter_value and committees_with_data:
            # Filter to only committees with data since the selected date
            committee_col = None
            for col in ['committee_name', 'committee_nm', 'committee']:
                if col in df_committees_filtered.columns:
                    committee_col = col
                    break
            if committee_col:
                df_committees_filtered = df_committees_filtered[
                    df_committees_filtered[committee_col].isin(committees_with_data)
                ]
        
        # Get filter options for each dropdown (excluding itself from filtering)
        filter_options_category, _ = get_filter_options(df_committees_filtered, st.session_state.filters, exclude_filter='category')
        filter_options_party, _ = get_filter_options(df_committees_filtered, st.session_state.filters, exclude_filter='party')
        filter_options_office, _ = get_filter_options(df_committees_filtered, st.session_state.filters, exclude_filter='office')
        filter_options_district, _ = get_filter_options(df_committees_filtered, st.session_state.filters, exclude_filter='district')
        filter_options_candidate, _ = get_filter_options(df_committees_filtered, st.session_state.filters, exclude_filter='candidate_name')
        filter_options_committee, _ = get_filter_options(df_committees_filtered, st.session_state.filters, exclude_filter='committee_name')
        
        # Track if any filter changed
        filter_changed = False
        
        # Committee Category filter
        category_options = filter_options_category.get('category', list(COMMITTEE_CATEGORIES.keys()))
        current_categories = st.session_state.filters.get('category', ["Statewide"])
        # Ensure current_categories is a list
        if not isinstance(current_categories, list):
            current_categories = [current_categories] if current_categories else []
        
        # Default to Statewide if no category selected
        default_categories = ["Statewide"] if not current_categories else current_categories
        
        selected_categories = st.multiselect(
            "Committee Category",
            options=category_options,
            default=default_categories,
            key=f"filter_category_{st.session_state.filter_reset_counter}"
        )
        if selected_categories != current_categories:
            st.session_state.filters['category'] = selected_categories
            filter_changed = True
        
        party_options = [None] + filter_options_party.get('party', [])
        current_party = st.session_state.filters.get('party')
        selected_party = st.selectbox(
            "Party",
            options=party_options,
            index=get_index_for_value(party_options, current_party),
            key=f"filter_party_{st.session_state.filter_reset_counter}"
        )
        if selected_party != current_party:
            st.session_state.filters['party'] = selected_party
            filter_changed = True
        
        office_options = [None] + filter_options_office.get('office', [])
        current_office = st.session_state.filters.get('office')
        selected_office = st.selectbox(
            "Office Sought",
            options=office_options,
            index=get_index_for_value(office_options, current_office),
            key=f"filter_office_{st.session_state.filter_reset_counter}"
        )
        if selected_office != current_office:
            st.session_state.filters['office'] = selected_office
            filter_changed = True
        
        district_options = [None] + filter_options_district.get('district', [])
        current_district = st.session_state.filters.get('district')
        selected_district = st.selectbox(
            "District",
            options=district_options,
            index=get_index_for_value(district_options, current_district),
            key=f"filter_district_{st.session_state.filter_reset_counter}"
        )
        if selected_district != current_district:
            st.session_state.filters['district'] = selected_district
            filter_changed = True
        
        candidate_options = [None] + filter_options_candidate.get('candidate_name', [])
        current_candidate = st.session_state.filters.get('candidate_name')
        selected_candidate = st.selectbox(
            "Candidate Name",
            options=candidate_options,
            index=get_index_for_value(candidate_options, current_candidate),
            key=f"filter_candidate_{st.session_state.filter_reset_counter}"
        )
        if selected_candidate != current_candidate:
            st.session_state.filters['candidate_name'] = selected_candidate
            filter_changed = True
        
        committee_options = [None] + filter_options_committee.get('committee_name', [])
        current_committee_filter = st.session_state.filters.get('committee_name')
        selected_committee_filter = st.selectbox(
            "Committee Name",
            options=committee_options,
            index=get_index_for_value(committee_options, current_committee_filter),
            key=f"filter_committee_{st.session_state.filter_reset_counter}"
        )
        if selected_committee_filter != current_committee_filter:
            st.session_state.filters['committee_name'] = selected_committee_filter
            filter_changed = True
        
        # Rerun if any filter changed
        if filter_changed:
            st.rerun()
        
        # Calculate result count for mobile display
        # Get filtered committees count
        _, filtered_committees = get_filter_options(df_committees_filtered, st.session_state.filters)
        committee_col = None
        for col in ['committee_name', 'committee_nm', 'committee']:
            if col in filtered_committees.columns:
                committee_col = col
                break
        
        result_count = 0
        if committee_col:
            result_count = len(filtered_committees[committee_col].dropna().unique())
        
        # Static results count message
        st.markdown(f"**{result_count} Result{'s' if result_count != 1 else ''} Found**")
        
        st.markdown("---")
        
        # Footer in sidebar
        st.markdown("<div style='margin-top: 2rem; padding-top: 1rem; border-top: 1px solid #e0e0e0; line-height: 1.2;'>", unsafe_allow_html=True)
        
        # Disclaimer and copyright
        st.markdown(
            "<p style='color: #000000; font-size: 0.85rem; line-height: 1.3;'>App Under Development, please excuse any errors or issues. Data Source: Data.Iowa.Gov.</p>",
            unsafe_allow_html=True
        )
        st.markdown(
            "<p style='color: #000000; font-size: 0.85rem; line-height: 1.3;'>© Peter Owens 2026</p>",
            unsafe_allow_html=True
        )
        
        # Links
        st.markdown(
            f"<small style='color: #000000;'>"
            f"<a href='https://x.com/pcowens_' target='_blank' style='color: {THEME_PRIMARY_COLOR}; text-decoration: none; margin-right: 0.5rem;'>X (Twitter)</a> | "
            f"<a href='mailto:16petero@gmail.com' style='color: {THEME_PRIMARY_COLOR}; text-decoration: none; margin-left: 0.5rem;'>Email</a>"
            "</small>",
            unsafe_allow_html=True
        )
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Main content area - Results
    # Get filtered committees (already filtered by 2025 data if checkbox is checked)
    _, filtered_committees = get_filter_options(df_committees_filtered, st.session_state.filters)
    final_filtered = filtered_committees.copy()
    
    # Get committee name column
    committee_col = None
    for col in ['committee_name', 'committee_nm', 'committee']:
        if col in final_filtered.columns:
            committee_col = col
            break
    
    # Check if filters are empty/default to show welcome message
    filters_empty = (
        st.session_state.filters.get('category') == ["Statewide"] and
        st.session_state.filters.get('election_year') is None and
        st.session_state.filters.get('party') is None and
        st.session_state.filters.get('office') is None and
        st.session_state.filters.get('district') is None and
        st.session_state.filters.get('candidate_name') is None and
        st.session_state.filters.get('committee_name') is None and
        st.session_state.date_filter_value == DEFAULT_START_DATE
    )
    
    if filters_empty:
        # Welcome message
        st.markdown("### ↖️ Start by searching in the sidebar")
        st.markdown("Filter by committee info. Defaults to statewides with data since 2024. Close the sidebar by clicking arrows at the top")
    
    if committee_col:
        # Get unique committees with their info
        committee_info_list = []
        for committee in final_filtered[committee_col].dropna().unique():
            committee_row = final_filtered[final_filtered[committee_col] == committee].iloc[0]
            
            # Get committee type
            committee_type_val = None
            for col in ['committee_type', 'type', 'type_nm', 'committee_type_nm']:
                if col in committee_row and pd.notna(committee_row[col]):
                    committee_type_val = str(committee_row[col])
                    break
            
            # Get office
            office_val = None
            for col in ['office', 'office_sought', 'office_nm', 'office_name']:
                if col in committee_row and pd.notna(committee_row[col]):
                    office_val = str(committee_row[col])
                    break
            
            # Get party
            party_val = None
            for col in ['party', 'party_nm', 'party_name', 'political_party']:
                if col in committee_row and pd.notna(committee_row[col]):
                    party_val = str(committee_row[col])
                    break
            
            committee_info_list.append({
                'name': committee,
                'type': committee_type_val,
                'office': office_val,
                'party': party_val
            })
        
        # Sort by name
        committee_info_list = sorted(committee_info_list, key=lambda x: x['name'])
        
        # Display results with better aesthetics
        if committee_info_list:
            st.markdown(f"### {len(committee_info_list)} Committee{'s' if len(committee_info_list) != 1 else ''} Found")
            
            # Create a compact, single-line list
            for i, committee_info in enumerate(committee_info_list):
                details_parts = []
                if committee_info['type']:
                    details_parts.append(committee_info['type'])
                if committee_info['office']:
                    details_parts.append(committee_info['office'])
                if committee_info['party']:
                    details_parts.append(committee_info['party'])
                
                # Get latest data date
                latest_date = get_committee_latest_date(committee_info['name'])
                if latest_date:
                    if hasattr(latest_date, 'strftime'):
                        latest_date_str = latest_date.strftime('%Y-%m-%d')
                    else:
                        latest_date_str = str(latest_date)
                    details_parts.append(f"Latest: {latest_date_str}")
                
                details = " • ".join(details_parts) if details_parts else ""
                
                # Single compact line with all info
                full_text = f"**{committee_info['name']}**"
                if details:
                    full_text += f" • {details}"
                
                # Compact button with all info on one line
                if st.button(
                    full_text,
                    key=f"committee_btn_{i}",
                    use_container_width=True
                ):
                    st.session_state.selected_committee = committee_info['name']
                    st.rerun()
        else:
            st.info("No committees match the selected filters. Please adjust your search criteria.")
    else:
        st.warning("Committee name column not found in dataset.")

elif st.session_state.selected_committee:
    # DETAIL PAGE
    # Back button at top of detail page
    if st.button("← Back to Search", type="secondary", key="back_to_search_main"):
        st.session_state.selected_committee = None
        st.rerun()
    st.markdown("<div style='margin-bottom: 1rem;'></div>", unsafe_allow_html=True)  # Small margin below button
    
    # Get committee name column for detail page
    committee_col_detail = None
    for col in ['committee_name', 'committee_nm', 'committee']:
        if col in df_committees.columns:
            committee_col_detail = col
            break
    
    # Get committee info from dataset
    committee_info = df_committees[df_committees[committee_col_detail] == st.session_state.selected_committee].iloc[0] if not df_committees.empty and committee_col_detail else None
    
    # Load committee data
    with st.spinner("Downloading financial records..."):
        df_contributions, df_expenditures = load_committee_data(st.session_state.selected_committee)
    
    # Process data
    df_contributions = process_contributions(df_contributions)
    df_expenditures = process_expenditures(df_expenditures)
    
    # Find date columns
    date_col_contrib = None
    for col in ['date', 'contribution_date', 'transaction_date']:
        if col in df_contributions.columns:
            date_col_contrib = col
            break
    
    date_col_expend = None
    for col in ['date', 'expenditure_date', 'transaction_date']:
        if col in df_expenditures.columns:
            date_col_expend = col
            break
    
    # Sidebar for filters
    with st.sidebar:
        st.header("Filters")
        
        # Year filter
        if date_col_contrib and not df_contributions.empty:
            all_years = sorted(df_contributions[date_col_contrib].dropna().dt.year.unique(), reverse=True)
        elif date_col_expend and not df_expenditures.empty:
            all_years = sorted(df_expenditures[date_col_expend].dropna().dt.year.unique(), reverse=True)
        else:
            all_years = []
        
        if 'filter_year' not in st.session_state:
            st.session_state.filter_year = None
        
        year_options = [None] + [str(y) for y in all_years]
        # Fix index calculation to handle case where filter_year is not in options
        if st.session_state.filter_year is None:
            selected_index = 0
        elif str(st.session_state.filter_year) in year_options:
            selected_index = year_options.index(str(st.session_state.filter_year))
        else:
            # Filter year not available for this committee, reset to None
            selected_index = 0
            st.session_state.filter_year = None
        
        selected_year = st.selectbox(
            "Year",
            options=year_options,
            index=selected_index,
            key="sidebar_filter_year"
        )
        st.session_state.filter_year = selected_year
        
        # Date range filter
        if 'filter_date_start' not in st.session_state:
            st.session_state.filter_date_start = None
        if 'filter_date_end' not in st.session_state:
            st.session_state.filter_date_end = None
        
        use_date_range = st.checkbox("Filter by Date Range", value=st.session_state.filter_date_start is not None)
        
        if use_date_range:
            if st.session_state.filter_date_start:
                default_start = st.session_state.filter_date_start
            elif date_col_contrib and not df_contributions.empty:
                default_start = df_contributions[date_col_contrib].min().date()
            else:
                default_start = datetime(2020, 1, 1).date()
            
            if st.session_state.filter_date_end:
                default_end = st.session_state.filter_date_end
            elif date_col_contrib and not df_contributions.empty:
                default_end = df_contributions[date_col_contrib].max().date()
            else:
                default_end = datetime.today().date()
            
            date_start = st.date_input("Start Date", value=default_start)
            date_end = st.date_input("End Date", value=default_end)
            
            st.session_state.filter_date_start = date_start
            st.session_state.filter_date_end = date_end
        else:
            st.session_state.filter_date_start = None
            st.session_state.filter_date_end = None
        
        st.markdown("---")
        
        # Footer in sidebar
        st.markdown("---")
        st.markdown("<div style='margin-top: 2rem; padding-top: 1rem; border-top: 1px solid #e0e0e0; line-height: 1.2;'>", unsafe_allow_html=True)
        
        # Disclaimer and copyright
        st.markdown(
            "<p style='color: #000000; font-size: 0.85rem; line-height: 1.3;'>App Under Development, please excuse any errors or issues. Data Source: Data.Iowa.Gov.</p>",
            unsafe_allow_html=True
        )
        st.markdown(
            "<p style='color: #000000; font-size: 0.85rem; line-height: 1.3;'>© Peter Owens 2026</p>",
            unsafe_allow_html=True
        )
        
        # Links
        st.markdown(
            f"<small style='color: #000000;'>"
            f"<a href='https://x.com/pcowens_' target='_blank' style='color: {THEME_PRIMARY_COLOR}; text-decoration: none; margin-right: 0.5rem;'>X (Twitter)</a> | "
            f"<a href='mailto:16petero@gmail.com' style='color: {THEME_PRIMARY_COLOR}; text-decoration: none; margin-left: 0.5rem;'>Email</a>"
            "</small>",
            unsafe_allow_html=True
        )
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Apply filters to data with error handling
    df_contributions_filtered = df_contributions.copy()
    df_expenditures_filtered = df_expenditures.copy()
    
    filter_error = False
    try:
        if st.session_state.filter_year and date_col_contrib:
            if not df_contributions_filtered.empty:
                df_contributions_filtered = df_contributions_filtered[
                    df_contributions_filtered[date_col_contrib].dt.year == int(st.session_state.filter_year)
                ]
        if st.session_state.filter_year and date_col_expend:
            if not df_expenditures_filtered.empty:
                df_expenditures_filtered = df_expenditures_filtered[
                    df_expenditures_filtered[date_col_expend].dt.year == int(st.session_state.filter_year)
                ]
        
        if st.session_state.filter_date_start and date_col_contrib:
            if not df_contributions_filtered.empty:
                df_contributions_filtered = df_contributions_filtered[
                    df_contributions_filtered[date_col_contrib] >= pd.Timestamp(st.session_state.filter_date_start)
                ]
        if st.session_state.filter_date_end and date_col_contrib:
            if not df_contributions_filtered.empty:
                df_contributions_filtered = df_contributions_filtered[
                    df_contributions_filtered[date_col_contrib] <= pd.Timestamp(st.session_state.filter_date_end)
                ]
        
        if st.session_state.filter_date_start and date_col_expend:
            if not df_expenditures_filtered.empty:
                df_expenditures_filtered = df_expenditures_filtered[
                    df_expenditures_filtered[date_col_expend] >= pd.Timestamp(st.session_state.filter_date_start)
                ]
        if st.session_state.filter_date_end and date_col_expend:
            if not df_expenditures_filtered.empty:
                df_expenditures_filtered = df_expenditures_filtered[
                    df_expenditures_filtered[date_col_expend] <= pd.Timestamp(st.session_state.filter_date_end)
                ]
    except Exception as e:
        filter_error = True
        st.warning(f"Error applying filters: {str(e)}. Filters have been reset.")
        # Reset filters
        st.session_state.filter_year = None
        st.session_state.filter_date_start = None
        st.session_state.filter_date_end = None
        df_contributions_filtered = df_contributions.copy()
        df_expenditures_filtered = df_expenditures.copy()
        st.rerun()
    
    # Overview Info Section - Condensed
    st.header(f"{st.session_state.selected_committee}")
    
    # Get committee details
    name = st.session_state.selected_committee  # Default to committee name
    committee_type = None
    party = None
    office = None
    district = None
    
    if committee_info is not None:
        # Get candidate name instead of committee name
        for col in ['candidate_name', 'candidate_nm', 'candidate', 'name']:
            if col in committee_info and pd.notna(committee_info[col]) and str(committee_info[col]).strip():
                name = str(committee_info[col])
                break
        for col in ['type', 'committee_type', 'type_nm', 'committee_type_nm']:
            if col in committee_info and pd.notna(committee_info[col]):
                committee_type = str(committee_info[col])
                break
        for col in ['party', 'party_nm', 'party_name', 'political_party']:
            if col in committee_info and pd.notna(committee_info[col]):
                party = str(committee_info[col])
                break
        for col in ['office', 'office_sought', 'office_nm', 'office_name']:
            if col in committee_info and pd.notna(committee_info[col]):
                office = str(committee_info[col])
                break
        for col in ['district', 'district_nbr', 'district_number', 'district_num']:
            if col in committee_info and pd.notna(committee_info[col]):
                district = str(committee_info[col])
                break
    
    # Calculate totals from filtered data
    amount_col_contrib = None
    for col in ['amount', 'contribution_amount', 'transaction_amount']:
        if col in df_contributions_filtered.columns:
            amount_col_contrib = col
            break
    
    amount_col_expend = None
    for col in ['amount', 'expenditure_amount', 'transaction_amount']:
        if col in df_expenditures_filtered.columns:
            amount_col_expend = col
            break
    
    total_raised = df_contributions_filtered[amount_col_contrib].sum() if amount_col_contrib and not df_contributions_filtered.empty else 0
    total_spent = df_expenditures_filtered[amount_col_expend].sum() if amount_col_expend and not df_expenditures_filtered.empty else 0
    
    # Get earliest and latest dates from filtered data
    earliest_date = None
    latest_date = None
    all_dates = []
    if date_col_contrib and not df_contributions_filtered.empty:
        valid_dates = df_contributions_filtered[date_col_contrib].dropna()
        if not valid_dates.empty:
            all_dates.extend(valid_dates.tolist())
    if date_col_expend and not df_expenditures_filtered.empty:
        valid_dates = df_expenditures_filtered[date_col_expend].dropna()
        if not valid_dates.empty:
            all_dates.extend(valid_dates.tolist())
    if all_dates:
        earliest_date = min(all_dates)
        latest_date = max(all_dates)
    
    # Get latest data date for display (from unfiltered data)
    latest_data_date_unfiltered = None
    all_dates_unfiltered = []
    if date_col_contrib and not df_contributions.empty:
        valid_dates = df_contributions[date_col_contrib].dropna()
        if not valid_dates.empty:
            all_dates_unfiltered.extend(valid_dates.tolist())
    if date_col_expend and not df_expenditures.empty:
        valid_dates = df_expenditures[date_col_expend].dropna()
        if not valid_dates.empty:
            all_dates_unfiltered.extend(valid_dates.tolist())
    if all_dates_unfiltered:
        latest_date_unfiltered = max(all_dates_unfiltered)
        if hasattr(latest_date_unfiltered, 'strftime'):
            latest_data_date_unfiltered = latest_date_unfiltered.strftime('%Y-%m-%d')
        else:
            latest_data_date_unfiltered = str(latest_date_unfiltered)
    
    # Compact info row
    info_text = f"{name}"
    if committee_type:
        info_text += f" • {committee_type}"
    if party:
        info_text += f" • {party}"
    if office:
        info_text += f" • {office}"
    if district:
        info_text += f" • District {district}"
    if earliest_date and latest_date:
        info_text += f" • {earliest_date.strftime('%Y-%m-%d') if hasattr(earliest_date, 'strftime') else str(earliest_date)} to {latest_date.strftime('%Y-%m-%d') if hasattr(latest_date, 'strftime') else str(latest_date)}"
    
    st.caption(info_text)
    
    # Latest Data Available line (from unfiltered data, above metrics)
    if latest_data_date_unfiltered:
        st.markdown(f"**Latest Data Available:** {latest_data_date_unfiltered}")
        st.markdown("**↖ Use the sidebar to filter by year or date.**")
    else: 
        st.markdown("**Latest Data Available:** NO DATA")
    
    # Calculate Cash on Hand to match Ending COH
    has_filters = (st.session_state.filter_year is not None or 
                  st.session_state.filter_date_start is not None or 
                  st.session_state.filter_date_end is not None)
    
    # Find transaction type column for contributions
    trans_type_col = None
    for col in ['transaction_type', 'trans_type', 'type', 'contribution_type', 'transaction_cd', 'trans_cd']:
        if col in df_contributions.columns:
            trans_type_col = col
            break
    
    # Filter contributions to only include "CON" (cash contributions) for COH
    def filter_cash_contributions(df):
        if df.empty or trans_type_col is None:
            return df
        filtered = df[df[trans_type_col].astype(str).str.upper().str.strip() == 'CON'].copy()
        return filtered
    
    # Calculate starting COH
    starting_coh = 0
    if has_filters and not df_contributions.empty and not df_expenditures.empty:
        pre_filter_contrib = df_contributions.copy()
        pre_filter_expend = df_expenditures.copy()
        pre_filter_contrib = filter_cash_contributions(pre_filter_contrib)
        
        if st.session_state.filter_year and date_col_contrib:
            pre_filter_contrib = pre_filter_contrib[
                pre_filter_contrib[date_col_contrib].dt.year < int(st.session_state.filter_year)
            ]
        if st.session_state.filter_year and date_col_expend:
            pre_filter_expend = pre_filter_expend[
                pre_filter_expend[date_col_expend].dt.year < int(st.session_state.filter_year)
            ]
        if st.session_state.filter_date_start and date_col_contrib:
            pre_filter_contrib = pre_filter_contrib[
                pre_filter_contrib[date_col_contrib] < pd.Timestamp(st.session_state.filter_date_start)
            ]
        if st.session_state.filter_date_start and date_col_expend:
            pre_filter_expend = pre_filter_expend[
                pre_filter_expend[date_col_expend] < pd.Timestamp(st.session_state.filter_date_start)
            ]
        
        if amount_col_contrib and not pre_filter_contrib.empty:
            pre_contrib_total = pre_filter_contrib[amount_col_contrib].sum()
        else:
            pre_contrib_total = 0
        if amount_col_expend and not pre_filter_expend.empty:
            pre_expend_total = pre_filter_expend[amount_col_expend].sum()
        else:
            pre_expend_total = 0
        starting_coh = pre_contrib_total - pre_expend_total
    
    # Calculate ending COH (same as in Analysis tab)
    ending_coh = starting_coh
    if has_filters:
        cash_contributions_filtered = filter_cash_contributions(df_contributions_filtered)
        total_contrib = cash_contributions_filtered[amount_col_contrib].sum() if amount_col_contrib and not cash_contributions_filtered.empty else 0
        total_expend = df_expenditures_filtered[amount_col_expend].sum() if amount_col_expend and not df_expenditures_filtered.empty else 0
        ending_coh = starting_coh + total_contrib - total_expend
    elif not df_contributions.empty and not df_expenditures.empty and amount_col_contrib and amount_col_expend:
        cash_contributions = filter_cash_contributions(df_contributions)
        total_contrib = cash_contributions[amount_col_contrib].sum() if not cash_contributions.empty else 0
        total_expend = df_expenditures[amount_col_expend].sum()
        ending_coh = starting_coh + total_contrib - total_expend
    
    cash_on_hand = ending_coh
    
    st.markdown("---")
    
    # Condensed overview
    metric_col1, metric_col2, metric_col3 = st.columns(3)
    with metric_col1:
        st.metric("Total Raised", f"${total_raised:,.2f}")
    with metric_col2:
        st.metric("Total Spent", f"${total_spent:,.2f}")
    with metric_col3:
        st.metric("Cash on Hand", f"${cash_on_hand:,.2f}")
    
    # Tabs
    st.markdown("<style>.stTabs [data-baseweb='tab-list'] { margin-top: 0 !important; }</style>", unsafe_allow_html=True)
    tab1, tab2 = st.tabs(["📊 Analysis", "📥 Exports"])
    
    with tab1:
        st.markdown("### Cash On Hand")
        
        # Calculate starting COH
        # If filters are applied, calculate COH from data before the filter
        # Otherwise, starting COH is 0
        starting_coh = 0
        
        has_filters = (st.session_state.filter_year is not None or 
                      st.session_state.filter_date_start is not None or 
                      st.session_state.filter_date_end is not None)
        
        # Find transaction type column for contributions
        trans_type_col = None
        for col in ['transaction_type', 'trans_type', 'type', 'contribution_type', 'transaction_cd', 'trans_cd']:
            if col in df_contributions.columns:
                trans_type_col = col
                break
        
        # Filter contributions to only include "CON" (cash contributions) for COH
        def filter_cash_contributions(df):
            if df.empty or trans_type_col is None:
                return df
            # Filter to only include rows where transaction type is "CON"
            filtered = df[df[trans_type_col].astype(str).str.upper().str.strip() == 'CON'].copy()
            return filtered
        
        if has_filters and not df_contributions.empty and not df_expenditures.empty:
            # Calculate COH from pre-filter data
            # Get contributions and expenditures before the filter date/year
            pre_filter_contrib = df_contributions.copy()
            pre_filter_expend = df_expenditures.copy()
            
            # Filter to only cash contributions
            pre_filter_contrib = filter_cash_contributions(pre_filter_contrib)
            
            # Apply pre-filter logic (before the selected year/date)
            if st.session_state.filter_year and date_col_contrib:
                pre_filter_contrib = pre_filter_contrib[
                    pre_filter_contrib[date_col_contrib].dt.year < int(st.session_state.filter_year)
                ]
            if st.session_state.filter_year and date_col_expend:
                pre_filter_expend = pre_filter_expend[
                    pre_filter_expend[date_col_expend].dt.year < int(st.session_state.filter_year)
                ]
            
            if st.session_state.filter_date_start and date_col_contrib:
                pre_filter_contrib = pre_filter_contrib[
                    pre_filter_contrib[date_col_contrib] < pd.Timestamp(st.session_state.filter_date_start)
                ]
            if st.session_state.filter_date_start and date_col_expend:
                pre_filter_expend = pre_filter_expend[
                    pre_filter_expend[date_col_expend] < pd.Timestamp(st.session_state.filter_date_start)
                ]
            
            # Calculate starting COH from pre-filter data
            if amount_col_contrib and not pre_filter_contrib.empty:
                pre_contrib_total = pre_filter_contrib[amount_col_contrib].sum()
            else:
                pre_contrib_total = 0
            
            if amount_col_expend and not pre_filter_expend.empty:
                pre_expend_total = pre_filter_expend[amount_col_expend].sum()
            else:
                pre_expend_total = 0
            
            starting_coh = pre_contrib_total - pre_expend_total
        
        # Calculate ending COH (from filtered data if filters are applied, otherwise all data)
        ending_coh = starting_coh
        if has_filters:
            # Use filtered data for ending COH calculation
            cash_contributions_filtered = filter_cash_contributions(df_contributions_filtered)
            total_contrib = cash_contributions_filtered[amount_col_contrib].sum() if amount_col_contrib and not cash_contributions_filtered.empty else 0
            total_expend = df_expenditures_filtered[amount_col_expend].sum() if amount_col_expend and not df_expenditures_filtered.empty else 0
            ending_coh = starting_coh + total_contrib - total_expend
        elif not df_contributions.empty and not df_expenditures.empty and amount_col_contrib and amount_col_expend:
            # No filters - use all data
            cash_contributions = filter_cash_contributions(df_contributions)
            total_contrib = cash_contributions[amount_col_contrib].sum() if not cash_contributions.empty else 0
            total_expend = df_expenditures[amount_col_expend].sum()
            ending_coh = starting_coh + total_contrib - total_expend
        
        # Display subtitle with Starting and Ending COH (using HTML to avoid green text)
        st.markdown(f'<p style="font-size: 1rem; color: #333;"><strong>Starting COH:</strong> ${starting_coh:,.2f}  |  <strong>Ending COH:</strong> ${ending_coh:,.2f}</p>', unsafe_allow_html=True)
        
        st.markdown("#### Cash on Hand by Year")
        # Calculate COH by Year
        if not df_contributions.empty and not df_expenditures.empty and amount_col_contrib and amount_col_expend:
            # Get years from filtered data if filters are applied, otherwise all data
            all_years = set()
            
            if has_filters:
                # Use filtered data to get years
                if date_col_contrib and not df_contributions_filtered.empty:
                    contrib_years = df_contributions_filtered[date_col_contrib].dropna().dt.year.unique()
                    all_years.update(contrib_years)
                
                if date_col_expend and not df_expenditures_filtered.empty:
                    expend_years = df_expenditures_filtered[date_col_expend].dropna().dt.year.unique()
                    all_years.update(expend_years)
            else:
                # No filters - use all data
                if date_col_contrib:
                    contrib_years = df_contributions[date_col_contrib].dropna().dt.year.unique()
                    all_years.update(contrib_years)
                
                if date_col_expend:
                    expend_years = df_expenditures[date_col_expend].dropna().dt.year.unique()
                    all_years.update(expend_years)
            
            if all_years:
                # Sort years
                sorted_years = sorted(all_years)
                
                # Calculate COH for each year
                coh_data = []
                running_coh = starting_coh
                
                for year in sorted_years:
                    # Get contributions for this year (only cash contributions "CON")
                    # Use filtered data if filters are applied
                    if has_filters:
                        if date_col_contrib and not df_contributions_filtered.empty:
                            year_contrib = df_contributions_filtered[
                                df_contributions_filtered[date_col_contrib].dt.year == year
                            ]
                        else:
                            year_contrib = pd.DataFrame()
                        
                        if date_col_expend and not df_expenditures_filtered.empty:
                            year_expend = df_expenditures_filtered[
                                df_expenditures_filtered[date_col_expend].dt.year == year
                            ]
                        else:
                            year_expend = pd.DataFrame()
                    else:
                        if date_col_contrib:
                            year_contrib = df_contributions[
                                df_contributions[date_col_contrib].dt.year == year
                            ]
                        else:
                            year_contrib = pd.DataFrame()
                        
                        if date_col_expend:
                            year_expend = df_expenditures[
                                df_expenditures[date_col_expend].dt.year == year
                            ]
                        else:
                            year_expend = pd.DataFrame()
                    
                    # Filter to only cash contributions for COH
                    year_contrib = filter_cash_contributions(year_contrib)
                    
                    year_contrib_total = year_contrib[amount_col_contrib].sum() if amount_col_contrib and not year_contrib.empty else 0
                    year_expend_total = year_expend[amount_col_expend].sum() if amount_col_expend and not year_expend.empty else 0
                    
                    # Calculate COH for this year
                    year_net = year_contrib_total - year_expend_total
                    running_coh += year_net
                    
                    coh_data.append({
                        'Year': int(year),
                        'Contributions': year_contrib_total,
                        'Expenditures': year_expend_total,
                        'Net': year_net,
                        'Ending COH': running_coh
                    })
                
                # Create DataFrame and display
                if coh_data:
                    df_coh = pd.DataFrame(coh_data)
                    # Store in session state for PDF generation
                    st.session_state.coh_data_for_pdf = df_coh.copy()
                    
                    # Format the display
                    df_display = df_coh.copy()
                    df_display['Contributions'] = df_display['Contributions'].apply(lambda x: f"${x:,.2f}")
                    df_display['Expenditures'] = df_display['Expenditures'].apply(lambda x: f"${x:,.2f}")
                    df_display['Net'] = df_display['Net'].apply(lambda x: f"${x:,.2f}")
                    df_display['Ending COH'] = df_display['Ending COH'].apply(lambda x: f"${x:,.2f}")
                    
                    st.dataframe(df_display, width='stretch', hide_index=True)
                else:
                    st.info("No data available for COH calculation by year.")
            else:
                st.info("No date information available to calculate COH by year.")
        else:
            st.warning("Insufficient data available for Cash on Hand analysis.")
        
        # Visualizations Section
        st.markdown("---")
        
        if not df_contributions_filtered.empty and amount_col_contrib:
            # Find state column
            state_col = None
            for col in ['state', 'contributor_state', 'state_cd', 'state_code']:
                if col in df_contributions_filtered.columns:
                    state_col = col
                    break
            
            # Row 1: Two charts side by side
            row1_col1, row1_col2 = st.columns(2)
            
            with row1_col1:
                st.markdown("#### Top 5 States by Number of Donors")
                # Top 5 States by Number of Donors
                if state_col and df_contributions_filtered[state_col].notna().any():
                    if 'contributor_final' in df_contributions_filtered.columns:
                        state_donor_counts = df_contributions_filtered.groupby(state_col)['contributor_final'].nunique().sort_values(ascending=False).head(5)
                    else:
                        state_donor_counts = df_contributions_filtered[df_contributions_filtered[state_col].notna()][state_col].value_counts().head(5)
                    
                    if not state_donor_counts.empty:
                        total_donors = state_donor_counts.sum()
                        fig_states_count = px.bar(
                            x=state_donor_counts.values,
                            y=state_donor_counts.index,
                            orientation='h',
                            labels={'x': 'Number of Donors', 'y': 'State'},
                            title="Top 5 States by Number of Donors",
                            color_discrete_sequence=[THEME_PRIMARY_COLOR]
                        )
                        annotations = []
                        for state, count in state_donor_counts.items():
                            pct = (count / total_donors * 100) if total_donors > 0 else 0
                            annotations.append(dict(
                                x=count,
                                y=state,
                                text=f"<b>{count} ({pct:.1f}%)</b>",
                                showarrow=False,
                                xanchor='left',
                                xshift=5,
                                font=dict(color='black', size=12)
                            ))
                        fig_states_count.update_layout(
                            yaxis={'categoryorder': 'total ascending'},
                            annotations=annotations,
                            plot_bgcolor='white',
                            paper_bgcolor='white'
                        )
                        st.plotly_chart(fig_states_count, use_container_width=True, config={'displayModeBar': False})
            
            with row1_col2:
                st.markdown("#### Top 5 States by Sum of Donations")
                # Top 5 States by Sum of Donations
                if state_col and df_contributions_filtered[state_col].notna().any():
                    state_totals = df_contributions_filtered.groupby(state_col)[amount_col_contrib].sum().sort_values(ascending=False).head(5)
                    if not state_totals.empty:
                        total_amount = state_totals.sum()
                        fig_states_sum = px.bar(
                            x=state_totals.values,
                            y=state_totals.index,
                            orientation='h',
                            labels={'x': 'Total Donations ($)', 'y': 'State'},
                            title="Top 5 States by Sum of Donations",
                            color_discrete_sequence=[THEME_PRIMARY_COLOR]
                        )
                        annotations = []
                        for state, amount in state_totals.items():
                            pct = (amount / total_amount * 100) if total_amount > 0 else 0
                            annotations.append(dict(
                                x=amount,
                                y=state,
                                text=f"<b>${amount:,.0f} ({pct:.1f}%)</b>",
                                showarrow=False,
                                xanchor='left',
                                xshift=5,
                                font=dict(color='black', size=12)
                            ))
                        fig_states_sum.update_layout(
                            yaxis={'categoryorder': 'total ascending'},
                            annotations=annotations,
                            plot_bgcolor='white',
                            paper_bgcolor='white'
                        )
                        st.plotly_chart(fig_states_sum, use_container_width=True, config={'displayModeBar': False})
            
            # Row 2: Two charts side by side
            row2_col1, row2_col2 = st.columns(2)
            
            with row2_col1:
                st.markdown("#### Top 5 Donors by Sum of Donations")
                # Top 5 Donors
                if 'contributor_final' in df_contributions_filtered.columns and state_col:
                    top_donors = df_contributions_filtered.groupby(['contributor_final', state_col])[amount_col_contrib].sum().reset_index()
                    top_donors = top_donors.sort_values(amount_col_contrib, ascending=False).head(5)
                    if not top_donors.empty:
                        top_donors['Donor'] = top_donors.apply(
                            lambda row: f"{row['contributor_final']} ({row[state_col]})" if pd.notna(row[state_col]) else row['contributor_final'],
                            axis=1
                        )
                        total_donor_amount = top_donors[amount_col_contrib].sum()
                        fig_donors = px.bar(
                            x=top_donors[amount_col_contrib].values,
                            y=top_donors['Donor'].values,
                            orientation='h',
                            labels={'x': 'Total Donations ($)', 'y': 'Donor'},
                            title="Top 5 Donors by Sum of Donations",
                            color_discrete_sequence=[THEME_PRIMARY_COLOR]
                        )
                        annotations = []
                        for _, row in top_donors.iterrows():
                            amount = row[amount_col_contrib]
                            pct = (amount / total_donor_amount * 100) if total_donor_amount > 0 else 0
                            annotations.append(dict(
                                x=amount,
                                y=row['Donor'],
                                text=f"<b>${amount:,.0f} ({pct:.1f}%)</b>",
                                showarrow=False,
                                xanchor='left',
                                xshift=5,
                                font=dict(color='black', size=11)
                            ))
                        fig_donors.update_layout(
                            yaxis={'categoryorder': 'total ascending'},
                            annotations=annotations,
                            plot_bgcolor='white',
                            paper_bgcolor='white'
                        )
                        st.plotly_chart(fig_donors, use_container_width=True, config={'displayModeBar': False})
                elif 'contributor_final' in df_contributions_filtered.columns:
                    top_donors = df_contributions_filtered.groupby('contributor_final')[amount_col_contrib].sum().sort_values(ascending=False).head(5)
                    if not top_donors.empty:
                        total_donor_amount = top_donors.sum()
                        fig_donors = px.bar(
                            x=top_donors.values,
                            y=top_donors.index,
                            orientation='h',
                            labels={'x': 'Total Donations ($)', 'y': 'Donor'},
                            title="Top 5 Donors by Sum of Donations",
                            color_discrete_sequence=[THEME_PRIMARY_COLOR]
                        )
                        annotations = []
                        for donor, amount in top_donors.items():
                            pct = (amount / total_donor_amount * 100) if total_donor_amount > 0 else 0
                            annotations.append(dict(
                                x=amount,
                                y=donor,
                                text=f"<b>${amount:,.0f} ({pct:.1f}%)</b>",
                                showarrow=False,
                                xanchor='left',
                                xshift=5,
                                font=dict(color='black', size=11)
                            ))
                        fig_donors.update_layout(
                            yaxis={'categoryorder': 'total ascending'},
                            annotations=annotations,
                            plot_bgcolor='white',
                            paper_bgcolor='white'
                        )
                        st.plotly_chart(fig_donors, use_container_width=True, config={'displayModeBar': False})
            
            with row2_col2:
                st.markdown("#### Donations Over Time (Monthly)")
                # Donations Over Time
                if date_col_contrib and df_contributions_filtered[date_col_contrib].notna().any():
                    df_contributions_filtered['year_month'] = df_contributions_filtered[date_col_contrib].dt.to_period('M')
                    monthly_totals = df_contributions_filtered.groupby('year_month')[amount_col_contrib].sum()
                    if not monthly_totals.empty:
                        monthly_totals.index = monthly_totals.index.astype(str)
                        fig_timeline = px.line(
                            x=monthly_totals.index,
                            y=monthly_totals.values,
                            labels={'x': 'Month', 'y': 'Total Donations ($)'},
                            title="Donations Over Time (Monthly)"
                        )
                        fig_timeline.update_traces(mode='lines+markers', line=dict(width=3, color=THEME_PRIMARY_COLOR))
                        fig_timeline.update_layout(
                            hovermode='x unified',
                            plot_bgcolor='white',
                            paper_bgcolor='white'
                        )
                        st.plotly_chart(fig_timeline, use_container_width=True, config={'displayModeBar': False})
            
            # Row 3: Top 5 Expenditure Recipients
            st.markdown("---")
            st.markdown("#### Top 5 Expenditure Recipients")
            if not df_expenditures_filtered.empty and amount_col_expend:
                # Create recipient name column (organization_nm or first_nm + last_nm + state)
                if 'organization_nm' in df_expenditures_filtered.columns:
                    df_expenditures_filtered['recipient_final'] = df_expenditures_filtered.apply(
                        lambda row: row['organization_nm'] if pd.notna(row['organization_nm']) and str(row['organization_nm']).strip() != '' 
                        else f"{row.get('first_nm', '')} {row.get('last_nm', '')}".strip() + (f" ({row.get('state', '')})" if pd.notna(row.get('state')) and str(row.get('state')).strip() else ""),
                        axis=1
                    )
                elif 'first_nm' in df_expenditures_filtered.columns and 'last_nm' in df_expenditures_filtered.columns:
                    df_expenditures_filtered['recipient_final'] = df_expenditures_filtered.apply(
                        lambda row: f"{row.get('first_nm', '')} {row.get('last_nm', '')}".strip() + (f" ({row.get('state', '')})" if pd.notna(row.get('state')) and str(row.get('state')).strip() else ""),
                        axis=1
                    )
                else:
                    # Fallback to finding recipient column
                    recipient_col = None
                    for col in ['recipient', 'recipient_nm', 'payee', 'payee_nm', 'vendor', 'vendor_nm', 'expenditure_recipient']:
                        if col in df_expenditures_filtered.columns:
                            recipient_col = col
                            break
                    if recipient_col:
                        df_expenditures_filtered['recipient_final'] = df_expenditures_filtered[recipient_col]
                    else:
                        df_expenditures_filtered['recipient_final'] = 'Unknown'
                
                if 'recipient_final' in df_expenditures_filtered.columns:
                    top_recipients = df_expenditures_filtered.groupby('recipient_final')[amount_col_expend].sum().sort_values(ascending=False).head(5)
                    if not top_recipients.empty:
                        total_recipient_amount = top_recipients.sum()
                        fig_recipients = px.bar(
                            x=top_recipients.values,
                            y=top_recipients.index,
                            orientation='h',
                            labels={'x': 'Total Expenditures ($)', 'y': 'Recipient'},
                            title="Top 5 Expenditure Recipients",
                            color_discrete_sequence=[THEME_PRIMARY_COLOR]
                        )
                        annotations = []
                        for recipient, amount in top_recipients.items():
                            pct = (amount / total_recipient_amount * 100) if total_recipient_amount > 0 else 0
                            annotations.append(dict(
                                x=amount,
                                y=recipient,
                                text=f"<b>${amount:,.0f} ({pct:.1f}%)</b>",
                                showarrow=False,
                                xanchor='left',
                                xshift=5,
                                font=dict(color='black', size=11)
                            ))
                        fig_recipients.update_layout(
                            yaxis={'categoryorder': 'total ascending'},
                            annotations=annotations,
                            plot_bgcolor='white',
                            paper_bgcolor='white'
                        )
                        st.plotly_chart(fig_recipients, use_container_width=True, config={'displayModeBar': False})
                else:
                    st.info("Unable to determine recipient names from expenditure data.")
            else:
                st.warning("No expenditure data available for visualization.")
        else:
            st.warning("No contribution data available for visualizations.")
    
    with tab2:
        # PDF Export Section - Direct download button
        st.subheader("📄 PDF Report")
        try:
            coh_data_for_pdf = st.session_state.get('coh_data_for_pdf', None)
            with st.spinner("Compiling PDF report..."):
                pdf_buffer = generate_pdf_report(
                    name, committee_info, total_raised, total_spent, cash_on_hand,
                    latest_data_date_unfiltered, df_contributions_filtered, df_expenditures_filtered,
                    coh_data_for_pdf, starting_coh, ending_coh, amount_col_contrib, amount_col_expend,
                    candidate_name=name, earliest_date=earliest_date, latest_date=latest_date
                )
            st.download_button(
                label="Download Report",
                data=pdf_buffer.getvalue(),
                file_name=f"{name}_report_{datetime.now().strftime('%Y%m%d')}.pdf",
                mime="application/pdf",
                key="download_pdf",
                use_container_width=True
            )
        except Exception as e:
            st.error(f"Error generating PDF: {str(e)}")
        
        st.markdown("---")
        
        # Contributions Export
        col_contrib1, col_contrib2 = st.columns([3, 1])
        with col_contrib1:
            st.subheader("Contributions Export")
        with col_contrib2:
            st.write("")
        
        if not df_contributions_filtered.empty:
            st.markdown(f"**Total Records:** {len(df_contributions_filtered)}")
            st.dataframe(df_contributions_filtered.head(10), width='stretch', height=300)
            csv_contrib = df_contributions_filtered.to_csv(index=False)
            st.download_button(
                label="📥 Download Contributions as CSV",
                data=csv_contrib,
                file_name=f"{st.session_state.selected_committee}_contributions_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                key="download_contributions"
            )
        else:
            st.warning("No contribution data available for export.")
        
        st.markdown("---")
        
        # Expenditures Export
        col_expend1, col_expend2 = st.columns([3, 1])
        with col_expend1:
            st.subheader("Expenditures Export")
        with col_expend2:
            st.write("")
        
        if not df_expenditures_filtered.empty:
            st.markdown(f"**Total Records:** {len(df_expenditures_filtered)}")
            st.dataframe(df_expenditures_filtered.head(10), width='stretch', height=300)
            csv_expend = df_expenditures_filtered.to_csv(index=False)
            st.download_button(
                label="📥 Download Expenditures as CSV",
                data=csv_expend,
                file_name=f"{st.session_state.selected_committee}_expenditures_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                key="download_expenditures"
            )
        else:
            st.warning("No expenditure data available for export.")
    
    # Footer at bottom of main page
    st.markdown("<hr style='margin-top: 3rem; margin-bottom: 1rem; border: 0; border-top: 1px solid #e0e0e0;'>", unsafe_allow_html=True)
    st.markdown(
        "<p style='color: #666; font-size: 0.85rem; text-align: center; line-height: 1.5;'>App Under Development, please excuse any errors or issues. Data Source: Data.Iowa.Gov.</p>",
        unsafe_allow_html=True
    )
    st.markdown(
        f"<p style='color: #666; font-size: 0.85rem; text-align: center; line-height: 1.5;'>© Peter Owens 2026 | "
        f"<a href='https://x.com/pcowens_' target='_blank' style='color: {THEME_PRIMARY_COLOR}; text-decoration: none;'>X (Twitter)</a> | "
        f"<a href='mailto:16petero@gmail.com' style='color: {THEME_PRIMARY_COLOR}; text-decoration: none;'>Email</a></p>",
        unsafe_allow_html=True
    )
