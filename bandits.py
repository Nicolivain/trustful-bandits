import numpy as np
from tests import test_pnl_increase


def simple_two_armed_bandit(X, C, alpha, pa, pb):
    """
    Test the two armed bandit algorithm using user defined probabilities pA and pB
    """

    fracA = [X]  # we store all x
    fracB = [1-X]
    for n in range(1000):
        gamma = (C / (C + n + 1))**alpha 
        if np.random.random_sample() < X:
            # test A:
            if np.random.sample() < pa:
                X = X + gamma * (1 - X)
        else:
            # test B:
            if np.random.sample() < pb:
                X = X - gamma * X  # we give gamma X to B
        fracA.append(X)
        fracB.append(1-X)
    return fracA, fracB


def agent_two_armed_bandit(data, agentA, agentB, X, C, alpha, n_iter=None):
    """
    Test the two armed bandit algorithm using user defined probabilities pA and pB
    """
    n_iter = n_iter if n_iter is not None else len(data)

    fracA = [X]  # we store all x
    fracB = [1-X]
    for n in range(n_iter):
        ask, bid = data.iloc[n][['AskPrice', 'BidPrice']]
        agentA.act(ask, bid)
        agentB.act(ask, bid)

        gamma = (C / (C + n + 1))**alpha 
        if np.random.random_sample() < X:
            # test A:
            agentA.calc_pnl(bid)
            if test_pnl_increase(agentA):
                nX = X + gamma * (1 - X)
                agentA.rescale_capital(nX/X)  # multiply everything by this ration to reach the new ratio
                agentB.rescale_capital((1-nX)/(1-X))
                X = nX
        else:
            # test B:
            agentB.calc_pnl(bid)
            if test_pnl_increase(agentB):
                nX = X - gamma * X  # we give gamma X to B
                agentA.rescale_capital(nX/X)
                agentB.rescale_capital((1-nX)/(1-X))
                X = nX
        fracA.append(X)
        fracB.append(1-X)
    return fracA, fracB


def simple_multi_armed_bandit(X, C, alpha, ps, n_iter=973):
    """
    Test the mutli armed bandit algorithm using user defined probabilities ps
    ps and X must be of size  #agent
    """

    fracs = np.zeros((n_iter+1, len(X)))
    fracs[0, :] = X 

    for n in range(n_iter):
        gamma = (C / (C + n + 1))**alpha 
        cs = np.cumsum(fracs[n, :])
        s = np.random.sample()
        for i in range(len(cs)):
            if s <= cs[i]:
                # we evaluate agent i
                if np.random.sample() < ps[i]:
                    x = fracs[n, i]
                    fracs[n+1, i] = x + gamma * (1 - x)
                    for k in range(len(X)):
                        if k != i:
                            fracs[n+1, k] = fracs[n, k] - fracs[n, k] * gamma  # we decrease each agent's capital proportionally 
                else:
                    fracs[n+1, :] = fracs[n, :]  # we do not punish when not passing the test
                break
    
    return fracs


def agent_multi_armed_bandit(data, agents, X, C, alpha, n_iter=None):
    """
    Test the multi armed bandit algorithm using agents
    """

    n_iter = n_iter if n_iter is not None else len(data)

    fracs = np.zeros((n_iter+1, len(X)))
    fracs[0, :] = X 

    for n in range(n_iter):
        # get the data and have each agent play
        ask, bid = data.iloc[n][['AskPrice', 'BidPrice']]
        for a in agents:
            a.act(ask, bid)

        gamma = (C / (C + n + 1))**alpha 
        cs = np.cumsum(fracs[n, :])
        s = np.random.sample()
        for i in range(len(cs)):
            if s <= cs[i]:
                # we evaluate agent i
                agents[i].calc_pnl(bid)
                if test_pnl_increase(agents[i]):
                    x = fracs[n, i]
                    fracs[n+1, i] = x + gamma * (1 - x)
                    for k in range(len(X)):
                        if k != i:
                            fracs[n+1, k] = fracs[n, k] - fracs[n, k] * gamma  # we decrease each agent's capital proportionally 
                        agents[i].rescale_capital(fracs[n+1, k]/fracs[n, k])  # rescale capital for all agents according the the new proportions
                else:
                    fracs[n+1, :] = fracs[n, :]  # we do not punish when not passing the test
                break
    
    return fracs
