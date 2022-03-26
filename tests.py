
def test_pnl_increase(agent):
    if agent.current_pnl - agent.previous_pnl > 0:
        return 1
    else:
        return 0


def test_highest_pnl(agent_a, agent_b):
    if agent_a.current_pnl > agent_b.current_pnl:
        return 1
    else:
        return 0
