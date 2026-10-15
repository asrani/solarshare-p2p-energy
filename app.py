from datetime import datetime, timezone
from math import sin, pi
import pandas as pd
import streamlit as st
from market import HOUSEHOLDS, initial_orders, make_order, clear_market

st.set_page_config(page_title='SolarShare | Community energy', page_icon='☀️', layout='wide')
st.markdown('''<style>
.stApp {background:#f5f7f5;color:#182e29;}
[data-testid="stSidebar"] {background:#e8efeb;}
h1,h2,h3 {letter-spacing:-.035em;}
[data-testid="stMetric"] {background:white;border:1px solid #dce6df;padding:20px;border-radius:14px;}
[data-testid="stMetricValue"] {color:#176b4c;}
div.stButton > button[kind="primary"] {background:#176b4c;border:0;}
.block-container {padding-top:2.2rem;}
</style>''', unsafe_allow_html=True)

def reset():
    st.session_state.orders = initial_orders()
    st.session_state.trades = []
    st.session_state.next_order = 7
    st.session_state.notice = ''

if 'orders' not in st.session_state:
    reset()

with st.sidebar:
    st.markdown('## ☀️ SolarShare')
    st.caption('COMMUNITY ENERGY EXCHANGE')
    st.divider()
    household = st.selectbox('Your household', HOUSEHOLDS, index=3)
    st.markdown('### Simulation settings')
    grid_rate = st.number_input('Grid import ($/kWh)', min_value=0.01, max_value=5.0, value=0.30, step=0.01)
    export_rate = st.number_input('Grid export ($/kWh)', min_value=0.0, max_value=5.0, value=0.08, step=0.01)
    st.caption('Illustrative USD rates. Change these to compare your own scenarios. Rates apply to the full ledger.')
    st.divider()
    st.button('Reset demo', on_click=reset, width='stretch')
    st.caption('Session-only data. Reloading or disconnecting may reset your trades.')

st.caption('SOLARSHARE  /  LOCAL MARKET')
st.title('Good energy. Shared locally.')
st.write('Trade surplus solar with your community and see where every kilowatt-hour goes.')
st.info('Demo market · All offers share one simulated delivery interval. No real electricity or payments are exchanged.')

if st.session_state.get('notice'):
    st.success(st.session_state.pop('notice'))

orders, trades = st.session_state.orders, st.session_state.trades
volume = sum(t['quantity'] for t in trades)
value = sum(t['value'] for t in trades)
supply = sum(o['remaining'] for o in orders if o['side']=='Sell')
demand = sum(o['remaining'] for o in orders if o['side']=='Buy')
a,b,c,d = st.columns(4)
a.metric('Energy traded', f'{volume:,.1f} kWh')
b.metric('Available solar', f'{supply:,.1f} kWh')
c.metric('Open demand', f'{demand:,.1f} kWh')
d.metric('Average trade price', f'${value/volume:.3f}/kWh' if volume else '—')

market, energy, wallet, methodology = st.tabs(['Marketplace', 'Community energy', 'My activity', 'How it works'])

def book_frame(side):
    rows = [dict(Offer=o['id'], Household=o['household'], **{'Remaining (kWh)':o['remaining'], 'Limit ($/kWh)':o['price']})
            for o in sorted(orders, key=lambda o:(o['price'] if side=='Sell' else -o['price'], o['id']))
            if o['side']==side and o['remaining']>1e-8]
    return pd.DataFrame(rows, columns=['Offer','Household','Remaining (kWh)','Limit ($/kWh)'])

with market:
    left,right = st.columns([2,1], gap='large')
    with right:
        st.subheader('Place an offer')
        st.caption(f'Posting as {household}')
        with st.form('offer', clear_on_submit=False):
            side = st.radio('I want to', ['Buy','Sell'], horizontal=True)
            quantity = st.number_input('Energy (kWh)', min_value=0.1, max_value=1000.0, value=5.0, step=0.1)
            price = st.number_input('Limit price ($/kWh)', min_value=0.001, max_value=5.0, value=0.20, step=0.01, format='%.3f')
            st.caption('Buy: maximum you will pay. Sell: minimum you will accept.')
            posted = st.form_submit_button('Post offer', type='primary', width='stretch')
        if posted:
            st.session_state.orders.append(make_order(st.session_state.next_order, household, side, quantity, price))
            st.session_state.next_order += 1
            st.session_state.notice = 'Your offer is in the order book. Run matching to settle compatible offers.'
            st.rerun()
        st.markdown('#### Clear the community market')
        st.caption('Match all compatible community offers using price priority and midpoint pricing.')
        if st.button('Run matching', type='primary', width='stretch'):
            updated, new = clear_market(orders, len(trades)+1)
            timestamp = datetime.now(timezone.utc).isoformat(timespec='seconds')
            for t in new:
                t['time_utc'] = timestamp
            st.session_state.orders = updated
            st.session_state.trades.extend(new)
            st.session_state.notice = f'Matched {len(new)} trades, totaling {sum(t["quantity"] for t in new):.1f} kWh.' if new else 'No compatible offers to match. Try a higher buy limit or lower sell limit.'
            st.rerun()
    with left:
        st.subheader('Community order book')
        st.caption('One shared demo interval · lower asks and higher bids get priority')
        st.markdown('##### ☀️ Solar for sale')
        st.dataframe(book_frame('Sell'), hide_index=True, width='stretch')
        st.markdown('##### ⚡ Energy wanted')
        st.dataframe(book_frame('Buy'), hide_index=True, width='stretch')
        own_open = [o for o in orders if o['household']==household and o['remaining']>1e-8]
        if own_open:
            with st.expander('Cancel one of my open offers'):
                selected = st.selectbox('Offer', [o['id'] for o in own_open], format_func=lambda oid: next(f'#{o["id"]} · {o["side"]} · {o["remaining"]:.1f} kWh' for o in own_open if o['id']==oid))
                if st.button('Cancel remaining quantity'):
                    st.session_state.orders = [o for o in orders if o['id']!=selected]
                    st.session_state.notice = f'Canceled the remaining quantity of offer #{selected}.'
                    st.rerun()
    st.subheader('Trade ledger')
    if trades:
        df = pd.DataFrame(trades)
        st.dataframe(df.rename(columns={'quantity':'Energy (kWh)','price':'Price ($/kWh)','value':'Value ($)'}), hide_index=True, width='stretch')
        st.download_button('Download trades · CSV', df.to_csv(index=False), 'solarshare-trades.csv', 'text/csv')
    else:
        st.caption('Your first trades will appear here. Run matching to settle the sample offers.')

with energy:
    st.subheader('A day in the community')
    st.caption('Illustrative hourly energy profile · independent of the order book and trading ledger')
    profile = pd.DataFrame([{'Hour':f'{h:02}:00', 'Solar generation (kWh)':round(max(0,sin((h-6)*pi/12))*22,2),
                             'Consumption (kWh)':round(8+5*(17<=h<=21)+3*(6<=h<=9),2)} for h in range(24)]).set_index('Hour')
    st.line_chart(profile, color=['#e6ac32','#176b4c'], x_label='Hour of day', y_label='Energy (kWh)')
    st.download_button('Download simulated energy profile', profile.to_csv(), 'community-profile.csv','text/csv')

with wallet:
    st.subheader(f'{household} · activity')
    bought = [t for t in trades if t['buyer']==household]
    sold = [t for t in trades if t['seller']==household]
    spend, revenue = sum(t['value'] for t in bought), sum(t['value'] for t in sold)
    savings = sum(t['quantity']*grid_rate-t['value'] for t in bought)
    uplift = sum(t['value']-t['quantity']*export_rate for t in sold)
    x,y,z = st.columns(3)
    x.metric('Energy purchased',f'{sum(t["quantity"] for t in bought):.1f} kWh',f'${spend:.2f} spent',delta_color='off')
    y.metric('Energy sold',f'{sum(t["quantity"] for t in sold):.1f} kWh',f'${revenue:.2f} earned',delta_color='off')
    z.metric('Net trading cost',f'${spend-revenue:.2f}')
    st.write(f'Buyer savings versus grid imports: **${savings:.2f}**. Seller revenue gain versus grid exports: **${uplift:.2f}**.')
    st.caption('Comparisons cover traded energy only, before fees. Negative values mean a worse result than the selected grid rate.')
    own = [t for t in trades if household in (t['buyer'], t['seller'])]
    if own:
        st.dataframe(pd.DataFrame(own),hide_index=True,width='stretch')
    else:
        st.caption('No completed trades for this household yet.')

with methodology:
    st.subheader('From surplus to shared value')
    st.markdown('''1. **Post an offer.** Select a household, energy quantity, and limit price.
2. **Run matching.** Buyers are processed by highest bid first; sellers by lowest ask first. Earlier offers break price ties. A household cannot trade with itself.
3. **Settle compatible offers.** When a bid meets an ask, the trade price is their midpoint. The smaller remaining quantity is filled; any remainder stays open.
4. **Review the result.** The ledger records simulated commitments. My activity compares those trades with the grid rates in the sidebar.

This is a teaching prototype. Offers are manually entered and are not constrained by the illustrative generation chart. The simulation excludes physical delivery, network capacity, losses, batteries, fees, authentication, metering, real payments, and persistent storage.''')
    st.caption('Built with Streamlit · https://docs.streamlit.io/')
