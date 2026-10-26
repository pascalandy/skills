def total(prices):
    return sum(prices)


def average(prices):
    return sum(prices) / len(prices)


def median(prices):
    ordered = sorted(prices)
    middle = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[middle]
    return (ordered[middle - 1] + ordered[middle]) / 2
