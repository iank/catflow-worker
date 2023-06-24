from typing import Callable, Any
import os
import aio_pika
import aioboto3


class Producer:
    @classmethod
    async def create(cls, url, exchange_name):
        self = Producer()
        self.connection = await aio_pika.connect_robust(url)
        self.channel = await self.connection.channel()
        self.exchange = await self.channel.declare_exchange(exchange_name, "topic")

        return self

    async def send_to_rabbitmq(self, routing_key, message_str):
        message = aio_pika.Message(body=message_str.encode())
        return await self.exchange.publish(message, routing_key=routing_key)

    async def close(self):
        return await self.connection.close()


async def work(handler: Callable[..., Any], queue_name: str, topics: str) -> bool:
    """Connects to AMQP, S3, and gets/publishes messages using the provided handler"""

    # Connect to AMQP
    producer = await Producer.create(
        os.environ["CATFLOW_AMQP_URL"],
        os.environ["CATFLOW_AMQP_EXCHANGE"],
    )

    # Connect to S3
    bucket_name = os.environ["CATFLOW_AWS_BUCKET_NAME"]
    session = aioboto3.Session(
        aws_access_key_id=os.environ["CATFLOW_AWS_ACCESS_KEY_ID"],
        aws_secret_access_key=os.environ["CATFLOW_AWS_SECRET_ACCESS_KEY"],
    )
    async with session.client(
        "s3", endpoint_url=os.environ["CATFLOW_S3_ENDPOINT_URL"]
    ) as s3:
        # Declare queue, bind, and get messages
        queue = await producer.channel.declare_queue(queue_name, auto_delete=True)
        await queue.bind(producer.exchange, routing_key=topics)

        # Wait for messages
        async with queue.iterator() as queue_iter:
            async for message in queue_iter:
                # Call handler for each message
                ok, responses = await handler(
                    message.body.decode(), message.routing_key, s3, bucket_name
                )
                # Acknowledge if the handler has succeeded, but we'll assume
                # that if they've provided responses AND a failure status that
                # they still want the responses to be sent, so we'll hold off
                # on exiting
                if ok:
                    await message.ack()

                # Send responses
                for response in responses:
                    routing_key, message = response
                    await producer.send_to_rabbitmq(routing_key, message)

                # Exit if the handler has failed
                if not ok:
                    await producer.close()
                    return False
