from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class Knowledge:

    id: str

    entity_type: str

    entity_id: str

    key: str

    value: Any

    value_type: str

    source: str

    confidence: float = 1.0

    collected_at: datetime = field(default_factory=datetime.utcnow)

    metadata: Optional[Dict[str, Any]] = None

    version: int = 1