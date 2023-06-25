import pytest
import catflow_worker
import asyncio
import aioboto3
from io import BytesIO
import os
import json

from .mock_server import start_service
from .mock_server import stop_process

AMQP_EXCHANGE = "catflow-worker-pytest"
S3_ENDPOINT_URL = "http://localhost:5002"
AWS_BUCKET_NAME = "catflow-test"
AWS_ACCESS_KEY_ID = "catflow-worker-test-key"
AWS_SECRET_ACCESS_KEY = "catflow-worker-secret-key"

os.environ["CATFLOW_AMQP_EXCHANGE"] = AMQP_EXCHANGE
os.environ["CATFLOW_AWS_ACCESS_KEY_ID"] = AWS_ACCESS_KEY_ID
os.environ["CATFLOW_AWS_SECRET_ACCESS_KEY"] = AWS_SECRET_ACCESS_KEY
os.environ["CATFLOW_S3_ENDPOINT_URL"] = S3_ENDPOINT_URL
os.environ["CATFLOW_AWS_BUCKET_NAME"] = AWS_BUCKET_NAME


@pytest.fixture(scope="session")
def s3_server():
    host = "localhost"
    port = 5002
    url = "http://{host}:{port}".format(host=host, port=port)
    process = start_service("s3", host, port)
    yield url
    stop_process(process)


@pytest.mark.asyncio
async def test_worker(rabbitmq, s3_server):
    # Set up mock rabbitmq
    rmq_port = rabbitmq._impl.params.port
    os.environ["CATFLOW_AMQP_URL"] = f"amqp://guest:guest@localhost:{rmq_port}/"

    # Push some files to the mock S3
    session = aioboto3.Session(
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    )
    async with session.client("s3", endpoint_url=S3_ENDPOINT_URL) as s3:
        await s3.create_bucket(Bucket=AWS_BUCKET_NAME)
        await s3.upload_fileobj(
            BytesIO(bytes("filecontents1", "utf-8")), AWS_BUCKET_NAME, "test1"
        )
        await s3.upload_fileobj(
            BytesIO(bytes("filecontentsbatch1", "utf-8")), AWS_BUCKET_NAME, "testbatch1"
        )
        await s3.upload_fileobj(
            BytesIO(bytes("filecontentsbatch2", "utf-8")), AWS_BUCKET_NAME, "testbatch2"
        )
        await s3.upload_fileobj(
            BytesIO(bytes("filecontents3", "utf-8")), AWS_BUCKET_NAME, "fail3"
        )

    # Declare an exchange, we'll publish some test data to it
    channel = rabbitmq.channel()
    channel.exchange_declare(exchange=AMQP_EXCHANGE, exchange_type="topic")

    # Declare and bind a queue to receive 'responses' from the worker
    channel.queue_declare("pytest-responses")
    channel.queue_bind(
        exchange=AMQP_EXCHANGE, queue="pytest-responses", routing_key="test-response.*"
    )

    # Set up test handler and run it
    messages_received = []
    files_received = []

    async def _handler(msg, key, s3, bucket):
        nonlocal messages_received
        nonlocal files_received

        messages_received.append(key)

        for s3_key in msg:
            s3obj = await s3.get_object(Bucket=bucket, Key=s3_key)
            file_content = await s3obj["Body"].read()
            files_received.append(file_content.decode("utf-8"))

        if key == "test.key1":
            return True, [("test-response.key", [file_content.decode("utf-8")])]
        else:
            return True, []

    worker = await catflow_worker.Worker.create(
        _handler, "catflow-worker-testq", "test.*"
    )
    task = asyncio.create_task(worker.work())

    # Give the consumer a chance to connect and declare its queue, then publish messages
    await asyncio.sleep(1)
    channel.basic_publish(AMQP_EXCHANGE, "test.key1", json.dumps(["test1"]))
    channel.basic_publish(
        AMQP_EXCHANGE, "test.key2", json.dumps(["testbatch1", "testbatch2"])
    )
    channel.basic_publish(AMQP_EXCHANGE, "fail.key3", json.dumps(["fail3"]))

    # Wait a moment then shut it down
    await asyncio.sleep(1)
    await worker.shutdown()
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass

    assert len(messages_received) == 2
    assert len(files_received) == 3
    assert set(messages_received) == set(["test.key1", "test.key2"])
    assert set(files_received) == set(
        ["filecontents1", "filecontentsbatch1", "filecontentsbatch2"]
    )

    _, _, body = channel.basic_get("pytest-responses")
    assert json.loads(body) == ["filecontents1"]

    method_frame, _, _ = channel.basic_get("pytest-responses")
    assert method_frame is None, "too many responses"
