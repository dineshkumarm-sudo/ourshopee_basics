import io
import re
import pandas as pd
import streamlit as st

# --- Page Config ---
st.set_page_config(
    page_title="Our Shopee Basic Data Checks",
    page_icon="🛍️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Base64 SVG Logo (Our Shopee Blue Cart Logo) ---
LOGO_SVG = """
<svg width="80" height="80" viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg">
    <rect width="100" height="100" rx="20" fill="#5C32CA"/>
    <path d="M22 28H32L38 60H72L80 38H36" stroke="white" stroke-width="6" stroke-linecap="round" stroke-linejoin="round"/>
    <circle cx="42" cy="72" r="5" fill="white"/>
    <circle cx="68" cy="72" r="5" fill="white"/>
</svg>
"""

# --- Comprehensive Styling (Fixes Dark Mode + Button Contrast) ---
st.markdown("""
<style>
    /* Force canvas to soft gray/white */
    .stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
        background-color: #F5F5F7 !important;
        color: #1D1D1F !important;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif !important;
    }

    /* Keep all labels and generic text legible */
    p, span, label, h1, h2, h3, h4, h5, h6, div {
        color: #1D1D1F;
    }

    /* Frosted Header Container */
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

    /* Uploader Visibility in Dark Mode */
    div[data-testid="stFileUploader"] {
        background-color: #FFFFFF !important;
        border: 2px dashed #0A2540 !important;
        border-radius: 16px !important;
        padding: 20px !important;
        box-shadow: 0 2px 10px rgba(0,0,0,0.03) !important;
    }
    div[data-testid="stFileUploader"] * {
        color: #1D1D1F !important;
    }

    /* Universal Button Contrast Overrides */
    .stButton>button, 
    .stDownloadButton>button,
    button[kind="secondary"],
    button[kind="primary"] {
        background-color: #0A2540 !important;
        color: #FFFFFF !important;
        border-radius: 10px !important;
        border: 1px solid #0A2540 !important;
        font-weight: 600 !important;
        padding: 0.6rem 1.4rem !important;
        box-shadow: 0 4px 12px rgba(10, 37, 64, 0.2) !important;
        transition: all 0.2s ease !important;
    }

    .stButton>button *, 
    .stDownloadButton>button * {
        color: #FFFFFF !important;
    }

    .stButton>button:hover, 
    .stDownloadButton>button:hover {
        background-color: #FF6B00 !important;
        border-color: #FF6B00 !important;
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
                if
