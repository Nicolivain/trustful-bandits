
def test_pnl_increase(agent):
    if agent.current_pnl - agent.previous_pnl > 0:
        return 1
    else:
        return 0
