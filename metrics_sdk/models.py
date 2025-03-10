from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List

@dataclass
class SystemMetrics:
    """System metrics data."""
    thread_count: int
    ram_usage_percent: float

    def to_dict(self) -> dict:
        return {
            'thread_count': self.thread_count,
            'ram_usage_percent': self.ram_usage_percent
        }

@dataclass
class CryptoMetrics:
    """Cryptocurrency metrics data."""
    bitcoin_price_usd: Optional[float]
    ethereum_price_usd: Optional[float]

    def to_dict(self) -> dict:
        return {
            'bitcoin_price_usd': self.bitcoin_price_usd,
            'ethereum_price_usd': self.ethereum_price_usd
        }

@dataclass
class MetricsSnapshot:
    """Complete metrics snapshot."""
    device_id: int
    timestamp: datetime
    system_metrics: Optional[SystemMetrics] = None
    crypto_metrics: Optional[CryptoMetrics] = None
    snapshot_id: Optional[int] = None

    def to_dict(self) -> dict:
        data = {
            'device_id': self.device_id,
            'timestamp': self.timestamp.isoformat()
        }
        if self.system_metrics:
            data['system_metrics'] = self.system_metrics.to_dict()
        if self.crypto_metrics:
            data['crypto_metrics'] = self.crypto_metrics.to_dict()
        if self.snapshot_id:
            data['snapshot_id'] = self.snapshot_id
        return data

    @classmethod
    def from_dict(cls, data: dict) -> 'MetricsSnapshot':
        """Create a MetricsSnapshot from a dictionary."""
        system_metrics = SystemMetrics(**data['system_metrics']) if data.get('system_metrics') else None
        crypto_metrics = CryptoMetrics(**data['crypto_metrics']) if data.get('crypto_metrics') else None
        
        return cls(
            device_id=data['device_id'],
            timestamp=datetime.fromisoformat(data['timestamp']),
            system_metrics=system_metrics,
            crypto_metrics=crypto_metrics,
            snapshot_id=data.get('snapshot_id')
        ) 