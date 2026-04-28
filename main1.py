import streamlit as st
import yfinance as yf
import pandas as pd

# --- Page Config ---
st.set_page_config(page_title="Shariah Stock Screener", layout="centered")
st.title("🕌 BSE/NSE Shariah Compliance Screener")
st.markdown("Automatically calculate AAOIFI financial ratios for Indian equities.")

# --- Search Interface ---
st.sidebar.header("Search Stock")
ticker_input = st.sidebar.text_input("Enter Ticker Symbol (e.g., RELIANCE, TCS, RISHABH):", "RELIANCE").upper()
exchange = st.sidebar.radio("Select Exchange:", ("NSE", "BSE"))

# Format ticker for Yahoo Finance
if exchange == "NSE":
    yf_ticker = f"{ticker_input}.NS"
else:
    yf_ticker = f"{ticker_input}.BO"

# --- Fetch Data Function ---
# Added 'financials' to fetch the income statement for the 5% revenue rule
@st.cache_data(ttl=3600) 
def fetch_financials(ticker_symbol):
    try:
        stock = yf.Ticker(ticker_symbol)
        info = stock.info
        bs = stock.balance_sheet
        financials = stock.financials
        return info, bs, financials
    except Exception as e:
        return None, None, None

if st.sidebar.button("Analyze Stock"):
    with st.spinner(f"Fetching financial data for {ticker_input}..."):
        info, bs, financials = fetch_financials(yf_ticker)
        
        # Check if info is a valid dictionary and dataframes aren't empty
        if not isinstance(info, dict) or "symbol" not in info or bs.empty or financials.empty:
            st.error("❌ Could not fetch complete data. Please check the ticker symbol or try a different exchange.")
        else:
            st.subheader(f"Results for {info.get('longName', ticker_input)} ({yf_ticker})")
            st.write(f"**Sector:** {info.get('sector', 'N/A')} | **Industry:** {info.get('industry', 'N/A')}")
            
            # --- Sector Screening Warning ---
            st.warning("**Step 1: Sector Screening (Manual Check Required)**\n\nEnsure this company does not derive its primary revenue from conventional banking, alcohol, gambling, or pork products.")
            
            # --- Financial Ratio Calculations ---
            st.markdown("### Step 2: Financial Ratios (AAOIFI Standards)")
            
            try:
                # Get most recent annual data from Balance Sheet and Income Statement
                recent_bs = bs.iloc[:, 0] 
                recent_inc = financials.iloc[:, 0]
                
                # --- Extract Data safely using .get() ---
                total_assets = recent_bs.get("Total Assets", 0)
                total_debt = recent_bs.get("Total Debt", 0)
                cash_and_equiv = recent_bs.get("Cash And Cash Equivalents", 0)
                short_term_investments = recent_bs.get("Other Short Term Investments", 0)
                
                total_revenue = recent_inc.get("Total Revenue", 0)
                interest_income = recent_inc.get("Interest Income", 0)
                
                total_cash_investments = cash_and_equiv + short_term_investments
                
                if total_assets > 0 and total_revenue > 0:
                    # --- Calculate Ratios ---
                    debt_to_assets = (total_debt / total_assets) * 100
                    cash_to_assets = (total_cash_investments / total_assets) * 100
                    interest_to_revenue = (interest_income / total_revenue) * 100
                    
                    # --- Layout Metrics ---
                    # Upgraded to 3 columns to include the new metric
                    col1, col2, col3 = st.columns(3)
                    
                    # 1. Debt Ratio Metric
                    with col1:
                        st.metric(label="Debt / Assets", value=f"{debt_to_assets:.2f}%")
                        if debt_to_assets < 33:
                            st.success("✅ Pass (< 33%)")
                        else:
                            st.error("❌ Fail (≥ 33%)")
                            
                    # 2. Cash Ratio Metric
                    with col2:
                        st.metric(label="Cash / Assets", value=f"{cash_to_assets:.2f}%")
                        if cash_to_assets < 33:
                            st.success("✅ Pass (< 33%)")
                        else:
                            st.error("❌ Fail (≥ 33%)")

                    # 3. Interest Income Ratio Metric
                    with col3:
                        st.metric(label="Interest / Revenue", value=f"{interest_to_revenue:.2f}%")
                        if interest_to_revenue < 5:
                            st.success("✅ Pass (< 5%)")
                        else:
                            st.error("❌ Fail (≥ 5%)")
                            
                    # --- Final Verdict Logic ---
                    st.divider()
                    if debt_to_assets < 33 and cash_to_assets < 33 and interest_to_revenue < 5:
                        st.success("### 🟢 Financial Ratios: COMPLIANT")
                        st.write("The company passes the AAOIFI financial screening thresholds. Verify the sector compliance to confirm overall Shariah status.")
                    else:
                        st.error("### 🔴 Financial Ratios: NON-COMPLIANT")
                        st.write("The company fails one or more of the AAOIFI financial screening thresholds.")
                        
                else:
                    st.warning("Total Assets or Total Revenue data is missing or zero. Cannot calculate ratios.")
                    
            except Exception as e:
                st.error(f"⚠️ Incomplete financial data available for this specific stock to calculate all ratios. (Error details: {e})")
