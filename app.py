import math
from dataclasses import dataclass, asdict
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title='Property Investment Dashboard', page_icon='🏠', layout='wide')
st.markdown('''<style>[data-testid="stMetric"]{background:#f6f8fb;border:1px solid #d9e2ec;padding:14px;border-radius:10px}.good{background:#e8f5e9;padding:12px;border-radius:8px;border-left:5px solid #2e7d32}.warn{background:#fff8e1;padding:12px;border-radius:8px;border-left:5px solid #f9a825}.bad{background:#ffebee;padding:12px;border-radius:8px;border-left:5px solid #c62828}</style>''', unsafe_allow_html=True)

def marginal(v, lower, base, rate): return base + max(0.0, v-lower)*rate

def estimate_duty(state, v):
    v=max(0.0,float(v))
    if state=='NSW':
        if v<=18000:return max(20,v*.0125)
        if v<=38000:return marginal(v,18000,225,.015)
        if v<=103000:return marginal(v,38000,525,.0175)
        if v<=387000:return marginal(v,103000,1662,.035)
        if v<=1290000:return marginal(v,387000,11602,.045)
        if v<=3870000:return marginal(v,1290000,52237,.055)
        return marginal(v,3870000,194137,.07)
    if state=='VIC':
        if v<=25000:return v*.014
        if v<=130000:return marginal(v,25000,350,.024)
        if v<=960000:return marginal(v,130000,2870,.06)
        if v<=2000000:return v*.055
        return marginal(v,2000000,110000,.065)
    if state=='QLD':
        if v<=5000:return 0
        if v<=75000:return (v-5000)*.015
        if v<=540000:return marginal(v,75000,1050,.035)
        if v<=1000000:return marginal(v,540000,17325,.045)
        return marginal(v,1000000,38025,.0575)
    if state=='WA':
        if v<=120000:return v*.019
        if v<=150000:return marginal(v,120000,2280,.0285)
        if v<=360000:return marginal(v,150000,3135,.038)
        if v<=725000:return marginal(v,360000,11115,.0475)
        return marginal(v,725000,28452.5,.0515)
    if state=='SA':
        bands=[(12000,0,0,.01),(30000,12000,120,.02),(50000,30000,480,.03),(100000,50000,1080,.035),(200000,100000,2830,.04),(250000,200000,6830,.0425),(300000,250000,8955,.0475),(500000,300000,11330,.05),(1e99,500000,21330,.055)]
        for u,l,b,r in bands:
            if v<=u:return marginal(v,l,b,r)
    if state=='TAS':
        if v<=1300:return 20
        if v<=10000:return v*.015
        if v<=30000:return marginal(v,10000,150,.02)
        if v<=75000:return marginal(v,30000,550,.025)
        if v<=150000:return marginal(v,75000,1675,.03)
        if v<=225000:return marginal(v,150000,3925,.035)
        if v<=375000:return marginal(v,225000,6550,.04)
        return marginal(v,375000,12550,.045)
    if state=='ACT':
        if v<=200000:return v*.012
        if v<=300000:return marginal(v,200000,2400,.022)
        if v<=500000:return marginal(v,300000,4600,.034)
        if v<=750000:return marginal(v,500000,11400,.0432)
        if v<=1000000:return marginal(v,750000,22200,.059)
        if v<=1455000:return marginal(v,1000000,36950,.064)
        return v*.0454
    if state=='NT':
        if v<=525000:
            x=v/1000; return (0.06571441*x*x+15*x)*1000
        if v<=3000000:return v*.0495
        if v<=5000000:return v*.0575
        return v*.0595
    return 0

@dataclass
class Inputs:
    property_name:str; state:str; purchase_price:float; market_value:float; deposit:float; interest_rate:float; loan_term_years:int; loan_type:str; io_years:int; offset_balance:float; extra_monthly:float; weekly_rent:float; vacancy_rate:float; management_fee:float; rent_growth:float; council:float; water:float; insurance:float; strata:float; repairs_pct:float; land_tax:float; other_expenses:float; capital_growth:float; selling_cost_pct:float; marginal_tax_rate:float; depreciation:float; horizon_years:int; official_duty_override:float; concession_adjustment:float; foreign_surcharge:float; lmi:float; legal:float; inspection:float; loan_fees:float; buyers_agent:float; initial_repairs:float; other_purchase_costs:float

def loan_schedule(x):
    loan=max(0,x.purchase_price-x.deposit+x.lmi); mr=x.interest_rate/12; total=x.loan_term_years*12; rows=[]; bal=loan; cum=0
    for m in range(1,total+1):
        opening=bal; eff=max(0,opening-x.offset_balance); interest=eff*mr
        if opening<=0: scheduled=principal=closing=0
        elif x.loan_type=='Interest Only' and m<=x.io_years*12:
            scheduled=interest; principal=min(opening,x.extra_monthly); closing=max(0,opening-principal)
        else:
            rem=max(1,total-m+1); scheduled=opening/rem if mr==0 else opening*mr*(1+mr)**rem/((1+mr)**rem-1); principal=min(opening,max(0,scheduled-interest)+x.extra_monthly); closing=max(0,opening-principal)
        cum+=interest; rows.append({'Month':m,'Year':math.ceil(m/12),'Opening Balance':opening,'Scheduled Payment':scheduled,'Extra Payment':min(x.extra_monthly,opening),'Interest':interest,'Principal':principal,'Closing Balance':closing,'Offset':x.offset_balance,'Cumulative Interest':cum}); bal=closing
    return pd.DataFrame(rows)

def calculate(x):
    auto=estimate_duty(x.state,max(x.purchase_price,x.market_value)); duty=x.official_duty_override if x.official_duty_override>0 else max(0,auto-x.concession_adjustment+x.foreign_surcharge)
    costs=sum([duty,x.lmi,x.legal,x.inspection,x.loan_fees,x.buyers_agent,x.initial_repairs,x.other_purchase_costs]); cash=x.deposit+costs; loan=max(0,x.purchase_price-x.deposit+x.lmi); lvr=loan/x.market_value if x.market_value else 0
    sched=loan_schedule(x); ai=sched.groupby('Year',as_index=False)['Interest'].sum(); ab=sched.groupby('Year',as_index=False)['Closing Balance'].last(); crows=[]; grows=[]; cumcf=0
    for y in range(1,x.loan_term_years+1):
        gross=x.weekly_rent*52*(1+x.rent_growth)**(y-1); vac=gross*x.vacancy_rate; eff=gross-vac; mgmt=eff*x.management_fee; council=x.council*(1+x.rent_growth)**(y-1); water=x.water*(1+x.rent_growth)**(y-1); ins=x.insurance*(1+x.rent_growth)**(y-1); strata=x.strata*(1+x.rent_growth)**(y-1); repairs=gross*x.repairs_pct; other=x.other_expenses*(1+x.rent_growth)**(y-1); interest=float(ai.loc[ai.Year==y,'Interest'].sum()); pre=eff-(mgmt+council+water+ins+strata+repairs+x.land_tax+other+interest); taxable=pre-x.depreciation; tax=-taxable*x.marginal_tax_rate; after=pre+tax; cumcf+=after
        crows.append({'Year':y,'Gross Rent':gross,'Vacancy':-vac,'Effective Rent':eff,'Management':-mgmt,'Council':-council,'Water':-water,'Insurance':-ins,'Strata':-strata,'Repairs':-repairs,'Land Tax':-x.land_tax,'Other':-other,'Interest':-interest,'Pre-tax Cash Flow':pre,'Depreciation':-x.depreciation,'Taxable Result':taxable,'Estimated Tax Effect':tax,'After-tax Cash Flow':after})
        value=x.purchase_price*(1+x.capital_growth)**y; balance=float(ab.loc[ab.Year==y,'Closing Balance'].iloc[0]); equity=value-balance; sell=value*x.selling_cost_pct; net=value-sell-balance; profit=net+cumcf-cash; grows.append({'Year':y,'Property Value':value,'Loan Balance':balance,'Gross Equity':equity,'Selling Costs':-sell,'Net Sale Proceeds':net,'Cumulative After-tax Cash Flow':cumcf,'Total Profit':profit,'Cash-on-Cash Return':profit/cash if cash else 0})
    return {'automatic_duty':auto,'duty_used':duty,'purchase_costs':costs,'cash_required':cash,'loan':loan,'lvr':lvr,'schedule':sched,'cashflow':pd.DataFrame(crows),'growth':pd.DataFrame(grows)}

def money(v): return f'${v:,.0f}'
def pct(v): return f'{v:.1%}'

def report_html(x,r):
    h=min(x.horizon_years,len(r['growth'])); g=r['growth'].iloc[h-1]; c=r['cashflow'].iloc[0]; fields={'Property':x.property_name,'State':x.state,'Purchase price':money(x.purchase_price),'Deposit':money(x.deposit),'Automatic duty estimate':money(r['automatic_duty']),'Duty used':money(r['duty_used']),'Total cash required':money(r['cash_required']),'Loan amount':money(r['loan']),'LVR':pct(r['lvr']),'Gross rental yield':pct(x.weekly_rent*52/x.purchase_price if x.purchase_price else 0),'Year 1 after-tax cash flow':money(c['After-tax Cash Flow']),f'Value after {h} years':money(g['Property Value']),f'Equity after {h} years':money(g['Gross Equity']),f'Total profit after {h} years':money(g['Total Profit']),f'Cash-on-cash return after {h} years':pct(g['Cash-on-Cash Return'])}; rows=''.join(f'<tr><th>{k}</th><td>{v}</td></tr>' for k,v in fields.items()); return f'<html><head><meta charset="utf-8"><style>body{{font-family:Arial;max-width:900px;margin:40px auto;color:#17324d}}table{{border-collapse:collapse;width:100%}}th,td{{padding:10px;border-bottom:1px solid #ddd;text-align:left}}th{{background:#f5f7fa}}</style></head><body><h1>Property Investment Decision Report</h1><table>{rows}</table><p>General estimates only. Verify duty, tax, finance, rental and growth assumptions independently.</p></body></html>'

st.sidebar.title('🏠 Property inputs')
with st.sidebar:
    property_name=st.text_input('Property name or address','Example investment property'); state=st.selectbox('State / Territory',['NSW','VIC','QLD','WA','SA','TAS','ACT','NT']); purchase_price=st.number_input('Purchase price ($)',0.0,value=1_000_000.0,step=10_000.0); market_value=st.number_input('Market value ($)',0.0,value=1_000_000.0,step=10_000.0); deposit=st.number_input('Deposit ($)',0.0,value=200_000.0,step=5_000.0)
    st.subheader('Loan'); interest_rate=st.number_input('Interest rate (%)',0.0,value=6.0,step=.1)/100; loan_term_years=st.slider('Loan term (years)',5,30,30); loan_type=st.selectbox('Loan structure',['Principal & Interest','Interest Only']); io_years=st.slider('Interest-only period (years)',0,10,5,disabled=loan_type!='Interest Only'); offset_balance=st.number_input('Offset balance ($)',0.0,value=0.0,step=5_000.0); extra_monthly=st.number_input('Extra monthly repayment ($)',0.0,value=0.0,step=100.0)
    st.subheader('Rent and costs'); weekly_rent=st.number_input('Weekly rent ($)',0.0,value=850.0,step=10.0); vacancy_rate=st.number_input('Vacancy rate (%)',0.0,100.0,3.0,.5)/100; management_fee=st.number_input('Management fee (%)',0.0,100.0,7.0,.5)/100; rent_growth=st.number_input('Annual rent growth (%)',-20.0,50.0,3.0,.5)/100; council=st.number_input('Council rates p.a. ($)',0.0,value=2200.0,step=100.0); water=st.number_input('Water p.a. ($)',0.0,value=900.0,step=100.0); insurance=st.number_input('Insurance p.a. ($)',0.0,value=1800.0,step=100.0); strata=st.number_input('Strata p.a. ($)',0.0,value=0.0,step=100.0); repairs_pct=st.number_input('Repairs (% of gross rent)',0.0,100.0,5.0,.5)/100; land_tax=st.number_input('Land tax p.a. ($)',0.0,value=0.0,step=100.0); other_expenses=st.number_input('Other expenses p.a. ($)',0.0,value=500.0,step=100.0)
    st.subheader('Growth, tax and exit'); capital_growth=st.number_input('Annual capital growth (%)',-20.0,50.0,5.0,.5)/100; selling_cost_pct=st.number_input('Selling costs (%)',0.0,20.0,2.5,.1)/100; marginal_tax_rate=st.number_input('Marginal tax rate (%)',0.0,60.0,37.0,1.0)/100; depreciation=st.number_input('Depreciation p.a. ($)',0.0,value=8000.0,step=500.0); horizon_years=st.slider('Decision horizon (years)',1,30,10)
    with st.expander('Duty and purchase-cost adjustments'):
        official_duty_override=st.number_input('Official duty override ($)',0.0,value=0.0,step=500.0); concession_adjustment=st.number_input('Concession reduction ($)',0.0,value=0.0,step=500.0); foreign_surcharge=st.number_input('Foreign purchaser surcharge ($)',0.0,value=0.0,step=500.0); lmi=st.number_input('LMI estimate ($)',0.0,value=0.0,step=500.0); legal=st.number_input('Legal and conveyancing ($)',0.0,value=2500.0,step=100.0); inspection=st.number_input('Building and pest ($)',0.0,value=700.0,step=100.0); loan_fees=st.number_input('Loan and valuation fees ($)',0.0,value=700.0,step=100.0); buyers_agent=st.number_input("Buyer's agent ($)",0.0,value=0.0,step=500.0); initial_repairs=st.number_input('Initial repairs ($)',0.0,value=0.0,step=500.0); other_purchase_costs=st.number_input('Other purchase costs ($)',0.0,value=500.0,step=100.0)

x=Inputs(property_name,state,purchase_price,market_value,deposit,interest_rate,loan_term_years,loan_type,io_years,offset_balance,extra_monthly,weekly_rent,vacancy_rate,management_fee,rent_growth,council,water,insurance,strata,repairs_pct,land_tax,other_expenses,capital_growth,selling_cost_pct,marginal_tax_rate,depreciation,horizon_years,official_duty_override,concession_adjustment,foreign_surcharge,lmi,legal,inspection,loan_fees,buyers_agent,initial_repairs,other_purchase_costs); r=calculate(x); g=r['growth'].iloc[horizon_years-1]; c=r['cashflow'].iloc[0]; gross_yield=weekly_rent*52/purchase_price if purchase_price else 0; net_yield=(c['Effective Rent']+c['Management']+c['Council']+c['Water']+c['Insurance']+c['Strata']+c['Repairs']+c['Land Tax']+c['Other'])/purchase_price if purchase_price else 0

st.title('Property Investment Decision Dashboard'); st.caption('Interactive feasibility, financing, cash-flow, tax-effect and growth modelling.')
t1,t2,t3,t4,t5,t6=st.tabs(['Executive dashboard','Purchase & loan','Cash flow','Growth & equity','Stress testing','Export'])
with t1:
    cols=st.columns(4); cols[0].metric('Total cash required',money(r['cash_required'])); cols[1].metric('Loan amount',money(r['loan'])); cols[2].metric('LVR',pct(r['lvr'])); cols[3].metric('Duty used',money(r['duty_used']))
    cols=st.columns(4); cols[0].metric('Gross rental yield',pct(gross_yield)); cols[1].metric('Net operating yield',pct(net_yield)); cols[2].metric('Year 1 after-tax cash flow',money(c['After-tax Cash Flow']),delta=f"{money(c['After-tax Cash Flow']/52)} per week"); cols[3].metric(f'{horizon_years}-year total profit',money(g['Total Profit']))
    cols=st.columns(4); cols[0].metric(f'Value after {horizon_years} years',money(g['Property Value'])); cols[1].metric(f'Equity after {horizon_years} years',money(g['Gross Equity'])); cols[2].metric('Cash-on-cash return',pct(g['Cash-on-Cash Return'])); cols[3].metric('Initial monthly payment',money(r['schedule'].iloc[0]['Scheduled Payment']))
    score=max(0,min(100,(25 if r['lvr']<=.8 else max(0,25-(r['lvr']-.8)*100))+(20 if gross_yield>=.05 else gross_yield/.05*20)+(20 if c['After-tax Cash Flow']>=0 else max(0,20+c['After-tax Cash Flow']/max(1,weekly_rent*52)*20))+(20 if g['Total Profit']>0 else 0)+(15 if capital_growth>=.04 else max(0,capital_growth/.04*15))))
    if score>=75: st.markdown(f'<div class="good"><b>Strong on entered assumptions — score {score:.0f}/100.</b></div>',unsafe_allow_html=True)
    elif score>=55: st.markdown(f'<div class="warn"><b>Potentially viable but assumption-sensitive — score {score:.0f}/100.</b></div>',unsafe_allow_html=True)
    else: st.markdown(f'<div class="bad"><b>Weak on entered assumptions — score {score:.0f}/100.</b></div>',unsafe_allow_html=True)
    a,b=st.columns(2)
    with a: st.plotly_chart(px.line(r['growth'].head(horizon_years),x='Year',y=['Property Value','Loan Balance','Gross Equity'],title='Value, debt and equity').update_layout(yaxis_tickprefix='$',yaxis_tickformat=',.0f'),use_container_width=True)
    with b: st.plotly_chart(px.bar(r['cashflow'].head(horizon_years),x='Year',y='After-tax Cash Flow',title='Annual after-tax cash flow').update_layout(yaxis_tickprefix='$',yaxis_tickformat=',.0f'),use_container_width=True)
with t2:
    a,b=st.columns(2)
    with a: st.subheader('Purchase summary'); st.dataframe(pd.DataFrame({'Item':['Purchase price','Automatic duty estimate','Duty used','LMI','Other purchase costs','Deposit','Total cash required','Loan amount','LVR'],'Value':[money(purchase_price),money(r['automatic_duty']),money(r['duty_used']),money(lmi),money(r['purchase_costs']-r['duty_used']-lmi),money(deposit),money(r['cash_required']),money(r['loan']),pct(r['lvr'])]}),hide_index=True,use_container_width=True); st.info('Duty is a general estimate. Use the override for official assessments, concessions or surcharges.')
    with b:
        s=r['schedule']; months=int(s.loc[s['Closing Balance']<=.01,'Month'].min()) if (s['Closing Balance']<=.01).any() else loan_term_years*12; st.subheader('Loan summary'); st.dataframe(pd.DataFrame({'Metric':['Initial payment','Total interest','Balance after 5 years','Balance after 10 years','Months to repay'],'Value':[money(s.iloc[0]['Scheduled Payment']),money(s['Interest'].sum()),money(s.loc[s.Month==min(60,len(s)),'Closing Balance'].iloc[0]),money(s.loc[s.Month==min(120,len(s)),'Closing Balance'].iloc[0]),f'{months} months']}),hide_index=True,use_container_width=True)
    st.plotly_chart(px.line(r['schedule'],x='Month',y='Closing Balance',title='Loan amortisation').update_layout(yaxis_tickprefix='$',yaxis_tickformat=',.0f'),use_container_width=True)
    with st.expander('View monthly amortisation schedule'): st.dataframe(r['schedule'],use_container_width=True,height=450)
with t3:
    d=r['cashflow'].head(horizon_years); fig=go.Figure(); fig.add_bar(x=d.Year,y=d['Pre-tax Cash Flow'],name='Pre-tax'); fig.add_bar(x=d.Year,y=d['After-tax Cash Flow'],name='After-tax'); fig.update_layout(barmode='group',yaxis_tickprefix='$',yaxis_tickformat=',.0f'); st.plotly_chart(fig,use_container_width=True); st.dataframe(d,use_container_width=True,height=500)
with t4:
    d=r['growth'].head(horizon_years); a,b=st.columns(2)
    with a: st.plotly_chart(px.area(d,x='Year',y='Gross Equity',title='Equity accumulation').update_layout(yaxis_tickprefix='$',yaxis_tickformat=',.0f'),use_container_width=True)
    with b: st.plotly_chart(px.line(d,x='Year',y='Total Profit',title='Total investment profit').update_layout(yaxis_tickprefix='$',yaxis_tickformat=',.0f'),use_container_width=True)
    st.dataframe(d,use_container_width=True)
with t5:
    rows=[]
    for rate in np.arange(.04,.101,.005):
        x2=Inputs(**{**asdict(x),'interest_rate':float(rate)}); rr=calculate(x2); rows.append({'Interest Rate':rate,'Monthly Payment':rr['schedule'].iloc[0]['Scheduled Payment'],'Year 1 After-tax Cash Flow':rr['cashflow'].iloc[0]['After-tax Cash Flow'],f'{horizon_years}-Year Profit':rr['growth'].iloc[horizon_years-1]['Total Profit']})
    stress=pd.DataFrame(rows); a,b=st.columns(2)
    with a: st.plotly_chart(px.line(stress,x='Interest Rate',y='Monthly Payment',markers=True,title='Repayment sensitivity').update_layout(xaxis_tickformat='.1%',yaxis_tickprefix='$',yaxis_tickformat=',.0f'),use_container_width=True)
    with b: st.plotly_chart(px.line(stress,x='Interest Rate',y='Year 1 After-tax Cash Flow',markers=True,title='Cash-flow sensitivity').update_layout(xaxis_tickformat='.1%',yaxis_tickprefix='$',yaxis_tickformat=',.0f'),use_container_width=True)
    gs=pd.DataFrame({'Growth Rate':np.arange(0,.081,.01)}); gs[f'Value after {horizon_years} years']=[purchase_price*(1+z)**horizon_years for z in gs['Growth Rate']]; st.plotly_chart(px.line(gs,x='Growth Rate',y=f'Value after {horizon_years} years',markers=True).update_layout(xaxis_tickformat='.0%',yaxis_tickprefix='$',yaxis_tickformat=',.0f'),use_container_width=True)
with t6:
    st.download_button('Download executive report (HTML)',report_html(x,r),'property_investment_report.html','text/html',use_container_width=True); a,b,c=st.columns(3); a.download_button('Download loan schedule CSV',r['schedule'].to_csv(index=False).encode(),'loan_schedule.csv','text/csv',use_container_width=True); b.download_button('Download cash-flow CSV',r['cashflow'].to_csv(index=False).encode(),'cash_flow.csv','text/csv',use_container_width=True); c.download_button('Download growth analysis CSV',r['growth'].to_csv(index=False).encode(),'growth_and_returns.csv','text/csv',use_container_width=True); st.download_button('Download assumptions CSV',pd.DataFrame([asdict(x)]).to_csv(index=False).encode(),'property_assumptions.csv','text/csv',use_container_width=True)
st.divider(); st.caption('General modelling tool only—not financial, tax, legal, valuation or lending advice. Verify duty, tax treatment, market rent and finance terms independently.')
