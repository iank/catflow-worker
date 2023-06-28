from typing import Any, Tuple, List
from catflow_worker.worker import Worker
from catflow_worker.types import (
    VideoFileSchema,
    RawFrameSchema,
    EmbeddedFrameSchema,
    AnnotatedFrameSchema,
)
import signal
import asyncio


async def example_handler(
    msg: str, key: str, s3: Any, bucket: str
) -> Tuple[bool, Tuple[str, List[Any]]]:
    """Example message handler function"""

    # Map routing keys to schemas
    pipeline, data_type = key.split(".")
    schema_map = {
        "video": VideoFileSchema,
        "rawframes": RawFrameSchema,
        "embeddings": EmbeddedFrameSchema,
        "annotatedframes": AnnotatedFrameSchema,
    }

    schema = schema_map[data_type](many=True)
    msg_obj = schema.load(msg)

    print(f"[*] Message received ({key}): {msg_obj}")

    # If it's a video file, let's also get it from S3 and display some metadata
    if data_type == "video":
        s3key = msg_obj.key  # msg_obj is a catflow_worker.types.VideoFile()
        s3obj = await s3.get_object(Bucket=bucket, Key=s3key)
        obj_info = s3obj["ResponseMetadata"]["HTTPHeaders"]
        print(f"[-] Video {s3key}:")
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
