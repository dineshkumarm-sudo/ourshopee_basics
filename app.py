import io
import re
import base64
import pandas as pd
import streamlit as st

# --- Page Config ---
st.set_page_config(
    page_title="Our Shopee Basic Data Checks",
    page_icon="🛍️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Base64 Embedded Logo (Our Shopee Logo) ---
LOGO_BASE64 = "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD/2wCEAAkGBxMSEhUTExMVFhUXGR4aGBgYGR0dIBodHR0fHx0dHR0dHSggHxlolx0dITEiJSkrLi4uHR8zODMtNygtLisBCgoKDg0OGxAQGy0lICYtLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLf/AABEIAOEA4QMBEQACEQEDEQH/xAAbAAACAwEBAQAAAAAAAAAAAAADBAECBQAGB//EAEQQAAECBAQDBQUGBQIFAwUAAAECEQADEiExQVFhBHFgA4GRsRMiA6HB0fAUMlKS4fFCYnKCsiNT0sKiM3OTFRY0Y2TD/8QAGQEAAwEBAQAAAAAAAAAAAAAAAAIDAQQF/8QAJhEAAgICAgICAwEBAQEAAAAAAAECEQMhEjEiQVFxBBNSYZFyI//aAAw50005/2Q=="

# --- Comprehensive Apple Light/Dark Universal Theme Styling ---
st.markdown("""
<style>
    /* Force Light background canvas & readable high-contrast typography across light/dark modes */
    .stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
        background-color: #F5F5F7 !important;
        color: #1D1D1F !important;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif !important;
    }

    /* Force all prose text, labels, and spans to dark gray/black */
    p, span, label, h1, h2, h3, h4, h5, h6, div {
        color: #1D1D1F;
    }

    /* Header Container Card */
    .header-card {
        background: #FFFFFF !important;
        border: 1px solid #E5E5EA !important;
        border-radius: 18px !important;
        padding: 24px 32px !important;
        margin-bottom: 24px !important;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.04) !important;
        display: flex !important;
        justify-content: space-between !important;
        align-items: center !important;
    }

    .gradient-title {
        font-size: 2.1rem !important;
        font-weight: 800 !important;
        background: linear-gradient(135deg, #0A2540 0%, #D4AF37 50%, #FF6B00 100%) !important;
        -webkit-background-clip: text !important;
        -webkit-text-fill-color: transparent !important;
        letter-spacing: -0.5px !important;
        margin: 0 0 6px 0 !important;
    }

    .header-sub {
        color: #86868B !important;
        font-size: 0.95rem !important;
        font-weight: 400 !important;
        margin: 0 !important;
    }

    .logo-img {
        width: 72px !important;
        height: 72px !important;
        border-radius: 16px !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.12) !important;
        object-fit: cover !important;
        background-color: #5C32CA !important;
    }

    /* Uploader Visibility in Dark Mode */
    div[data-testid="stFileUploader"] {
        background-color: #FFFFFF !important;
        border: 2px dashed #0A2540 !important;
        border-radius: 16px !important;
        padding: 24px !important;
        box-shadow: 0 2px 10px rgba(0,0,0,0.03) !important;
    }
    div[data-testid="stFileUploader"] * {
        color: #1D1D1F !important;
    }

    /* Universal Button Fixes */
    .stButton>button, .stDownloadButton>button {
        background-color: #0A2540 !important;
        color: #FFFFFF !important;
        border-radius: 10px !important;
        border: none !important;
        font-weight: 600 !important;
        padding: 0.55rem 1.4rem !important;
        box-shadow: 0 4px 12px rgba(10, 37, 64, 0.2) !important;
        transition: all 0.2s ease !important;
    }
    .stButton>button:hover, .stDownloadButton>button:hover {
        background-color: #FF6B00 !important;
        color: #FFFFFF !important;
        box-shadow: 0 6px 16px rgba(255, 107, 0, 0.3) !important;
    }

    /* Metrics Styling */
    div[data-testid="stMetric"] {
        background-color: #FFFFFF !important;
        border: 1px solid #E5E5EA !important;
        border-radius: 14px !important;
        padding: 16px 20px !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.02) !important;
    }
    div[data-testid="stMetricLabel"] {
        color: #86868B !important;
        font-size: 0.85rem !important;
        font-weight: 600 !important;
    }
    div[data-testid="stMetricValue"] {
        color: #0A2540 !important;
        font-weight: 700 !important;
    }

    /* Tabs Styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 12px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        padding: 8px 18px;
        background-color: #E5E5EA;
        color: #1D1D1F !important;
        font-weight: 600;
        border: none;
    }
    .stTabs [aria-selected="true"] {
        background-color: #0A2540 !important;
        color: #FFFFFF !important;
    }
    .stTabs [aria-selected="true"] * {
        color: #FFFFFF !important;
    }
</style>
""", unsafe_allow_html=True)


# --- Data Validation Engine ---
class DataValidator:
    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()
        self.errors = []
        self.countries = ['UAE', 'OMAN', 'QATAR', 'KUWAIT', 'BAHRAIN', 'SAUDI']

    def log_error(self, row_idx, sku, column, category, message):
        self.errors.append({
            'Row': row_idx + 2,
            'SKU': sku if sku else 'N/A',
            'Column': column,
            'Category': category,
            'Error Description': message
        })

    def run_all_validations(self):
        self.validate_brand_integrity()
        self.validate_barcodes()

        for idx, row in self.df.iterrows():
            sku = str(row['product_model_no']).strip() if 'product_model_no' in row and not pd.isna(row['product_model_no']) else 'N/A'
            
            self.validate_product_title(idx, sku, row)
            self.validate_product_status(idx, sku, row)
            self.validate_shipping(idx, sku, row)
            self.validate_long_description(idx, sku, row)
            self.validate_highlights(idx, sku, row)
            self.validate_attributes(idx, sku, row)
            self.validate_seo_titles(idx, sku, row)
            self.validate_seo_descriptions(idx, sku, row)
            self.validate_seo_keywords(idx, sku, row)
            self.validate_pricing(idx, sku, row)

        return pd.DataFrame(self.errors)

    def validate_product_title(self, idx, sku, row):
        col = 'product_title'
        cat = 'Title Rules'
        if col not in row or pd.isna(row[col]):
            self.log_error(idx, sku, col, cat, "Title is missing.")
            return

        title = str(row[col]).strip()

        # Length check
        if not (150 <= len(title) <= 180):
            self.log_error(idx, sku, col, cat, f"Title length ({len(title)}) out of range [150-180].")

        # Disallowed characters
        disallowed = r'[\(\)\&\+\.\/:;\'"%\#@!–—]'
        if re.search(disallowed, title):
            self.log_error(idx, sku, col, cat, "Contains forbidden punctuation or copy-pasted dashes.")

        # Must start with Brand_Name
        brand = str(row['Brand_Name']).strip() if 'Brand_Name' in row and not pd.isna(row['Brand_Name']) else ""
        if brand and not title.startswith(brand):
            self.log_error(idx, sku, col, cat, f"Title must start with Brand Name '{brand}'.")

        # Must end with product_model_no formatted as " - SKU"
        if sku != 'N/A':
            expected_ending = f" - {sku}"
            if not title.endswith(expected_ending):
                self.log_error(idx, sku, col, cat, f"Title must end with SKU format ' - {sku}'.")

    def validate_brand_integrity(self):
        cat = 'Brand Mapping'
        if 'Brand_Name' in self.df.columns and 'brand_id' in self.df.columns:
            grouped = self.df.groupby('Brand_Name')['brand_id'].nunique()
            invalid_brands = grouped[grouped > 1].index.tolist()

            for idx, row in self.df.iterrows():
                sku = str(row['product_model_no']).strip() if 'product_model_no' in row and not pd.isna(row['product_model_no']) else 'N/A'
                if row['Brand_Name'] in invalid_brands:
                    self.log_error(idx, sku, 'Brand_Name', cat, f"Brand '{row['Brand_Name']}' maps to multiple brand_ids.")

    def validate_product_status(self, idx, sku, row):
        col = 'product_status'
        if col in row and str(row[col]).strip() not in ['1', '1.0']:
            self.log_error(idx, sku, col, 'Product Status', f"Status is '{row[col]}'; must equal 1.")

    def validate_barcodes(self):
        col = 'barcode_value'
        if col in self.df.columns:
            duplicates = self.df[self.df.duplicated(subset=[col], keep=False)]
            for idx in duplicates.index:
                val = self.df.loc[idx, col]
                sku = str(self.df.loc[idx, 'product_model_no']).strip() if 'product_model_no' in self.df.columns and not pd.isna(self.df.loc[idx, 'product_model_no']) else 'N/A'
                if not pd.isna(val):
                    self.log_error(idx, sku, col, 'Duplicates', f"Duplicate barcode value: '{val}'.")

    def validate_shipping(self, idx, sku, row):
        col = 'ship_charge_AED'
        if col in row and str(row[col]).strip() not in ['10', '10.0']:
            self.log_error(idx, sku, col, 'Shipping', f"Ship charge is '{row[col]}'; must equal 10.")

    def validate_long_description(self, idx, sku, row):
        col = 'product_long_description'
        if col in row and (pd.isna(row[col]) or str(row[col]).strip() == ""):
            self.log_error(idx, sku, col, 'Descriptions', "Product long description is empty.")

    def validate_highlights(self, idx, sku, row):
        highlight_cols = [c for c in self.df.columns if c.startswith('product_highlight_')]
        for col in highlight_cols:
            val = str(row[col]) if not pd.isna(row[col]) else ""
            if val:
                if ';' in val:
                    self.log_error(idx, sku, col, 'Highlights', "Semicolons ';' are not allowed in highlights.")
                if val.endswith('.'):
                    self.log_error(idx, sku, col, 'Highlights', "Must not end with a full stop.")
                if not (120 <= len(val) <= 150):
                    self.log_error(idx, sku, col, 'Highlights', f"Length ({len(val)}) out of range [120-150].")

    def validate_attributes(self, idx, sku, row):
        attr_cols = [c for c in self.df.columns if c.startswith('product_attribute_')]
        for col in attr_cols:
            val = str(row[col]) if not pd.isna(row[col]) else ""
            if val and not re.match(r'^[^\s:]+:[^\s:].*$', val):
                self.log_error(idx, sku, col, 'Attributes', "Invalid format. Expected 'Header:Value' with no space around colon.")

    def validate_seo_titles(self, idx, sku, row):
        for country in self.countries:
            seo_col = f"seo_title_{country}"
            cost_col = f"cost_{country}"
            if cost_col in row and not pd.isna(row[cost_col]):
                val = str(row[seo_col]) if seo_col in row and not pd.isna(row[seo_col]) else ""
                expected_suffix = f"Online at Best Prices in {country} | Ourshopee"
                if not val.endswith(expected_suffix):
                    self.log_error(idx, sku, seo_col, 'SEO Titles', f"Must end with '{expected_suffix}'.")

    def validate_seo_descriptions(self, idx, sku, row):
        for country in self.countries:
            col = f"seo_description_{country}"
            val = str(row[col]) if col in row and not pd.isna(row[col]) else ""
            if val:
                if not val.startswith("Buy "):
                    self.log_error(idx, sku, col, 'SEO Descriptions', "Must start with 'Buy '.")
                expected_suffix = f". Explore great deals at the best price. Get fast delivery across {country} | Ourshopee."
                if not val.endswith(expected_suffix):
                    self.log_error(idx, sku, col, 'SEO Descriptions', f"Must end with '{expected_suffix}'.")

    def validate_seo_keywords(self, idx, sku, row):
        for country in self.countries:
            col = f"seo_keywords_{country}"
            val = str(row[col]) if col in row and not pd.isna(row[col]) else ""
            if val:
                if re.search(r'\s,', val):
                    self.log_error(idx, sku, col, 'SEO Keywords', "Comma should not have a space before it.")
                if val.strip().endswith(','):
                    self.log_error(idx, sku, col, 'SEO Keywords', "Must not end with a trailing comma.")

    def validate_pricing(self, idx, sku, row):
        cost_cols = [c for c in self.df.columns if c.startswith('cost_')]
        for c_col in cost_cols:
            suffix = c_col.replace('cost_', '')
            p_col, sp_col = f"price_{suffix}", f"sp_price_{suffix}"
            try:
                cost = float(row[c_col]) if c_col in row and not pd.isna(row[c_col]) else None
                price = float(row[p_col]) if p_col in row and not pd.isna(row[p_col]) else None
                sp_price = float(row[sp_col]) if sp_col in row and not pd.isna(row[sp_col]) else None

                if cost is not None:
                    if price is not None and cost >= price:
                        self.log_error(idx, sku, c_col, 'Pricing', f"Cost ({cost}) must be lower than price ({price}).")
                    if sp_price is not None and cost >= sp_price:
                        self.log_error(idx, sku, c_col, 'Pricing', f"Cost ({cost}) must be lower than sp_price ({sp_price}).")
            except ValueError:
                self.log_error(idx, sku, c_col, 'Pricing', "Non-numeric values in pricing columns.")


# --- Helper Function to Create Sample Data ---
def generate_sample_data():
    return pd.DataFrame({
        'product_model_no': ['SKU-1001', 'SKU-1002', 'SKU-1003', 'SKU-1004'],
        'Brand_Name': ['Sony', 'Sony', 'Samsung', 'Apple'],
        'brand_id': ['B-10', 'B-10', 'B-20', 'B-30'],
        'product_title': [
            'Sony Wireless Noise Canceling Headphones Extra Bass Premium Sound - SKU-1001',
            'Incorrect Title Format Sample Without SKU End',
            'Samsung OLED Smart TV High Dynamic Range Resolution - SKU-1003',
            'Apple iPhone 15 Pro Max Natural Titanium 256GB Storage Edition - SKU-1004'
        ],
        'product_status': [1, 2, 1, 1],
        'barcode_value': ['880123456789', '880123456789', '880987654321', '880555444333'],
        'ship_charge_AED': [10, 15, 10, 10],
        'product_long_description': ['Detailed description here', '', 'Smart TV description', 'iPhone description'],
        'product_highlight_1': [
            'Feature one with proper length; invalid semicolon inside sentence description text length check here to reach minimum characters',
            'Feature two ending with full stop.',
            'Feature three with good characters count and no invalid punctuation or full stop at the end of the text line here now',
            'Feature four text line with proper length and format for testing sample validation rules successfully without issues'
        ],
        'product_attribute_1': ['Color:Black', 'Warranty: 2 Years', 'Screen:65 Inch', 'Storage:256GB'],
