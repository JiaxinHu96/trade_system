from decimal import Decimal


def decimal_or_zero(value):
    if value is None or value == '':
        return Decimal('0')
    return Decimal(str(value))
