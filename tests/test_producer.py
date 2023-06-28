from catflow_worker.worker import Producer
import pytest


@pytest.mark.asyncio
async def test_send_to_rabbitmq(rabbitmq):
    """Test that send_to_rabbitmq sends a message to an exchange"""
    # Mock setup
    rmq_port = rabbitmq._impl.params.port
    rabbitmq_url = f"amqp://guest:guest@localhost:{rmq_port}/"
    channel = rabbitmq.channel()
    channel.exchange_declare(exchange="test-exchange", exchange_type="topic")
    channel.queue_declare("testkey_queue")
    channel.queue_bind(
        exchange="test-exchange", queue="testkey_queue", routing_key="testkey"
    )

    # Object under test
    producer = await Producer.create(rabbitmq_url, "test-exchange")
    await producer.send_to_rabbitmq("testkey", "test message")
    await producer.close()

    # Verify
    _, _, body = channel.basic_get("testkey_queue")
    assert body.decode() == "test message"
