import re

value = '!= Testing'

operators = {
        ">": "$gt",
        "<": "$lt",
        ">=": "$gte",
        "<=": "$lte",
        "!=": "$ne",
        "EXISTS": {"$exists": True},
        "NOT EXISTS": {"$exists": False},
    }

for op, func in operators.items():
    if re.match(rf"^{op}", value):
        value = value.replace(op, "").strip()
        print(value)