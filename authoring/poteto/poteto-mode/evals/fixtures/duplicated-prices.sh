# Two functions in shop.py format prices with the same inline code; test_shop.py pins their output
set -euo pipefail
cat > shop.py <<'PY'
def cart_total_label(items):
    total = sum(price for _, price in items)
    return "Total: $" + format(total / 100, ",.2f")


def receipt_line(name, cents):
    return name + " ... $" + format(cents / 100, ",.2f")
PY
cat > test_shop.py <<'PY'
from shop import cart_total_label, receipt_line

assert cart_total_label([("tea", 450), ("cake", 125050)]) == "Total: $1,255.00"
assert receipt_line("tea", 450) == "tea ... $4.50"
print("ok")
PY
printf '__pycache__/\n' > .gitignore
git add -A && git commit -qm "Add shop pricing" && git branch -M main
