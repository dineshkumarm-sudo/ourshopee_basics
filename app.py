import io
import re
import pandas as pd
import streamlit as st

# Set page configuration
st.set_page_config(
    page_title="Our Shopee Basic Data Checks",
    page_icon="🛍️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apple-inspired Frosted Glass / Light Theme CSS
st.markdown("""
<style>
    /* Force Light Background everywhere */
    .stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
        background-color: #F5F5F7 !important;
        color: #1D1D1F !important;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif !important;
    }
    
    /* Header Card */
    .header-card {
        background: rgba(255, 255, 255, 0.75);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.8);
        border-radius: 18px;
        padding: 24px 32px;
        margin-bottom: 28px;
        box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.06);
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    
    .gradient-title {
        font-size: 2.2rem;
        font-weight: 800;
        background: linear-gradient(135deg, #0A2540 0%, #D4AF37 50%, #FF6B00 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        letter-spacing: -0.5px;
        margin: 0;
    }
    
    .header-sub {
        color: #86868B;
        font-size: 0.95rem;
        margin-top: 4px;
        font-weight: 400;
    }
    
    .logo-img {
        width: 80px;
        height: 80px;
        border-radius: 16px;
        box-shadow: 0 4px 14px rgba(0,0,0,0.1);
        object-fit: cover;
    }

    /* Clean Uploader Box */
    [data-testid="stFileUploader"] {
        background: rgba(255, 255, 255, 0.8) !important;
        border: 2px dashed #0A2540 !important;
        border-radius: 16px !important;
        padding: 20px !important;
    }
    
    [data-testid="stFileUploader"] section {
        background: transparent !important;
    }
    
    [data-testid="stFileUploader"] label, [data-testid="stFileUploader"] span {
        color: #1D1D1F !important;
    }

    /* Glass Cards for Metrics */
    div[data-testid="stMetric"] {
        background: rgba(255, 255, 255, 0.7) !important;
        border: 1px solid rgba(255, 255, 255, 0.8) !important;
        border-radius: 16px !important;
        padding: 16px 20px !important;
        box-shadow: 0 4px 16px rgba(0,0,0,0.03) !important;
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

    /* Primary Navy Accent Button */
    .stButton>button, .stDownloadButton>button {
        background-color: #0A2540 !important;
        color: #FFFFFF !important;
        border-radius: 12px !important;
        border: none !important;
        font-weight: 600 !important;
        padding: 0.6rem 1.8rem !important;
        box-shadow: 0 4px 12px rgba(10, 37, 64, 0.2) !important;
        transition: all 0.2s ease !important;
    }

    .stButton>button:hover, .stDownloadButton>button:hover {
        background-color: #FF6B00 !important;
        box-shadow: 0 6px 16px rgba(255, 107, 0, 0.3) !important;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 12px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 10px;
        padding: 10px 20px;
        background-color: rgba(255, 255, 255, 0.6);
        color: #1D1D1F;
        font-weight: 600;
        border: 1px solid #E5E5EA;
    }
    .stTabs [aria-selected="true"] {
        background-color: #0A2540 !important;
        color: #FFFFFF !important;
        border: 1px solid #0A2540 !important;
    }
</style>
""", unsafe_allow_html=True)


# --- Data Validator Logic ---
class DataValidator:
    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()
        self.errors = []
        self.countries = ['UAE', 'OMAN', 'QATAR', 'KUWAIT', 'BAHRAIN', 'SAUDI']

    def log_error(self, row_idx, sku, column, message):
        self.errors.append({
            'Row': row_idx + 2,
            'SKU': sku if sku else 'N/A',
            'Column': column,
            'Error': message
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
        if col not in row or pd.isna(row[col]):
            self.log_error(idx, sku, col, "Title is missing.")
            return

        title = str(row[col]).strip()

        # Length check [150-180]
        if not (150 <= len(title) <= 180):
            self.log_error(idx, sku, col, f"Title length ({len(title)}) out of range [150-180].")

        # Disallowed characters check
        disallowed = r'[\(\)\&\+\.\/:;\'"%\#@!–—]'
        if re.search(disallowed, title):
            self.log_error(idx, sku, col, "Contains forbidden punctuation or copy-pasted dashes.")

        # Must start with Brand_Name
        brand = str(row['Brand_Name']).strip() if 'Brand_Name' in row and not pd.isna(row['Brand_Name']) else ""
        if brand and not title.startswith(brand):
            self.log_error(idx, sku, col, f"Title must start with Brand Name '{brand}'.")

        # Must end with product_model_no (SKU) formatted as " - SKU"
        if sku != 'N/A':
            expected_ending = f" - {sku}"
            if not title.endswith(expected_ending):
                self.log_error(idx, sku, col, f"Title must end with ' - {sku}'.")

    def validate_brand_integrity(self):
        if 'Brand_Name' in self.df.columns and 'brand_id' in self.df.columns:
            grouped = self.df.groupby('Brand_Name')['brand_id'].nunique()
            invalid_brands = grouped[grouped > 1].index.tolist()

            for idx, row in self.df.iterrows():
                sku = str(row['product_model_no']).strip() if 'product_model_no' in row and not pd.isna(row['product_model_no']) else 'N/A'
                if row['Brand_Name'] in invalid_brands:
                    self.log_error(idx, sku, 'Brand_Name', f"Brand '{row['Brand_Name']}' maps to multiple brand_ids.")

    def validate_product_status(self, idx, sku, row):
        col = 'product_status'
        if col in row and str(row[col]).strip() not in ['1', '1.0']:
            self.log_error(idx, sku, col, f"Status is '{row[col]}'; must be 1.")

    def validate_barcodes(self):
        col = 'barcode_value'
        if col in self.df.columns:
            duplicates = self.df[self.df.duplicated(subset=[col], keep=False)]
            for idx in duplicates.index:
                val = self.df.loc[idx, col]
                sku = str(self.df.loc[idx, 'product_model_no']).strip() if 'product_model_no' in self.df.columns and not pd.isna(self.df.loc[idx, 'product_model_no']) else 'N/A'
                if not pd.isna(val):
                    self.log_error(idx, sku, col, f"Duplicate barcode value: '{val}'.")

    def validate_shipping(self, idx, sku, row):
        col = 'ship_charge_AED'
        if col in row and str(row[col]).strip() not in ['10', '10.0']:
            self.log_error(idx, sku, col, f"Ship charge is '{row[col]}'; must be 10.")

    def validate_long_description(self, idx, sku, row):
        col = 'product_long_description'
        if col in row and (pd.isna(row[col]) or str(row[col]).strip() == ""):
            self.log_error(idx, sku, col, "Product long description is empty.")

    def validate_highlights(self, idx, sku, row):
        highlight_cols = [c for c in self.df.columns if c.startswith('product_highlight_')]
        for col in highlight_cols:
            val = str(row[col]) if not pd.isna(row[col]) else ""
            if val:
                if ';' in val:
                    self.log_error(idx, sku, col, "Semicolons ';' are not allowed in highlights.")
                if val.endswith('.'):
                    self.log_error(idx, sku, col, "Must not end with a full stop.")
                if not (120 <= len(val) <= 150):
                    self.log_error(idx, sku, col, f"Length ({len(val)}) out of range [120-150].")

    def validate_attributes(self, idx, sku, row):
        attr_cols = [c for c in self.df.columns if c.startswith('product_attribute_')]
        for col in attr_cols:
            val = str(row[col]) if not pd.isna(row[col]) else ""
            if val and not re.match(r'^[^\s:]+:[^\s:].*$', val):
                self.log_error(idx, sku, col, "Invalid format. Expected 'Header:Value' with no spaces around colon.")

    def validate_seo_titles(self, idx, sku, row):
        for country in self.countries:
            seo_col = f"seo_title_{country}"
            cost_col = f"cost_{country}"
            if cost_col in row and not pd.isna(row[cost_col]):
                val = str(row[seo_col]) if seo_col in row and not pd.isna(row[seo_col]) else ""
                expected_suffix = f"Online at Best Prices in {country} | Ourshopee"
                if not val.endswith(expected_suffix):
                    self.log_error(idx, sku, seo_col, f"Must end with '{expected_suffix}'.")

    def validate_seo_descriptions(self, idx, sku, row):
        for country in self.countries:
            col = f"seo_description_{country}"
            val = str(row[col]) if col in row and not pd.isna(row[col]) else ""
            if val:
                if not val.startswith("Buy "):
                    self.log_error(idx, sku, col, "Must start with 'Buy '.")
                expected_suffix = f". Explore great deals at the best price. Get fast delivery across {country} | Ourshopee."
                if not val.endswith(expected_suffix):
                    self.log_error(idx, sku, col, f"Must end with '{expected_suffix}'.")

    def validate_seo_keywords(self, idx, sku, row):
        for country in self.countries:
            col = f"seo_keywords_{country}"
            val = str(row[col]) if col in row and not pd.isna(row[col]) else ""
            if val:
                if re.search(r'\s,', val):
                    self.log_error(idx, sku, col, "Comma should not have a space before it.")
                if val.strip().endswith(','):
                    self.log_error(idx, sku, col, "Must not end with a trailing comma.")

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
                        self.log_error(idx, sku, c_col, f"Cost ({cost}) must be lower than price ({price}).")
                    if sp_price is not None and cost >= sp_price:
                        self.log_error(idx, sku, c_col, f"Cost ({cost}) must be lower than sp_price ({sp_price}).")
            except ValueError:
                self.log_error(idx, sku, c_col, "Non-numeric values in pricing columns.")


# --- UI Setup ---
LOGO_URL = "https://raw.githubusercontent.com/streamlit/app-examples/main/assets/logo.png"  # Placeholder or direct URL

st.markdown(f"""
<div class="header-card">
    <div>
        <h1 class="gradient-title">Our Shopee Basic Data Checks</h1>
        <div class="header-sub">Upload catalog spreadsheets for automatic title, SKU, SEO, highlight, and price validation.</div>
    </div>
    <img src="https://i.ibb.co/6P0w4H9/ourshopee-logo.jpg" class="logo-img" alt="OurShopee Logo" onerror="this.onerror=null; this.src='https://via.placeholder.com/80/0A2540/FFFFFF?text=OS';">
</div>
""", unsafe_allow_html=True)

uploaded_file = st.file_uploader("Drop your Excel or CSV file here", type=["csv", "xlsx", "xls"])

if uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
        
        validator = DataValidator(df)
        error_df = validator.run_all_validations()

        total_rows = len(df)
        error_rows = error_df['Row'].nunique() if not error_df.empty else 0
        total_errors = len(error_df)

        # Overview Cards
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Rows Evaluated", f"{total_rows:,}")
        c2.metric("Flagged Rows", f"{error_rows:,}")
        c3.metric("Total Issues", f"{total_errors:,}")
        c4.metric("Compliance Rate", f"{((total_rows - error_rows) / total_rows * 100):.1f}%" if total_rows > 0 else "100%")

        st.markdown("<br>", unsafe_allow_html=True)

        if not error_df.empty:
            tab1, tab2 = st.tabs(["📋 Validation Issue Logs", "📊 SKU Issue Dashboard"])

            with tab1:
                st.subheader("Row-by-Row Error Logs")
                st.dataframe(error_df, use_container_width=True, height=380)

                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df.to_excel(writer, index=False, sheet_name='Original Data')
                    error_df.to_excel(writer, index=False, sheet_name='Validation Errors')

                st.download_button(
                    label="Download Full Error Report (.xlsx)",
                    data=output.getvalue(),
                    file_name="ourshopee_validation_report.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

            with tab2:
                st.subheader("SKU Issue Breakdown Dashboard")
                
                # Breakdown by Column
                col_breakdown = error_df['Column'].value_counts().reset_index()
                col_breakdown.columns = ['Column Field', 'Error Count']
                
                col_left, col_right = st.columns([1, 1])
                with col_left:
                    st.markdown("**Top Invalid Fields**")
                    st.bar_chart(col_breakdown.set_index('Column Field'))

                with col_right:
                    st.markdown("**SKUs with Most Violations**")
                    sku_breakdown = error_df[error_df['SKU'] != 'N/A']['SKU'].value_counts().head(10).reset_index()
                    sku_breakdown.columns = ['SKU ID', 'Total Errors']
                    st.dataframe(sku_breakdown, use_container_width=True)

        else:
            st.balloons()
            st.success("All data validations passed! File is completely clean.")

    except Exception as e:
        st.error(f"Error reading file: {str(e)}")
