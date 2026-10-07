import io
import re
import pandas as pd
import streamlit as st

# --- Page Configuration ---
st.set_page_config(
    page_title="Our Shopee Basic Data Checks",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    /* Global Apple-inspired Light Background */
    .stApp {
        background-color: #F5F5F7 !important;
        font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "SF Pro Text", "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        color: #1D1D1F !important;
    }

    /* Top Main Title Banner */
    .header-banner {
        background: rgba(255, 255, 255, 0.85);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        padding: 1.8rem 2.2rem;
        border-radius: 20px;
        border: 1px solid rgba(229, 229, 234, 0.8);
        box-shadow: 0 8px 30px rgba(0, 0, 0, 0.04);
        margin-bottom: 2rem;
        display: flex;
        align-items: center;
        justify-content: space-between;
    }

    .header-title-text {
        background: linear-gradient(135deg, #0A2540 0%, #0071E3 45%, #D4AF37 75%, #FF6B00 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2.2rem;
        font-weight: 800;
        letter-spacing: -0.8px;
        margin: 0;
    }

    .header-sub-text {
        color: #86868B;
        font-size: 0.9rem;
        font-weight: 500;
        margin-top: 0.2rem;
    }

    /* Frosted Card Container */
    .glass-card {
        background: rgba(255, 255, 255, 0.75) !important;
        backdrop-filter: blur(15px);
        border-radius: 18px !important;
        border: 1px solid rgba(255, 255, 255, 0.9) !important;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.03) !important;
        padding: 1.5rem !important;
    }

    /* Metric Cards Override */
    div[data-testid="stMetric"] {
        background: rgba(255, 255, 255, 0.85) !important;
        border-radius: 16px !important;
        border: 1px solid #E5E5EA !important;
        padding: 1rem 1.2rem !important;
        box-shadow: 0 2px 10px rgba(0,0,0,0.02) !important;
    }

    /* File Uploader Light Mode High Contrast Fix */
    div[data-testid="stFileUploader"] {
        background-color: #FFFFFF !important;
        border: 2px dashed #0071E3 !important;
        border-radius: 16px !important;
        padding: 1.2rem !important;
        box-shadow: 0 4px 15px rgba(0, 113, 227, 0.05) !important;
    }

    /* Buttons */
    .stButton>button {
        background-color: #0A2540 !important;
        color: #FFFFFF !important;
        border-radius: 12px !important;
        font-weight: 600 !important;
        padding: 0.6rem 1.8rem !important;
        border: none !important;
        transition: all 0.2s ease;
    }
    .stButton>button:hover {
        background-color: #0071E3 !important;
        box-shadow: 0 4px 14px rgba(0, 113, 227, 0.3) !important;
    }
</style>
""", unsafe_allow_html=True)


class CatalogDataValidator:
    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()
        self.errors = []
        self.countries = ['UAE', 'OMAN', 'QATAR', 'KUWAIT', 'BAHRAIN', 'SAUDI']

    def log_error(self, row_idx, sku, brand, column, message):
        self.errors.append({
            'Excel Row': row_idx + 2,
            'SKU': sku,
            'Brand': brand,
            'Column': column,
            'Violation Error Message': message
        })

    def execute_validation(self):
        # 1-to-1 Brand Name mapping check
        brand_map = {}
        if 'Brand_Name' in self.df.columns and 'brand_id' in self.df.columns:
            for _, r in self.df.iterrows():
                b = str(r['Brand_Name']).strip()
                b_id = str(r['brand_id']).strip()
                if b and b_id and b != 'nan':
                    if b not in brand_map:
                        brand_map[b] = set()
                    brand_map[b].add(b_id)

        # Duplicate Barcode check
        bc_counts = self.df['barcode_value'].value_counts() if 'barcode_value' in self.df.columns else {}

        # Row-level iterations
        for idx, row in self.df.iterrows():
            sku = str(row.get('product_model_no', f'ROW-{idx+2}')).strip()
            brand = str(row.get('Brand_Name', 'Unknown')).strip()

            # 1. product_title checks
            t_col = 'product_title'
            if t_col in row and not pd.isna(row[t_col]):
                title = str(row[t_col]).strip()
                
                # Length check
                if not (150 <= len(title) <= 180):
                    self.log_error(idx, sku, brand, t_col, f"Title length ({len(title)}) out of range [150-180].")
                
                # Must start with Brand_Name
                if brand != 'Unknown' and not title.startswith(brand):
                    self.log_error(idx, sku, brand, t_col, f"Title MUST start with Brand_Name '{brand}'.")
                
                # Must end with product_model_no
                if 'product_model_no' in row and not pd.isna(row['product_model_no']):
                    if not title.endswith(sku):
                        self.log_error(idx, sku, brand, t_col, f"Title MUST end with product_model_no '{sku}'.")
                    if f" - {sku}" not in title:
                        self.log_error(idx, sku, brand, t_col, f"Title must contain hyphen format ' - {sku}' before model no.")

                # Forbidden Punctuation Check
                forbidden = r'[\(\)\&\+\.\/:;\'"%\#@!–—]'
                if re.search(forbidden, title):
                    self.log_error(idx, sku, brand, t_col, "Contains forbidden punctuation or en/em dashes.")
            else:
                self.log_error(idx, sku, brand, t_col, "product_title is missing.")

            # 2. Brand mapping check
            if brand in brand_map and len(brand_map[brand]) > 1:
                self.log_error(idx, sku, brand, 'Brand_Name', f"Brand '{brand}' maps to multiple brand_ids.")

            # 3. product_status
            if 'product_status' in row and str(row['product_status']).strip() not in ['1', '1.0']:
                self.log_error(idx, sku, brand, 'product_status', f"product_status must equal 1.")

            # 4. barcode_value uniqueness
            if 'barcode_value' in row and not pd.isna(row['barcode_value']):
                bc = row['barcode_value']
                if bc_counts.get(bc, 0) > 1:
                    self.log_error(idx, sku, brand, 'barcode_value', f"Duplicate barcode_value '{bc}'.")

            # 5. ship_charge_AED
            if 'ship_charge_AED' in row and str(row['ship_charge_AED']).strip() not in ['10', '10.0']:
                self.log_error(idx, sku, brand, 'ship_charge_AED', "ship_charge_AED must equal 10.")

            # 6. product_long_description
            if 'product_long_description' in row and (pd.isna(row['product_long_description']) or str(row['product_long_description']).strip() == ''):
                self.log_error(idx, sku, brand, 'product_long_description', "product_long_description cannot be empty.")

            # 7. product_highlight_*
            for col in [c for c in self.df.columns if c.startswith('product_highlight_')]:
                val = str(row[col]).strip() if not pd.isna(row[col]) else ''
                if val:
                    if not (120 <= len(val) <= 150):
                        self.log_error(idx, sku, brand, col, f"Highlight length ({len(val)}) out of range [120-150].")
                    if val.endswith('.'):
                        self.log_error(idx, sku, brand, col, "Must NOT end with a full stop (.).")
                    if ';' in val:
                        self.log_error(idx, sku, brand, col, "Must NOT contain semi-colons (;).")

            # 8. product_attribute_*
            for col in [c for c in self.df.columns if c.startswith('product_attribute_')]:
                val = str(row[col]).strip() if not pd.isna(row[col]) else ''
                if val and not re.match(r'^[^\s:]+:[^\s:].*$', val):
                    self.log_error(idx, sku, brand, col, "Format must be 'Header:Value' with NO spaces around colon.")

            # 9. Pricing Checks
            for c in self.countries:
                c_col = f"cost_{c}"
                p_col = f"price_{c}"
                sp_col = f"sp_price_{c}"
                if c_col in row and not pd.isna(row[c_col]):
                    try:
                        cost = float(row[c_col])
                        if p_col in row and not pd.isna(row[p_col]) and cost >= float(row[p_col]):
                            self.log_error(idx, sku, brand, c_col, f"cost ({cost}) must be lower than price.")
                        if sp_col in row and not pd.isna(row[sp_col]) and cost >= float(row[sp_col]):
                            self.log_error(idx, sku, brand, c_col, f"cost ({cost}) must be lower than sp_price.")
                    except ValueError:
                        pass

        return pd.DataFrame(self.errors)


st.markdown("""
<div class="header-banner">
    <div>
        <h1 class="header-title-text">Our Shopee Basic Data Checks</h1>
        <p class="header-subtitle">Quality Assurance & Product Catalog Compliance Engine</p>
    </div>
    <div style="background: rgba(255,255,255,0.9); padding: 10px 18px; border-radius: 16px; border: 1px solid #E5E5EA; text-align: center;">
        <span style="font-size: 14px; font-weight: 800; color: #0A2540; display: block;">OURSHOPEE</span>
        <span style="font-size: 10px; font-weight: 700; color: #FF6B00;">VALIDATION APP</span>
    </div>
</div>
""", unsafe_allow_html=True)

# Main Navigation Sidebar
st.sidebar.title("Navigation & Settings")
page = st.sidebar.radio("Select View Page", ["Validator App", "SKU Issues Dashboard"])

uploaded_file = st.sidebar.file_uploader("Upload Product File (.xlsx, .csv)", type=["csv", "xlsx", "xls"])

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
    validator = CatalogDataValidator(df)
    err_df = validator.execute_validation()

    if page == "Validator App":
        st.subheader("Validation Overview")
        
        # KPI Row
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Catalog Rows", len(df))
        flagged_count = err_df['SKU'].nunique() if not err_df.empty else 0
        col2.metric("Flagged SKUs", flagged_count)
        col3.metric("Total Rule Errors", len(err_df))
        pass_rate = round(((len(df) - flagged_count) / len(df)) * 100, 1) if len(df) > 0 else 100
        col4.metric("Catalog Compliance Rate", f"{pass_rate}%")

        st.markdown("<br>", unsafe_allow_html=True)

        if not err_df.empty:
            st.error(f"Found {len(err_df)} errors across {flagged_count} SKUs.")
            st.dataframe(err_df, use_container_width=True)

            # Export Button
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='Catalog Data')
                err_df.to_excel(writer, index=False, sheet_name='Validation Errors')
            
            st.download_button(
                label="Download Validation Excel Report",
                data=output.getvalue(),
                file_name="OurShopee_Data_Validation_Report.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            st.success("🎉 All data checks passed cleanly!")

    elif page == "SKU Issues Dashboard":
        st.subheader("SKU Issue Breakdown Analytics")
        if not err_df.empty:
            # Bar chart by Column
            col_counts = err_df['Column'].value_counts()
            st.write("##### Violations Count by Column")
            st.bar_chart(col_counts)

            st.write("##### Flagged SKU List")
            sku_summary = err_df.groupby(['SKU', 'Brand']).agg({'Violation Error Message': 'count', 'Column': lambda x: ', '.join(set(x))}).reset_index()
            sku_summary.columns = ['SKU Model No', 'Brand', 'Total Errors', 'Violated Columns']
            st.dataframe(sku_summary, use_container_width=True)
        else:
            st.info("No validation errors recorded. Load a file with issues to explore the dashboard.")
else:
    st.info("👈 Please upload an Excel or CSV catalog file in the sidebar to begin checking.")
