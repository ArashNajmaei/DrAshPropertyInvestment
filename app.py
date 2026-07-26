import math
from dataclasses import asdict, dataclass, replace

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


st.set_page_config(
    page_title="Property Investment Dashboard",
    page_icon="🏠",
    layout="wide",
)

st.markdown(
    """
    <style>
    .block-container {padding-top: 1rem; padding-bottom: 2rem;}
    [data-testid="stSidebar"] {min-width: 350px; max-width: 350px;}
    [data-testid="stMetric"] {
        background: #f5f8fc;
        border: 1px solid #d7e1ec;
        padding: 14px;
        border-radius: 10px;
    }
    .good {
        background: #e8f5e9;
        padding: 14px;
        border-radius: 8px;
        border-left: 5px solid #2e7d32;
    }
    .warn {
        background: #fff8e1;
        padding: 14px;
        border-radius: 8px;
        border-left: 5px solid #f9a825;
    }
    .bad {
        background: #ffebee;
        padding: 14px;
        border-radius: 8px;
        border-left: 5px solid #c62828;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def money(value: float) -> str:
    return f"${value:,.0f}"


def money2(value: float) -> str:
    return f"${value:,.2f}"


def pct(value: float) -> str:
    return f"{value:.1%}"


def marginal(value: float, lower: float, base: float, rate: float) -> float:
    return base + max(0.0, value - lower) * rate


def estimate_duty(state: str, value: float) -> float:
    """General duty estimate only. Official state calculators should be used before purchase."""
    v = max(0.0, float(value))

    if state == "NSW":
        if v <= 18_000:
            return max(20, v * 0.0125)
        if v <= 38_000:
            return marginal(v, 18_000, 225, 0.015)
        if v <= 103_000:
            return marginal(v, 38_000, 525, 0.0175)
        if v <= 387_000:
            return marginal(v, 103_000, 1_662, 0.035)
        if v <= 1_290_000:
            return marginal(v, 387_000, 11_602, 0.045)
        if v <= 3_870_000:
            return marginal(v, 1_290_000, 52_237, 0.055)
        return marginal(v, 3_870_000, 194_137, 0.07)

    if state == "VIC":
        if v <= 25_000:
            return v * 0.014
        if v <= 130_000:
            return marginal(v, 25_000, 350, 0.024)
        if v <= 960_000:
            return marginal(v, 130_000, 2_870, 0.06)
        if v <= 2_000_000:
            return v * 0.055
        return marginal(v, 2_000_000, 110_000, 0.065)

    if state == "QLD":
        if v <= 5_000:
            return 0
        if v <= 75_000:
            return (v - 5_000) * 0.015
        if v <= 540_000:
            return marginal(v, 75_000, 1_050, 0.035)
        if v <= 1_000_000:
            return marginal(v, 540_000, 17_325, 0.045)
        return marginal(v, 1_000_000, 38_025, 0.0575)

    if state == "WA":
        if v <= 120_000:
            return v * 0.019
        if v <= 150_000:
            return marginal(v, 120_000, 2_280, 0.0285)
        if v <= 360_000:
            return marginal(v, 150_000, 3_135, 0.038)
        if v <= 725_000:
            return marginal(v, 360_000, 11_115, 0.0475)
        return marginal(v, 725_000, 28_452.5, 0.0515)

    if state == "SA":
        bands = [
            (12_000, 0, 0, 0.01),
            (30_000, 12_000, 120, 0.02),
            (50_000, 30_000, 480, 0.03),
            (100_000, 50_000, 1_080, 0.035),
            (200_000, 100_000, 2_830, 0.04),
            (250_000, 200_000, 6_830, 0.0425),
            (300_000, 250_000, 8_955, 0.0475),
            (500_000, 300_000, 11_330, 0.05),
            (float("inf"), 500_000, 21_330, 0.055),
        ]
        for upper, lower, base, rate in bands:
            if v <= upper:
                return marginal(v, lower, base, rate)

    if state == "TAS":
        if v <= 1_300:
            return 20
        if v <= 10_000:
            return v * 0.015
        if v <= 30_000:
            return marginal(v, 10_000, 150, 0.02)
        if v <= 75_000:
            return marginal(v, 30_000, 550, 0.025)
        if v <= 150_000:
            return marginal(v, 75_000, 1_675, 0.03)
        if v <= 225_000:
            return marginal(v, 150_000, 3_925, 0.035)
        if v <= 375_000:
            return marginal(v, 225_000, 6_550, 0.04)
        return marginal(v, 375_000, 12_550, 0.045)

    if state == "ACT":
        if v <= 200_000:
            return v * 0.012
        if v <= 300_000:
            return marginal(v, 200_000, 2_400, 0.022)
        if v <= 500_000:
            return marginal(v, 300_000, 4_600, 0.034)
        if v <= 750_000:
            return marginal(v, 500_000, 11_400, 0.0432)
        if v <= 1_000_000:
            return marginal(v, 750_000, 22_200, 0.059)
        if v <= 1_455_000:
            return marginal(v, 1_000_000, 36_950, 0.064)
        return v * 0.0454

    if state == "NT":
        if v <= 525_000:
            x = v / 1_000
            return (0.06571441 * x * x + 15 * x) * 1_000
        if v <= 3_000_000:
            return v * 0.0495
        if v <= 5_000_000:
            return v * 0.0575
        return v * 0.0595

    return 0.0


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
    marginal_tax_rate: float
    depreciation: float
    horizon: int

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


def loan_info(x: Inputs):
    base_loan = max(0.0, x.purchase_price - x.deposit)
    base_lvr = base_loan / x.market_value if x.market_value else 0.0
    lmi_used = max(0.0, x.lmi_quote) if base_lvr > 0.80 else 0.0
    total_loan = base_loan + lmi_used
    final_lvr = total_loan / x.market_value if x.market_value else 0.0
    return base_loan, base_lvr, lmi_used, total_loan, final_lvr


def loan_schedule(x: Inputs) -> pd.DataFrame:
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
                scheduled = (
                    opening
                    * monthly_rate
                    * (1 + monthly_rate) ** remaining
                    / ((1 + monthly_rate) ** remaining - 1)
                )
            extra = min(x.extra_monthly, opening)
            principal = min(opening, max(0.0, scheduled - interest) + extra)
            closing = max(0.0, opening - principal)

        cumulative_interest += interest
        rows.append(
            {
                "Month": month,
                "Year": math.ceil(month / 12),
                "Opening Balance": opening,
                "Scheduled Payment": scheduled,
                "Extra Payment": extra,
                "Total Payment": scheduled + extra,
                "Interest": interest,
                "Principal": principal,
                "Closing Balance": closing,
                "Offset Balance": x.offset_balance,
                "Cumulative Interest": cumulative_interest,
            }
        )
        balance = closing

    return pd.DataFrame(rows)


def calculate(x: Inputs) -> dict:
    base_loan, base_lvr, lmi_used, total_loan, final_lvr = loan_info(x)

    automatic_duty = estimate_duty(
        x.state,
        max(x.purchase_price, x.market_value),
    )
    duty_used = (
        x.duty_override
        if x.duty_override > 0
        else max(
            0.0,
            automatic_duty - x.concession_reduction + x.foreign_surcharge,
        )
    )

    other_purchase_costs = sum(
        [
            x.legal,
            x.inspection,
            x.loan_fees,
            x.buyers_agent,
            x.initial_repairs,
            x.other_purchase_costs,
        ]
    )
    purchase_costs = duty_used + lmi_used + other_purchase_costs
    cash_required = x.deposit + purchase_costs

    schedule = loan_schedule(x)
    annual_interest = schedule.groupby("Year", as_index=False)["Interest"].sum()
    annual_balance = schedule.groupby("Year", as_index=False)["Closing Balance"].last()
    annual_payment = schedule.groupby("Year", as_index=False)["Total Payment"].sum()

    cashflow_rows = []
    growth_rows = []
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

        interest = float(
            annual_interest.loc[
                annual_interest["Year"] == year,
                "Interest",
            ].sum()
        )
        loan_payments = float(
            annual_payment.loc[
                annual_payment["Year"] == year,
                "Total Payment",
            ].sum()
        )

        operating_expenses = sum(
            [
                management,
                leasing,
                council,
                water,
                insurance,
                strata,
                special_levies,
                repairs,
                x.land_tax,
                x.accounting,
                other,
            ]
        )

        net_operating_income = effective_rent - operating_expenses
        pre_tax_cashflow = net_operating_income - loan_payments
        taxable_result = (
            effective_rent
            - operating_expenses
            - interest
            - x.depreciation
        )
        estimated_tax_effect = -taxable_result * x.marginal_tax_rate
        after_tax_cashflow = pre_tax_cashflow + estimated_tax_effect
        cumulative_after_tax_cashflow += after_tax_cashflow

        cashflow_rows.append(
            {
                "Year": year,
                "Gross Rent": gross_rent,
                "Vacancy": -vacancy,
                "Effective Rent": effective_rent,
                "Management Fee": -management,
                "Leasing / Advertising": -leasing,
                "Council Rates": -council,
                "Water Charges": -water,
                "Insurance": -insurance,
                "Strata Levies": -strata,
                "Special Levies": -special_levies,
                "Repairs / Maintenance": -repairs,
                "Land Tax": -x.land_tax,
                "Accounting": -x.accounting,
                "Other Expenses": -other,
                "Net Operating Income": net_operating_income,
                "Loan Payments": -loan_payments,
                "Loan Interest": -interest,
                "Pre-tax Cash Flow": pre_tax_cashflow,
                "Depreciation": -x.depreciation,
                "Taxable Result": taxable_result,
                "Estimated Tax Effect": estimated_tax_effect,
                "After-tax Cash Flow": after_tax_cashflow,
            }
        )

        property_value = x.purchase_price * (1 + x.capital_growth) ** year
        loan_balance = float(
            annual_balance.loc[
                annual_balance["Year"] == year,
                "Closing Balance",
            ].iloc[0]
        )
        gross_equity = property_value - loan_balance
        selling_costs = property_value * x.selling_cost_pct
        net_sale_proceeds = property_value - selling_costs - loan_balance
        total_profit = (
            net_sale_proceeds
            + cumulative_after_tax_cashflow
            - cash_required
        )

        growth_rows.append(
            {
                "Year": year,
                "Property Value": property_value,
                "Loan Balance": loan_balance,
                "Gross Equity": gross_equity,
                "Selling Costs": -selling_costs,
                "Net Sale Proceeds": net_sale_proceeds,
                "Cumulative After-tax Cash Flow": cumulative_after_tax_cashflow,
                "Total Profit": total_profit,
                "Cash-on-Cash Return": (
                    total_profit / cash_required if cash_required else 0.0
                ),
            }
        )

    return {
        "base_loan": base_loan,
        "base_lvr": base_lvr,
        "lmi_used": lmi_used,
        "total_loan": total_loan,
        "final_lvr": final_lvr,
        "automatic_duty": automatic_duty,
        "duty_used": duty_used,
        "other_purchase_costs": other_purchase_costs,
        "purchase_costs": purchase_costs,
        "cash_required": cash_required,
        "schedule": schedule,
        "cashflow": pd.DataFrame(cashflow_rows),
        "growth": pd.DataFrame(growth_rows),
    }


def investment_score(x: Inputs, results: dict) -> tuple[float, pd.DataFrame]:
    first_year = results["cashflow"].iloc[0]
    horizon_result = results["growth"].iloc[x.horizon - 1]
    gross_yield = (
        x.weekly_rent * 52 / x.purchase_price
        if x.purchase_price
        else 0.0
    )

    lvr_score = (
        25.0
        if results["final_lvr"] <= 0.80
        else max(0.0, 25.0 - (results["final_lvr"] - 0.80) * 100)
    )
    yield_score = (
        20.0
        if gross_yield >= 0.05
        else max(0.0, gross_yield / 0.05 * 20)
    )
    cashflow_score = (
        20.0
        if first_year["After-tax Cash Flow"] >= 0
        else max(
            0.0,
            20.0
            + first_year["After-tax Cash Flow"]
            / max(1.0, x.weekly_rent * 52)
            * 20,
        )
    )
    profit_score = 20.0 if horizon_result["Total Profit"] > 0 else 0.0
    growth_score = (
        15.0
        if x.capital_growth >= 0.04
        else max(0.0, x.capital_growth / 0.04 * 15)
    )

    total = max(
        0.0,
        min(
            100.0,
            lvr_score
            + yield_score
            + cashflow_score
            + profit_score
            + growth_score,
        ),
    )

    breakdown = pd.DataFrame(
        {
            "Component": [
                "Final LVR",
                "Gross rental yield",
                "Year 1 after-tax cash flow",
                f"{x.horizon}-year projected total profit",
                "Assumed annual capital growth",
            ],
            "Result": [
                pct(results["final_lvr"]),
                pct(gross_yield),
                money(first_year["After-tax Cash Flow"]),
                money(horizon_result["Total Profit"]),
                pct(x.capital_growth),
            ],
            "Points earned": [
                f"{lvr_score:.1f} / 25",
                f"{yield_score:.1f} / 20",
                f"{cashflow_score:.1f} / 20",
                f"{profit_score:.1f} / 20",
                f"{growth_score:.1f} / 15",
            ],
        }
    )

    return total, breakdown


def report_html(x: Inputs, results: dict, score: float) -> str:
    h = min(x.horizon, len(results["growth"]))
    first_year = results["cashflow"].iloc[0]
    horizon_result = results["growth"].iloc[h - 1]
    shortfall = max(0.0, -first_year["After-tax Cash Flow"])

    fields = {
        "Property": x.property_name,
        "Property type": x.property_type,
        "Bedrooms": x.bedrooms,
        "Bathrooms": f"{x.bathrooms:g}",
        "Car spaces": x.car_spaces,
        "Land size": (
            f"{x.land_size:,.0f} m²"
            if x.land_size > 0
            else "Not entered"
        ),
        "Strata applies": "Yes" if x.strata_applies else "No",
        "State": x.state,
        "Purpose": x.purpose,
        "Purchase price": money(x.purchase_price),
        "Market value": money(x.market_value),
        "Deposit": money(x.deposit),
        "Weekly rent": money2(x.weekly_rent),
        "Gross rental yield": pct(
            x.weekly_rent * 52 / x.purchase_price
            if x.purchase_price
            else 0
        ),
        "Base LVR": pct(results["base_lvr"]),
        "Final LVR": pct(results["final_lvr"]),
        "LMI added": money(results["lmi_used"]),
        "Total loan": money(results["total_loan"]),
        "Duty used": money(results["duty_used"]),
        "Total cash required": money(results["cash_required"]),
        "Investment feasibility score": f"{score:.0f}/100",
        "Year 1 pre-tax cash flow": money(
            first_year["Pre-tax Cash Flow"]
        ),
        "Year 1 after-tax cash flow": money(
            first_year["After-tax Cash Flow"]
        ),
        "Weekly out-of-pocket": money2(shortfall / 52),
        "Fortnightly out-of-pocket": money2(shortfall / 26),
        "Monthly out-of-pocket": money2(shortfall / 12),
        f"Value after {h} years": money(
            horizon_result["Property Value"]
        ),
        f"Equity after {h} years": money(
            horizon_result["Gross Equity"]
        ),
        f"Total profit after {h} years": money(
            horizon_result["Total Profit"]
        ),
    }

    rows = "".join(
        f"<tr><th>{key}</th><td>{value}</td></tr>"
        for key, value in fields.items()
    )

    return f"""
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{
                font-family: Arial, sans-serif;
                max-width: 900px;
                margin: 40px auto;
                color: #17324d;
            }}
            table {{
                border-collapse: collapse;
                width: 100%;
            }}
            th, td {{
                padding: 10px;
                border-bottom: 1px solid #ddd;
                text-align: left;
            }}
            th {{
                background: #f5f7fa;
            }}
        </style>
    </head>
    <body>
        <h1>Property Investment Decision Report</h1>
        <table>{rows}</table>
        <p>
            The score is an internal feasibility indicator based on entered
            assumptions. It is not a suburb rating, valuation, forecast,
            lending assessment or financial recommendation.
        </p>
        <p>
            Verify duty, LMI, tax treatment, rent, strata, land tax,
            insurance and finance terms independently.
        </p>
    </body>
    </html>
    """


st.sidebar.title("🏠 Property inputs")

with st.sidebar:
    property_name = st.text_input(
        "Property name or address",
        "Example investment property",
    )
    property_type = st.selectbox(
        "Property type",
        [
            "House",
            "Apartment / Unit",
            "Townhouse",
            "Villa",
            "Duplex",
            "Terrace",
            "Vacant Land",
            "Other",
        ],
    )
    default_strata = property_type in {
        "Apartment / Unit",
        "Townhouse",
        "Villa",
    }
    strata_applies = st.checkbox(
        "Strata / owners corporation applies",
        value=default_strata,
    )
    state = st.selectbox(
        "State / Territory",
        ["NSW", "VIC", "QLD", "WA", "SA", "TAS", "ACT", "NT"],
    )
    purpose = st.selectbox(
        "Property purpose",
        ["Investment", "Owner Occupier"],
    )

    st.subheader("Property details")
    details_left, details_right = st.columns(2)

    with details_left:
        bedrooms = st.number_input(
            "Bedrooms",
            min_value=0,
            max_value=20,
            value=3,
            step=1,
        )
        car_spaces = st.number_input(
            "Car spaces",
            min_value=0,
            max_value=20,
            value=1,
            step=1,
        )

    with details_right:
        bathrooms = st.number_input(
            "Bathrooms",
            min_value=0.0,
            max_value=20.0,
            value=2.0,
            step=0.5,
        )
        default_land_size = (
            500.0
            if property_type
            in {
                "House",
                "Duplex",
                "Terrace",
                "Vacant Land",
                "Other",
            }
            else 0.0
        )
        land_size = st.number_input(
            "Land size (m²)",
            min_value=0.0,
            value=default_land_size,
            step=10.0,
            help=(
                "Enter 0 when land size is unknown or not separately "
                "applicable."
            ),
        )

    st.subheader("Purchase")
    purchase_price = st.number_input(
        "Purchase price ($)",
        min_value=0.0,
        value=600_000.0,
        step=10_000.0,
    )
    market_value = st.number_input(
        "Market value / bank valuation ($)",
        min_value=0.0,
        value=600_000.0,
        step=10_000.0,
    )
    deposit = st.number_input(
        "Deposit ($)",
        min_value=0.0,
        value=120_000.0,
        step=5_000.0,
    )

    st.subheader("Loan")
    interest_rate = (
        st.number_input(
            "Interest rate (%)",
            min_value=0.0,
            value=6.0,
            step=0.1,
        )
        / 100
    )
    loan_term_years = st.slider(
        "Loan term (years)",
        5,
        30,
        30,
    )
    loan_type = st.selectbox(
        "Loan structure",
        ["Principal & Interest", "Interest Only"],
    )
    io_years = st.slider(
        "Interest-only period (years)",
        0,
        10,
        5,
        disabled=loan_type != "Interest Only",
    )
    offset_balance = st.number_input(
        "Offset balance ($)",
        min_value=0.0,
        value=0.0,
        step=5_000.0,
    )
    extra_monthly = st.number_input(
        "Extra monthly repayment ($)",
        min_value=0.0,
        value=0.0,
        step=100.0,
    )

    st.subheader("Rent and management")
    weekly_rent = st.number_input(
        "Weekly rent ($)",
        min_value=0.0,
        value=600.0,
        step=10.0,
    )
    vacancy_rate = (
        st.number_input(
            "Vacancy allowance (%)",
            min_value=0.0,
            max_value=100.0,
            value=3.0,
            step=0.5,
        )
        / 100
    )
    management_fee = (
        st.number_input(
            "Rental-agent management fee (%)",
            min_value=0.0,
            max_value=100.0,
            value=7.0,
            step=0.5,
        )
        / 100
    )
    leasing_fees = st.number_input(
        "Leasing, advertising and inspection fees p.a. ($)",
        min_value=0.0,
        value=700.0,
        step=100.0,
    )
    rent_growth = (
        st.number_input(
            "Annual rent growth (%)",
            min_value=-20.0,
            max_value=50.0,
            value=3.0,
            step=0.5,
        )
        / 100
    )

    st.subheader("Property expenses")
    council = st.number_input(
        "Council rates p.a. ($)",
        min_value=0.0,
        value=2_200.0,
        step=100.0,
    )
    water = st.number_input(
        "Owner-paid water charges p.a. ($)",
        min_value=0.0,
        value=900.0,
        step=100.0,
    )
    insurance = st.number_input(
        "Landlord / building insurance p.a. ($)",
        min_value=0.0,
        value=1_800.0,
        step=100.0,
    )

    strata_input = st.number_input(
        "Strata / owners-corporation levies p.a. ($)",
        min_value=0.0,
        value=4_000.0 if strata_applies else 0.0,
        step=100.0,
        disabled=not strata_applies,
    )
    strata = strata_input if strata_applies else 0.0

    special_levies_input = st.number_input(
        "Known special levies p.a. ($)",
        min_value=0.0,
        value=0.0,
        step=500.0,
        disabled=not strata_applies,
    )
    special_levies = (
        special_levies_input if strata_applies else 0.0
    )

    repairs_pct = (
        st.number_input(
            "Repairs and maintenance (% of gross rent)",
            min_value=0.0,
            max_value=100.0,
            value=5.0,
            step=0.5,
        )
        / 100
    )
    land_tax = st.number_input(
        "Land tax p.a. ($)",
        min_value=0.0,
        value=0.0,
        step=100.0,
    )
    accounting = st.number_input(
        "Accounting / tax-return costs p.a. ($)",
        min_value=0.0,
        value=500.0,
        step=100.0,
    )
    other_expenses = st.number_input(
        "Other annual expenses ($)",
        min_value=0.0,
        value=500.0,
        step=100.0,
    )

    st.subheader("Growth, tax and sale")
    capital_growth = (
        st.number_input(
            "Annual capital growth (%)",
            min_value=-20.0,
            max_value=50.0,
            value=5.0,
            step=0.5,
        )
        / 100
    )
    selling_cost_pct = (
        st.number_input(
            "Selling costs (% of sale price)",
            min_value=0.0,
            max_value=20.0,
            value=2.5,
            step=0.1,
        )
        / 100
    )
    marginal_tax_rate = (
        st.number_input(
            "Marginal tax rate (%)",
            min_value=0.0,
            max_value=60.0,
            value=37.0,
            step=1.0,
        )
        / 100
    )
    depreciation = st.number_input(
        "Depreciation deduction p.a. ($)",
        min_value=0.0,
        value=8_000.0,
        step=500.0,
    )
    horizon = st.slider(
        "Decision horizon (years)",
        1,
        30,
        10,
    )

    with st.expander("Duty, LMI and purchase costs"):
        duty_override = st.number_input(
            "Official duty override ($; 0 = automatic)",
            min_value=0.0,
            value=0.0,
            step=500.0,
        )
        concession_reduction = st.number_input(
            "Concession / exemption reduction ($)",
            min_value=0.0,
            value=0.0,
            step=500.0,
        )
        foreign_surcharge = st.number_input(
            "Foreign purchaser surcharge ($)",
            min_value=0.0,
            value=0.0,
            step=500.0,
        )
        lmi_quote = st.number_input(
            "LMI quote from lender / broker ($)",
            min_value=0.0,
            value=0.0,
            step=500.0,
            help="Used only when base LVR exceeds 80%.",
        )
        legal = st.number_input(
            "Legal and conveyancing ($)",
            min_value=0.0,
            value=2_500.0,
            step=100.0,
        )
        inspection = st.number_input(
            "Building and pest inspection ($)",
            min_value=0.0,
            value=700.0,
            step=100.0,
        )
        loan_fees = st.number_input(
            "Loan, valuation and registration fees ($)",
            min_value=0.0,
            value=700.0,
            step=100.0,
        )
        buyers_agent = st.number_input(
            "Buyer's agent fee ($)",
            min_value=0.0,
            value=0.0,
            step=500.0,
        )
        initial_repairs = st.number_input(
            "Initial repairs / renovation ($)",
            min_value=0.0,
            value=0.0,
            step=500.0,
        )
        other_purchase_costs = st.number_input(
            "Other purchase costs ($)",
            min_value=0.0,
            value=500.0,
            step=100.0,
        )


inputs = Inputs(
    property_name=property_name,
    property_type=property_type,
    strata_applies=strata_applies,
    state=state,
    purpose=purpose,
    bedrooms=int(bedrooms),
    bathrooms=float(bathrooms),
    car_spaces=int(car_spaces),
    land_size=float(land_size),
    purchase_price=purchase_price,
    market_value=market_value,
    deposit=deposit,
    interest_rate=interest_rate,
    loan_term_years=loan_term_years,
    loan_type=loan_type,
    io_years=io_years,
    offset_balance=offset_balance,
    extra_monthly=extra_monthly,
    weekly_rent=weekly_rent,
    vacancy_rate=vacancy_rate,
    management_fee=management_fee,
    leasing_fees=leasing_fees,
    rent_growth=rent_growth,
    council=council,
    water=water,
    insurance=insurance,
    strata=strata,
    special_levies=special_levies,
    repairs_pct=repairs_pct,
    land_tax=land_tax,
    accounting=accounting,
    other_expenses=other_expenses,
    capital_growth=capital_growth,
    selling_cost_pct=selling_cost_pct,
    marginal_tax_rate=marginal_tax_rate,
    depreciation=depreciation,
    horizon=horizon,
    duty_override=duty_override,
    concession_reduction=concession_reduction,
    foreign_surcharge=foreign_surcharge,
    lmi_quote=lmi_quote,
    legal=legal,
    inspection=inspection,
    loan_fees=loan_fees,
    buyers_agent=buyers_agent,
    initial_repairs=initial_repairs,
    other_purchase_costs=other_purchase_costs,
)

results = calculate(inputs)
first_year = results["cashflow"].iloc[0]
horizon_result = results["growth"].iloc[horizon - 1]

gross_yield = (
    weekly_rent * 52 / purchase_price
    if purchase_price
    else 0.0
)
net_yield = (
    first_year["Net Operating Income"] / purchase_price
    if purchase_price
    else 0.0
)

after_tax_shortfall = max(
    0.0,
    -first_year["After-tax Cash Flow"],
)
pre_tax_shortfall = max(
    0.0,
    -first_year["Pre-tax Cash Flow"],
)

score, score_breakdown = investment_score(inputs, results)


st.title("All-In-One Property Investment Decision Dashboard by Dr Ash Najmaei")
st.caption(
    "Interactive purchase, loan, rental, cash-flow, tax-effect, "
    "growth and stress-test modelling."
)

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(
    [
        "Executive dashboard",
        "Purchase & loan",
        "Cash flow",
        "Growth & equity",
        "Stress testing",
        "Export",
    ]
)


with tab1:
    metrics = st.columns(4)
    metrics[0].metric(
        "Total cash required",
        money(results["cash_required"]),
    )
    metrics[1].metric(
        "Total loan",
        money(results["total_loan"]),
    )
    metrics[2].metric(
        "Final LVR",
        pct(results["final_lvr"]),
    )
    metrics[3].metric(
        "Duty used",
        money(results["duty_used"]),
    )

    metrics = st.columns(4)
    metrics[0].metric(
        "Gross rental yield",
        pct(gross_yield),
    )
    metrics[1].metric(
        "Net operating yield",
        pct(net_yield),
    )
    metrics[2].metric(
        "Year 1 pre-tax cash flow",
        money(first_year["Pre-tax Cash Flow"]),
    )
    metrics[3].metric(
        "Year 1 after-tax cash flow",
        money(first_year["After-tax Cash Flow"]),
    )

    st.subheader("Estimated out-of-pocket contribution — Year 1")
    metrics = st.columns(4)
    metrics[0].metric(
        "Weekly",
        money2(after_tax_shortfall / 52),
    )
    metrics[1].metric(
        "Fortnightly",
        money2(after_tax_shortfall / 26),
    )
    metrics[2].metric(
        "Monthly",
        money2(after_tax_shortfall / 12),
    )
    metrics[3].metric(
        "Annual",
        money2(after_tax_shortfall),
    )

    st.caption(
        f"Before the estimated tax effect: "
        f"{money2(pre_tax_shortfall / 52)} weekly, "
        f"{money2(pre_tax_shortfall / 26)} fortnightly and "
        f"{money2(pre_tax_shortfall / 12)} monthly."
    )

    metrics = st.columns(4)
    metrics[0].metric(
        f"Value after {horizon} years",
        money(horizon_result["Property Value"]),
    )
    metrics[1].metric(
        f"Equity after {horizon} years",
        money(horizon_result["Gross Equity"]),
    )
    metrics[2].metric(
        f"{horizon}-year total profit",
        money(horizon_result["Total Profit"]),
    )
    metrics[3].metric(
        "Initial monthly loan payment",
        money(results["schedule"].iloc[0]["Total Payment"]),
    )

    st.subheader("Property profile")
    profile = st.columns(4)
    profile[0].metric("Bedrooms", f"{inputs.bedrooms}")
    profile[1].metric("Bathrooms", f"{inputs.bathrooms:g}")
    profile[2].metric("Car spaces", f"{inputs.car_spaces}")
    profile[3].metric(
        "Land size",
        (
            f"{inputs.land_size:,.0f} m²"
            if inputs.land_size > 0
            else "Not entered"
        ),
    )

    st.subheader("LMI treatment")
    if results["base_lvr"] <= 0.80:
        st.success(
            f"Base LVR is {pct(results['base_lvr'])}. "
            "LMI added to the loan: $0 because base LVR is at "
            "or below 80%."
        )
    elif results["lmi_used"] > 0:
        st.warning(
            f"Base LVR is {pct(results['base_lvr'])}. "
            f"The entered LMI quote of "
            f"{money(results['lmi_used'])} has been added "
            "to the loan."
        )
    else:
        st.warning(
            f"Base LVR is {pct(results['base_lvr'])}, above 80%, "
            "but no LMI quote has been entered."
        )

    if score >= 75:
        st.markdown(
            f'<div class="good"><b>Strong on entered assumptions '
            f"— {score:.0f}/100.</b></div>",
            unsafe_allow_html=True,
        )
    elif score >= 55:
        st.markdown(
            f'<div class="warn"><b>Potentially viable but '
            f"assumption-sensitive — {score:.0f}/100.</b></div>",
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f'<div class="bad"><b>Weak on entered assumptions '
            f"— {score:.0f}/100.</b></div>",
            unsafe_allow_html=True,
        )

    with st.expander("How the investment score is calculated"):
        st.dataframe(
            score_breakdown,
            hide_index=True,
            use_container_width=True,
        )
        st.caption(
            "This is an internal feasibility indicator based only "
            "on the assumptions entered. It is not a suburb-quality "
            "score, valuation, market forecast, lending assessment "
            "or recommendation. Bedrooms, bathrooms, car spaces and "
            "land size are recorded but are not awarded points "
            "automatically because their value depends on local "
            "comparable sales and rents."
        )

    left, right = st.columns(2)
    with left:
        fig = px.line(
            results["growth"].head(horizon),
            x="Year",
            y=["Property Value", "Loan Balance", "Gross Equity"],
            title="Value, debt and equity",
        )
        fig.update_layout(
            yaxis_tickprefix="$",
            yaxis_tickformat=",.0f",
            legend_title_text="",
        )
        st.plotly_chart(fig, use_container_width=True)

    with right:
        fig = px.bar(
            results["cashflow"].head(horizon),
            x="Year",
            y="After-tax Cash Flow",
            title="Annual after-tax cash flow",
        )
        fig.update_layout(
            yaxis_tickprefix="$",
            yaxis_tickformat=",.0f",
        )
        st.plotly_chart(fig, use_container_width=True)


with tab2:
    left, right = st.columns(2)

    with left:
        st.subheader("Purchase summary")
        summary = pd.DataFrame(
            {
                "Item": [
                    "Property type",
                    "Bedrooms",
                    "Bathrooms",
                    "Car spaces",
                    "Land size",
                    "Purchase price",
                    "Market value",
                    "Deposit",
                    "Automatic duty estimate",
                    "Duty used",
                    "LMI added",
                    "Other purchase costs",
                    "Total cash required",
                    "Base loan",
                    "Total loan",
                    "Base LVR",
                    "Final LVR",
                ],
                "Value": [
                    inputs.property_type,
                    inputs.bedrooms,
                    f"{inputs.bathrooms:g}",
                    inputs.car_spaces,
                    (
                        f"{inputs.land_size:,.0f} m²"
                        if inputs.land_size > 0
                        else "Not entered"
                    ),
                    money(inputs.purchase_price),
                    money(inputs.market_value),
                    money(inputs.deposit),
                    money(results["automatic_duty"]),
                    money(results["duty_used"]),
                    money(results["lmi_used"]),
                    money(results["other_purchase_costs"]),
                    money(results["cash_required"]),
                    money(results["base_loan"]),
                    money(results["total_loan"]),
                    pct(results["base_lvr"]),
                    pct(results["final_lvr"]),
                ],
            }
        )
        st.dataframe(
            summary,
            hide_index=True,
            use_container_width=True,
        )
        st.info(
            "Duty is a general estimate. Use the override for an "
            "official assessment, concessions, exemptions or "
            "surcharges."
        )

    with right:
        schedule = results["schedule"]
        zero_balance = schedule.loc[
            schedule["Closing Balance"] <= 0.01,
            "Month",
        ]
        months_to_repay = (
            int(zero_balance.min())
            if not zero_balance.empty
            else loan_term_years * 12
        )

        balance_5 = schedule.loc[
            schedule["Month"] == min(60, len(schedule)),
            "Closing Balance",
        ].iloc[0]
        balance_10 = schedule.loc[
            schedule["Month"] == min(120, len(schedule)),
            "Closing Balance",
        ].iloc[0]

        st.subheader("Loan summary")
        loan_summary = pd.DataFrame(
            {
                "Metric": [
                    "Initial scheduled payment",
                    "Initial total payment",
                    "Total interest",
                    "Balance after 5 years",
                    "Balance after 10 years",
                    "Months to repay",
                ],
                "Value": [
                    money(schedule.iloc[0]["Scheduled Payment"]),
                    money(schedule.iloc[0]["Total Payment"]),
                    money(schedule["Interest"].sum()),
                    money(balance_5),
                    money(balance_10),
                    f"{months_to_repay} months",
                ],
            }
        )
        st.dataframe(
            loan_summary,
            hide_index=True,
            use_container_width=True,
        )

    fig = px.line(
        results["schedule"],
        x="Month",
        y="Closing Balance",
        title="Loan amortisation",
    )
    fig.update_layout(
        yaxis_tickprefix="$",
        yaxis_tickformat=",.0f",
    )
    st.plotly_chart(fig, use_container_width=True)

    with st.expander("View monthly amortisation schedule"):
        st.dataframe(
            results["schedule"],
            use_container_width=True,
            height=500,
        )


with tab3:
    cashflow = results["cashflow"].head(horizon)

    fig = go.Figure()
    fig.add_bar(
        x=cashflow["Year"],
        y=cashflow["Pre-tax Cash Flow"],
        name="Pre-tax",
    )
    fig.add_bar(
        x=cashflow["Year"],
        y=cashflow["After-tax Cash Flow"],
        name="After-tax",
    )
    fig.update_layout(
        barmode="group",
        yaxis_tickprefix="$",
        yaxis_tickformat=",.0f",
        title="Annual cash flow",
    )
    st.plotly_chart(fig, use_container_width=True)

    expense_fields = [
        "Management Fee",
        "Leasing / Advertising",
        "Council Rates",
        "Water Charges",
        "Insurance",
        "Strata Levies",
        "Special Levies",
        "Repairs / Maintenance",
        "Land Tax",
        "Accounting",
        "Other Expenses",
        "Loan Payments",
    ]
    expenses = pd.DataFrame(
        {
            "Expense": expense_fields,
            "Annual amount": [
                abs(float(first_year[field]))
                for field in expense_fields
            ],
        }
    )
    expenses = expenses[expenses["Annual amount"] > 0]

    fig = px.bar(
        expenses,
        x="Annual amount",
        y="Expense",
        orientation="h",
        title="Year 1 expenses and loan payments",
    )
    fig.update_layout(
        xaxis_tickprefix="$",
        xaxis_tickformat=",.0f",
    )
    st.plotly_chart(fig, use_container_width=True)

    st.dataframe(
        cashflow,
        use_container_width=True,
        height=550,
    )


with tab4:
    growth = results["growth"].head(horizon)
    left, right = st.columns(2)

    with left:
        fig = px.area(
            growth,
            x="Year",
            y="Gross Equity",
            title="Equity accumulation",
        )
        fig.update_layout(
            yaxis_tickprefix="$",
            yaxis_tickformat=",.0f",
        )
        st.plotly_chart(fig, use_container_width=True)

    with right:
        fig = px.line(
            growth,
            x="Year",
            y="Total Profit",
            markers=True,
            title="Total investment profit",
        )
        fig.update_layout(
            yaxis_tickprefix="$",
            yaxis_tickformat=",.0f",
        )
        st.plotly_chart(fig, use_container_width=True)

    st.dataframe(
        growth,
        use_container_width=True,
    )


with tab5:
    stress_rows = []

    for rate in np.arange(0.04, 0.101, 0.005):
        stressed_results = calculate(
            replace(inputs, interest_rate=float(rate))
        )
        stressed_cashflow = stressed_results["cashflow"].iloc[0]

        stress_rows.append(
            {
                "Interest Rate": rate,
                "Initial Monthly Payment": stressed_results[
                    "schedule"
                ].iloc[0]["Total Payment"],
                "Year 1 After-tax Cash Flow": stressed_cashflow[
                    "After-tax Cash Flow"
                ],
                "Weekly Out-of-pocket": (
                    max(
                        0.0,
                        -stressed_cashflow["After-tax Cash Flow"],
                    )
                    / 52
                ),
            }
        )

    stress = pd.DataFrame(stress_rows)
    left, right = st.columns(2)

    with left:
        fig = px.line(
            stress,
            x="Interest Rate",
            y="Initial Monthly Payment",
            markers=True,
            title="Monthly repayment sensitivity",
        )
        fig.update_layout(
            xaxis_tickformat=".1%",
            yaxis_tickprefix="$",
            yaxis_tickformat=",.0f",
        )
        st.plotly_chart(fig, use_container_width=True)

    with right:
        fig = px.line(
            stress,
            x="Interest Rate",
            y="Weekly Out-of-pocket",
            markers=True,
            title="Weekly out-of-pocket sensitivity",
        )
        fig.update_layout(
            xaxis_tickformat=".1%",
            yaxis_tickprefix="$",
            yaxis_tickformat=",.0f",
        )
        st.plotly_chart(fig, use_container_width=True)

    growth_rates = np.arange(0.0, 0.081, 0.01)
    growth_sensitivity = pd.DataFrame(
        {
            "Growth Rate": growth_rates,
            f"Value after {horizon} years": [
                purchase_price * (1 + rate) ** horizon
                for rate in growth_rates
            ],
        }
    )

    fig = px.line(
        growth_sensitivity,
        x="Growth Rate",
        y=f"Value after {horizon} years",
        markers=True,
        title="Capital-growth sensitivity",
    )
    fig.update_layout(
        xaxis_tickformat=".0%",
        yaxis_tickprefix="$",
        yaxis_tickformat=",.0f",
    )
    st.plotly_chart(fig, use_container_width=True)


with tab6:
    st.download_button(
        "Download executive report (HTML)",
        report_html(inputs, results, score),
        "property_investment_report.html",
        "text/html",
        use_container_width=True,
    )

    export_left, export_middle, export_right = st.columns(3)

    export_left.download_button(
        "Download loan schedule CSV",
        results["schedule"].to_csv(index=False).encode(),
        "loan_schedule.csv",
        "text/csv",
        use_container_width=True,
    )
    export_middle.download_button(
        "Download cash-flow CSV",
        results["cashflow"].to_csv(index=False).encode(),
        "cash_flow.csv",
        "text/csv",
        use_container_width=True,
    )
    export_right.download_button(
        "Download growth analysis CSV",
        results["growth"].to_csv(index=False).encode(),
        "growth_and_returns.csv",
        "text/csv",
        use_container_width=True,
    )

    st.download_button(
        "Download assumptions CSV",
        pd.DataFrame([asdict(inputs)]).to_csv(index=False).encode(),
        "property_assumptions.csv",
        "text/csv",
        use_container_width=True,
    )

    st.download_button(
        "Download score breakdown CSV",
        score_breakdown.to_csv(index=False).encode(),
        "investment_score_breakdown.csv",
        "text/csv",
        use_container_width=True,
    )


st.divider()
st.caption(
    "General modelling only—not financial, tax, legal, valuation, "
    "insurance or lending advice. Verify duty, LMI, tax treatment, "
    "council and water charges, strata levies, land tax, rent and "
    "finance terms independently."
)
