from dataclasses import dataclass, field


@dataclass
class Record:
    trade_id: str = field(default_factory=str)
    account_id: int = field(default_factory=int)
    version: int = field(default_factory=int)
    event_id: str = field(default_factory=str)
    status: str = field(default_factory=str)
    pnl: str = field(default_factory=str)

    def business_key(self) -> str:
        return f"{self.trade_id}:{self.account_id}"