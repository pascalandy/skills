"""The kitchen's preorder sheet."""


def title(day):
    return f"Orders for {day:%a} {day.isoformat()}"


def subject(day, count):
    return f"Preorders for {day:%a} {day.isoformat()} ({count})"


def line(order):
    return f"{order.pickup}  #{order.id}  {order.customer:<22}{order.items}"


def render(day, orders):
    lines = [title(day)] + [line(order) for order in orders]
    return "\n".join(lines) + "\n"
