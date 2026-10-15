import unittest
from market import initial_orders, clear_market, make_order

class MarketTests(unittest.TestCase):
    def test_seeded_clearing_and_conservation(self):
        original = initial_orders()
        book, trades = clear_market(original)
        self.assertEqual(sum(t['quantity'] for t in trades), 19)
        self.assertEqual(original[0]['remaining'], 12)
        for order in book:
            filled = sum(t['quantity'] for t in trades if order['id'] in (t['buy_order'],t['sell_order']))
            self.assertAlmostEqual(order['quantity'],order['remaining']+filled)
            self.assertGreaterEqual(order['remaining'],0)
        for t in trades:
            bid = next(o for o in original if o['id']==t['buy_order'])
            ask = next(o for o in original if o['id']==t['sell_order'])
            self.assertLessEqual(ask['price'], t['price'])
            self.assertLessEqual(t['price'], bid['price'])
        self.assertEqual(clear_market(book)[1], [])

    def test_self_trade_excluded_and_other_seller_found(self):
        orders = [make_order(1,'Willow House','Buy',5,.3),make_order(2,'Willow House','Sell',5,.1),make_order(3,'Maple Home','Sell',2,.2)]
        book, trades = clear_market(orders)
        self.assertEqual(len(trades),1)
        self.assertEqual(trades[0]['seller'],'Maple Home')
        self.assertEqual(book[0]['remaining'],3)

    def test_incompatible_limits_and_invalid_numbers(self):
        orders = [make_order(1,'Willow House','Buy',5,.1),make_order(2,'Maple Home','Sell',5,.2)]
        self.assertEqual(clear_market(orders)[1],[])
        for qty in (-1,0,float('nan'),float('inf')):
            with self.assertRaises(ValueError):
                make_order(3,'Willow House','Buy',qty,.2)

    def test_price_then_time_priority(self):
        orders = [make_order(1,'Willow House','Buy',2,.25),make_order(2,'Maple Home','Buy',2,.3),make_order(3,'Oak Residence','Buy',2,.3),make_order(4,'Cedar Cottage','Sell',3,.15)]
        _, trades = clear_market(orders)
        self.assertEqual([t['buy_order'] for t in trades],[2,3])
        self.assertEqual([t['quantity'] for t in trades],[2,1])

if __name__=='__main__':
    unittest.main()
