import io
import re
import pandas as pd
import streamlit as st

# --- Page Configuration ---
st.set_page_config(
    page_title="Product Data Validator",
    page_icon="✔",
    layout="wide"
)

# --- Custom Styling (Apple Minimalist + Navy Blue Accent) ---
st.markdown("""
<style>
    /* Main container background & font styling */
    .stApp {
        background-color: #F8F9FA;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        color: #1D1D1F;
    }
    
    /* Header Container */
    .header-container {
        background: #FFFFFF;
        padding: 1.8rem 2rem;
        border-radius: 14px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.04);
        margin-bottom: 2rem;
        border: 1px solid #E5E5EA;
    }
    .header-title {
        color: #0A2540;
        font-size: 1.8rem;
        font-weight: 700;
        margin: 0 0 0.4rem 0;
        letter-spacing: -0.5px;
    }
    .header-subtitle {
        color: #86868B;
        font-size: 0.95rem;
        margin: 0;
    }

    /* Metric Cards */
    div[data-testid="stMetric"] {
        background-color: #FFFFFF;
        border-radius: 12px;
        padding: 1.2rem;
        border: 1px solid #E5E5EA;
        box-shadow: 0 2px 8px rgba(0,0,0,0.02);
    }
    div[data-testid="stMetricLabel"] {
        color: #86868B;
        font-weight: 500;
    }
    div[data-testid="stMetricValue"] {
        color: #0A2540;
        font-weight: 700;
    }

    /* File Uploader Container */
    div[data-testid="stFileUploader"] {
        background-color: #FFFFFF;
        border: 2px dashed #0A2540;
        border-radius: 12px;
        padding: 1.5rem;
    }

    /* Primary Accent Buttons */
    .stButton>button {
        background-color: #0A2540 !important;
        color: #FFFFFF !important;
        border-radius: 8px !important;
        border: none !important;
        font-weight: 600 !important;
        padding: 0.5rem 1.5rem !important;
        transition: all 0.2s ease;
    }
    .stButton>button:hover {
        background-color: #001429 !important;
        box-shadow: 0 4px 12px rgba(10, 37, 64, 0.25);
    }
    
    /* Download Button Override */
    .stDownloadButton>button {
        background-color: #0A2540 !important;
        color: #FFFFFF !important;
        border-radius: 8px !important;
        border: none !important;
        font-weight: 600 !important;
    }

    /* Tabs Styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 6px;
        padding: 8px 16px;
        background-color: #E5E5EA;
        color: #1D1D1F;
        font-weight: 500;
    }
    .stTabs [aria-selected="true"] {
        background-color: #0A2540 !important;
        color: #FFFFFF !important;
    }
</style>
""", unsafe_allow_html=True)


# --- Core Validation Logic ---
class DataValidator:
    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()
        self.errors = []  # List of dicts: {'Row': int, 'Column': str, 'Error': str}
        self.countries = ['UAE', 'OMAN', 'QATAR', 'KUWAIT', 'BAHRAIN', 'SAUDI']

    def log_error(self, row_idx, column, message):
        self.errors.append({
            'Row': row_idx + 2,  # 1-indexed + header offset
            'Column': column,
            'Error': message
        })

    def run_all_validations(self):
        self.validate_brand_integrity()
        self.validate_barcodes()
        
        for idx, row in self.df.iterrows():
            self.validate_product_title(idx, row)
            self.validate_product_status(idx, row)
            self.validate_shipping(idx, row)
            self.validate_long_description(idx, row)
            self.validate_highlights(idx, row)
            self.validate_attributes(idx, row)
            self.validate_seo_titles(idx, row)
            self.validate_seo_descriptions(idx, row)
            self.validate_seo_keywords(idx, row)
            self.validate_pricing(idx, row)

        return pd.DataFrame(self.errors)

    def validate_product_title(self, idx, row):
        col = 'product_title'
        if col not in row or pd.isna(row[col]):
            self.log_error(idx, col, "Title is missing.")
            return

        title = str(row[col])

        # Length check
        if not (150 <= len(title) <= 180):
            self.log_error(idx, col, f"Title length ({len(title)}) out of range [150-180].")

        # Disallowed characters check ( ) & + . / : ; ' " % # @ ! and en/em dashes
        disallowed = r'[\(\)\&\+\.\/:;\'"%\#@!–—]'
        if re.search(disallowed, title):
            self.log_error(idx, col, "Contains forbidden punctuation or non-standard dash.")

        # SKU check &Hyphen formatting
        sku_col = 'product_model_no'
        if sku_col in row and not pd.isna(row[sku_col]):
            sku = str(row[sku_col]).strip()
            if sku not in title:
                self.log_error(idx, col, f"Does not contain SKU '{sku}'.")
            
            # Hyphen before SKU format check: " - "
            hyphen_pattern = rf" - {re.escape(sku)}"
            if not re.search(hyphen_pattern, title):
                self.log_error(idx, col, f"Hyphen before SKU must strictly be formatted as ' - {sku}'.")

        # Allowed characters check: A-Z, a-z, 0-9, space, comma, hyphen
        clean_title = title.replace(f" - {sku}", "") if (sku_col in row and not pd.isna(row[sku_col])) else title
        invalid_chars = re.findall(r'[^A-Za-z0-9, ]', clean_title)
        if invalid_chars:
            unique_invalids = list(set(invalid_chars))
            self.log_error(idx, col, f"Contains invalid characters: {unique_invalids}")

    def validate_brand_integrity(self):
        if 'Brand_Name' in self.df.columns and 'brand_id' in self.df.columns:
            # Check 1 Brand Name mapping to multiple brand_ids
            grouped = self.df.groupby('Brand_Name')['brand_id'].nunique()
            invalid_brands = grouped[grouped > 1].index.tolist()
            
            for idx, row in self.df.iterrows():
                if row['Brand_Name'] in invalid_brands:
                    self.log_error(idx, 'Brand_Name', f"Brand '{row['Brand_Name']}' maps to multiple brand_ids.")

    def validate_product_status(self, idx, row):
        col = 'product_status'
        if col in row:
            if str(row[col]).strip() not in ['1', '1.0']:
                self.log_error(idx, col, f"Status is {row[col]}; must be 1.")

    def validate_barcodes(self):
        col = 'barcode_value'
        if col in self.df.columns:
            duplicates = self.df[self.df.duplicated(subset=[col], keep=False)]
            for idx in duplicates.index:
                val = self.df.loc[idx, col]
                if not pd.isna(val):
                    self.log_error(idx, col, f"Duplicate barcode value: '{val}'.")

    def validate_shipping(self, idx, row):
        col = 'ship_charge_AED'
        if col in row:
            if str(row[col]).strip() not in ['10', '10.0']:
                self.log_error(idx, col, f"Ship charge is {row[col]}; must be 10.")

    def validate_long_description(self, idx, row):
        col = 'product_long_description'
        if col in row:
            if pd.isna(row[col]) or str(row[col]).strip() == "":
                self.log_error(idx, col, "Product long description is empty.")

    def validate_highlights(self, idx, row):
        highlight_cols = [c for c in self.df.columns if c.startswith('product_highlight_')]
        for col in highlight_cols:
            val = str(row[col]) if not pd.isna(row[col]) else ""
            if val:
                if val.endswith('.'):
                    self.log_error(idx, col, "Must not end with a full stop.")
                if not (120 <= len(val) <= 150):
                    self.log_error(idx, col, f"Length ({len(val)}) out of range [120-150].")
                # Single sentence check (no internal sentence boundaries)
                if len(re.split(r'[\.\!\?]\s+', val)) > 1:
                    self.log_error(idx, col, "Contains more than 1 sentence.")

    def validate_attributes(self, idx, row):
        attr_cols = [c for c in self.df.columns if c.startswith('product_attribute_')]
        for col in attr_cols:
            val = str(row[col]) if not pd.isna(row[col]) else ""
            if val:
                # Format check Header:Value (no space around colon)
                if not re.match(r'^[^\s:]+:[^\s:].*$', val):
                    self.log_error(idx, col, "Invalid format. Expected 'Header:Value' without spaces around colon.")

    def validate_seo_titles(self, idx, row):
        for country in self.countries:
            seo_col = f"seo_title_{country}"
            cost_col = f"cost_{country}"
            
            # Run if cost column for this country is present and filled
            if cost_col in row and not pd.isna(row[cost_col]):
                val = str(row[seo_col]) if seo_col in row and not pd.isna(row[seo_col]) else ""
                expected_suffix = f"Online at Best Prices in {country} | Ourshopee"
                if not val.endswith(expected_suffix):
                    self.log_error(idx, seo_col, f"Must end with '{expected_suffix}'.")

    def validate_seo_descriptions(self, idx, row):
        title = str(row['product_title']) if 'product_title' in row and not pd.isna(row['product_title']) else ""
        for country in self.countries:
            col = f"seo_description_{country}"
            val = str(row[col]) if col in row and not pd.isna(row[col]) else ""
            if val:
                if not val.startswith("Buy "):
                    self.log_error(idx, col, "Must start with 'Buy '.")
                
                expected_suffix = f". Explore great deals at the best price. Get fast delivery across {country} | Ourshopee."
                if not val.endswith(expected_suffix):
                    self.log_error(idx, col, f"Must end with '{expected_suffix}'.")

    def validate_seo_keywords(self, idx, row):
        for country in self.countries:
            col = f"seo_keywords_{country}"
            val = str(row[col]) if col in row and not pd.isna(row[col]) else ""
            if val:
                if re.search(r'\s,', val):
                    self.log_error(idx, col, "Comma should not have a space before it.")
                if val.strip().endswith(','):
                    self.log_error(idx, col, "Must not end with a trailing comma.")
                
                # Check cross-country mention restrictions
                other_countries = [c for c in self.countries if c != country and c != 'UAE']
                for other in other_countries:
                    if re.search(rf'\b{other}\b', val, re.IGNORECASE):
                        self.log_error(idx, col, f"Cannot mention '{other}' in {col}.")

    def validate_pricing(self, idx, row):
        # Match pattern like cost_AED, cost_OMR, etc.
        cost_cols = [c for c in self.df.columns if c.startswith('cost_')]
        for c_col in cost_cols:
            suffix = c_col.replace('cost_', '')
            p_col = f"price_{suffix}"
            sp_col = f"sp_price_{suffix}"
            
            try:
                cost = float(row[c_col]) if c_col in row and not pd.isna(row[c_col]) else None
                price = float(row[p_col]) if p_col in row and not pd.isna(row[p_col]) else None
                sp_price = float(row[sp_col]) if sp_col in row and not pd.isna(row[sp_col]) else None

                if cost is not None:
                    if price is not None and cost >= price:
                        self.log_error(idx, c_col, f"Cost ({cost}) must be strictly lower than price ({price}).")
                    if sp_price is not None and cost >= sp_price:
                        self.log_error(idx, c_col, f"Cost ({cost}) must be strictly lower than sp_price ({sp_price}).")
            except ValueError:
                self.log_error(idx, c_col, "Non-numeric values found in pricing columns.")


# --- UI Layout ---
st.markdown("""
<div class="header-container">
    <h1 class="header-title">Product Catalog Validation Tool</h1>
    <p class="header-subtitle">Upload your CSV or Excel file to check against product, title, SEO, and pricing rules.</p>
</div>
""", unsafe_allow_html=True)

uploaded_file = st.file_uploader("Choose a file (.csv, .xlsx, .xls)", type=["csv", "xlsx", "xls"])

if uploaded_file is not None:
    try:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)

        st.success(f"Successfully loaded `{uploaded_file.name}` ({len(df)} rows)")

        # Run Validation
        validator = DataValidator(df)
        error_df = validator.run_all_validations()

        # Key Metrics
        total_rows = len(df)
        error_rows = error_df['Row'].nunique() if not error_df.empty else 0
        total_errors = len(error_df)

        col1, col2, col3 = st.columns(3)
        col1.metric("Total Rows Evaluated", total_rows)
        col2.metric("Rows with Errors", error_rows)
        col3.metric("Total Issues Found", total_errors)

        st.markdown("<br>", unsafe_allow_html=True)

        if not error_df.empty:
            tab1, tab2 = st.tabs(["Error Summary Table", "Detailed Cell Inspector"])

            with tab1:
                st.subheader("Validation Issues Log")
                st.dataframe(error_df, use_container_width=True, height=350)

                # Export Error Report to Excel
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df.to_excel(writer, index=False, sheet_name='Original Data')
                    error_df.to_excel(writer, index=False, sheet_name='Validation Errors')
                
                st.download_button(
                    label="Download Full Error Report (.xlsx)",
                    data=output.getvalue(),
                    file_name="validation_report.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

            with tab2:
                st.subheader("Data Grid with Flagged Cells")

                # Highlight bad cells in red
                def highlight_errors(val, row_idx, col_name):
                    is_err = not error_df[(error_df['Row'] == row_idx + 2) & (error_df['Column'] == col_name)].empty
                    return 'background-color: #FFE5E5; color: #D8000C; font-weight: bold;' if is_err else ''

                styled_df = df.style.apply(
                    lambda col: [highlight_errors(val, r_idx, col.name) for r_idx, val in enumerate(col)],
                    axis=0
                )
                st.dataframe(styled_df, use_container_width=True, height=450)
        else:
            st.balloons()
            st.success("All validations passed! No errors found in the file.")

    except Exception as e:
        st.error(f"Error processing file: {str(e)}")