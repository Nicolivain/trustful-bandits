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
