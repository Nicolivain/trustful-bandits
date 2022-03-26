import numpy as np


class Agent:
    def __init__(self, capital):
        self.capital = capital
        self.cash = capital
        self.asset = 0

        self.current_pnl = capital
        self.previous_pnl = 0

    def calc_pnl(self, bid):
        self.previous_pnl = self.current_pnl
        self.current_pnl = self.cash + self.asset * bid - self.capital
        return self.current_pnl

    def rescale_capital(self, frac):
        self.current_pnl *= frac
        self.previous_pnl *= frac
        self.capital *= frac
        self.cash *= frac
        self.asset *= frac    


class RandomAgent(Agent):
    def __init__(self, capital, p_buy=0.15, p_sell=0.15, volume=0.1):
        super().__init__(capital)
        self.p_sell = p_sell
        self.p_buy = p_buy
        self.volume = volume

    def act(self, bid, ask):
        # 15% buy, 15% sell, 70% wait
        r = np.random.random_sample()
        if r < self.p_buy:
            c = self.volume * self.cash
            self.cash -= c
            self.asset += c / ask
        elif r < self.p_buy + self.p_sell:
            c = self.volume * self.asset
            self.cash += bid * c
            self.asset -= self.asset
        else:
            pass


class MMAgent(Agent):
    def __init__(self, capital, tick_size, volume=100, patience=15):
        super().__init__(capital)

        self.tick_size = tick_size
        self.volume = volume

        self.cpt_a = 0
        self.cpt_b = 0
        self.patience = patience

        self.ask_order_price = None 
        self.ask_order_vol = None

        self.bid_order_price = None
        self.bid_order_vol = None

    def act(self, bid, ask):
        self.calc_limit_orders(bid, ask)

        if bid <= self.bid_order_price:
            #print(self.bid_order_price, self.bid_order_vol)
            self.cash -= min(self.bid_order_price * self.bid_order_vol, self.cash)
            self.asset += min(self.bid_order_vol, self.cash / bid)  # make sure we don't go negative in cash
            self.bid_order_price, self.bid_order_vol = None, None
            self.cpt_a = 0
        else:
            self.cpt_b += 1

        if ask >= self.ask_order_price:
            self.cash += self.ask_order_price * self.ask_order_vol
            self.asset -= self.ask_order_vol
            self.ask_order_price, self.ask_order_vol = None, None
            self.cpt_b = 0
        else:
            self.cpt_a += 1

        if self.cpt_b>=self.patience:
            self.bid_order_price, self.bid_order_vol = None, None
            self.cpt_b = 0
        if self.cpt_a>=self.patience:
            self.ask_order_price, self.ask_order_vol = None, None
            self.cpt_a = 0

    def calc_limit_orders(self, bid, ask):
        pass
        

class StaticMMAgent(MMAgent): 
    def __init__(self, capital, dbid, dask, tick_size, volume=100,patience=15):
        super().__init__(capital, tick_size, volume, patience)
        self.dbid = dbid
        self.dask = dask

    def calc_limit_orders(self, bid, ask):
        self.ask_order_price = ask + self.dask * self.tick_size if self.ask_order_price is None else self.ask_order_price
        self.ask_order_vol = self.volume if self.ask_order_vol is None else self.ask_order_vol

        self.bid_order_price = bid - self.dbid * self.tick_size if self.bid_order_price is None else self.bid_order_price
        self.bid_order_vol = self.volume if self.bid_order_vol is None else self.bid_order_vol


class DynamicMMAgent(MMAgent): 
    def __init__(self, capital, cbid, cask, tick_size, volume=100, patience=15):
        super().__init__(capital, tick_size, volume, patience)

        self.cbid = cbid
        self.cask = cask

        self.sigma_ask = 0
        self.avg_ask = 0
        self.sigma_bid = 0
        self.avg_bid = 0

        self.old_ask = None
        self.old_bid = None

        self.cpt = 0

    def calc_limit_orders(self, bid, ask):
        self.calc_volatility(bid, ask)

        self.ask_order_price = ask + self.cask * self.sigma_ask if self.ask_order_price is None else self.ask_order_price
        self.ask_order_vol = self.volume if self.ask_order_vol is None else self.ask_order_vol

        self.bid_order_price = bid - self.cbid * self.sigma_bid if self.bid_order_price is None else self.bid_order_price
        self.bid_order_vol = self.volume if self.bid_order_vol is None else self.bid_order_vol

    def calc_volatility(self, bid, ask):
        self.cpt += 1

        if self.old_ask is not None:
            xa = ask - self.old_ask
            xb = bid - self.old_bid
            self.old_ask = ask
            self.old_bid = bid
        else:
            self.old_ask = ask
            self.old_bid = bid
            return 0

        old_avg_ask = self.avg_ask
        self.avg_ask = (self.cpt-1) / self.cpt * self.avg_ask + 1 / self.cpt * xa 
        old_avg_bid = self.avg_bid
        self.avg_bid = (self.cpt-1) / self.cpt * self.avg_bid + 1 / self.cpt * xb 

        self.sigma_ask = self.sigma_ask**2 + old_avg_ask**2 - self.avg_ask**2 + (xa**2 - self.sigma_ask**2 - old_avg_ask**2) / self.cpt   
        self.sigma_ask = self.sigma_ask ** (1/2)     

        self.sigma_bid = self.sigma_bid**2 + old_avg_bid**2 - self.avg_bid**2 + (xb**2 - self.sigma_bid**2 - old_avg_bid**2) / self.cpt   
        self.sigma_bid = self.sigma_bid ** (1/2)   
 

class ExpAvgAgent(Agent):
    def __init__(self, capital, alpha=0.8, volume=0.1):
        super().__init__(capital)

        self.alpha = alpha
        self.ma_bid = 0
        self.ma_ask = 0

        self.volume = volume

    def act(self, bid, ask):
        self.ma_bid = self.alpha * self.ma_bid + (1 - self.alpha) * bid
        self.ma_ask = self.alpha * self.ma_ask + (1 - self.alpha) * ask
        if ask < self.ma_ask:
            # we buy if price is below the moving average
            c = self.volume * self.cash
            self.cash -= c
            self.asset += c / ask
        elif bid > self.ma_bid:
            # we sell if price is above the moving average
            c = self.volume * self.asset
            self.cash += bid * c
            self.asset -= self.asset
        else:
            # else we move on
            pass

class PwAgent(Agent):
    def __init__(self, capital, streak=3, volume=0.1):
        super().__init__(capital)
        self.last_bid = 0
        self.last_ask = 0
        self.b_streak = 0
        self.a_streak = 0
        self.action_streak = streak
        self.volume = volume

    def act(self, bid, ask):
        if bid >= self.last_bid: self.b_streak += 1
        else: self.b_streak = 0
        if ask <= self.last_ask: self.a_streak += 1
        else: self.a_streak = 0

        self.last_ask = ask
        self.last_bid = bid

        if self.a_streak >= self.action_streak:
            # we buy if price is below the moving average
            c = min(self.cash, self.volume * self.capital)
            self.cash -= c
            self.asset += c / ask
            self.a_streak = 0
        if self.b_streak >= self.action_streak:
            # we sell if price is above the moving average
            c = min(self.volume * self.capital / bid, self.asset)
            self.cash += bid * c
            self.asset -= self.asset 
            self.b_streak = 0
