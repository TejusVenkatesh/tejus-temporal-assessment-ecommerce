"""
E-Commerce Order Processor (Original Implementation)
===================================================
Manual implementation of order processing without workflow orchestration from Temporal.
"""

import random
import logging
import asyncio
from dataclasses import dataclass
from datetime import datetime


@dataclass
class Order:
    """Represents an e-commerce order. Manually tracking all state."""
    order_id: str       # Unique order identifier
    user_id: str        # Customer ID
    items: list[dict]   # Items in format: [{"item_id": "abc", "quantity": 2}]
    total_amount: float # Total charge amount


# Custom Exceptions
class InventoryUnavailableError(Exception):
    """Thrown when inventory service fails or items are out of stock"""
    pass

class PaymentDeclinedError(Exception):
    """Thrown when payment gateway rejects the transaction"""
    pass

class EmailServiceError(Exception):
    """Thrown when confirmation email fails to send"""
    pass


# Service Functions -  a function for each critical step in the order process
# Each could fail and requires manual recovery

async def validate_inventory(order: Order) -> bool:
    """Check inventory availability. 
    """
    logging.info(f"[Inventory] Validating order {order.order_id}")
    await asyncio.sleep(1)  # Simulate network delay
    if random.random() < 0.1:
        raise InventoryUnavailableError("Item out of stock")
    return True

async def process_payment(order: Order) -> str:
    """Charge customer's payment method.
    """
    logging.info(f"[Payment] Processing ${order.total_amount:.2f} for {order.order_id}")
    await asyncio.sleep(2)  # Simulate slower payment processing
    if random.random() < 0.15: # 155 
        raise PaymentDeclinedError("Card declined")
    return f"txn_{order.order_id}_{random.randint(1000,9999)}"  # Mock transaction ID

async def update_inventory(order: Order) -> bool:
    """Update stock levels after successful payment.
    """
    logging.info(f"[Inventory] Updating stock for {order.order_id}")
    await asyncio.sleep(1)
    return True  # Imagine database calls here

async def send_confirmation(order: Order, txn_id: str) -> bool:
    """Send order confirmation email.
    """
    logging.info(f"[Email] Sending receipt for {order.order_id}")
    await asyncio.sleep(1.5)
    if random.random() < 0.05:
        raise EmailServiceError("SMTP service unavailable")
    return True


# Core Order Processing Logic
# NOTE: All orchestration is manual with nested error handling

async def process_order(order: Order) -> str:
    """Main order fulfillment handler
    """
    txn_id = None  # Must track state manually
    
    # PHASE 1: Inventory Check (NO RETRIES - Fail fast if unavailable)
    try:
        await validate_inventory(order)
    except InventoryUnavailableError as e:
        logging.error(f"Inventory unavailable for {order.order_id}: {str(e)}")
        raise  # Business decision: Don't retry for stock issues

    # PHASE 2: Payment Processing (WITH RETRIES)
    last_payment_error = None
    for attempt in range(3):  # Retry declined payments
        try:
            txn_id = await process_payment(order)
            break  # Success! Exit retry loop
        except PaymentDeclinedError as e:
            last_payment_error = e
            if attempt == 2:  # Final attempt failed
                logging.error(f"Payment failed after 3 attempts: {str(e)}")
                raise
            await asyncio.sleep(1 * (attempt + 1))  # Linear backoff
            logging.warning(f"Retrying payment (attempt {attempt + 1}/3)...")

    # PHASE 3: Inventory Update 
    try:
        await update_inventory(order)
    except Exception as e:
        logging.critical(f"Inventory update failed after payment! {str(e)}")
        if txn_id:
            logging.warning(f"Attempting to refund {txn_id}...")
            # ... ( refund logic would go here)
        raise

    # PHASE 4: Confirmation 
    try:
        await send_confirmation(order, txn_id)
    except EmailServiceError as e:
        logging.warning(f"Non-critical email failure: {str(e)}")

    return f"Order {order.order_id} completed. Txn: {txn_id}"


# Test Harness
async def main():
    """Run a test order through the system."""
    order = Order(
        order_id="order_" + str(random.randint(1000, 9999)),
        user_id="user_123",
        items=[{"item_id": "prod_xyz", "quantity": 2}],
        total_amount=99.99
    )
    
    try:
        result = await process_order(order)
        print(f"✅ SUCCESS: {result}")
    except Exception as e:
        print(f"❌ FAILURE: {str(e)}")
        # In production, we'd need to persist this failure state

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())