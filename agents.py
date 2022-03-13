import numpy as np


class RandomAgent:
    def __init__(self, capital, p_buy=0.15, p_sell=0.15, volume=0.1):
        self.capital = capital
        self.cash = capital
        self.asset = 0

        self.current_pnl = capital
        self.previous_pnl = 0

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


class ExpAvgAgent:
    def __init__(self, capital, alpha=0.8, volume=0.1):
        self.capital = capital
        self.cash = capital
        self.asset = 0

        self.current_pnl = capital
        self.previous_pnl = 0

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

