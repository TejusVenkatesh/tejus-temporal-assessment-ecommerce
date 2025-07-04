from datetime import timedelta
from temporalio import workflow
from temporalio.common import RetryPolicy
from temporalio.exceptions import ActivityError
from shared import Order, WORKFLOW_TIMEOUT

# Import the activities and custom exceptions defined in activities.py
from activities import (
    validate_inventory,
    process_payment,
    update_inventory,
    send_confirmation,
    InventoryUnavailableError,
    PaymentDeclinedError,
    EmailServiceError
)

@workflow.defn
class OrderProcessingWorkflow:
    """
    Temporal Workflow for processing an e-commerce order.

    This workflow orchestrates the following business activities:
      1. Inventory validation
      2. Payment processing
      3. Inventory update (post-payment)
      4. Sending order confirmation email

    Each activity is executed with appropriate retry policies and error handling.
    Custom exceptions are used to distinguish between retryable and non-retryable errors,
    allowing for fine-grained workflow control and compensation logic.

    Args:
        order (Order): The order object containing order details.

    Returns:
        str: A status message indicating the result of the workflow execution.
    """

    @workflow.run
    async def run(self, order: Order) -> str:
        """
        Main entrypoint for the OrderProcessingWorkflow.

        Orchestrates the order fulfillment process by sequentially executing
        business activities with robust error handling and retry logic.

        Args:
            order (Order): The order to be processed.

        Returns:
            str: Final status of the order processing.
        """
        workflow.logger.info(f"⚡ Workflow started for order_id: {order.order_id}")


        txn_id: str | None = None

        # 1. Validate Inventory
        try:
            workflow.logger.info(f"Attempting to validate inventory for order {order.order_id}...")
            await workflow.execute_activity(
                validate_inventory,
                order,
                start_to_close_timeout=timedelta(seconds=5),
                # Retry policy for inventory validation
                # This will retry the activity if it fails due to InventoryUnavailableError
                # up to 3 times with exponential backoff.
                # If the error is InventoryUnavailableError, it will not retry.
                # This allows the workflow to gracefully handle inventory issues without failing immediately.
                # This is the best feature of Temporal Workflows, as it allows for retrying
                # activities that are likely to succeed on subsequent attempts, while also
                # allowing for non-retryable errors to be handled gracefully.
                retry_policy=RetryPolicy(
                    initial_interval=timedelta(seconds=1),
                    maximum_interval=timedelta(seconds=10),
                    maximum_attempts=3,
                    non_retryable_error_types=[InventoryUnavailableError.__name__]
                )
            )
            workflow.logger.info(f"Inventory validated for order {order.order_id}.")
        except ActivityError as e:
            # If inventory is unavailable, fail the workflow gracefully
            if isinstance(e.cause, InventoryUnavailableError):
                workflow.logger.error(f"Inventory unavailable for order {order.order_id}. Workflow failed.")
                return f"Order {order.order_id} failed: Inventory unavailable."
            # Propagate other errors
            raise

        # 2. Process Payment
        try:
            workflow.logger.info(f"Attempting to process payment for order {order.order_id}...")
            txn_id = await workflow.execute_activity(
                process_payment,
                order,
                start_to_close_timeout=timedelta(seconds=10),
                
                retry_policy=RetryPolicy(
                    initial_interval=timedelta(seconds=1),
                    maximum_interval=timedelta(seconds=5),
                    maximum_attempts=5, # Retry up to 5 times for payment processing as payment failures are common
                    non_retryable_error_types=[PaymentDeclinedError.__name__]
                )
            )
            workflow.logger.info(f"Payment processed successfully for order {order.order_id}. Tx ID: {txn_id}")
        except ActivityError as e:
            # If payment is declined, fail the workflow gracefully
            if isinstance(e.cause, PaymentDeclinedError):
                workflow.logger.error(f"Payment explicitly declined for order {order.order_id}.")
                return f"Order {order.order_id} failed: Payment declined."
            raise

        # 3. Update Inventory (after payment)
        try:
            workflow.logger.info(f"Attempting to update inventory for order {order.order_id}...")
            await workflow.execute_activity(
                update_inventory,
                order,
                start_to_close_timeout=timedelta(seconds=5),
                retry_policy=RetryPolicy(
                    initial_interval=timedelta(seconds=1),
                    maximum_interval=timedelta(seconds=10),
                    maximum_attempts=3
                )
            )
            workflow.logger.info(f"Inventory updated for order {order.order_id}.")
        except ActivityError as e:
            # If inventory update fails after payment, log and return failure.
            workflow.logger.error(f"Inventory update failed for order {order.order_id}: {e}. Initiating compensation if possible.")
            return f"Order {order.order_id} failed: Inventory update failed. Payment possibly refunded."

        # 4. Send Confirmation
        try:
            workflow.logger.info(f"Attempting to send confirmation email for order {order.order_id}...")
            await workflow.execute_activity(
                send_confirmation,
                args=[order, txn_id],  # Pass multiple arguments as a list
                start_to_close_timeout=timedelta(seconds=5),
                retry_policy=RetryPolicy(
                    initial_interval=timedelta(seconds=1),
                    maximum_interval=timedelta(seconds=5),
                    maximum_attempts=2,
                    non_retryable_error_types=[EmailServiceError.__name__]
                )
            )
            workflow.logger.info(f"Confirmation email sent for order {order.order_id}.")
        except ActivityError as e:
            # If confirmation email fails, log a warning but do not fail the workflow
            workflow.logger.warning(f"Failed to send confirmation email for order {order.order_id}: {e}. Order is still processed.")
            pass

        workflow.logger.info(f"✅ Order {order.order_id} fulfillment process complete!")
        return f"Order {order.order_id} completed successfully. Transaction: {txn_id}"