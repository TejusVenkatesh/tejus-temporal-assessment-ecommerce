import asyncio
from temporalio.client import Client
from temporalio.worker import Worker
from workflows import OrderProcessingWorkflow
from activities import (
    validate_inventory,
    process_payment,
    update_inventory,
    send_confirmation
)

async def main():
    # Connect to local Temporal server
    client = await Client.connect("localhost:7233")
    
    # Run worker
    worker = Worker(
        client,
        task_queue="ECOMMERCE_TASK_QUEUE",
        workflows=[OrderProcessingWorkflow],
        activities=[
            validate_inventory,
            process_payment,
            update_inventory,
            send_confirmation
        ]
    )
    print("Worker started. Ctrl+C to exit.")
    await worker.run()

if __name__ == "__main__":
    asyncio.run(main())