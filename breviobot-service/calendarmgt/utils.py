from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import re

def parse_date_formula(formula: str) -> str:
    match = re.fullmatch(r'([+-])(\d+)([DWMY])', formula.strip().upper())
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
