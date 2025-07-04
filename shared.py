from dataclasses import dataclass
from datetime import timedelta

@dataclass
class Order:
    """Tutorial-style data class with type hints"""
    order_id: str
    user_id: str
    items: list[dict]  # [{item_id: str, quantity: int}]
    total_amount: float

# Timeout constants (moved here from workflows.py)
WORKFLOW_TIMEOUT = timedelta(minutes=10)
TASK_QUEUE = "ECOMMERCE_TASK_QUEUE"