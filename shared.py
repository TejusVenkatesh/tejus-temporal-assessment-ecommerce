from dataclasses import dataclass
from datetime import timedelta


@dataclass
class Order:
    """Represents an e-commerce order. Instead of passing multiple parameters,
    we encapsulate all order-related data in a single object."""
    order_id: str
    user_id: str
    items: list[dict]  # [{item_id: str, quantity: int}]
    total_amount: float


WORKFLOW_TIMEOUT = timedelta(minutes=10)
TASK_QUEUE = "ECOMMERCE_TASK_QUEUE"

