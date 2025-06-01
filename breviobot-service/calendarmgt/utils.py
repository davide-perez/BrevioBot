from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import re

def parse_date_formula(formula: str) -> str:
    if not formula:
        raise ValueError("Formula is empty")
    formula = formula.strip()
    # If no sign, prepend '+' to the formula assuming positive by default
    if not formula.startswith(('+', '-')):
        formula = '+' + formula
    match = re.fullmatch(r'([+-])(\d+)([DWMY])', formula.upper())
    if not match:
        raise ValueError(f"Invalid formula: '{formula}'")
    
    sign, value_str, unit = match.groups()
    value = int(value_str)
    
    if unit == 'D':
        delta = timedelta(days=value)
    elif unit == 'W':
        delta = timedelta(weeks=value)
    elif unit == 'M':
        delta = relativedelta(months=value)
    elif unit == 'Y':
        delta = relativedelta(years=value)
    else:
        raise ValueError(f"Unsupported unit: '{unit}'")

    now = datetime.utcnow()
    result = now + delta if sign == '+' else now - delta
    
    return result.isoformat(timespec="seconds") + 'Z'


def is_date_formula(formula: str) -> bool:
    if not formula:
        return False
    formula = formula.strip()
    if not formula.startswith(('+', '-')):
        formula = '+' + formula
    return bool(re.fullmatch(r'([+-])(\d+)([DWMY])', formula.upper()))