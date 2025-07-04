import random
import logging
import asyncio 
from temporalio import activity
from shared import Order


# Activities are the building blocks of workflows in Temporal and it is best to start with defining them first



# Defining specific exceptions for better error handling in workflow
class InventoryUnavailableError(Exception): pass
class PaymentDeclinedError(Exception): pass
class EmailServiceError(Exception): pass


# Using the @activity.defn decorator to define activities

# Starting wtih the inventory validation activity, which checks if all items in the order are in stock.
@activity.defn
async def validate_inventory(order: Order) -> bool:
    """Check if all items are in stock"""
    logging.info(f"Validating inventory for order {order.order_id}")
    await asyncio.sleep(1) # Simulate inventory check delay
    if random.random() < 0.1:
        raise InventoryUnavailableError("Inventory service unavailable or item out of stock") # <--- USE CUSTOM EXCEPTION
    return True


# Next, we define the payment processing activity, which simulates payment processing and can fail.
# I have used 0.3 as the failure rate for payment processing are typically higher than inventory checks and other activities.
@activity.defn
async def process_payment(order: Order) -> str:
    """Process payment and return transaction ID"""
    logging.info(f"Processing payment for order {order.order_id}")
    await asyncio.sleep(2) # Simulate payment processing delay
    if random.random() < 0.3:
        raise PaymentDeclinedError("Payment declined by gateway") # <--- USE CUSTOM EXCEPTION
    return f"txn_{order.order_id}_{random.randint(1000, 9999)}" # Add random suffix for uniqueness


# Finally, we define the inventory update activity, which updates the inventory after a successful payment.
# This activity does not fail in this example, but you can add failure conditions if needed.
# Note that if the payment fails, this activity will not be called, as the workflow logic will handle retries and failures.
@activity.defn
async def update_inventory(order: Order) -> bool:
    """Update inventory after successful payment"""
    logging.info(f"Updating inventory for order {order.order_id}")
    await asyncio.sleep(1) # Simulate inventory update delay
    # Not adding any specific failure condition here, assuming inventory update is always successful
    # even if there was a payment failure, retry logic in the workflow will handle it
    return True

# Lastly, we define the confirmation email sending activity, which simulates sending an email confirmation.
# This activity can also fail, simulating a scenario where the email service is temporarily unavailable.
# I have used a 5% failure rate for email sending, which is the lowest in this example, as email services are generally reliable.
@activity.defn
async def send_confirmation(order: Order, txn_id: str) -> bool:
    """Send order confirmation email"""
    logging.info(f"Sending confirmation for order {order.order_id} with transaction {txn_id}")
    await asyncio.sleep(1.5) # Simulate email sending delay
    if random.random() < 0.05:
        raise EmailServiceError("Email service unavailable") 
    return True

