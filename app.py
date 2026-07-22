import streamlit as st
import pandas as pd
import datetime

# ---------------------------------------------------------
# Page Setup
# ---------------------------------------------------------
st.set_page_config(
    page_title="Baital Betting Engine",
    page_icon="🎯",
    layout="wide"
)

# Initialize Session State for Bet History Ledger
if 'ledger' not in st.session_state:
    st.session_state.ledger = pd.DataFrame(columns=[
        "Date", "Match", "Market", "Stake (₹)", "Odds", "Result", "P&L (₹)"
    ])

# Header Title
st.title("🎯 Baital Betting Engine & Risk Dashboard")
st.caption("Powered by Ed Miller, Stanford Wong & Fractional Kelly Models")

# ---------------------------------------------------------
# Tabs Navigation
# ---------------------------------------------------------
tab1, tab2, tab3 = st.tabs(["🧮 +EV & Stake Calculator", "📊 P&L Ledger & Analytics", "📜 Baital Core Rules"])

# =========================================================
# TAB 1: CALCULATOR & DECISION ENGINE
# =========================================================
with tab1:
    st.header("🧮 Mathematical Edge Calculator")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("1. Market Odds & Bankroll")
        bankroll = st.number_input("Current Total Bankroll (₹)", min_value=100.0, value=10000.0, step=500.0)
        
        odds_a = st.number_input("Bookie Odds - Option A / YES", min_value=1.01, value=1.90, step=0.05)
        odds_b = st.number_input("Bookie Odds - Option B / NO", min_value=1.01, value=1.90, step=0.05)
        
        # Vig Calculation
        implied_a = 1 / odds_a
        implied_b = 1 / odds_b
        total_implied = implied_a + implied_b
        vig_pct = (total_implied - 1) * 100
        true_prob_a = implied_a / total_implied
        
        st.info(f"**Bookie Vig (Commission):** {vig_pct:.2f}% | **Fair Probability (Option A):** {true_prob_a*100:.1f}%")

    with col2:
        st.subheader("2. Your Assessment & Recommendation")
        
        user_est_prob = st.slider("Your Win Probability Estimate (%)", min_value=1.0, max_value=99.0, value=60.0) / 100.0
        
        selected_odds = odds_a
        
        # Expected Value Math
        net_odds = selected_odds - 1.0
        ev = (user_est_prob * net_odds) - (1.0 - user_est_prob)
        ev_pct = ev * 100.0
        
        # Kelly Criterion Math
        if net_odds > 0:
            kelly_f = (net_odds * user_est_prob - (1.0 - user_est_prob)) / net_odds
        else:
            kelly_f = 0
            
        quarter_kelly = max(0.0, kelly_f / 4.0)
        recommended_stake = quarter_kelly * bankroll

        st.markdown("---")
        st.subheader("🎯 Baital Decision Output")
        
        # Action Logic
        if vig_pct > 8.5:
            st.error("🛑 **ACTION: SKIP / PASS** (Bookie Vig is too high!)")
        elif ev <= 0:
            st.error(f"🛑 **ACTION: SKIP / PASS** (Negative EV: {ev_pct:.2f}%)")
        else:
            st.success(f"✅ **ACTION: BET RECOMMENDED!** (+EV: +{ev_pct:.2f}%)")
            st.metric("Recommended Risk Stake (Quarter Kelly)", f"₹{recommended_stake:.2f}", f"{quarter_kelly*100:.2f}% of Bankroll")

# =========================================================
# TAB 2: P&L LEDGER & ANALYTICS
# =========================================================
with tab2:
    st.header("📊 Performance Ledger & Tracker")
    
    # Summary Metrics
    df = st.session_state.ledger
    total_bets = len(df)
    
    if total_bets > 0:
        total_stake = df["Stake (₹)"].sum()
        net_pnl = df["P&L (₹)"].sum()
        wins = len(df[df["Result"] == "WIN"])
        win_rate = (wins / total_bets) * 100 if total_bets > 0 else 0
        roi = (net_pnl / total_stake) * 100 if total_stake > 0 else 0
    else:
        total_stake = 0
        net_pnl = 0
        win_rate = 0
        roi = 0

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Bets", total_bets)
    m2.metric("Win Rate", f"{win_rate:.1f}%")
    m3.metric("Net Profit/Loss", f"₹{net_pnl:.2f}")
    m4.metric("ROI", f"{roi:.2f}%")

    st.markdown("---")
    
    # Input Form to Log New Bet
    st.subheader("➕ Log New Bet Result")
    with st.form("bet_entry_form", clear_on_submit=True):
        f_col1, f_col2, f_col3 = st.columns(3)
        with f_col1:
            match_name = st.text_input("Match Name", placeholder="e.g. IND vs AUS")
            market_name = st.text_input("Market / Session", placeholder="e.g. 6-Over Runs")
        with f_col2:
            stake_val = st.number_input("Stake Amount (₹)", min_value=10.0, value=500.0)
            odds_val = st.number_input("Odds Taken", min_value=1.01, value=1.90)
        with f_col3:
            result_val = st.selectbox("Outcome", ["WIN", "LOSS", "VOID"])
            submit_btn = st.form_submit_button("Save Bet")

    if submit_btn:
        if result_val == "WIN":
            pnl_val = stake_val * (odds_val - 1.0)
        elif result_val == "LOSS":
            pnl_val = -stake_val
        else:
            pnl_val = 0.0

        new_entry = {
            "Date": datetime.date.today().strftime("%Y-%m-%d"),
            "Match": match_name,
            "Market": market_name,
            "Stake (₹)": stake_val,
            "Odds": odds_val,
            "Result": result_val,
            "P&L (₹)": round(pnl_val, 2)
        }
        st.session_state.ledger = pd.concat([st.session_state.ledger, pd.DataFrame([new_entry])], ignore_index=True)
        st.success("Bet Logged Successfully!")
        st.rerun()

    # Display History Table
    st.subheader("📋 Bet History Table")
    if total_bets > 0:
        st.dataframe(st.session_state.ledger, use_container_width=True)
        
        # Export to CSV
        csv_data = st.session_state.ledger.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download Ledger CSV",
            data=csv_data,
            file_name=f"betting_ledger_{datetime.date.today()}.csv",
            mime="text/csv"
        )
    else:
        st.info("No bets recorded yet. Add your first bet above!")

# =========================================================
# TAB 3: CORE RULES
# =========================================================
with tab3:
    st.header("📜 Baital's Mathematical Rules")
    st.markdown("""
    * **1. Positive Expected Value (+EV):** Never bet unless $EV > 0$.
      $$EV = (P_{\\text{win}} \\times \\text{Net Odds}) - (1 - P_{\\text{win}})$$
    * **2. Low Vig Rule:** If Bookie Vig is $> 8\\%$, **SKIP/PASS** the market immediately.
    * **3. Quarter Kelly Sizing:** Always use fractional bankroll sizing to avoid ruin:
      $$f^* = \\frac{b \\cdot p - q}{b} \\quad \\implies \\quad \\text{Stake} = \\frac{f^*}{4} \\times \\text{Bankroll}$$
    * **4. Zero Emotion:** No revenge bets or doubling down after losses.
    """)
  
