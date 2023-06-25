from typing import Any, Tuple, List
from catflow_worker.worker import Worker
import signal
import asyncio


async def example_handler(
    msg: str, key: str, s3: Any, bucket: str
) -> Tuple[bool, List[Tuple[str, str]]]:
    """Example message handler function

    Queries S3 for metadata about the object in the message and displays it."""
    print(f"[*] Message received ({key}):")

    for s3key in msg:
        s3obj = await s3.get_object(Bucket=bucket, Key=s3key)
        obj_info = s3obj["ResponseMetadata"]["HTTPHeaders"]
        print(f"[-] {s3key}:")
        print(f"    Content-Type {obj_info['content-type']}")
        print(f"    Content-Length {obj_info['content-length']}")

    return True, []


async def shutdown(worker, task):
    await worker.shutdown()
    task.cancel()
    try:
        await task
    except asyncio.exceptions.CancelledError:
        pass


async def main(topic_key: str) -> bool:
    """Run an example worker"""

    worker = await Worker.create(example_handler, "catflow-worker-example", topic_key)
    task = asyncio.create_task(worker.work())

    def handle_sigint(sig, frame):
        print("^ SIGINT received, shutting down...")
        asyncio.create_task(shutdown(worker, task))

    signal.signal(signal.SIGINT, handle_sigint)

    try:
        if not await task:
            print("[!] Exited with error")
            return False
    except asyncio.exceptions.CancelledError:
        return True

    return True
