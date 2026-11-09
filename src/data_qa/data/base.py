from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation


@dataclass
class Record:
    trade_id: str = field(default_factory=str)
    account_id: int = field(default_factory=int)
    version: int = field(default_factory=int)
    event_id: str = field(default_factory=str)
    status: str = field(default_factory=str)
    pnl: str = field(default_factory=str)

    def business_key(self) -> tuple[str, int]:
        """Typed composite business key; not a serialized display string."""
        return (self.trade_id, self.account_id)

def pnl_value(value: str | None) -> Decimal | str | None:
    """Semantic PnL key: valid decimals compare numerically, not lexically."""
    if value is None:
        return None
    try:
        number = Decimal(value)
    except (InvalidOperation, TypeError, ValueError):
        return value
    return number if number.is_finite() else value
