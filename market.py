"""Deterministic, session-local energy market simulation."""
from copy import deepcopy
from math import isfinite

HOUSEHOLDS = ['Willow House', 'Sunrise Villa', 'Cedar Cottage', 'Maple Home', 'River Apartment', 'Oak Residence']

def initial_orders():
    rows = [('Willow House', 'Sell', 12., .14), ('Sunrise Villa', 'Sell', 8., .18),
            ('Cedar Cottage', 'Sell', 6., .22), ('Maple Home', 'Buy', 10., .25),
            ('River Apartment', 'Buy', 9., .20), ('Oak Residence', 'Buy', 5., .16)]
    return [dict(id=i+1, household=h, side=s, quantity=q, remaining=q, price=p) for i,(h,s,q,p) in enumerate(rows)]

def make_order(order_id, household, side, quantity, price):
    if household not in HOUSEHOLDS or side not in ('Buy', 'Sell'):
        raise ValueError('Choose a valid household and order side.')
    if not all(isfinite(x) and x > 0 for x in (quantity, price)):
        raise ValueError('Quantity and price must be finite and greater than zero.')
    return dict(id=order_id, household=household, side=side, quantity=quantity, remaining=quantity, price=price)

def clear_market(orders, first_trade_id=1):
    """Price/time priority; no self-trades; midpoint settlement; partial fills.

    Each order is for the same demo delivery interval. Matching makes simulated
    commitments only; grid delivery, network limits, and metering are excluded.
    """
    book = deepcopy(orders)
    buys = sorted((o for o in book if o['side']=='Buy' and o['remaining']>1e-8), key=lambda o:(-o['price'],o['id']))
    sells = sorted((o for o in book if o['side']=='Sell' and o['remaining']>1e-8), key=lambda o:(o['price'],o['id']))
    trades = []
    for buy in buys:
        for sell in sells:
            if buy['remaining']<=1e-8:
                break
            if sell['remaining']<=1e-8 or sell['household']==buy['household'] or sell['price']>buy['price']:
                continue
            quantity = round(min(buy['remaining'], sell['remaining']), 6)
            price = round((buy['price']+sell['price'])/2, 6)
            buy['remaining'] = round(buy['remaining']-quantity, 6)
            sell['remaining'] = round(sell['remaining']-quantity, 6)
            trades.append(dict(id=first_trade_id+len(trades), buyer=buy['household'], seller=sell['household'],
                               buy_order=buy['id'], sell_order=sell['id'], quantity=quantity, price=price, value=quantity*price))
    return book, trades
