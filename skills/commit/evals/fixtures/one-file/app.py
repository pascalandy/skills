def total(prices):
    return sum(prices)


def average(prices):
    if not prices:
        return 0.0
    return sum(prices) / len(prices)


def maximum(prices):
    return max(prices, default=0)
