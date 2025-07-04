import asyncio
from datetime import timedelta
import uuid
from temporalio.client import Client
from temporalio.exceptions import ApplicationError
from shared import Order, TASK_QUEUE
from workflows import OrderProcessingWorkflow

async def main():
    print("🚀 Connecting to Temporal server...")
    client = await Client.connect("localhost:7233")
    print("✅ Connected to Temporal server.")

    # Create sample order
    unique_order_id = str(uuid.uuid4())
    order = Order(
        order_id=unique_order_id,
        user_id="user-456",
        items=[{"item_id": "item-789", "quantity": 2}],
        total_amount=99.99
    )

    try:
        print(f"\n✨ Starting OrderProcessingWorkflow for Order ID: {order.order_id}...")
        

        final_status: str = await client.execute_workflow(
            OrderProcessingWorkflow.run,
            order,
            id=f"order-{order.order_id}", # Ensure Workflow ID is unique
            task_queue=TASK_QUEUE,
            execution_timeout=timedelta(minutes=10)
        )
        
        print(f"\n🎉 Workflow finished for Order ID: {order.order_id} with status: {final_status}")

    except ApplicationError as ae:
        # This block catches errors that occur *within* the workflow's execution
        print(f"\n❌ Workflow failed during execution for Order ID {order.order_id}:")
        print(f"   Workflow Error Type: {ae.type}")
        if ae.message:
            print(f"   Message: {ae.message}")
        if ae.cause: # The underlying cause (e.g., specific activity error)
            print(f"   Cause: {str(ae.cause)}")
        # No workflow_handle to get ID/Run ID from if it failed to return it in the first place

    except Exception as e:
        # This block catches any other unexpected errors (e.g., connection errors,
        # immediate client-side validation errors before starting workflow).
        print(f"\n❌ FAILED to start or establish Workflow for Order ID {order.order_id}: {str(e)}")
        # No workflow_handle to get ID/Run ID from if it failed to return it in the first place


if __name__ == "__main__":
    asyncio.run(main())