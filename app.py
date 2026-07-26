import math
from dataclasses import dataclass, asdict, replace

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title="Property Investment Dashboard", page_icon="🏠", layout="wide")
st.markdown("""
<style>
.block-container{padding-top:1rem;padding-bottom:2rem}
[data-testid="stSidebar"]{min-width:330px;max-width:330px}
[data-testid="stMetric"]{background:#f5f8fc;border:1px solid #d7e1ec;padding:14px;border-radius:10px}
.good{background:#e8f5e9;padding:14px;border-radius:8px;border-left:5px solid #2e7d32}
.warn{background:#fff8e1;padding:14px;border-radius:8px;border-left:5px solid #f9a825}
.bad{background:#ffebee;padding:14px;border-radius:8px;border-left:5px solid #c62828}
</style>
""", unsafe_allow_html=True)


def money(v): return f"${v:,.0f}"
def money2(v): return f"${v:,.2f}"
def pct(v): return f"{v:.1%}"
def marginal(v, lower, base, rate): return base + max(0.0, v-lower)*rate


def estimate_duty(state, value):
    v=max(0.0,float(value))
    if state=="NSW":
        if v<=18000:return max(20,v*.0125)
        if v<=38000:return marginal(v,18000,225,.015)
        if v<=103000:return marginal(v,38000,525,.0175)
        if v<=387000:return marginal(v,103000,1662,.035)
        if v<=1290000:return marginal(v,387000,11602,.045)
        if v<=3870000:return marginal(v,1290000,52237,.055)
        return marginal(v,3870000,194137,.07)
    if state=="VIC":
        if v<=25000:return v*.014
        if v<=130000:return marginal(v,25000,350,.024)
        if v<=960000:return marginal(v,130000,2870,.06)
        if v<=2000000:return v*.055
        return marginal(v,2000000,110000,.065)
    if state=="QLD":
        if v<=5000:return 0
        if v<=75000:return (v-5000)*.015
        if v<=540000:return marginal(v,75000,1050,.035)
        if v<=1000000:return marginal(v,540000,17325,.045)
        return marginal(v,1000000,38025,.0575)
    if state=="WA":
        if v<=120000:return v*.019
        if v<=150000:return marginal(v,120000,2280,.0285)
        if v<=360000:return marginal(v,150000,3135,.038)
        if v<=725000:return marginal(v,360000,11115,.0475)
        return marginal(v,725000,28452.5,.0515)
    if state=="SA":
        bands=[(12000,0,0,.01),(30000,12000,120,.02),(50000,30000,480,.03),(100000,50000,1080,.035),(200000,100000,2830,.04),(250000,200000,6830,.0425),(300000,250000,8955,.0475),(500000,300000,11330,.05),(float('inf'),500000,21330,.055)]
        for upper,lower,base,rate in bands:
            if v<=upper:return marginal(v,lower,base,rate)
    if state=="TAS":
        if v<=1300:return 20
        if v<=10000:return v*.015
        if v<=30000:return marginal(v,10000,150,.02)
        if v<=75000:return marginal(v,30000,550,.025)
        if v<=150000:return marginal(v,75000,1675,.03)
        if v<=225000:return marginal(v,150000,3925,.035)
        if v<=375000:return marginal(v,225000,6550,.04)
        return marginal(v,375000,12550,.045)
    if state=="ACT":
        if v<=200000:return v*.012
        if v<=300000:return marginal(v,200000,2400,.022)
        if v<=500000:return marginal(v,300000,4600,.034)
        if v<=750000:return marginal(v,500000,11400,.0432)
        if v<=1000000:return marginal(v,750000,22200,.059)
        if v<=1455000:return marginal(v,1000000,36950,.064)
        return v*.0454
    if state=="NT":
        if v<=525000:
            x=v/1000
            return (0.06571441*x*x+15*x)*1000
        if v<=3000000:return v*.0495
        if v<=5000000:return v*.0575
        return v*.0595
    return 0


@dataclass
class Inputs:
    property_name:str; property_type:str; strata_applies:bool; state:str; purpose:str
    purchase_price:float; market_value:float; deposit:float
    interest_rate:float; loan_term_years:int; loan_type:str; io_years:int; offset_balance:float; extra_monthly:float
    weekly_rent:float; vacancy_rate:float; management_fee:float; leasing_fees:float; rent_growth:float
    council:float; water:float; insurance:float; strata:float; special_levies:float; repairs_pct:float; land_tax:float; accounting:float; other_expenses:float
    capital_growth:float; selling_cost_pct:float; marginal_tax_rate:float; depreciation:float; horizon:int
    duty_override:float; concession_reduction:float; foreign_surcharge:float; lmi_quote:float
    legal:float; inspection:float; loan_fees:float; buyers_agent:float; initial_repairs:float; other_purchase_costs:float


def loan_info(x):
    base_loan=max(0.0,x.purchase_price-x.deposit)
    base_lvr=base_loan/x.market_value if x.market_value else 0
    lmi_used=max(0.0,x.lmi_quote) if base_lvr>.80 else 0.0
    total_loan=base_loan+lmi_used
    return base_loan,base_lvr,lmi_used,total_loan,(total_loan/x.market_value if x.market_value else 0)


def loan_schedule(x):
    base_loan,base_lvr,lmi,total_loan,final_lvr=loan_info(x)
    mr=x.interest_rate/12; months=x.loan_term_years*12; bal=total_loan; rows=[]; cum=0
    for m in range(1,months+1):
        opening=bal; interest=max(0,opening-x.offset_balance)*mr
        if opening<=.005:
            scheduled=extra=principal=closing=0
        elif x.loan_type=="Interest Only" and m<=x.io_years*12:
            scheduled=interest; extra=min(x.extra_monthly,opening); principal=extra; closing=max(0,opening-principal)
        else:
            rem=max(1,months-m+1)
            scheduled=opening/rem if mr==0 else opening*mr*(1+mr)**rem/((1+mr)**rem-1)
            extra=min(x.extra_monthly,opening)
            principal=min(opening,max(0,scheduled-interest)+extra)
            closing=max(0,opening-principal)
        cum+=interest
        rows.append({"Month":m,"Year":math.ceil(m/12),"Opening Balance":opening,"Scheduled Payment":scheduled,"Extra Payment":extra,"Total Payment":scheduled+extra,"Interest":interest,"Principal":principal,"Closing Balance":closing,"Offset Balance":x.offset_balance,"Cumulative Interest":cum})
        bal=closing
    return pd.DataFrame(rows)


def calculate(x):
    base_loan,base_lvr,lmi_used,total_loan,final_lvr=loan_info(x)
    auto_duty=estimate_duty(x.state,max(x.purchase_price,x.market_value))
    duty=x.duty_override if x.duty_override>0 else max(0,auto_duty-x.concession_reduction+x.foreign_surcharge)
    other_purchase=sum([x.legal,x.inspection,x.loan_fees,x.buyers_agent,x.initial_repairs,x.other_purchase_costs])
    purchase_costs=duty+lmi_used+other_purchase
    cash_required=x.deposit+purchase_costs
    sched=loan_schedule(x)
    annual_interest=sched.groupby("Year",as_index=False)["Interest"].sum()
    annual_balance=sched.groupby("Year",as_index=False)["Closing Balance"].last()
    annual_payment=sched.groupby("Year",as_index=False)["Total Payment"].sum()
    crows=[]; grows=[]; cumulative_cf=0
    for y in range(1,x.loan_term_years+1):
        esc=(1+x.rent_growth)**(y-1)
        gross=x.weekly_rent*52*esc; vacancy=gross*x.vacancy_rate; effective=gross-vacancy
        mgmt=effective*x.management_fee; leasing=x.leasing_fees*esc; council=x.council*esc; water=x.water*esc; insurance=x.insurance*esc
        strata=x.strata*esc if x.strata_applies else 0; special=x.special_levies if x.strata_applies else 0
        repairs=gross*x.repairs_pct; other=x.other_expenses*esc
        interest=float(annual_interest.loc[annual_interest.Year==y,"Interest"].sum())
        payments=float(annual_payment.loc[annual_payment.Year==y,"Total Payment"].sum())
        operating=sum([mgmt,leasing,council,water,insurance,strata,special,repairs,x.land_tax,x.accounting,other])
        noi=effective-operating
        pre_tax=noi-payments
        taxable=effective-operating-interest-x.depreciation
        tax_effect=-taxable*x.marginal_tax_rate
        after_tax=pre_tax+tax_effect
        cumulative_cf+=after_tax
        crows.append({"Year":y,"Gross Rent":gross,"Vacancy":-vacancy,"Effective Rent":effective,"Management Fee":-mgmt,"Leasing / Advertising":-leasing,"Council Rates":-council,"Water Charges":-water,"Insurance":-insurance,"Strata Levies":-strata,"Special Levies":-special,"Repairs / Maintenance":-repairs,"Land Tax":-x.land_tax,"Accounting":-x.accounting,"Other Expenses":-other,"Net Operating Income":noi,"Loan Payments":-payments,"Loan Interest":-interest,"Pre-tax Cash Flow":pre_tax,"Depreciation":-x.depreciation,"Taxable Result":taxable,"Estimated Tax Effect":tax_effect,"After-tax Cash Flow":after_tax})
        value=x.purchase_price*(1+x.capital_growth)**y
        balance=float(annual_balance.loc[annual_balance.Year==y,"Closing Balance"].iloc[0])
        equity=value-balance; selling=value*x.selling_cost_pct; net_sale=value-selling-balance
        profit=net_sale+cumulative_cf-cash_required
        grows.append({"Year":y,"Property Value":value,"Loan Balance":balance,"Gross Equity":equity,"Selling Costs":-selling,"Net Sale Proceeds":net_sale,"Cumulative After-tax Cash Flow":cumulative_cf,"Total Profit":profit,"Cash-on-Cash Return":profit/cash_required if cash_required else 0})
    return {"base_loan":base_loan,"base_lvr":base_lvr,"lmi_used":lmi_used,"total_loan":total_loan,"final_lvr":final_lvr,"automatic_duty":auto_duty,"duty_used":duty,"other_purchase_costs":other_purchase,"purchase_costs":purchase_costs,"cash_required":cash_required,"schedule":sched,"cashflow":pd.DataFrame(crows),"growth":pd.DataFrame(grows)}


def report_html(x,r):
    h=min(x.horizon,len(r["growth"])); c=r["cashflow"].iloc[0]; g=r["growth"].iloc[h-1]; short=max(0,-c["After-tax Cash Flow"])
    fields={
        "Property":x.property_name,
        "Property type":x.property_type,
        "Strata applies":"Yes" if x.strata_applies else "No",
        "State":x.state,
        "Purchase price":money(x.purchase_price),
        "Deposit":money(x.deposit),
        "Weekly rent":money2(x.weekly_rent),
        "Base LVR":pct(r["base_lvr"]),
        "Final LVR":pct(r["final_lvr"]),
        "LMI added":money(r["lmi_used"]),
        "Total loan":money(r["total_loan"]),
        "Duty used":money(r["duty_used"]),
        "Total cash required":money(r["cash_required"]),
        "Year 1 pre-tax cash flow":money(c["Pre-tax Cash Flow"]),
        "Year 1 after-tax cash flow":money(c["After-tax Cash Flow"]),
        "Weekly out-of-pocket":money2(short/52),
        "Fortnightly out-of-pocket":money2(short/26),
        "Monthly out-of-pocket":money2(short/12),
        f"Value after {h} years":money(g["Property Value"]),
        f"Equity after {h} years":money(g["Gross Equity"]),
        f"Total profit after {h} years":money(g["Total Profit"])
    }
    rows=''.join(f'<tr><th>{k}</th><td>{v}</td></tr>' for k,v in fields.items())
    return f'<html><head><meta charset="utf-8"><style>body{{font-family:Arial;max-width:900px;margin:40px auto;color:#17324d}}table{{border-collapse:collapse;width:100%}}th,td{{padding:10px;border-bottom:1px solid #ddd;text-align:left}}th{{background:#f5f7fa}}</style></head><body><h1>Property Investment Decision Report</h1><table>{rows}</table><p>General modelling only. Verify duty, LMI, tax, rent, strata, land tax and finance terms independently.</p></body></html>'


st.sidebar.title("🏠 Property inputs")
with st.sidebar:
    property_name=st.text_input("Property name or address","Example investment property")
    property_type=st.selectbox("Property type",["House","Apartment / Unit","Townhouse","Villa","Duplex","Terrace","Vacant Land","Other"])
    default_strata=property_type in {"Apartment / Unit","Townhouse","Villa"}
    strata_applies=st.checkbox("Strata / owners corporation applies",value=default_strata)
    state=st.selectbox("State / Territory",["NSW","VIC","QLD","WA","SA","TAS","ACT","NT"])
    purpose=st.selectbox("Property purpose",["Investment","Owner Occupier"])

    st.subheader("Purchase")
    purchase_price=st.number_input("Purchase price ($)",0.0,value=1_000_000.0,step=10_000.0)
    market_value=st.number_input("Market value / bank valuation ($)",0.0,value=1_000_000.0,step=10_000.0)
    deposit=st.number_input("Deposit ($)",0.0,value=200_000.0,step=5_000.0)

    st.subheader("Loan")
    interest_rate=st.number_input("Interest rate (%)",0.0,value=6.0,step=.1)/100
    loan_term_years=st.slider("Loan term (years)",5,30,30)
    loan_type=st.selectbox("Loan structure",["Principal & Interest","Interest Only"])
    io_years=st.slider("Interest-only period (years)",0,10,5,disabled=loan_type!="Interest Only")
    offset_balance=st.number_input("Offset balance ($)",0.0,value=0.0,step=5_000.0)
    extra_monthly=st.number_input("Extra monthly repayment ($)",0.0,value=0.0,step=100.0)

    st.subheader("Rent and management")
    weekly_rent=st.number_input("Weekly rent ($)",0.0,value=850.0,step=10.0)
    vacancy_rate=st.number_input("Vacancy allowance (%)",0.0,100.0,3.0,.5)/100
    management_fee=st.number_input("Rental-agent management fee (%)",0.0,100.0,7.0,.5)/100
    leasing_fees=st.number_input("Leasing, advertising and inspection fees p.a. ($)",0.0,value=700.0,step=100.0)
    rent_growth=st.number_input("Annual rent growth (%)",-20.0,50.0,3.0,.5)/100

    st.subheader("Property expenses")
    council=st.number_input("Council rates p.a. ($)",0.0,value=2200.0,step=100.0)
    water=st.number_input("Owner-paid water charges p.a. ($)",0.0,value=900.0,step=100.0)
    insurance=st.number_input("Landlord / building insurance p.a. ($)",0.0,value=1800.0,step=100.0)
    strata_input=st.number_input("Strata / owners-corporation levies p.a. ($)",0.0,value=4000.0 if strata_applies else 0.0,step=100.0,disabled=not strata_applies)
    strata=strata_input if strata_applies else 0.0
    special_input=st.number_input("Known special levies p.a. ($)",0.0,value=0.0,step=500.0,disabled=not strata_applies)
    special_levies=special_input if strata_applies else 0.0
    repairs_pct=st.number_input("Repairs and maintenance (% of gross rent)",0.0,100.0,5.0,.5)/100
    land_tax=st.number_input("Land tax p.a. ($)",0.0,value=0.0,step=100.0)
    accounting=st.number_input("Accounting / tax-return costs p.a. ($)",0.0,value=500.0,step=100.0)
    other_expenses=st.number_input("Other annual expenses ($)",0.0,value=500.0,step=100.0)

    st.subheader("Growth, tax and sale")
    capital_growth=st.number_input("Annual capital growth (%)",-20.0,50.0,5.0,.5)/100
    selling_cost_pct=st.number_input("Selling costs (% of sale price)",0.0,20.0,2.5,.1)/100
    marginal_tax_rate=st.number_input("Marginal tax rate (%)",0.0,60.0,37.0,1.0)/100
    depreciation=st.number_input("Depreciation deduction p.a. ($)",0.0,value=8000.0,step=500.0)
    horizon=st.slider("Decision horizon (years)",1,30,10)

    with st.expander("Duty, LMI and purchase costs"):
        duty_override=st.number_input("Official duty override ($; 0 = automatic)",0.0,value=0.0,step=500.0)
        concession_reduction=st.number_input("Concession / exemption reduction ($)",0.0,value=0.0,step=500.0)
        foreign_surcharge=st.number_input("Foreign purchaser surcharge ($)",0.0,value=0.0,step=500.0)
        lmi_quote=st.number_input("LMI quote from lender / broker ($)",0.0,value=0.0,step=500.0,help="Used only when base LVR exceeds 80%.")
        legal=st.number_input("Legal and conveyancing ($)",0.0,value=2500.0,step=100.0)
        inspection=st.number_input("Building and pest inspection ($)",0.0,value=700.0,step=100.0)
        loan_fees=st.number_input("Loan, valuation and registration fees ($)",0.0,value=700.0,step=100.0)
        buyers_agent=st.number_input("Buyer's agent fee ($)",0.0,value=0.0,step=500.0)
        initial_repairs=st.number_input("Initial repairs / renovation ($)",0.0,value=0.0,step=500.0)
        other_purchase_costs=st.number_input("Other purchase costs ($)",0.0,value=500.0,step=100.0)

x=Inputs(property_name,property_type,strata_applies,state,purpose,purchase_price,market_value,deposit,interest_rate,loan_term_years,loan_type,io_years,offset_balance,extra_monthly,weekly_rent,vacancy_rate,management_fee,leasing_fees,rent_growth,council,water,insurance,strata,special_levies,repairs_pct,land_tax,accounting,other_expenses,capital_growth,selling_cost_pct,marginal_tax_rate,depreciation,horizon,duty_override,concession_reduction,foreign_surcharge,lmi_quote,legal,inspection,loan_fees,buyers_agent,initial_repairs,other_purchase_costs)
r=calculate(x); c=r["cashflow"].iloc[0]; g=r["growth"].iloc[horizon-1]
gross_yield=weekly_rent*52/purchase_price if purchase_price else 0
net_yield=c["Net Operating Income"]/purchase_price if purchase_price else 0
after_short=max(0,-c["After-tax Cash Flow"]); pre_short=max(0,-c["Pre-tax Cash Flow"])

st.title("All-in-One Property Investment Decision Dashboard By Dr Arash")
st.caption("Interactive purchase, loan, rental, cash-flow, tax-effect, growth and stress-test modelling.")
t1,t2,t3,t4,t5,t6=st.tabs(["Executive dashboard","Purchase & loan","Cash flow","Growth & equity","Stress testing","Export"])

with t1:
    a=st.columns(4); a[0].metric("Total cash required",money(r["cash_required"])); a[1].metric("Total loan",money(r["total_loan"])); a[2].metric("Final LVR",pct(r["final_lvr"])); a[3].metric("Duty used",money(r["duty_used"]))
    a=st.columns(4); a[0].metric("Gross rental yield",pct(gross_yield)); a[1].metric("Net operating yield",pct(net_yield)); a[2].metric("Year 1 pre-tax cash flow",money(c["Pre-tax Cash Flow"])); a[3].metric("Year 1 after-tax cash flow",money(c["After-tax Cash Flow"]))
    st.subheader("Estimated out-of-pocket contribution — Year 1")
    a=st.columns(4); a[0].metric("Weekly",money2(after_short/52)); a[1].metric("Fortnightly",money2(after_short/26)); a[2].metric("Monthly",money2(after_short/12)); a[3].metric("Annual",money2(after_short))
    st.caption(f"Before the estimated tax effect: {money2(pre_short/52)} weekly, {money2(pre_short/26)} fortnightly and {money2(pre_short/12)} monthly.")
    a=st.columns(4); a[0].metric(f"Value after {horizon} years",money(g["Property Value"])); a[1].metric(f"Equity after {horizon} years",money(g["Gross Equity"])); a[2].metric(f"{horizon}-year total profit",money(g["Total Profit"])); a[3].metric("Initial monthly loan payment",money(r["schedule"].iloc[0]["Total Payment"]))
    st.subheader("LMI treatment")
    if r["base_lvr"]<=.80: st.success(f"Base LVR is {pct(r['base_lvr'])}. LMI added to the loan: $0 because the base LVR is at or below 80%.")
    elif r["lmi_used"]>0: st.warning(f"Base LVR is {pct(r['base_lvr'])}. The entered LMI quote of {money(r['lmi_used'])} has been added to the loan.")
    else: st.warning(f"Base LVR is {pct(r['base_lvr'])}, above 80%, but no LMI quote has been entered.")
    score=max(0,min(100,(25 if r["final_lvr"]<=.8 else max(0,25-(r["final_lvr"]-.8)*100))+(20 if gross_yield>=.05 else gross_yield/.05*20)+(20 if c["After-tax Cash Flow"]>=0 else max(0,20+c["After-tax Cash Flow"]/max(1,weekly_rent*52)*20))+(20 if g["Total Profit"]>0 else 0)+(15 if capital_growth>=.04 else max(0,capital_growth/.04*15))))
    if score>=75: st.markdown(f'<div class="good"><b>Strong on entered assumptions — {score:.0f}/100.</b></div>',unsafe_allow_html=True)
    elif score>=55: st.markdown(f'<div class="warn"><b>Potentially viable but assumption-sensitive — {score:.0f}/100.</b></div>',unsafe_allow_html=True)
    else: st.markdown(f'<div class="bad"><b>Weak on entered assumptions — {score:.0f}/100.</b></div>',unsafe_allow_html=True)
    left,right=st.columns(2)
    with left:
        fig=px.line(r["growth"].head(horizon),x="Year",y=["Property Value","Loan Balance","Gross Equity"],title="Value, debt and equity"); fig.update_layout(yaxis_tickprefix="$",yaxis_tickformat=",.0f",legend_title_text=""); st.plotly_chart(fig,use_container_width=True)
    with right:
        fig=px.bar(r["cashflow"].head(horizon),x="Year",y="After-tax Cash Flow",title="Annual after-tax cash flow"); fig.update_layout(yaxis_tickprefix="$",yaxis_tickformat=",.0f"); st.plotly_chart(fig,use_container_width=True)

with t2:
    left,right=st.columns(2)
    with left:
        st.subheader("Purchase summary")
        summary=pd.DataFrame({"Item":["Property type","Purchase price","Market value","Deposit","Automatic duty estimate","Duty used","LMI added","Other purchase costs","Total cash required","Base loan","Total loan","Base LVR","Final LVR"],"Value":[x.property_type,money(x.purchase_price),money(x.market_value),money(x.deposit),money(r["automatic_duty"]),money(r["duty_used"]),money(r["lmi_used"]),money(r["other_purchase_costs"]),money(r["cash_required"]),money(r["base_loan"]),money(r["total_loan"]),pct(r["base_lvr"]),pct(r["final_lvr"])]}); st.dataframe(summary,hide_index=True,use_container_width=True)
        st.info("Duty is a general estimate. Use the override for an official assessment, concessions, exemptions or surcharges.")
    with right:
        s=r["schedule"]; zero=s.loc[s["Closing Balance"]<=.01,"Month"]; months=int(zero.min()) if not zero.empty else loan_term_years*12
        st.subheader("Loan summary")
        sm=pd.DataFrame({"Metric":["Initial scheduled payment","Initial total payment","Total interest","Balance after 5 years","Balance after 10 years","Months to repay"],"Value":[money(s.iloc[0]["Scheduled Payment"]),money(s.iloc[0]["Total Payment"]),money(s["Interest"].sum()),money(s.loc[s.Month==min(60,len(s)),"Closing Balance"].iloc[0]),money(s.loc[s.Month==min(120,len(s)),"Closing Balance"].iloc[0]),f"{months} months"]}); st.dataframe(sm,hide_index=True,use_container_width=True)
    fig=px.line(r["schedule"],x="Month",y="Closing Balance",title="Loan amortisation"); fig.update_layout(yaxis_tickprefix="$",yaxis_tickformat=",.0f"); st.plotly_chart(fig,use_container_width=True)
    with st.expander("View monthly amortisation schedule"): st.dataframe(r["schedule"],use_container_width=True,height=500)

with t3:
    d=r["cashflow"].head(horizon); fig=go.Figure(); fig.add_bar(x=d.Year,y=d["Pre-tax Cash Flow"],name="Pre-tax"); fig.add_bar(x=d.Year,y=d["After-tax Cash Flow"],name="After-tax"); fig.update_layout(barmode="group",yaxis_tickprefix="$",yaxis_tickformat=",.0f"); st.plotly_chart(fig,use_container_width=True)
    expense_fields=["Management Fee","Leasing / Advertising","Council Rates","Water Charges","Insurance","Strata Levies","Special Levies","Repairs / Maintenance","Land Tax","Accounting","Other Expenses","Loan Payments"]
    expenses=pd.DataFrame({"Expense":expense_fields,"Annual amount":[abs(float(c[f])) for f in expense_fields]}); expenses=expenses[expenses["Annual amount"]>0]
    fig=px.bar(expenses,x="Annual amount",y="Expense",orientation="h",title="Year 1 expenses and loan payments"); fig.update_layout(xaxis_tickprefix="$",xaxis_tickformat=",.0f"); st.plotly_chart(fig,use_container_width=True)
    st.dataframe(d,use_container_width=True,height=550)

with t4:
    d=r["growth"].head(horizon); left,right=st.columns(2)
    with left:
        fig=px.area(d,x="Year",y="Gross Equity",title="Equity accumulation"); fig.update_layout(yaxis_tickprefix="$",yaxis_tickformat=",.0f"); st.plotly_chart(fig,use_container_width=True)
    with right:
        fig=px.line(d,x="Year",y="Total Profit",markers=True,title="Total investment profit"); fig.update_layout(yaxis_tickprefix="$",yaxis_tickformat=",.0f"); st.plotly_chart(fig,use_container_width=True)
    st.dataframe(d,use_container_width=True)

with t5:
    rows=[]
    for rate in np.arange(.04,.101,.005):
        rr=calculate(replace(x,interest_rate=float(rate))); cc=rr["cashflow"].iloc[0]
        rows.append({"Interest Rate":rate,"Initial Monthly Payment":rr["schedule"].iloc[0]["Total Payment"],"Year 1 After-tax Cash Flow":cc["After-tax Cash Flow"],"Weekly Out-of-pocket":max(0,-cc["After-tax Cash Flow"])/52})
    stress=pd.DataFrame(rows); left,right=st.columns(2)
    with left:
        fig=px.line(stress,x="Interest Rate",y="Initial Monthly Payment",markers=True,title="Monthly repayment sensitivity"); fig.update_layout(xaxis_tickformat=".1%",yaxis_tickprefix="$",yaxis_tickformat=",.0f"); st.plotly_chart(fig,use_container_width=True)
    with right:
        fig=px.line(stress,x="Interest Rate",y="Weekly Out-of-pocket",markers=True,title="Weekly out-of-pocket sensitivity"); fig.update_layout(xaxis_tickformat=".1%",yaxis_tickprefix="$",yaxis_tickformat=",.0f"); st.plotly_chart(fig,use_container_width=True)
    growth_rates=np.arange(0,.081,.01); gs=pd.DataFrame({"Growth Rate":growth_rates,f"Value after {horizon} years":[purchase_price*(1+z)**horizon for z in growth_rates]})
    fig=px.line(gs,x="Growth Rate",y=f"Value after {horizon} years",markers=True,title="Capital-growth sensitivity"); fig.update_layout(xaxis_tickformat=".0%",yaxis_tickprefix="$",yaxis_tickformat=",.0f"); st.plotly_chart(fig,use_container_width=True)

with t6:
    st.download_button("Download executive report (HTML)",report_html(x,r),"property_investment_report.html","text/html",use_container_width=True)
    a,b,c=st.columns(3)
    a.download_button("Download loan schedule CSV",r["schedule"].to_csv(index=False).encode(),"loan_schedule.csv","text/csv",use_container_width=True)
    b.download_button("Download cash-flow CSV",r["cashflow"].to_csv(index=False).encode(),"cash_flow.csv","text/csv",use_container_width=True)
    c.download_button("Download growth analysis CSV",r["growth"].to_csv(index=False).encode(),"growth_and_returns.csv","text/csv",use_container_width=True)
    st.download_button("Download assumptions CSV",pd.DataFrame([asdict(x)]).to_csv(index=False).encode(),"property_assumptions.csv","text/csv",use_container_width=True)

st.divider()
st.caption("General modelling only—not financial, tax, legal, valuation, insurance or lending advice. Verify duty, LMI, tax treatment, council and water charges, strata levies, land tax, rent and finance terms independently.")
