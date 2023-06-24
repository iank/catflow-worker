from typing import Any, Tuple, List
import catflow_worker.worker


async def example_handler(
    msg: str, key: str, s3: Any, bucket: str
) -> Tuple[bool, List[Tuple[str, str]]]:
    """Example message handler function

    Queries S3 for metadata about the object in the message and displays it."""
    print(f"[*] Message received ({key}): {msg}")
    s3obj = await s3.get_object(Bucket=bucket, Key=msg)
    obj_info = s3obj["ResponseMetadata"]["HTTPHeaders"]
    print(f"[-] Content-Type {obj_info['content-type']}")
    print(f"[-] Content-Length {obj_info['content-length']}")

    return True, []


async def main(topic_key: str) -> bool:
    """Run an example worker"""

    if not await catflow_worker.worker.work(
        example_handler, "catflow-worker-example", topic_key
    ):
        print("[!] Exited with error")
        return False

    return True
