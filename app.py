import json
import math
from dataclasses import asdict, dataclass, replace

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
import streamlit as st


# ===========================================================================
# Brand tokens (navy / brass premium identity) and shared Plotly theme.
# ===========================================================================
INK = "#0F2138"
INK_2 = "#1C3350"
BRASS = "#C29B4A"
SLATE = "#55677B"
POS = "#1F7A5C"
NEG = "#A83A46"
WARN = "#B9821F"
GRID = "#EDF1F6"

BRAND_SEQUENCE = [INK, BRASS, "#4C7A99", POS, NEG, "#8A7CB0", "#B5643C"]

_brand_template = go.layout.Template()
_brand_template.layout = go.Layout(
    font=dict(family="Inter, system-ui, sans-serif", color="#1A2A3A", size=13),
    title=dict(font=dict(family="Fraunces, Georgia, serif", size=17, color=INK),
               x=0, xanchor="left", y=0.97, pad=dict(b=6)),
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    colorway=BRAND_SEQUENCE,
    xaxis=dict(gridcolor=GRID, zerolinecolor="#D8E0EA", linecolor="#D8E0EA",
               ticks="outside", tickcolor="#D8E0EA"),
    yaxis=dict(gridcolor=GRID, zerolinecolor="#D8E0EA", linecolor="rgba(0,0,0,0)"),
    legend=dict(bgcolor="rgba(0,0,0,0)", orientation="h", yanchor="bottom", y=1.02, x=0),
    margin=dict(l=8, r=8, t=56, b=8),
    hoverlabel=dict(font=dict(family="Inter, sans-serif"), bgcolor=INK,
                    font_color="#FFFFFF", bordercolor=BRASS),
)
pio.templates["synaptive"] = _brand_template
pio.templates.default = "plotly_white+synaptive"
px.defaults.template = "plotly_white+synaptive"
px.defaults.color_discrete_sequence = BRAND_SEQUENCE


st.set_page_config(page_title="Property Investment Dashboard", page_icon="🏠", layout="wide")

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,500;9..144,600;9..144,700&family=Inter:wght@400;500;600;700&display=swap');
    :root { --ink:#0F2138; --ink-2:#1C3350; --brass:#C29B4A; --brass-soft:#E7D6AC;
        --paper:#F5F7FA; --surface:#FFFFFF; --line:#E4EAF1; --slate:#55677B;
        --pos:#1F7A5C; --warn:#B9821F; --neg:#A83A46; }
    html, body, [data-testid="stAppViewContainer"], [data-testid="stApp"] {
        font-family:'Inter',system-ui,-apple-system,sans-serif; color:#1A2A3A; }
    [data-testid="stAppViewContainer"] { background:var(--paper); }
    .block-container { padding-top:1.4rem; padding-bottom:3rem; max-width:1320px; }
    h1,h2,h3,h4 { font-family:'Fraunces',Georgia,serif; color:var(--ink); letter-spacing:-0.01em; }
    [data-testid="stMarkdownContainer"] h3 { font-weight:600; font-size:1.18rem; margin-top:0.6rem;
        padding-bottom:0.4rem; border-bottom:1px solid var(--line); }

    .hero { display:flex; flex-wrap:wrap; align-items:center; justify-content:space-between; gap:24px;
        background: radial-gradient(1200px 400px at 88% -40%, rgba(194,155,74,0.20), transparent 60%),
        linear-gradient(120deg,var(--ink) 0%,var(--ink-2) 100%);
        color:#EAF0F7; border-radius:18px; padding:30px 34px; margin-bottom:22px;
        border:1px solid rgba(194,155,74,0.28); box-shadow:0 18px 40px -24px rgba(15,33,56,0.55); }
    .hero-copy { max-width:760px; }
    .hero-eyebrow { text-transform:uppercase; letter-spacing:0.22em; font-size:0.68rem; font-weight:600;
        color:var(--brass); margin-bottom:10px; }
    .hero-title { font-family:'Fraunces',Georgia,serif; color:#FFF !important; font-size:2.15rem;
        font-weight:600; line-height:1.08; margin:0 0 8px 0; }
    .hero-sub { font-size:0.92rem; color:#B9C6D6; margin:0; line-height:1.5; }
    .hero-byline { margin-top:14px; font-size:0.8rem; letter-spacing:0.04em; color:#93A6BC; }
    .hero-byline b { color:var(--brass); font-weight:600; }
    .hero-score { display:flex; flex-direction:column; align-items:center; gap:10px; }
    .score-ring { width:116px; height:116px; border-radius:50%;
        background:conic-gradient(var(--brass) calc(var(--val)*1%), rgba(255,255,255,0.12) 0);
        display:grid; place-items:center; position:relative; }
    .score-ring::before { content:""; position:absolute; inset:9px; border-radius:50%;
        background:var(--ink); box-shadow:inset 0 0 0 1px rgba(194,155,74,0.25); }
    .score-inner { position:relative; z-index:1; display:flex; flex-direction:column; align-items:center; line-height:1; }
    .score-num { font-family:'Fraunces',serif; font-size:2.3rem; font-weight:600; color:#FFF; }
    .score-den { font-size:0.72rem; color:#93A6BC; margin-top:3px; letter-spacing:0.05em; }
    .score-verdict { text-transform:uppercase; letter-spacing:0.14em; font-size:0.7rem; font-weight:700;
        padding:5px 13px; border-radius:999px; }
    .is-strong .score-verdict { background:rgba(31,122,92,0.20); color:#7FD6B3; border:1px solid rgba(31,122,92,0.5); }
    .is-viable .score-verdict { background:rgba(194,155,74,0.18); color:#E7D6AC; border:1px solid rgba(194,155,74,0.5); }
    .is-weak   .score-verdict { background:rgba(168,58,70,0.20); color:#EBA6AE; border:1px solid rgba(168,58,70,0.5); }

    [data-testid="stMetric"] { background:var(--surface); border:1px solid var(--line); padding:16px 16px 14px;
        border-radius:14px; position:relative; overflow:hidden; box-shadow:0 1px 2px rgba(15,33,56,0.04);
        transition:box-shadow 0.18s ease, transform 0.18s ease; }
    [data-testid="stMetric"]::before { content:""; position:absolute; top:0; left:0; right:0; height:3px; background:var(--brass); }
    [data-testid="stMetric"]:hover { box-shadow:0 10px 26px -16px rgba(15,33,56,0.35); transform:translateY(-1px); }
    [data-testid="stMetricLabel"] { text-transform:uppercase; letter-spacing:0.08em; font-size:0.68rem !important;
        font-weight:600; color:var(--slate); }
    [data-testid="stMetricValue"] { font-weight:700; color:var(--ink); font-variant-numeric:tabular-nums; font-size:1.42rem; }

    [data-testid="stTabs"] [data-baseweb="tab-list"] { gap:4px; border-bottom:1px solid var(--line); }
    [data-testid="stTabs"] [data-baseweb="tab"] { font-weight:600; font-size:0.9rem; color:var(--slate);
        background:transparent; border-radius:8px 8px 0 0; padding:8px 14px; }
    [data-testid="stTabs"] [data-baseweb="tab"]:hover { color:var(--ink); background:rgba(15,33,56,0.03); }
    [data-testid="stTabs"] [aria-selected="true"] { color:var(--ink) !important; }
    [data-testid="stTabs"] [data-baseweb="tab-highlight"] { background:var(--brass); height:3px; }

    .good,.warn,.bad { padding:16px 18px; border-radius:12px; border:1px solid var(--line);
        border-left-width:5px; color:var(--ink); font-size:0.96rem; }
    .good { background:#ECF5F0; border-left-color:var(--pos); }
    .warn { background:#FBF3E3; border-left-color:var(--warn); }
    .bad  { background:#F8ECEE; border-left-color:var(--neg); }

    [data-testid="stSidebar"] { min-width:360px; max-width:360px;
        background:linear-gradient(180deg,#FBFCFE 0%,#F1F4F9 100%); border-right:1px solid var(--line); }
    [data-testid="stSidebar"] h1 { font-size:1.2rem; padding-bottom:10px; margin-bottom:4px; border-bottom:2px solid var(--brass); }
    [data-testid="stSidebar"] h3 { font-size:0.78rem !important; text-transform:uppercase; letter-spacing:0.1em;
        color:var(--slate); font-family:'Inter',sans-serif; font-weight:700; border:none; margin-top:1.1rem; padding-bottom:0; }

    [data-testid="stDownloadButton"] button, .stButton button { background:var(--ink); color:#FFF; border:1px solid var(--ink);
        border-radius:10px; font-weight:600; transition:background 0.16s ease, border-color 0.16s ease, transform 0.16s ease; }
    [data-testid="stDownloadButton"] button:hover, .stButton button:hover { background:var(--brass); border-color:var(--brass); color:var(--ink); transform:translateY(-1px); }

    [data-baseweb="input"]:focus-within, [data-baseweb="select"]:focus-within { border-color:var(--brass) !important; box-shadow:0 0 0 2px rgba(194,155,74,0.18); }
    [data-testid="stDataFrame"] { border:1px solid var(--line); border-radius:12px; overflow:hidden; }
    [data-testid="stExpander"] { border:1px solid var(--line); border-radius:12px; background:var(--surface); }

    .eyebrow { text-transform:uppercase; letter-spacing:0.16em; font-size:0.7rem; font-weight:700; color:var(--brass); }
    .lead { color:var(--slate); font-size:0.92rem; line-height:1.5; margin:2px 0 14px; }

    @media (max-width:640px) { .hero { padding:24px; } .hero-title { font-size:1.7rem; }
        [data-testid="stSidebar"] { min-width:300px; max-width:300px; } }
    </style>
    """,
    unsafe_allow_html=True,
)


# ===========================================================================
# Formatting helpers
# ===========================================================================
def money(v):
    return f"${v:,.0f}"


def money2(v):
    return f"${v:,.2f}"


def pct(v):
    return f"{v:.1%}"


def pct1(v):
    return "—" if v is None or (isinstance(v, float) and math.isnan(v)) else f"{v:.1%}"


def marginal(value, lower, base, rate):
    return base + max(0.0, value - lower) * rate


# ===========================================================================
# Australian income tax (2024-25 resident rates) + 2% Medicare levy.
# Vectorised: accepts scalars or numpy arrays.
# ===========================================================================
def income_tax(taxable, medicare=True):
    ti = np.maximum(0.0, np.asarray(taxable, dtype=float))
    tax = np.zeros_like(ti)
    tax += np.clip(ti - 18_200, 0, 45_000 - 18_200) * 0.16
    tax += np.clip(ti - 45_000, 0, 135_000 - 45_000) * 0.30
    tax += np.clip(ti - 135_000, 0, 190_000 - 135_000) * 0.37
    tax += np.clip(ti - 190_000, 0, None) * 0.45
    if medicare:
        tax += ti * 0.02
    return tax


def marginal_rate(income, medicare=True):
    i = max(0.0, income)
    if i <= 18_200:
        r = 0.0
    elif i <= 45_000:
        r = 0.16
    elif i <= 135_000:
        r = 0.30
    elif i <= 190_000:
        r = 0.37
    else:
        r = 0.45
    return r + (0.02 if medicare else 0.0)


# ===========================================================================
# Stamp duty (general estimates only)
# ===========================================================================
def estimate_duty(state, value):
    v = max(0.0, float(value))
    if state == "NSW":
        if v <= 18_000: return max(20, v * 0.0125)
        if v <= 38_000: return marginal(v, 18_000, 225, 0.015)
        if v <= 103_000: return marginal(v, 38_000, 525, 0.0175)
        if v <= 387_000: return marginal(v, 103_000, 1_662, 0.035)
        if v <= 1_290_000: return marginal(v, 387_000, 11_602, 0.045)
        if v <= 3_870_000: return marginal(v, 1_290_000, 52_237, 0.055)
        return marginal(v, 3_870_000, 194_137, 0.07)
    if state == "VIC":
        if v <= 25_000: return v * 0.014
        if v <= 130_000: return marginal(v, 25_000, 350, 0.024)
        if v <= 960_000: return marginal(v, 130_000, 2_870, 0.06)
        if v <= 2_000_000: return v * 0.055
        return marginal(v, 2_000_000, 110_000, 0.065)
    if state == "QLD":
        if v <= 5_000: return 0
        if v <= 75_000: return (v - 5_000) * 0.015
        if v <= 540_000: return marginal(v, 75_000, 1_050, 0.035)
        if v <= 1_000_000: return marginal(v, 540_000, 17_325, 0.045)
        return marginal(v, 1_000_000, 38_025, 0.0575)
    if state == "WA":
        if v <= 120_000: return v * 0.019
        if v <= 150_000: return marginal(v, 120_000, 2_280, 0.0285)
        if v <= 360_000: return marginal(v, 150_000, 3_135, 0.038)
        if v <= 725_000: return marginal(v, 360_000, 11_115, 0.0475)
        return marginal(v, 725_000, 28_452.5, 0.0515)
    if state == "SA":
        bands = [(12_000, 0, 0, 0.01), (30_000, 12_000, 120, 0.02), (50_000, 30_000, 480, 0.03),
                 (100_000, 50_000, 1_080, 0.035), (200_000, 100_000, 2_830, 0.04),
                 (250_000, 200_000, 6_830, 0.0425), (300_000, 250_000, 8_955, 0.0475),
                 (500_000, 300_000, 11_330, 0.05), (float("inf"), 500_000, 21_330, 0.055)]
        for upper, lower, base, rate in bands:
            if v <= upper:
                return marginal(v, lower, base, rate)
    if state == "TAS":
        if v <= 1_300: return 20
        if v <= 10_000: return v * 0.015
        if v <= 30_000: return marginal(v, 10_000, 150, 0.02)
        if v <= 75_000: return marginal(v, 30_000, 550, 0.025)
        if v <= 150_000: return marginal(v, 75_000, 1_675, 0.03)
        if v <= 225_000: return marginal(v, 150_000, 3_925, 0.035)
        if v <= 375_000: return marginal(v, 225_000, 6_550, 0.04)
        return marginal(v, 375_000, 12_550, 0.045)
    if state == "ACT":
        if v <= 200_000: return v * 0.012
        if v <= 300_000: return marginal(v, 200_000, 2_400, 0.022)
        if v <= 500_000: return marginal(v, 300_000, 4_600, 0.034)
        if v <= 750_000: return marginal(v, 500_000, 11_400, 0.0432)
        if v <= 1_000_000: return marginal(v, 750_000, 22_200, 0.059)
        if v <= 1_455_000: return marginal(v, 1_000_000, 36_950, 0.064)
        return v * 0.0454
    if state == "NT":
        if v <= 525_000:
            xx = v / 1_000
            return (0.06571441 * xx * xx + 15 * xx) * 1_000
        if v <= 3_000_000: return v * 0.0495
        if v <= 5_000_000: return v * 0.0575
        return v * 0.0595
    return 0.0


# ===========================================================================
# Inputs
# ===========================================================================
@dataclass
class Inputs:
    property_name: str
    property_type: str
    strata_applies: bool
    state: str
    purpose: str
    bedrooms: int
    bathrooms: float
    car_spaces: int
    land_size: float
    purchase_price: float
    market_value: float
    deposit: float
    interest_rate: float
    loan_term_years: int
    loan_type: str
    io_years: int
    offset_balance: float
    extra_monthly: float
    weekly_rent: float
    vacancy_rate: float
    management_fee: float
    leasing_fees: float
    rent_growth: float
    council: float
    water: float
    insurance: float
    strata: float
    special_levies: float
    repairs_pct: float
    land_tax: float
    accounting: float
    other_expenses: float
    capital_growth: float
    selling_cost_pct: float
    depreciation: float
    horizon: int
    other_income: float
    use_progressive_tax: bool
    include_medicare: bool
    marginal_tax_rate: float
    apply_cgt: bool
    benchmark_rate: float
    duty_override: float
    concession_reduction: float
    foreign_surcharge: float
    lmi_quote: float
    legal: float
    inspection: float
    loan_fees: float
    buyers_agent: float
    initial_repairs: float
    other_purchase_costs: float

    # ---- Market intelligence (optional external data; defaults = not provided) ----
    use_valuation_data: bool = False
    avm_estimate: float = 0.0
    avm_confidence: str = "Medium"
    use_market_benchmarks: bool = False
    suburb_growth_10yr: float = 0.0
    suburb_growth_vol: float = 0.0
    median_weekly_rent: float = 0.0
    use_liquidity_data: bool = False
    days_on_market: float = 0.0
    vendor_discount: float = 0.0
    months_of_supply: float = 0.0
    auction_clearance: float = 0.0
    use_demand_data: bool = False
    population_growth: float = 0.0
    renter_proportion: float = 0.0
    suburb_vacancy: float = 0.0
    use_risk_data: bool = False
    hazard_exposure: str = "Low"
    approvals_trend: str = "Stable"


# ===========================================================================
# Loan
# ===========================================================================
def loan_info(x):
    base_loan = max(0.0, x.purchase_price - x.deposit)
    base_lvr = base_loan / x.market_value if x.market_value else 0.0
    lmi_used = max(0.0, x.lmi_quote) if base_lvr > 0.80 else 0.0
    total_loan = base_loan + lmi_used
    final_lvr = total_loan / x.market_value if x.market_value else 0.0
    return base_loan, base_lvr, lmi_used, total_loan, final_lvr


def loan_schedule(x):
    _, _, _, total_loan, _ = loan_info(x)
    monthly_rate = x.interest_rate / 12
    months = x.loan_term_years * 12
    balance = total_loan
    rows = []
    cumulative_interest = 0.0
    for month in range(1, months + 1):
        opening = balance
        interest = max(0.0, opening - x.offset_balance) * monthly_rate
        if opening <= 0.005:
            scheduled = extra = principal = closing = 0.0
        elif x.loan_type == "Interest Only" and month <= x.io_years * 12:
            scheduled = interest
            extra = min(x.extra_monthly, opening)
            principal = extra
            closing = max(0.0, opening - principal)
        else:
            remaining = max(1, months - month + 1)
            if monthly_rate == 0:
                scheduled = opening / remaining
            else:
                scheduled = (opening * monthly_rate * (1 + monthly_rate) ** remaining
                             / ((1 + monthly_rate) ** remaining - 1))
            extra = min(x.extra_monthly, opening)
            principal = min(opening, max(0.0, scheduled - interest) + extra)
            closing = max(0.0, opening - principal)
        cumulative_interest += interest
        rows.append({
            "Month": month, "Year": math.ceil(month / 12), "Opening Balance": opening,
            "Scheduled Payment": scheduled, "Extra Payment": extra,
            "Total Payment": scheduled + extra, "Interest": interest, "Principal": principal,
            "Closing Balance": closing, "Offset Balance": x.offset_balance,
            "Cumulative Interest": cumulative_interest,
        })
        balance = closing
    return pd.DataFrame(rows)


# ===========================================================================
# Tax helpers used by the deterministic engine
# ===========================================================================
def tax_effect_on_result(x, taxable_result):
    if x.use_progressive_tax:
        base = float(income_tax(x.other_income, x.include_medicare))
        withp = float(income_tax(x.other_income + taxable_result, x.include_medicare))
        return base - withp
    return -taxable_result * x.marginal_tax_rate


def capital_gains_tax(x, gross_gain, held_years):
    if not x.apply_cgt or gross_gain <= 0:
        return 0.0
    discount = 0.5 if held_years >= 1 else 1.0
    taxable_gain = gross_gain * discount
    if x.use_progressive_tax:
        return float(income_tax(x.other_income + taxable_gain, x.include_medicare)
                     - income_tax(x.other_income, x.include_medicare))
    return taxable_gain * x.marginal_tax_rate


# ===========================================================================
# Core deterministic calculation
# ===========================================================================
def calculate(x):
    base_loan, base_lvr, lmi_used, total_loan, final_lvr = loan_info(x)
    automatic_duty = estimate_duty(x.state, max(x.purchase_price, x.market_value))
    duty_used = (x.duty_override if x.duty_override > 0
                 else max(0.0, automatic_duty - x.concession_reduction + x.foreign_surcharge))
    other_purchase_costs = sum([x.legal, x.inspection, x.loan_fees, x.buyers_agent,
                                x.initial_repairs, x.other_purchase_costs])
    purchase_costs = duty_used + lmi_used + other_purchase_costs
    cash_required = x.deposit + purchase_costs
    cost_base = x.purchase_price + purchase_costs

    schedule = loan_schedule(x)
    annual_interest = schedule.groupby("Year", as_index=False)["Interest"].sum()
    annual_balance = schedule.groupby("Year", as_index=False)["Closing Balance"].last()
    annual_payment = schedule.groupby("Year", as_index=False)["Total Payment"].sum()

    cashflow_rows, growth_rows = [], []
    cumulative_after_tax_cashflow = 0.0

    for year in range(1, x.loan_term_years + 1):
        escalation = (1 + x.rent_growth) ** (year - 1)
        gross_rent = x.weekly_rent * 52 * escalation
        vacancy = gross_rent * x.vacancy_rate
        effective_rent = gross_rent - vacancy
        management = effective_rent * x.management_fee
        leasing = x.leasing_fees * escalation
        council = x.council * escalation
        water = x.water * escalation
        insurance = x.insurance * escalation
        strata = x.strata * escalation if x.strata_applies else 0.0
        special_levies = x.special_levies if x.strata_applies else 0.0
        repairs = gross_rent * x.repairs_pct
        other = x.other_expenses * escalation
        interest = float(annual_interest.loc[annual_interest["Year"] == year, "Interest"].sum())
        loan_payments = float(annual_payment.loc[annual_payment["Year"] == year, "Total Payment"].sum())
        operating_expenses = sum([management, leasing, council, water, insurance, strata,
                                  special_levies, repairs, x.land_tax, x.accounting, other])
        net_operating_income = effective_rent - operating_expenses
        pre_tax_cashflow = net_operating_income - loan_payments
        taxable_result = effective_rent - operating_expenses - interest - x.depreciation
        estimated_tax_effect = tax_effect_on_result(x, taxable_result)
        after_tax_cashflow = pre_tax_cashflow + estimated_tax_effect
        cumulative_after_tax_cashflow += after_tax_cashflow

        cashflow_rows.append({
            "Year": year, "Gross Rent": gross_rent, "Vacancy": -vacancy,
            "Effective Rent": effective_rent, "Management Fee": -management,
            "Leasing / Advertising": -leasing, "Council Rates": -council, "Water Charges": -water,
            "Insurance": -insurance, "Strata Levies": -strata, "Special Levies": -special_levies,
            "Repairs / Maintenance": -repairs, "Land Tax": -x.land_tax, "Accounting": -x.accounting,
            "Other Expenses": -other, "Net Operating Income": net_operating_income,
            "Loan Payments": -loan_payments, "Loan Interest": -interest,
            "Pre-tax Cash Flow": pre_tax_cashflow, "Depreciation": -x.depreciation,
            "Taxable Result": taxable_result, "Estimated Tax Effect": estimated_tax_effect,
            "After-tax Cash Flow": after_tax_cashflow,
        })

        property_value = x.purchase_price * (1 + x.capital_growth) ** year
        loan_balance = float(annual_balance.loc[annual_balance["Year"] == year, "Closing Balance"].iloc[0])
        gross_equity = property_value - loan_balance
        selling_costs = property_value * x.selling_cost_pct
        gross_gain = max(0.0, property_value - selling_costs - cost_base)
        cgt = capital_gains_tax(x, gross_gain, year)
        net_sale_proceeds = property_value - selling_costs - loan_balance - cgt
        total_profit = net_sale_proceeds + cumulative_after_tax_cashflow - cash_required

        growth_rows.append({
            "Year": year, "Property Value": property_value, "Loan Balance": loan_balance,
            "Gross Equity": gross_equity, "Selling Costs": -selling_costs,
            "Capital Gains Tax": -cgt, "Net Sale Proceeds": net_sale_proceeds,
            "Cumulative After-tax Cash Flow": cumulative_after_tax_cashflow,
            "Total Profit": total_profit,
            "Cash-on-Cash Return": (total_profit / cash_required if cash_required else 0.0),
        })

    return {
        "base_loan": base_loan, "base_lvr": base_lvr, "lmi_used": lmi_used,
        "total_loan": total_loan, "final_lvr": final_lvr, "automatic_duty": automatic_duty,
        "duty_used": duty_used, "other_purchase_costs": other_purchase_costs,
        "purchase_costs": purchase_costs, "cash_required": cash_required, "cost_base": cost_base,
        "schedule": schedule, "cashflow": pd.DataFrame(cashflow_rows),
        "growth": pd.DataFrame(growth_rows),
    }


# ===========================================================================
# Return metrics: IRR, NPV, equity multiple, payback
# ===========================================================================
def npv(rate, flows):
    f = np.asarray(flows, dtype=float)
    t = np.arange(len(f))
    return float(np.sum(f / (1 + rate) ** t))


def irr(flows, lo=-0.9999, hi=10.0):
    f = np.asarray(flows, dtype=float)
    if not (np.any(f > 0) and np.any(f < 0)):
        return float("nan")
    a, b = lo, hi
    fa, fb = npv(a, f), npv(b, f)
    if np.isnan(fa) or np.isnan(fb) or fa * fb > 0:
        return float("nan")
    for _ in range(200):
        m = (a + b) / 2
        fm = npv(m, f)
        if fa * fm <= 0:
            b, fb = m, fm
        else:
            a, fa = m, fm
    return (a + b) / 2


def cash_flow_vector(x, results):
    h = min(x.horizon, len(results["growth"]))
    cf = results["cashflow"]["After-tax Cash Flow"].values[:h].astype(float)
    net_sale = float(results["growth"].iloc[h - 1]["Net Sale Proceeds"])
    flows = np.zeros(h + 1)
    flows[0] = -results["cash_required"]
    flows[1:h + 1] = cf
    flows[h] += net_sale
    return flows, h, net_sale


def return_metrics(x, results):
    flows, h, net_sale = cash_flow_vector(x, results)
    cash = results["cash_required"]
    project_irr = irr(flows)
    project_npv = npv(x.benchmark_rate, flows)
    total_return = flows[1:].sum()
    equity_multiple = (total_return / cash) if cash else float("nan")
    cumulative = np.cumsum(flows)
    payback = next((i for i, c in enumerate(cumulative) if c >= 0), None)
    alt_value = cash * (1 + x.benchmark_rate) ** h
    alt_profit = alt_value - cash
    property_profit = float(results["growth"].iloc[h - 1]["Total Profit"])
    return {
        "flows": flows, "horizon": h, "irr": project_irr, "npv": project_npv,
        "equity_multiple": equity_multiple, "payback": payback, "net_sale": net_sale,
        "alt_value": alt_value, "alt_profit": alt_profit, "property_profit": property_profit,
        "excess_over_benchmark": property_profit - alt_profit,
    }


# ===========================================================================
# Vectorised Monte Carlo risk engine (all simulations at once — fast)
# ===========================================================================
def irr_vec(flows2d):
    t1, n = flows2d.shape
    t = np.arange(t1)[:, None]
    lo = np.full(n, -0.9999)
    hi = np.full(n, 5.0)
    for _ in range(80):
        mid = (lo + hi) / 2.0
        denom = (1.0 + mid)[None, :] ** t
        npvm = np.sum(flows2d / denom, axis=0)
        pos = npvm > 0
        lo = np.where(pos, mid, lo)
        hi = np.where(pos, hi, mid)
    res = (lo + hi) / 2.0
    has_neg = np.any(flows2d < 0, axis=0)
    has_pos = np.any(flows2d > 0, axis=0)
    return np.where(has_neg & has_pos, res, np.nan)


def monte_carlo(x, n_sims, vol, seed=42):
    rng = np.random.default_rng(seed)
    n = int(n_sims)
    horizon = min(x.horizon, x.loan_term_years)

    cg = rng.normal(x.capital_growth, vol["cg"], n)
    rate = np.clip(rng.normal(x.interest_rate, vol["rate"], n), 0.0, None)
    rg = rng.normal(x.rent_growth, vol["rg"], n)
    vac = np.clip(rng.normal(x.vacancy_rate, vol["vac"], n), 0.0, 0.95)

    _, _, lmi_used, total_loan, _ = loan_info(x)
    other_purchase_costs = sum([x.legal, x.inspection, x.loan_fees, x.buyers_agent,
                                x.initial_repairs, x.other_purchase_costs])
    duty_used = (x.duty_override if x.duty_override > 0
                 else max(0.0, estimate_duty(x.state, max(x.purchase_price, x.market_value))
                          - x.concession_reduction + x.foreign_surcharge))
    purchase_costs = duty_used + lmi_used + other_purchase_costs
    cash_required = x.deposit + purchase_costs
    cost_base = x.purchase_price + purchase_costs

    months = x.loan_term_years * 12
    horizon_months = min(months, horizon * 12)
    mrate = rate / 12.0
    balance = np.full(n, total_loan)
    io_months = x.io_years * 12 if x.loan_type == "Interest Only" else 0
    annual_interest = np.zeros((horizon, n))
    annual_payment = np.zeros((horizon, n))
    year_end_balance = np.zeros((horizon, n))

    for m in range(1, horizon_months + 1):
        opening = balance
        active = opening > 0.005
        interest = np.maximum(0.0, opening - x.offset_balance) * mrate
        if m <= io_months:
            scheduled = interest
            extra = np.minimum(x.extra_monthly, opening)
            principal = extra
        else:
            remaining = max(1, months - m + 1)
            factor = (1 + mrate) ** remaining
            with np.errstate(divide="ignore", invalid="ignore"):
                scheduled = np.where(mrate == 0, opening / remaining,
                                     opening * mrate * factor / (factor - 1))
            extra = np.minimum(x.extra_monthly, opening)
            principal = np.minimum(opening, np.maximum(0.0, scheduled - interest) + extra)
        interest = np.where(active, interest, 0.0)
        principal = np.where(active, principal, 0.0)
        total_pay = np.where(active, scheduled + extra, 0.0)
        closing = np.maximum(0.0, opening - principal)
        idx = math.ceil(m / 12) - 1
        annual_interest[idx] += interest
        annual_payment[idx] += total_pay
        year_end_balance[idx] = closing
        balance = closing

    base_tax = income_tax(x.other_income, x.include_medicare)
    cum_after_tax = np.zeros(n)
    year_after_tax = np.zeros((horizon, n))
    equity_path = np.zeros((horizon, n))
    min_equity = np.full(n, np.inf)

    for y in range(1, horizon + 1):
        esc = (1 + rg) ** (y - 1)
        gross = x.weekly_rent * 52 * esc
        vacancy = gross * vac
        effective = gross - vacancy
        management = effective * x.management_fee
        leasing = x.leasing_fees * esc
        council = x.council * esc
        water = x.water * esc
        insurance = x.insurance * esc
        strata = (x.strata * esc) if x.strata_applies else 0.0
        special = x.special_levies if x.strata_applies else 0.0
        repairs = gross * x.repairs_pct
        other = x.other_expenses * esc
        opex = (management + leasing + council + water + insurance + strata + special
                + repairs + x.land_tax + x.accounting + other)
        interest_y = annual_interest[y - 1]
        pay_y = annual_payment[y - 1]
        pretax = (effective - opex) - pay_y
        taxable = effective - opex - interest_y - x.depreciation
        if x.use_progressive_tax:
            tax_effect = base_tax - income_tax(x.other_income + taxable, x.include_medicare)
        else:
            tax_effect = -taxable * x.marginal_tax_rate
        after_tax = pretax + tax_effect
        year_after_tax[y - 1] = after_tax
        cum_after_tax += after_tax
        value_y = x.purchase_price * (1 + cg) ** y
        equity_y = value_y - year_end_balance[y - 1]
        equity_path[y - 1] = equity_y
        min_equity = np.minimum(min_equity, equity_y)

    value_h = x.purchase_price * (1 + cg) ** horizon
    bal_h = year_end_balance[horizon - 1]
    selling = value_h * x.selling_cost_pct
    gross_gain = np.maximum(0.0, value_h - selling - cost_base)
    if x.apply_cgt:
        taxable_gain = gross_gain * (0.5 if horizon >= 1 else 1.0)
        if x.use_progressive_tax:
            cgt = income_tax(x.other_income + taxable_gain, x.include_medicare) - base_tax
        else:
            cgt = taxable_gain * x.marginal_tax_rate
    else:
        cgt = np.zeros(n)
    net_sale = value_h - selling - bal_h - cgt
    total_profit = net_sale + cum_after_tax - cash_required

    flows = np.zeros((horizon + 1, n))
    flows[0] = -cash_required
    flows[1:horizon + 1] = year_after_tax
    flows[horizon] += net_sale
    irr_dist = irr_vec(flows)

    alt_profit = cash_required * ((1 + x.benchmark_rate) ** horizon - 1)

    return {
        "n": n, "horizon": horizon, "cash_required": cash_required,
        "total_profit": total_profit, "year1_after_tax": year_after_tax[0],
        "irr": irr_dist, "min_equity": min_equity, "terminal_value": value_h,
        "prob_negative_cashflow_y1": float(np.mean(year_after_tax[0] < 0)),
        "prob_negative_equity": float(np.mean(min_equity < 0)),
        "prob_profit": float(np.mean(total_profit > 0)),
        "prob_beats_benchmark": float(np.mean(total_profit > alt_profit)),
        "alt_profit": alt_profit,
        "equity_p10": np.percentile(equity_path, 10, axis=1),
        "equity_p50": np.percentile(equity_path, 50, axis=1),
        "equity_p90": np.percentile(equity_path, 90, axis=1),
        "sampled": {"Capital growth": cg, "Interest rate": rate,
                    "Rent growth": rg, "Vacancy rate": vac},
    }


# ===========================================================================
# Sensitivity (tornado) and break-even solvers
# ===========================================================================
def _profit_at_horizon(inp):
    r = calculate(inp)
    h = min(inp.horizon, len(r["growth"]))
    return float(r["growth"].iloc[h - 1]["Total Profit"])


def tornado(x, pct_shift=0.15):
    base_profit = _profit_at_horizon(x)
    drivers = [
        ("Capital growth", "capital_growth"),
        ("Interest rate", "interest_rate"),
        ("Weekly rent", "weekly_rent"),
        ("Rent growth", "rent_growth"),
        ("Vacancy rate", "vacancy_rate"),
        ("Purchase price", "purchase_price"),
        ("Management fee", "management_fee"),
    ]
    rows = []
    for label, field in drivers:
        val = getattr(x, field)
        low = _profit_at_horizon(replace(x, **{field: val * (1 - pct_shift)}))
        high = _profit_at_horizon(replace(x, **{field: val * (1 + pct_shift)}))
        rows.append({"Driver": label, "Low": low - base_profit, "High": high - base_profit})
    df = pd.DataFrame(rows)
    df["Range"] = (df["High"] - df["Low"]).abs()
    return base_profit, df.sort_values("Range").reset_index(drop=True)


def _bisect(f, lo, hi, target=0.0, iters=64):
    flo, fhi = f(lo) - target, f(hi) - target
    if flo == 0:
        return lo
    if fhi == 0:
        return hi
    if flo * fhi > 0:
        return None
    for _ in range(iters):
        mid = (lo + hi) / 2.0
        fm = f(mid) - target
        if flo * fm <= 0:
            hi, fhi = mid, fm
        else:
            lo, flo = mid, fm
    return (lo + hi) / 2.0


def break_even_table(x):
    h = min(x.horizon, x.loan_term_years)

    def y1(rent):
        return float(calculate(replace(x, weekly_rent=rent))["cashflow"].iloc[0]["After-tax Cash Flow"])

    def y1_rate(rate):
        return float(calculate(replace(x, interest_rate=rate))["cashflow"].iloc[0]["After-tax Cash Flow"])

    def profit_g(g):
        r = calculate(replace(x, capital_growth=g))
        return float(r["growth"].iloc[h - 1]["Total Profit"])

    def profit_rent(rent):
        r = calculate(replace(x, weekly_rent=rent))
        return float(r["growth"].iloc[h - 1]["Total Profit"])

    be_rent_cf = _bisect(y1, 1.0, x.weekly_rent * 4 + 2000, 0.0)
    be_rate_cf = _bisect(y1_rate, 0.0005, 0.25, 0.0)
    be_growth = _bisect(profit_g, -0.20, 0.30, 0.0)
    be_rent_profit = _bisect(profit_rent, 1.0, x.weekly_rent * 4 + 2000, 0.0)

    def fmt_rent(v):
        return money2(v) + " / wk" if v is not None else "Not reachable in range"

    def fmt_rate(v):
        return pct(v) if v is not None else "Not reachable in range"

    return pd.DataFrame({
        "Break-even target": [
            "Weekly rent for $0 Year-1 after-tax cash flow",
            "Interest rate for $0 Year-1 after-tax cash flow",
            f"Capital growth for $0 total profit over {h} years",
            f"Weekly rent for $0 total profit over {h} years",
        ],
        "Break-even level": [
            fmt_rent(be_rent_cf), fmt_rate(be_rate_cf),
            fmt_rate(be_growth), fmt_rent(be_rent_profit),
        ],
        "Your current level": [
            money2(x.weekly_rent) + " / wk", pct(x.interest_rate),
            pct(x.capital_growth), money2(x.weekly_rent) + " / wk",
        ],
    })


# ===========================================================================
# Feasibility score
# ===========================================================================
def investment_score(x, results):
    first_year = results["cashflow"].iloc[0]
    horizon_result = results["growth"].iloc[x.horizon - 1]
    gross_yield = (x.weekly_rent * 52 / x.purchase_price) if x.purchase_price else 0.0
    lvr_score = 25.0 if results["final_lvr"] <= 0.80 else max(0.0, 25.0 - (results["final_lvr"] - 0.80) * 100)
    yield_score = 20.0 if gross_yield >= 0.05 else max(0.0, gross_yield / 0.05 * 20)
    cashflow_score = (20.0 if first_year["After-tax Cash Flow"] >= 0
                      else max(0.0, 20.0 + first_year["After-tax Cash Flow"] / max(1.0, x.weekly_rent * 52) * 20))
    profit_score = 20.0 if horizon_result["Total Profit"] > 0 else 0.0
    growth_score = 15.0 if x.capital_growth >= 0.04 else max(0.0, x.capital_growth / 0.04 * 15)
    total = max(0.0, min(100.0, lvr_score + yield_score + cashflow_score + profit_score + growth_score))
    breakdown = pd.DataFrame({
        "Component": ["Final LVR", "Gross rental yield", "Year 1 after-tax cash flow",
                      f"{x.horizon}-year projected total profit", "Assumed annual capital growth"],
        "Result": [pct(results["final_lvr"]), pct(gross_yield),
                   money(first_year["After-tax Cash Flow"]), money(horizon_result["Total Profit"]),
                   pct(x.capital_growth)],
        "Points earned": [f"{lvr_score:.1f} / 25", f"{yield_score:.1f} / 20",
                          f"{cashflow_score:.1f} / 20", f"{profit_score:.1f} / 20",
                          f"{growth_score:.1f} / 15"],
    })
    return total, breakdown


# ===========================================================================
# Advanced composite score — blends financial feasibility with market
# intelligence pillars. Missing pillars are excluded and their weight is
# redistributed, so the score is never diluted by absent data. A separate
# "data confidence" figure reports how much of the market weighting is backed
# by entered evidence.
# ===========================================================================
def _clip(v, lo=0.0, hi=100.0):
    return float(max(lo, min(hi, v)))


def _mean(vals):
    return float(sum(vals) / len(vals)) if vals else None


def advanced_score(x, results, base_financial_score):
    pillars = {}

    # 1) Financial feasibility (always present)
    pillars["Financial feasibility"] = {
        "score": base_financial_score, "weight": 0.35, "active": True,
        "detail": "LVR, yield, cash flow, profit and growth from the deterministic model.",
    }

    # 2) Assumption realism — disciplines optimistic inputs against market data
    realism = []
    detail_bits = []
    if x.use_market_benchmarks and x.suburb_growth_10yr > 0:
        diff = x.capital_growth - x.suburb_growth_10yr
        realism.append(_clip(100 - max(0.0, diff) * 1000 - max(0.0, -diff) * 200))
        detail_bits.append("growth vs history")
    if x.use_market_benchmarks and x.median_weekly_rent > 0:
        ratio = x.weekly_rent / x.median_weekly_rent
        realism.append(100.0 if ratio <= 1 else _clip(100 - (ratio - 1) * 400))
        detail_bits.append("rent vs median")
    if x.use_demand_data and x.suburb_vacancy > 0:
        realism.append(100.0 if x.vacancy_rate >= x.suburb_vacancy
                       else _clip(100 - (x.suburb_vacancy - x.vacancy_rate) * 2000))
        detail_bits.append("vacancy vs suburb")
    pillars["Assumption realism"] = {
        "score": _mean(realism), "weight": 0.12, "active": bool(realism),
        "detail": "How closely your growth, rent and vacancy match the market ("
                  + (", ".join(detail_bits) if detail_bits else "no benchmarks entered") + ").",
    }

    # 3) Valuation — over/underpay vs automated valuation, shrunk by confidence
    val_gap = None
    if x.use_valuation_data and x.avm_estimate > 0 and x.purchase_price > 0:
        val_gap = (x.avm_estimate - x.purchase_price) / x.purchase_price
        raw = _clip(70 + val_gap * 300)
        shrink = {"High": 1.0, "Medium": 0.7, "Low": 0.4}.get(x.avm_confidence, 0.7)
        pillars["Valuation"] = {
            "score": 50 + (raw - 50) * shrink, "weight": 0.13, "active": True,
            "detail": f"Purchase price vs AVM {money(x.avm_estimate)} "
                      f"({x.avm_confidence} confidence): gap {val_gap:+.1%}.",
        }
    else:
        pillars["Valuation"] = {"score": None, "weight": 0.13, "active": False,
                                "detail": "No automated valuation entered."}

    # 4) Liquidity & exit — how easily and quickly the asset can be sold
    if x.use_liquidity_data:
        parts = []
        if x.days_on_market > 0:
            parts.append(_clip(100 - (x.days_on_market - 30) * 0.8))
        if x.vendor_discount > 0:
            parts.append(_clip(100 - abs(x.vendor_discount) * 10))
        if x.months_of_supply > 0:
            parts.append(_clip(100 - (x.months_of_supply - 3) * 11))
        if x.auction_clearance > 0:
            parts.append(_clip((x.auction_clearance - 40) * 2.5))
        pillars["Liquidity & exit"] = {
            "score": _mean(parts), "weight": 0.13, "active": bool(parts),
            "detail": "Days on market, vendor discount, months of supply and clearance rate.",
        }
    else:
        pillars["Liquidity & exit"] = {"score": None, "weight": 0.13, "active": False,
                                       "detail": "No liquidity data entered."}

    # 5) Demand fundamentals — population, tenant pool, tightness
    if x.use_demand_data:
        parts = [_clip(30 + x.population_growth * 3000)]
        if x.renter_proportion > 0:
            parts.append(_clip(x.renter_proportion * 2))
        if x.suburb_vacancy > 0:
            parts.append(_clip(100 - (x.suburb_vacancy * 100 - 1) * 20))
        pillars["Demand fundamentals"] = {
            "score": _mean(parts), "weight": 0.17, "active": True,
            "detail": "Population growth, renter proportion and suburb vacancy.",
        }
    else:
        pillars["Demand fundamentals"] = {"score": None, "weight": 0.17, "active": False,
                                          "detail": "No demand data entered."}

    # 6) Risk overlay — hazard exposure and supply pipeline
    if x.use_risk_data:
        hz = {"None": 100, "Low": 85, "Moderate": 55, "High": 25}.get(x.hazard_exposure, 85)
        ap = {"Falling": 90, "Stable": 70, "Rising": 45}.get(x.approvals_trend, 70)
        pillars["Risk overlay"] = {
            "score": (hz + ap) / 2, "weight": 0.10, "active": True,
            "detail": f"{x.hazard_exposure} hazard exposure; building approvals {x.approvals_trend.lower()}.",
        }
    else:
        pillars["Risk overlay"] = {"score": None, "weight": 0.10, "active": False,
                                   "detail": "No hazard or supply data entered."}

    active = {k: v for k, v in pillars.items() if v["active"] and v["score"] is not None}
    total_w = sum(v["weight"] for v in active.values())
    composite = sum(v["score"] * v["weight"] for v in active.values()) / total_w if total_w else base_financial_score
    for k, v in pillars.items():
        v["effective_weight"] = (v["weight"] / total_w) if (v["active"] and v["score"] is not None and total_w) else 0.0

    max_market_w = sum(v["weight"] for k, v in pillars.items() if k != "Financial feasibility")
    have_market_w = sum(v["weight"] for k, v in active.items() if k != "Financial feasibility")
    confidence = have_market_w / max_market_w if max_market_w else 0.0

    # Advisory flags
    flags = []
    if x.use_market_benchmarks and x.suburb_growth_10yr > 0 and x.capital_growth > x.suburb_growth_10yr + 0.015:
        flags.append(("warn", f"Assumed capital growth of {pct(x.capital_growth)} is above the suburb's "
                              f"~{pct(x.suburb_growth_10yr)} long-run history. Stress-test a lower rate."))
    if x.use_market_benchmarks and x.median_weekly_rent > 0:
        ratio = x.weekly_rent / x.median_weekly_rent
        if ratio > 1.05:
            flags.append(("warn", f"Entered rent {money2(x.weekly_rent)} is ~{ratio - 1:.0%} above the market "
                                  f"median {money2(x.median_weekly_rent)} — the yield may be optimistic."))
        elif ratio < 0.95:
            flags.append(("good", f"Entered rent is ~{1 - ratio:.0%} below the market median — possible rental upside."))
    if val_gap is not None:
        if val_gap <= -0.05:
            flags.append(("bad", f"Purchase price is ~{-val_gap:.0%} above the automated valuation "
                                 f"({money(x.avm_estimate)}) — potential overpay."))
        elif val_gap >= 0.05:
            flags.append(("good", f"Purchase price is ~{val_gap:.0%} below the automated valuation — buying under estimate."))
    if x.use_demand_data and x.suburb_vacancy > 0 and x.vacancy_rate < x.suburb_vacancy:
        flags.append(("warn", f"Your vacancy allowance {pct(x.vacancy_rate)} is below the suburb's "
                              f"~{pct(x.suburb_vacancy)} — cash flow may be optimistic."))
    if x.use_risk_data and x.hazard_exposure in ("Moderate", "High"):
        sev = "bad" if x.hazard_exposure == "High" else "warn"
        flags.append((sev, f"{x.hazard_exposure} natural-hazard exposure — confirm insurability and premium loadings, "
                           f"which can materially change holding costs."))

    return {"composite": composite, "pillars": pillars, "confidence": confidence,
            "val_gap": val_gap, "flags": flags}


# ===========================================================================
# Branded HTML export report
# ===========================================================================
def report_html(x, results, score, metrics, adv):
    h = metrics["horizon"]
    first_year = results["cashflow"].iloc[0]
    horizon_result = results["growth"].iloc[h - 1]
    shortfall = max(0.0, -first_year["After-tax Cash Flow"])
    tax_basis = ("Progressive ATO 2024-25" + (" + Medicare" if x.include_medicare else "")
                 if x.use_progressive_tax else f"Flat {pct(x.marginal_tax_rate)}")
    composite = adv["composite"]
    verdict = "Strong" if composite >= 75 else "Viable" if composite >= 55 else "Weak"
    active_pillars = ", ".join(k for k, v in adv["pillars"].items()
                               if v["active"] and v["score"] is not None) or "Financial feasibility only"

    fields = {
        "Property": x.property_name, "Property type": x.property_type,
        "Bedrooms": x.bedrooms, "Bathrooms": f"{x.bathrooms:g}", "Car spaces": x.car_spaces,
        "Land size": (f"{x.land_size:,.0f} m²" if x.land_size > 0 else "Not entered"),
        "Strata applies": "Yes" if x.strata_applies else "No", "State": x.state, "Purpose": x.purpose,
        "Purchase price": money(x.purchase_price), "Market value": money(x.market_value),
        "Deposit": money(x.deposit), "Weekly rent": money2(x.weekly_rent),
        "Gross rental yield": pct(x.weekly_rent * 52 / x.purchase_price if x.purchase_price else 0),
        "Base LVR": pct(results["base_lvr"]), "Final LVR": pct(results["final_lvr"]),
        "LMI added": money(results["lmi_used"]), "Total loan": money(results["total_loan"]),
        "Duty used": money(results["duty_used"]), "Total cash required": money(results["cash_required"]),
        "Tax basis": tax_basis,
        "Composite score": f"{composite:.0f}/100 ({verdict})",
        "Financial feasibility score": f"{score:.0f}/100",
        "Data confidence": pct(adv["confidence"]),
        "Scored pillars": active_pillars,
        "Valuation gap vs AVM": (f"{adv['val_gap']:+.1%}" if adv["val_gap"] is not None else "Not provided"),
        "Year 1 pre-tax cash flow": money(first_year["Pre-tax Cash Flow"]),
        "Year 1 after-tax cash flow": money(first_year["After-tax Cash Flow"]),
        "Weekly out-of-pocket": money2(shortfall / 52),
        f"Project IRR ({h}-yr, after-tax)": pct1(metrics["irr"]),
        f"NPV @ {pct(x.benchmark_rate)} discount": money(metrics["npv"]),
        "Equity multiple": (f"{metrics['equity_multiple']:.2f}x"
                            if not math.isnan(metrics["equity_multiple"]) else "—"),
        "Payback period": (f"{metrics['payback']} years" if metrics["payback"] is not None
                           else f"Beyond {h} years"),
        f"CGT at exit (year {h})": money(-horizon_result["Capital Gains Tax"]),
        f"Value after {h} years": money(horizon_result["Property Value"]),
        f"Equity after {h} years": money(horizon_result["Gross Equity"]),
        f"Total profit after {h} years": money(horizon_result["Total Profit"]),
        f"Benchmark alternative ({pct(x.benchmark_rate)})": money(metrics["alt_profit"]),
        "Excess profit over benchmark": money(metrics["excess_over_benchmark"]),
    }
    rows = "".join(f"<tr><th>{k}</th><td>{v}</td></tr>" for k, v in fields.items())

    return f"""
    <html><head><meta charset="utf-8"><title>Property Investment Decision Report</title>
    <link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,600&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {{ --ink:#0F2138; --brass:#C29B4A; --slate:#55677B; --line:#E4EAF1; }}
        * {{ box-sizing:border-box; }}
        body {{ font-family:'Inter',Arial,sans-serif; max-width:860px; margin:0 auto;
            padding:48px 28px 64px; color:#1A2A3A; background:#F5F7FA; }}
        .report {{ background:#fff; border:1px solid var(--line); border-radius:16px; overflow:hidden;
            box-shadow:0 20px 50px -30px rgba(15,33,56,0.5); }}
        .report-head {{ display:flex; justify-content:space-between; align-items:center; gap:24px;
            padding:34px 38px; color:#EAF0F7; background:linear-gradient(120deg,var(--ink) 0%,#1C3350 100%);
            border-bottom:3px solid var(--brass); }}
        .report-head .eyebrow {{ text-transform:uppercase; letter-spacing:0.2em; font-size:0.66rem;
            font-weight:600; color:var(--brass); margin-bottom:8px; }}
        .report-head h1 {{ font-family:'Fraunces',Georgia,serif; font-weight:600; font-size:1.7rem;
            margin:0; color:#fff; line-height:1.1; }}
        .report-head .prop {{ margin-top:6px; font-size:0.9rem; color:#B9C6D6; }}
        .badge {{ text-align:center; flex-shrink:0; }}
        .badge .num {{ font-family:'Fraunces',serif; font-size:2.6rem; font-weight:600; color:#fff;
            border:3px solid var(--brass); border-radius:50%; width:96px; height:96px;
            display:grid; place-items:center; margin:0 auto; }}
        .badge .verdict {{ margin-top:8px; text-transform:uppercase; letter-spacing:0.12em;
            font-size:0.68rem; font-weight:700; color:var(--brass); }}
        .report-body {{ padding:12px 38px 30px; }}
        table {{ border-collapse:collapse; width:100%; }}
        th, td {{ padding:11px 12px; border-bottom:1px solid var(--line); text-align:left; font-size:0.92rem; }}
        th {{ color:var(--slate); font-weight:600; width:52%; font-size:0.78rem;
            text-transform:uppercase; letter-spacing:0.03em; }}
        td {{ font-weight:600; color:var(--ink); font-variant-numeric:tabular-nums; }}
        tr:last-child th, tr:last-child td {{ border-bottom:none; }}
        .notes {{ padding:0 38px 34px; }}
        .notes p {{ font-size:0.82rem; color:var(--slate); line-height:1.55;
            border-left:3px solid var(--brass); padding-left:14px; margin:12px 0; }}
    </style></head>
    <body><div class="report">
        <div class="report-head">
            <div>
                <div class="eyebrow">Property Investment Decision Report</div>
                <h1>{x.property_name}</h1>
                <div class="prop">{x.property_type} · {x.state} · {x.purpose}</div>
            </div>
            <div class="badge"><div class="num">{score:.0f}</div><div class="verdict">{verdict}</div></div>
        </div>
        <div class="report-body"><table>{rows}</table></div>
        <div class="notes">
            <p>The score is an internal feasibility indicator based on entered assumptions. It is not a
            suburb rating, valuation, forecast, lending assessment or financial recommendation.</p>
            <p>Tax figures use simplified {tax_basis} settings. Verify duty, LMI, tax treatment, CGT,
            rent, strata, land tax, insurance and finance terms independently.</p>
        </div>
    </div></body></html>
    """


# ===========================================================================
# Sidebar inputs
# ===========================================================================
st.sidebar.title("🏠 Property inputs")

with st.sidebar:
    property_name = st.text_input("Property name or address", "Example investment property")
    property_type = st.selectbox("Property type",
        ["House", "Apartment / Unit", "Townhouse", "Villa", "Duplex", "Terrace", "Vacant Land", "Other"])
    default_strata = property_type in {"Apartment / Unit", "Townhouse", "Villa"}
    strata_applies = st.checkbox("Strata / owners corporation applies", value=default_strata)
    state = st.selectbox("State / Territory", ["NSW", "VIC", "QLD", "WA", "SA", "TAS", "ACT", "NT"])
    purpose = st.selectbox("Property purpose", ["Investment", "Owner Occupier"])

    st.subheader("Property details")
    dl, dr = st.columns(2)
    with dl:
        bedrooms = st.number_input("Bedrooms", 0, 20, 3, 1)
        car_spaces = st.number_input("Car spaces", 0, 20, 1, 1)
    with dr:
        bathrooms = st.number_input("Bathrooms", 0.0, 20.0, 2.0, 0.5)
        default_land = 500.0 if property_type in {"House", "Duplex", "Terrace", "Vacant Land", "Other"} else 0.0
        land_size = st.number_input("Land size (m²)", 0.0, value=default_land, step=10.0,
                                    help="Enter 0 when land size is unknown or not applicable.")

    st.subheader("Purchase")
    purchase_price = st.number_input("Purchase price ($)", 0.0, value=600_000.0, step=10_000.0)
    market_value = st.number_input("Market value / bank valuation ($)", 0.0, value=600_000.0, step=10_000.0)
    deposit = st.number_input("Deposit ($)", 0.0, value=120_000.0, step=5_000.0)

    st.subheader("Loan")
    interest_rate = st.number_input("Interest rate (%)", 0.0, value=6.0, step=0.1) / 100
    loan_term_years = st.slider("Loan term (years)", 5, 30, 30)
    loan_type = st.selectbox("Loan structure", ["Principal & Interest", "Interest Only"])
    io_years = st.slider("Interest-only period (years)", 0, 10, 5, disabled=loan_type != "Interest Only")
    offset_balance = st.number_input("Offset balance ($)", 0.0, value=0.0, step=5_000.0)
    extra_monthly = st.number_input("Extra monthly repayment ($)", 0.0, value=0.0, step=100.0)

    st.subheader("Rent and management")
    weekly_rent = st.number_input("Weekly rent ($)", 0.0, value=600.0, step=10.0)
    vacancy_rate = st.number_input("Vacancy allowance (%)", 0.0, 100.0, 3.0, 0.5) / 100
    management_fee = st.number_input("Rental-agent management fee (%)", 0.0, 100.0, 7.0, 0.5) / 100
    leasing_fees = st.number_input("Leasing / advertising fees p.a. ($)", 0.0, value=700.0, step=100.0)
    rent_growth = st.number_input("Annual rent growth (%)", -20.0, 50.0, 3.0, 0.5) / 100

    st.subheader("Property expenses")
    council = st.number_input("Council rates p.a. ($)", 0.0, value=2_200.0, step=100.0)
    water = st.number_input("Owner-paid water charges p.a. ($)", 0.0, value=900.0, step=100.0)
    insurance = st.number_input("Landlord / building insurance p.a. ($)", 0.0, value=1_800.0, step=100.0)
    strata_input = st.number_input("Strata levies p.a. ($)", 0.0, value=4_000.0 if strata_applies else 0.0,
                                   step=100.0, disabled=not strata_applies)
    strata = strata_input if strata_applies else 0.0
    special_input = st.number_input("Known special levies p.a. ($)", 0.0, value=0.0, step=500.0,
                                    disabled=not strata_applies)
    special_levies = special_input if strata_applies else 0.0
    repairs_pct = st.number_input("Repairs & maintenance (% of gross rent)", 0.0, 100.0, 5.0, 0.5) / 100
    land_tax = st.number_input("Land tax p.a. ($)", 0.0, value=0.0, step=100.0)
    accounting = st.number_input("Accounting / tax-return costs p.a. ($)", 0.0, value=500.0, step=100.0)
    other_expenses = st.number_input("Other annual expenses ($)", 0.0, value=500.0, step=100.0)

    st.subheader("Growth and sale")
    capital_growth = st.number_input("Annual capital growth (%)", -20.0, 50.0, 5.0, 0.5) / 100
    selling_cost_pct = st.number_input("Selling costs (% of sale price)", 0.0, 20.0, 2.5, 0.1) / 100
    depreciation = st.number_input("Depreciation deduction p.a. ($)", 0.0, value=8_000.0, step=500.0)
    horizon = st.slider("Decision / exit horizon (years)", 1, 30, 10)

    st.subheader("Tax treatment")
    use_progressive_tax = st.checkbox("Use progressive ATO 2024-25 tax", value=True,
        help="Models negative gearing against your other income using real tax brackets.")
    other_income = st.number_input("Your other taxable income ($)", 0.0, value=110_000.0, step=5_000.0,
        disabled=not use_progressive_tax,
        help="Used to work out the marginal benefit of rental losses and CGT on sale.")
    include_medicare = st.checkbox("Include 2% Medicare levy", value=True, disabled=not use_progressive_tax)
    marginal_tax_rate = st.number_input("Flat marginal tax rate (%)", 0.0, 60.0, 37.0, 1.0,
        disabled=use_progressive_tax, help="Used only when progressive tax is switched off.") / 100
    apply_cgt = st.checkbox("Apply capital gains tax on sale (50% discount)", value=True,
        help="Adds the discounted capital gain to income in the exit year.")

    st.subheader("Benchmark and returns")
    benchmark_rate = st.number_input("Benchmark / discount rate (%)", 0.0, 30.0, 7.0, 0.5,
        help="Your alternative return (e.g. ETFs). Used for NPV discounting and opportunity cost.") / 100

    with st.expander("Duty, LMI and purchase costs"):
        duty_override = st.number_input("Official duty override ($; 0 = automatic)", 0.0, value=0.0, step=500.0)
        concession_reduction = st.number_input("Concession / exemption reduction ($)", 0.0, value=0.0, step=500.0)
        foreign_surcharge = st.number_input("Foreign purchaser surcharge ($)", 0.0, value=0.0, step=500.0)
        lmi_quote = st.number_input("LMI quote from lender / broker ($)", 0.0, value=0.0, step=500.0,
                                    help="Used only when base LVR exceeds 80%.")
        legal = st.number_input("Legal and conveyancing ($)", 0.0, value=2_500.0, step=100.0)
        inspection = st.number_input("Building and pest inspection ($)", 0.0, value=700.0, step=100.0)
        loan_fees = st.number_input("Loan, valuation and registration fees ($)", 0.0, value=700.0, step=100.0)
        buyers_agent = st.number_input("Buyer's agent fee ($)", 0.0, value=0.0, step=500.0)
        initial_repairs = st.number_input("Initial repairs / renovation ($)", 0.0, value=0.0, step=500.0)
        other_purchase_costs = st.number_input("Other purchase costs ($)", 0.0, value=500.0, step=100.0)

with st.sidebar:
    st.subheader("Market intelligence")
    st.caption("Optional external data. Each block you switch on adds an evidence-backed pillar to the "
               "advanced score. Sources are listed in the Market & scoring tab.")

    use_valuation_data = st.checkbox("Valuation data (AVM)", value=False)
    avm_estimate = st.number_input("Automated valuation estimate ($)", 0.0, value=0.0, step=10_000.0,
        disabled=not use_valuation_data, help="CoreLogic AVM / RP Data, PropTrack Estimate or Domain estimate.")
    avm_confidence = st.selectbox("AVM confidence band", ["High", "Medium", "Low"], index=1,
        disabled=not use_valuation_data, help="CoreLogic reports an FSD / confidence score with each AVM.")

    use_market_benchmarks = st.checkbox("Growth & rent benchmarks", value=False)
    suburb_growth_10yr = st.number_input("Suburb 10-yr avg capital growth (%)", -10.0, 30.0, 5.0, 0.5,
        disabled=not use_market_benchmarks,
        help="CoreLogic Home Value Index, PropTrack or Domain suburb profile, for this dwelling type.") / 100
    suburb_growth_vol = st.number_input("Suburb growth volatility (± %)", 0.0, 20.0, 0.0, 0.5,
        disabled=not use_market_benchmarks,
        help="Std deviation of annual growth. Pre-fills the Monte Carlo volatility if provided.") / 100
    median_weekly_rent = st.number_input("Median weekly rent, this type ($)", 0.0, value=0.0, step=10.0,
        disabled=not use_market_benchmarks, help="CoreLogic or PropTrack median rent for the same bed/dwelling type.")

    use_liquidity_data = st.checkbox("Liquidity & supply", value=False)
    days_on_market = st.number_input("Median days on market", 0.0, value=0.0, step=1.0,
        disabled=not use_liquidity_data, help="CoreLogic / PropTrack suburb days-on-market.")
    vendor_discount = st.number_input("Median vendor discount (%)", 0.0, 30.0, 0.0, 0.5,
        disabled=not use_liquidity_data, help="CoreLogic median vendor discounting (enter the magnitude, e.g. 4).")
    months_of_supply = st.number_input("Months of supply / stock", 0.0, 36.0, 0.0, 0.5,
        disabled=not use_liquidity_data, help="CoreLogic listings vs sales. Under ~3 = tight, over ~6 = soft.")
    auction_clearance = st.number_input("Auction clearance rate (%)", 0.0, 100.0, 0.0, 1.0,
        disabled=not use_liquidity_data, help="Domain / CoreLogic (mainly metro; leave 0 if not applicable).")

    use_demand_data = st.checkbox("Demand fundamentals", value=False)
    population_growth = st.number_input("Annual population growth (%)", -5.0, 15.0, 1.0, 0.1,
        disabled=not use_demand_data, help="ABS Regional Population, .id community profiles or state forecasts.") / 100
    renter_proportion = st.number_input("Renter proportion (%)", 0.0, 100.0, 0.0, 1.0,
        disabled=not use_demand_data, help="ABS Census QuickStats — share of dwellings rented.")
    suburb_vacancy = st.number_input("Suburb vacancy rate (%)", 0.0, 20.0, 0.0, 0.1,
        disabled=not use_demand_data, help="SQM Research is the market standard for suburb vacancy.") / 100

    use_risk_data = st.checkbox("Hazard & risk overlay", value=False)
    hazard_exposure = st.selectbox("Natural-hazard exposure", ["None", "Low", "Moderate", "High"], index=1,
        disabled=not use_risk_data, help="Geoscience Australia, NSW RFS bushfire / state flood maps, insurer quotes.")
    approvals_trend = st.selectbox("Building approvals trend", ["Falling", "Stable", "Rising"], index=1,
        disabled=not use_risk_data, help="ABS 8731.0 Building Approvals — rising supply can cap growth.")


inputs = Inputs(
    property_name=property_name, property_type=property_type, strata_applies=strata_applies,
    state=state, purpose=purpose, bedrooms=int(bedrooms), bathrooms=float(bathrooms),
    car_spaces=int(car_spaces), land_size=float(land_size), purchase_price=purchase_price,
    market_value=market_value, deposit=deposit, interest_rate=interest_rate,
    loan_term_years=loan_term_years, loan_type=loan_type, io_years=io_years,
    offset_balance=offset_balance, extra_monthly=extra_monthly, weekly_rent=weekly_rent,
    vacancy_rate=vacancy_rate, management_fee=management_fee, leasing_fees=leasing_fees,
    rent_growth=rent_growth, council=council, water=water, insurance=insurance, strata=strata,
    special_levies=special_levies, repairs_pct=repairs_pct, land_tax=land_tax, accounting=accounting,
    other_expenses=other_expenses, capital_growth=capital_growth, selling_cost_pct=selling_cost_pct,
    depreciation=depreciation, horizon=horizon, other_income=other_income,
    use_progressive_tax=use_progressive_tax, include_medicare=include_medicare,
    marginal_tax_rate=marginal_tax_rate, apply_cgt=apply_cgt, benchmark_rate=benchmark_rate,
    duty_override=duty_override, concession_reduction=concession_reduction,
    foreign_surcharge=foreign_surcharge, lmi_quote=lmi_quote, legal=legal, inspection=inspection,
    loan_fees=loan_fees, buyers_agent=buyers_agent, initial_repairs=initial_repairs,
    other_purchase_costs=other_purchase_costs,
    use_valuation_data=use_valuation_data, avm_estimate=avm_estimate, avm_confidence=avm_confidence,
    use_market_benchmarks=use_market_benchmarks, suburb_growth_10yr=suburb_growth_10yr,
    suburb_growth_vol=suburb_growth_vol, median_weekly_rent=median_weekly_rent,
    use_liquidity_data=use_liquidity_data, days_on_market=days_on_market, vendor_discount=vendor_discount,
    months_of_supply=months_of_supply, auction_clearance=auction_clearance,
    use_demand_data=use_demand_data, population_growth=population_growth,
    renter_proportion=renter_proportion, suburb_vacancy=suburb_vacancy,
    use_risk_data=use_risk_data, hazard_exposure=hazard_exposure, approvals_trend=approvals_trend,
)

results = calculate(inputs)
first_year = results["cashflow"].iloc[0]
hz = min(horizon, len(results["growth"]))
horizon_result = results["growth"].iloc[hz - 1]
metrics = return_metrics(inputs, results)
score, score_breakdown = investment_score(inputs, results)
adv = advanced_score(inputs, results, score)
composite = adv["composite"]

gross_yield = weekly_rent * 52 / purchase_price if purchase_price else 0.0
net_yield = first_year["Net Operating Income"] / purchase_price if purchase_price else 0.0
after_tax_shortfall = max(0.0, -first_year["After-tax Cash Flow"])
pre_tax_shortfall = max(0.0, -first_year["Pre-tax Cash Flow"])


# ===========================================================================
# Hero
# ===========================================================================
verdict = "Strong" if composite >= 75 else "Viable" if composite >= 55 else "Weak"
verdict_class = "is-strong" if composite >= 75 else "is-viable" if composite >= 55 else "is-weak"

st.markdown(
    f"""
    <div class="hero {verdict_class}">
        <div class="hero-copy">
            <div class="hero-eyebrow">Property Investment Decision Dashboard</div>
            <div class="hero-title">{property_name}</div>
            <p class="hero-sub">{property_type} · {state} · {purpose} — a full feasibility, cash-flow,
            tax, risk and returns model with Monte Carlo simulation, IRR/NPV, progressive ATO tax with CGT,
            sensitivity analysis, market-intelligence scoring and an opportunity-cost benchmark.</p>
            <div class="hero-byline">Analytical property intelligence · <b>Dr Ash Najmaei</b></div>
        </div>
        <div class="hero-score" style="--val:{composite:.0f}">
            <div class="score-ring">
                <div class="score-inner">
                    <span class="score-num">{composite:.0f}</span>
                    <span class="score-den">/ 100</span>
                </div>
            </div>
            <span class="score-verdict">{verdict}</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

tab_dash, tab_market, tab_loan, tab_cash, tab_growth, tab_risk, tab_sens, tab_scen, tab_export = st.tabs([
    "Executive dashboard", "Market & scoring", "Purchase & loan", "Cash flow & tax",
    "Growth, equity & returns", "Risk & Monte Carlo", "Sensitivity & break-even", "Scenarios", "Export",
])


# ---------------------------------------------------------------------------
# TAB 1 — Executive dashboard
# ---------------------------------------------------------------------------
with tab_dash:
    st.markdown('<div class="eyebrow">Decision summary</div>', unsafe_allow_html=True)
    st.markdown('<p class="lead">The headline feasibility, funding and return metrics for this deal '
                'at your chosen exit horizon.</p>', unsafe_allow_html=True)

    a, b, c, d = st.columns(4)
    a.metric("Total cash required", money(results["cash_required"]))
    b.metric("Final LVR", pct(results["final_lvr"]))
    c.metric("Year 1 after-tax cash flow", money(first_year["After-tax Cash Flow"]),
             help="Positive is cash-flow positive after tax effects.")
    d.metric("Gross rental yield", pct(gross_yield))

    e, f, g, h_ = st.columns(4)
    e.metric(f"IRR ({metrics['horizon']}-yr, after-tax)", pct1(metrics["irr"]),
             help="Internal rate of return on the after-tax cash flows plus net sale proceeds.")
    f.metric(f"NPV @ {pct(inputs.benchmark_rate)}", money(metrics["npv"]),
             help="Net present value discounted at your benchmark rate. Above zero beats the benchmark.")
    g.metric("Equity multiple",
             f"{metrics['equity_multiple']:.2f}x" if not math.isnan(metrics["equity_multiple"]) else "—")
    h_.metric("Payback period",
              f"{metrics['payback']} yrs" if metrics["payback"] is not None else f">{metrics['horizon']} yrs")

    if results["lmi_used"] > 0:
        st.markdown(
            f'<div class="warn">Base LVR of {pct(results["base_lvr"])} exceeds 80%, so an estimated '
            f'<b>{money(results["lmi_used"])}</b> of LMI has been added to the loan. Final LVR is '
            f'<b>{pct(results["final_lvr"])}</b>.</div>', unsafe_allow_html=True)

    if composite >= 75:
        st.markdown(f'<div class="good">Composite score <b>{composite:.0f}/100 — Strong</b>. The deal is well '
                    f'structured on the entered assumptions, projecting <b>{money(horizon_result["Total Profit"])}</b> '
                    f'total profit over {metrics["horizon"]} years.</div>', unsafe_allow_html=True)
    elif composite >= 55:
        st.markdown(f'<div class="warn">Composite score <b>{composite:.0f}/100 — Viable</b>. The deal stacks up '
                    f'but has sensitivities worth stress-testing in the Risk and Sensitivity tabs.</div>',
                    unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="bad">Composite score <b>{composite:.0f}/100 — Weak</b> on current assumptions. '
                    f'Review LVR, yield, cash flow, growth and the market pillars before proceeding.</div>',
                    unsafe_allow_html=True)

    st.caption(f"Headline is the composite score ({composite:.0f}) blending financial feasibility "
               f"({score:.0f}/100) with the market-intelligence pillars. Full breakdown, radar and data "
               f"sources are in the Market & scoring tab.")

    with st.expander("Financial feasibility components"):
        st.dataframe(score_breakdown, use_container_width=True, hide_index=True)

    st.markdown("### Value, equity and returns at a glance")
    left, right = st.columns(2)
    g_df = results["growth"].iloc[:metrics["horizon"]]
    with left:
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=g_df["Year"], y=g_df["Property Value"], name="Property value",
                                 mode="lines", line=dict(color=INK, width=3)))
        fig.add_trace(go.Scatter(x=g_df["Year"], y=g_df["Loan Balance"], name="Loan balance",
                                 mode="lines", line=dict(color=NEG, width=2, dash="dot")))
        fig.add_trace(go.Scatter(x=g_df["Year"], y=g_df["Gross Equity"], name="Equity",
                                 mode="lines", fill="tozeroy", line=dict(color=BRASS, width=2.5),
                                 fillcolor="rgba(194,155,74,0.15)"))
        fig.update_layout(title="Projected value, debt and equity", height=360,
                          yaxis_tickprefix="$", yaxis_tickformat=",.0f")
        st.plotly_chart(fig, use_container_width=True)
    with right:
        cf_df = results["cashflow"].iloc[:metrics["horizon"]]
        colors = [POS if v >= 0 else NEG for v in cf_df["After-tax Cash Flow"]]
        fig = go.Figure(go.Bar(x=cf_df["Year"], y=cf_df["After-tax Cash Flow"], marker_color=colors))
        fig.update_layout(title="After-tax cash flow by year", height=360,
                          yaxis_tickprefix="$", yaxis_tickformat=",.0f")
        st.plotly_chart(fig, use_container_width=True)


# ---------------------------------------------------------------------------
# TAB — Market & scoring
# ---------------------------------------------------------------------------
with tab_market:
    st.markdown('<div class="eyebrow">Market intelligence &amp; advanced scoring</div>', unsafe_allow_html=True)
    st.markdown('<p class="lead">The composite score blends the financial model with external evidence you '
                'enter in the sidebar. Each data block you switch on adds an evidence-backed pillar; anything '
                'left off is simply excluded, and the remaining weights are re-normalised so the score is never '
                'dragged toward the middle by missing data.</p>', unsafe_allow_html=True)

    pillars = adv["pillars"]
    active = {k: v for k, v in pillars.items() if v["active"] and v["score"] is not None}

    m1, m2, m3 = st.columns(3)
    m1.metric("Composite score", f"{composite:.0f}/100", verdict)
    m2.metric("Financial pillar", f"{score:.0f}/100")
    m3.metric("Data confidence", pct(adv["confidence"]),
              help="Share of the market-intelligence weighting that is backed by data you entered.")

    st.progress(min(1.0, adv["confidence"]))
    provided = [k for k in active if k not in ("Financial feasibility", "Assumption realism")]
    st.caption(f"{len(provided)} of 4 market pillars are evidence-backed. Switch on more data blocks in the "
               "sidebar (Valuation, Liquidity & supply, Demand, Hazard & risk) to raise confidence.")

    for sev, msg in adv["flags"]:
        st.markdown(f'<div class="{sev}">{msg}</div>', unsafe_allow_html=True)

    left, right = st.columns([1.05, 1])
    with left:
        cats = list(active.keys())
        vals = [active[k]["score"] for k in cats]
        if len(cats) >= 3:
            fig = go.Figure()
            fig.add_trace(go.Scatterpolar(r=vals + [vals[0]], theta=cats + [cats[0]], fill="toself",
                          line=dict(color=INK, width=2.5), fillcolor="rgba(194,155,74,0.22)", name="Score"))
            fig.update_layout(title="Score pillars", height=430, showlegend=False,
                              polar=dict(radialaxis=dict(range=[0, 100], tickfont=dict(size=10), gridcolor=GRID),
                                         angularaxis=dict(tickfont=dict(size=11))))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Enable at least two market-intelligence blocks in the sidebar to populate the radar. "
                    "With no external data, the composite equals the financial feasibility score.")
    with right:
        st.markdown("### Pillar breakdown")
        rows = []
        for k, v in pillars.items():
            rows.append({
                "Pillar": k,
                "Score": f"{v['score']:.0f}" if v["score"] is not None else "—",
                "Weight": pct(v["effective_weight"]) if v["effective_weight"] > 0 else "—",
                "Status": "Data-backed" if (v["active"] and v["score"] is not None) else "Not provided",
            })
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        st.caption("Weight is the effective, re-normalised contribution of each pillar to the composite.")

    with st.expander("What each pillar measures"):
        for k, v in pillars.items():
            st.markdown(f"**{k}** — {v['detail']}")

    st.markdown("### Where to source each input")
    guide = pd.DataFrame({
        "Data point": [
            "Suburb capital growth & volatility", "Automated valuation (AVM) & confidence",
            "Median weekly rent (by dwelling type)", "Suburb vacancy rate", "Days on market & vendor discount",
            "Auction clearance rate", "Months of supply / stock on market", "Annual population growth",
            "Renter proportion", "Building approvals trend", "Natural-hazard exposure",
        ],
        "Recommended source": [
            "CoreLogic Home Value Index; PropTrack; Domain suburb profiles",
            "CoreLogic AVM / RP Data; PropTrack Estimate; Domain estimate (note the confidence/FSD band)",
            "CoreLogic; PropTrack; Domain rental medians",
            "SQM Research (industry standard); state REI vacancy series",
            "CoreLogic; PropTrack suburb statistics",
            "Domain; CoreLogic (mainly capital-city markets)",
            "CoreLogic total listings vs sales; SQM stock-on-market",
            "ABS Regional Population; .id community profiles; state government forecasts",
            "ABS Census QuickStats (tenure of occupied dwellings)",
            "ABS 8731.0 Building Approvals",
            "Geoscience Australia; NSW RFS bushfire-prone mapping; state flood portals; insurer quotes",
        ],
    })
    st.dataframe(guide, use_container_width=True, hide_index=True)
    st.caption("Guidance only — verify each provider's current access terms and licensing. This build takes "
               "manual entry; an automated data feed can be added later as a separate tool.")


# ---------------------------------------------------------------------------
# TAB 2 — Purchase & loan
# ---------------------------------------------------------------------------
with tab_loan:
    st.markdown('<div class="eyebrow">Acquisition and finance</div>', unsafe_allow_html=True)
    st.markdown('<p class="lead">How the purchase is funded and how the loan amortises over time.</p>',
                unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("### Purchase summary")
        purchase_summary = pd.DataFrame({
            "Item": ["Purchase price", "Market value", "Deposit", "Stamp duty (used)", "LMI added",
                     "Other purchase costs", "Total purchase costs", "Total cash required", "CGT cost base"],
            "Amount": [money(purchase_price), money(market_value), money(deposit),
                       money(results["duty_used"]), money(results["lmi_used"]),
                       money(results["other_purchase_costs"]), money(results["purchase_costs"]),
                       money(results["cash_required"]), money(results["cost_base"])],
        })
        st.dataframe(purchase_summary, use_container_width=True, hide_index=True)
    with c2:
        st.markdown("### Loan summary")
        loan_summary = pd.DataFrame({
            "Item": ["Base loan", "Base LVR", "Final loan (incl. LMI)", "Final LVR", "Interest rate",
                     "Loan term", "Structure", "Offset balance", "Extra monthly"],
            "Value": [money(results["base_loan"]), pct(results["base_lvr"]), money(results["total_loan"]),
                      pct(results["final_lvr"]), pct(interest_rate), f"{loan_term_years} years",
                      loan_type + (f" (IO {io_years}y)" if loan_type == "Interest Only" else ""),
                      money(offset_balance), money(extra_monthly)],
        })
        st.dataframe(loan_summary, use_container_width=True, hide_index=True)

    st.markdown("### Loan amortisation")
    sched = results["schedule"]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=sched["Month"] / 12, y=sched["Closing Balance"], name="Loan balance",
                             mode="lines", line=dict(color=INK, width=2.5), fill="tozeroy",
                             fillcolor="rgba(15,33,56,0.06)"))
    fig.add_trace(go.Scatter(x=sched["Month"] / 12, y=sched["Cumulative Interest"], name="Cumulative interest",
                             mode="lines", line=dict(color=BRASS, width=2, dash="dash")))
    fig.update_layout(title="Balance and cumulative interest over the loan life", height=380,
                      xaxis_title="Year", yaxis_tickprefix="$", yaxis_tickformat=",.0f")
    st.plotly_chart(fig, use_container_width=True)

    with st.expander("View full amortisation schedule (monthly)"):
        show = sched.copy()
        for col in ["Opening Balance", "Scheduled Payment", "Extra Payment", "Total Payment",
                    "Interest", "Principal", "Closing Balance", "Cumulative Interest"]:
            show[col] = show[col].map(money2)
        st.dataframe(show, use_container_width=True, hide_index=True, height=360)


# ---------------------------------------------------------------------------
# TAB 3 — Cash flow & tax
# ---------------------------------------------------------------------------
with tab_cash:
    st.markdown('<div class="eyebrow">Operating cash flow and tax</div>', unsafe_allow_html=True)
    st.markdown('<p class="lead">Rental income, holding costs and the tax position, including negative or '
                'positive gearing against your other income.</p>', unsafe_allow_html=True)

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Year 1 pre-tax cash flow", money(first_year["Pre-tax Cash Flow"]))
    m2.metric("Year 1 after-tax cash flow", money(first_year["After-tax Cash Flow"]))
    m3.metric("Year 1 taxable result", money(first_year["Taxable Result"]),
              help="Negative means a rental loss that offsets other income (negative gearing).")
    tax_effect = first_year["Estimated Tax Effect"]
    m4.metric("Year 1 tax effect", money(tax_effect),
              help="Positive is a tax saving/refund; negative is extra tax payable.")

    if inputs.use_progressive_tax:
        mr = marginal_rate(inputs.other_income, inputs.include_medicare)
        st.markdown(
            f'<div class="good">Progressive ATO 2024-25 basis. At your other income of '
            f'<b>{money(inputs.other_income)}</b>, your marginal rate is <b>{pct(mr)}</b>'
            f'{" incl. Medicare" if inputs.include_medicare else ""}. A Year 1 rental result of '
            f'<b>{money(first_year["Taxable Result"])}</b> produces a tax effect of '
            f'<b>{money(tax_effect)}</b>.</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="warn">Flat tax basis at <b>{pct(inputs.marginal_tax_rate)}</b>. '
                    f'Switch on progressive ATO tax in the sidebar for a more accurate position.</div>',
                    unsafe_allow_html=True)

    left, right = st.columns(2)
    cf_df = results["cashflow"].iloc[:metrics["horizon"]]
    with left:
        fig = go.Figure()
        fig.add_trace(go.Bar(x=cf_df["Year"], y=cf_df["Effective Rent"], name="Effective rent",
                             marker_color=INK))
        fig.add_trace(go.Bar(x=cf_df["Year"], y=cf_df["Pre-tax Cash Flow"], name="Pre-tax cash flow",
                             marker_color=BRASS))
        fig.add_trace(go.Bar(x=cf_df["Year"], y=cf_df["After-tax Cash Flow"], name="After-tax cash flow",
                             marker_color=POS))
        fig.update_layout(title="Income and cash flow by year", barmode="group", height=360,
                          yaxis_tickprefix="$", yaxis_tickformat=",.0f")
        st.plotly_chart(fig, use_container_width=True)
    with right:
        exp_items = {"Management": -first_year["Management Fee"], "Leasing": -first_year["Leasing / Advertising"],
                     "Council": -first_year["Council Rates"], "Water": -first_year["Water Charges"],
                     "Insurance": -first_year["Insurance"], "Strata": -first_year["Strata Levies"],
                     "Repairs": -first_year["Repairs / Maintenance"], "Land tax": -first_year["Land Tax"],
                     "Accounting": -first_year["Accounting"], "Other": -first_year["Other Expenses"]}
        exp_items = {k: v for k, v in exp_items.items() if v > 0}
        edf = pd.DataFrame({"Expense": list(exp_items), "Amount": list(exp_items.values())}).sort_values("Amount")
        fig = go.Figure(go.Bar(x=edf["Amount"], y=edf["Expense"], orientation="h", marker_color=SLATE))
        fig.update_layout(title="Year 1 operating expenses", height=360,
                          xaxis_tickprefix="$", xaxis_tickformat=",.0f")
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("### Annual cash-flow detail")
    show = cf_df[["Year", "Effective Rent", "Net Operating Income", "Loan Interest", "Pre-tax Cash Flow",
                  "Taxable Result", "Estimated Tax Effect", "After-tax Cash Flow"]].copy()
    for col in show.columns[1:]:
        show[col] = show[col].map(money)
    st.dataframe(show, use_container_width=True, hide_index=True)


# ---------------------------------------------------------------------------
# TAB 4 — Growth, equity & returns
# ---------------------------------------------------------------------------
with tab_growth:
    st.markdown('<div class="eyebrow">Wealth, returns and opportunity cost</div>', unsafe_allow_html=True)
    st.markdown('<p class="lead">Equity build-up, capital gains tax on exit, discounted returns and how the '
                'deal compares with investing the same capital elsewhere.</p>', unsafe_allow_html=True)

    h = metrics["horizon"]
    m1, m2, m3, m4 = st.columns(4)
    m1.metric(f"Value after {h} yrs", money(horizon_result["Property Value"]))
    m2.metric(f"Equity after {h} yrs", money(horizon_result["Gross Equity"]))
    m3.metric(f"CGT at exit", money(-horizon_result["Capital Gains Tax"]),
              help="Discounted capital gain added to income in the sale year.")
    m4.metric(f"Total profit ({h} yrs)", money(horizon_result["Total Profit"]))

    g_df = results["growth"].iloc[:h]
    left, right = st.columns(2)
    with left:
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=g_df["Year"], y=g_df["Property Value"], name="Property value",
                                 line=dict(color=INK, width=3)))
        fig.add_trace(go.Scatter(x=g_df["Year"], y=g_df["Gross Equity"], name="Equity", fill="tozeroy",
                                 line=dict(color=BRASS, width=2.5), fillcolor="rgba(194,155,74,0.15)"))
        fig.update_layout(title="Value and equity growth", height=360,
                          yaxis_tickprefix="$", yaxis_tickformat=",.0f")
        st.plotly_chart(fig, use_container_width=True)
    with right:
        # Opportunity cost: property total profit vs benchmark alternative
        years = g_df["Year"].values
        alt_profit_path = results["cash_required"] * ((1 + inputs.benchmark_rate) ** years - 1)
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=years, y=g_df["Total Profit"], name="Property total profit",
                                 line=dict(color=POS, width=3)))
        fig.add_trace(go.Scatter(x=years, y=alt_profit_path,
                                 name=f"Benchmark @ {pct(inputs.benchmark_rate)}",
                                 line=dict(color=SLATE, width=2, dash="dash")))
        fig.update_layout(title="Property vs benchmark (opportunity cost)", height=360,
                          yaxis_tickprefix="$", yaxis_tickformat=",.0f")
        st.plotly_chart(fig, use_container_width=True)

    if metrics["excess_over_benchmark"] >= 0:
        st.markdown(f'<div class="good">Over {h} years the property is projected to beat your '
                    f'{pct(inputs.benchmark_rate)} benchmark by <b>{money(metrics["excess_over_benchmark"])}</b> '
                    f'(property {money(metrics["property_profit"])} vs benchmark {money(metrics["alt_profit"])}).'
                    f'</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="warn">Over {h} years the benchmark alternative is projected to out-earn the '
                    f'property by <b>{money(-metrics["excess_over_benchmark"])}</b>. The deal must be justified '
                    f'on leverage, diversification or other grounds.</div>', unsafe_allow_html=True)

    st.markdown("### Growth and equity detail")
    show = g_df[["Year", "Property Value", "Loan Balance", "Gross Equity", "Capital Gains Tax",
                 "Net Sale Proceeds", "Total Profit", "Cash-on-Cash Return"]].copy()
    show["Cash-on-Cash Return"] = show["Cash-on-Cash Return"].map(pct)
    for col in ["Property Value", "Loan Balance", "Gross Equity", "Capital Gains Tax",
                "Net Sale Proceeds", "Total Profit"]:
        show[col] = show[col].map(money)
    st.dataframe(show, use_container_width=True, hide_index=True)


# ---------------------------------------------------------------------------
# TAB 5 — Risk & Monte Carlo
# ---------------------------------------------------------------------------
with tab_risk:
    st.markdown('<div class="eyebrow">Probabilistic risk analysis</div>', unsafe_allow_html=True)
    st.markdown('<p class="lead">Instead of single point estimates, let the key drivers vary and simulate '
                'thousands of outcomes. Set how uncertain each driver is, then read the spread of results.</p>',
                unsafe_allow_html=True)

    cset1, cset2 = st.columns([1, 1])
    with cset1:
        n_sims = st.select_slider("Number of simulations", options=[500, 1000, 2000, 5000, 10000], value=2000)
        _cg_default = (inputs.suburb_growth_vol if (inputs.use_market_benchmarks and inputs.suburb_growth_vol > 0)
                       else 0.02)
        cg_sd = st.slider("Capital growth volatility (± p.a.)", 0.0, 0.08, min(0.08, _cg_default), 0.005,
                          format="%.3f",
                          help="Pre-filled from your entered suburb growth volatility when available.")
        rate_sd = st.slider("Interest rate volatility (± p.a.)", 0.0, 0.05, 0.015, 0.005, format="%.3f")
    with cset2:
        rg_sd = st.slider("Rent growth volatility (± p.a.)", 0.0, 0.06, 0.015, 0.005, format="%.3f")
        vac_sd = st.slider("Vacancy volatility (±)", 0.0, 0.06, 0.02, 0.005, format="%.3f")
        st.caption("Drivers are sampled around your sidebar assumptions each run. "
                   "Results are indicative, not a forecast.")

    vol = {"cg": cg_sd, "rate": rate_sd, "rg": rg_sd, "vac": vac_sd}
    with st.spinner("Running simulations…"):
        mc = monte_carlo(inputs, n_sims, vol)

    p1, p2, p3, p4 = st.columns(4)
    p1.metric("P(profitable exit)", pct(mc["prob_profit"]))
    p2.metric("P(beats benchmark)", pct(mc["prob_beats_benchmark"]))
    p3.metric("P(negative Yr-1 cash flow)", pct(mc["prob_negative_cashflow_y1"]))
    p4.metric("P(negative equity ever)", pct(mc["prob_negative_equity"]))

    profit = mc["total_profit"]
    p10, p50, p90 = np.percentile(profit, [10, 50, 90])
    left, right = st.columns(2)
    with left:
        fig = go.Figure(go.Histogram(x=profit, nbinsx=60, marker_color=INK, opacity=0.85))
        for val, lab, col in [(p10, "P10", NEG), (p50, "Median", BRASS), (p90, "P90", POS)]:
            fig.add_vline(x=val, line=dict(color=col, width=2, dash="dash"),
                          annotation_text=f"{lab}: {money(val)}", annotation_position="top")
        fig.update_layout(title=f"Distribution of {metrics['horizon']}-year total profit", height=380,
                          xaxis_tickprefix="$", xaxis_tickformat=",.0s", showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
    with right:
        irr_clean = mc["irr"][~np.isnan(mc["irr"])]
        if irr_clean.size:
            i10, i50, i90 = np.percentile(irr_clean, [10, 50, 90])
            fig = go.Figure(go.Histogram(x=irr_clean, nbinsx=60, marker_color=BRASS, opacity=0.85))
            for val, lab, col in [(i10, "P10", NEG), (i50, "Median", INK), (i90, "P90", POS)]:
                fig.add_vline(x=val, line=dict(color=col, width=2, dash="dash"),
                              annotation_text=f"{lab}: {pct(val)}", annotation_position="top")
            fig.add_vline(x=inputs.benchmark_rate, line=dict(color=SLATE, width=2),
                          annotation_text=f"Benchmark {pct(inputs.benchmark_rate)}", annotation_position="bottom")
            fig.update_layout(title="Distribution of after-tax IRR", height=380,
                              xaxis_tickformat=".0%", showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("IRR could not be resolved for these simulations (cash-flow signs did not cross).")

    st.markdown("### Equity fan chart")
    yrs = np.arange(1, metrics["horizon"] + 1)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=np.concatenate([yrs, yrs[::-1]]),
                             y=np.concatenate([mc["equity_p90"], mc["equity_p10"][::-1]]),
                             fill="toself", fillcolor="rgba(194,155,74,0.18)",
                             line=dict(color="rgba(0,0,0,0)"), name="P10–P90 band", hoverinfo="skip"))
    fig.add_trace(go.Scatter(x=yrs, y=mc["equity_p50"], name="Median equity",
                             line=dict(color=INK, width=3)))
    fig.update_layout(title="Projected equity — median with 10th–90th percentile band", height=380,
                      xaxis_title="Year", yaxis_tickprefix="$", yaxis_tickformat=",.0f")
    st.plotly_chart(fig, use_container_width=True)

    pct_table = pd.DataFrame({
        "Percentile": ["P10 (pessimistic)", "P50 (median)", "P90 (optimistic)"],
        f"{metrics['horizon']}-yr total profit": [money(p10), money(p50), money(p90)],
        "Year 1 after-tax cash flow": [money(v) for v in np.percentile(mc["year1_after_tax"], [10, 50, 90])],
    })
    st.dataframe(pct_table, use_container_width=True, hide_index=True)


# ---------------------------------------------------------------------------
# TAB 6 — Sensitivity & break-even
# ---------------------------------------------------------------------------
with tab_sens:
    st.markdown('<div class="eyebrow">What the decision hinges on</div>', unsafe_allow_html=True)
    st.markdown('<p class="lead">Rank the assumptions by impact, find the levels at which the deal breaks even, '
                'and stress-test interest rates and growth.</p>', unsafe_allow_html=True)

    shift = st.slider("Tornado shift applied to each driver (±%)", 5, 30, 15, 5) / 100
    base_profit, tdf = tornado(inputs, shift)

    st.markdown("### Sensitivity tornado")
    fig = go.Figure()
    fig.add_trace(go.Bar(y=tdf["Driver"], x=tdf["Low"], orientation="h", name=f"−{int(shift*100)}%",
                         marker_color=NEG, base=0))
    fig.add_trace(go.Bar(y=tdf["Driver"], x=tdf["High"], orientation="h", name=f"+{int(shift*100)}%",
                         marker_color=POS, base=0))
    fig.update_layout(title=f"Impact on {metrics['horizon']}-year total profit vs base "
                            f"({money(base_profit)})", barmode="overlay", height=380,
                      xaxis_tickprefix="$", xaxis_tickformat=",.0s")
    st.plotly_chart(fig, use_container_width=True)
    st.caption("Bars show the change in projected total profit when each driver alone moves by the chosen "
               "percentage. The widest bars are the assumptions your decision is most exposed to.")

    st.markdown("### Break-even analysis")
    st.dataframe(break_even_table(inputs), use_container_width=True, hide_index=True)

    st.markdown("### Interest-rate and growth stress tests")
    left, right = st.columns(2)
    with left:
        rates = np.round(np.arange(max(0.01, inputs.interest_rate - 0.03),
                                   inputs.interest_rate + 0.0301, 0.005), 4)
        y1cf = [float(calculate(replace(inputs, interest_rate=r))["cashflow"].iloc[0]["After-tax Cash Flow"])
                for r in rates]
        colors = [POS if v >= 0 else NEG for v in y1cf]
        fig = go.Figure(go.Bar(x=[pct(r) for r in rates], y=y1cf, marker_color=colors))
        fig.add_vline(x=pct(inputs.interest_rate), line=dict(color=INK, width=2, dash="dot"))
        fig.update_layout(title="Year 1 after-tax cash flow vs interest rate", height=340,
                          yaxis_tickprefix="$", yaxis_tickformat=",.0f")
        st.plotly_chart(fig, use_container_width=True)
    with right:
        growths = np.round(np.arange(max(-0.05, inputs.capital_growth - 0.04),
                                     inputs.capital_growth + 0.0401, 0.01), 4)
        prof = []
        for gr in growths:
            r = calculate(replace(inputs, capital_growth=gr))
            hh = min(inputs.horizon, len(r["growth"]))
            prof.append(float(r["growth"].iloc[hh - 1]["Total Profit"]))
        colors = [POS if v >= 0 else NEG for v in prof]
        fig = go.Figure(go.Bar(x=[pct(gr) for gr in growths], y=prof, marker_color=colors))
        fig.add_vline(x=pct(inputs.capital_growth), line=dict(color=INK, width=2, dash="dot"))
        fig.update_layout(title=f"{metrics['horizon']}-year profit vs capital growth", height=340,
                          yaxis_tickprefix="$", yaxis_tickformat=",.0s")
        st.plotly_chart(fig, use_container_width=True)


# ---------------------------------------------------------------------------
# TAB 7 — Scenarios
# ---------------------------------------------------------------------------
with tab_scen:
    st.markdown('<div class="eyebrow">Compare deals side by side</div>', unsafe_allow_html=True)
    st.markdown('<p class="lead">Save the current assumption set as a named scenario, then compare feasibility, '
                'returns and profit across saved deals. Download the set as JSON to reload later.</p>',
                unsafe_allow_html=True)

    if "scenarios" not in st.session_state:
        st.session_state["scenarios"] = {}

    def snapshot(name, x, results, metrics, score):
        h = metrics["horizon"]
        gy = x.weekly_rent * 52 / x.purchase_price if x.purchase_price else 0.0
        adv_s = advanced_score(x, results, score)
        return {
            "inputs": asdict(x), "Score": round(adv_s["composite"], 1),
            "Financial": round(score, 1), "Confidence": adv_s["confidence"],
            "Final LVR": results["final_lvr"],
            "Gross yield": gy, "Cash required": results["cash_required"],
            "Year 1 after-tax CF": float(results["cashflow"].iloc[0]["After-tax Cash Flow"]),
            "IRR": metrics["irr"], "NPV": metrics["npv"],
            "Total profit": metrics["property_profit"], "Horizon": h,
        }

    csave1, csave2 = st.columns([2, 1])
    with csave1:
        scen_name = st.text_input("Scenario name", value=property_name)
    with csave2:
        st.write("")
        st.write("")
        if st.button("💾 Save current scenario", use_container_width=True):
            st.session_state["scenarios"][scen_name] = snapshot(scen_name, inputs, results, metrics, score)
            st.success(f"Saved '{scen_name}'.")

    scenarios = st.session_state["scenarios"]
    if scenarios:
        comp = pd.DataFrame({
            "Metric": ["Composite score", "Financial score", "Data confidence", "Final LVR", "Gross yield",
                       "Cash required", "Year 1 after-tax CF", "IRR (after-tax)", "NPV @ benchmark",
                       "Total profit", "Horizon"],
        })
        for name, s in scenarios.items():
            comp[name] = [f"{s['Score']:.0f}/100", f"{s.get('Financial', s['Score']):.0f}/100",
                          pct(s.get("Confidence", 0.0)), pct(s["Final LVR"]), pct(s["Gross yield"]),
                          money(s["Cash required"]), money(s["Year 1 after-tax CF"]), pct1(s["IRR"]),
                          money(s["NPV"]), money(s["Total profit"]), f"{s['Horizon']} yrs"]
        st.markdown("### Scenario comparison")
        st.dataframe(comp, use_container_width=True, hide_index=True)

        if len(scenarios) >= 2:
            names = list(scenarios)
            fig = go.Figure()
            fig.add_trace(go.Bar(x=names, y=[scenarios[n]["Total profit"] for n in names],
                                 name="Total profit", marker_color=INK,
                                 yaxis="y1", offsetgroup=1))
            fig.add_trace(go.Bar(x=names, y=[scenarios[n]["Score"] for n in names],
                                 name="Composite score", marker_color=BRASS,
                                 yaxis="y2", offsetgroup=2))
            fig.update_layout(title="Profit and composite score across scenarios", height=380, barmode="group",
                              yaxis=dict(title="Total profit", tickprefix="$", tickformat=",.0s"),
                              yaxis2=dict(title="Score", overlaying="y", side="right", range=[0, 100]))
            st.plotly_chart(fig, use_container_width=True)

        cman1, cman2 = st.columns(2)
        with cman1:
            to_delete = st.selectbox("Remove a scenario", ["—"] + list(scenarios))
            if st.button("Delete selected", use_container_width=True) and to_delete != "—":
                st.session_state["scenarios"].pop(to_delete, None)
                st.rerun()
        with cman2:
            payload = {n: s["inputs"] for n, s in scenarios.items()}
            st.download_button("⬇ Download scenarios (JSON)",
                               data=json.dumps(payload, indent=2), file_name="property_scenarios.json",
                               mime="application/json", use_container_width=True)
    else:
        st.info("No scenarios saved yet. Set your assumptions in the sidebar and click **Save current scenario**.")

    uploaded = st.file_uploader("Restore scenarios from a JSON file", type="json")
    if uploaded is not None:
        try:
            data = json.load(uploaded)
            restored = 0
            for name, inp in data.items():
                xi = Inputs(**inp)
                ri = calculate(xi)
                mi = return_metrics(xi, ri)
                si, _ = investment_score(xi, ri)
                st.session_state["scenarios"][name] = snapshot(name, xi, ri, mi, si)
                restored += 1
            st.success(f"Restored {restored} scenario(s).")
        except Exception as exc:  # noqa: BLE001
            st.error(f"Could not read that file: {exc}")


# ---------------------------------------------------------------------------
# TAB 8 — Export
# ---------------------------------------------------------------------------
with tab_export:
    st.markdown('<div class="eyebrow">Share and archive</div>', unsafe_allow_html=True)
    st.markdown('<p class="lead">Download a branded one-page decision report or the underlying data tables.</p>',
                unsafe_allow_html=True)

    report = report_html(inputs, results, score, metrics, adv)
    st.download_button("⬇ Download branded HTML report", data=report,
                       file_name=f"{property_name.replace(' ', '_')}_report.html",
                       mime="text/html", use_container_width=True)

    st.markdown("### Data tables (CSV)")
    c1, c2 = st.columns(2)
    with c1:
        st.download_button("Amortisation schedule",
                           results["schedule"].to_csv(index=False),
                           "amortisation_schedule.csv", "text/csv", use_container_width=True)
        st.download_button("Cash-flow projection",
                           results["cashflow"].to_csv(index=False),
                           "cashflow_projection.csv", "text/csv", use_container_width=True)
        st.download_button("Growth & equity projection",
                           results["growth"].to_csv(index=False),
                           "growth_projection.csv", "text/csv", use_container_width=True)
    with c2:
        assumptions = pd.DataFrame([{"Field": k, "Value": v} for k, v in asdict(inputs).items()])
        st.download_button("Assumptions",
                           assumptions.to_csv(index=False),
                           "assumptions.csv", "text/csv", use_container_width=True)
        st.download_button("Feasibility score breakdown",
                           score_breakdown.to_csv(index=False),
                           "feasibility_score.csv", "text/csv", use_container_width=True)
        summary = pd.DataFrame([{
            "Property": property_name, "Composite score": round(composite, 1),
            "Financial score": round(score, 1), "Verdict": verdict,
            "Data confidence": adv["confidence"], "Final LVR": results["final_lvr"],
            "Cash required": results["cash_required"],
            "Year1 after-tax CF": first_year["After-tax Cash Flow"], "IRR": metrics["irr"],
            "NPV": metrics["npv"], "Total profit": metrics["property_profit"],
        }])
        st.download_button("Decision summary",
                           summary.to_csv(index=False),
                           "decision_summary.csv", "text/csv", use_container_width=True)

    with st.expander("Preview the report"):
        st.components.v1.html(report, height=680, scrolling=True)


st.divider()
st.caption("This dashboard is an educational modelling tool. It does not constitute financial, tax, credit, "
           "legal or investment advice. Stamp duty, LMI, land tax, CGT and income-tax figures are simplified "
           "estimates using 2024-25 settings and should be verified with qualified professionals and current "
           "government sources before any decision.")
