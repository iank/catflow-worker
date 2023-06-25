from typing import Callable, Any
import os
import aio_pika
import aioboto3
import json


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


class Worker:
    """Connects to AMQP, S3, and gets/publishes messages using the provided handler"""

    @classmethod
    async def create(
        cls, handler: Callable[..., Any], queue_name: str, topics: str
    ) -> "Worker":
        self = Worker()

        self.handler = handler
        self.queue_name = queue_name
        self.topics = topics

        # Connect to AMQP
        self.producer = await Producer.create(
            os.environ["CATFLOW_AMQP_URL"],
            os.environ["CATFLOW_AMQP_EXCHANGE"],
        )

        return self

    async def shutdown(self):
        return await self.producer.close()

    async def work(self) -> bool:
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
            queue = await self.producer.channel.declare_queue(
                self.queue_name, auto_delete=True
            )
            await queue.bind(self.producer.exchange, routing_key=self.topics)

            # Wait for messages
            async with queue.iterator() as queue_iter:
                async for message in queue_iter:
                    # Call handler for each message
                    ok, responses = await self.handler(
                        json.loads(message.body), message.routing_key, s3, bucket_name
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
                        await self.producer.send_to_rabbitmq(
                            routing_key, json.dumps(message)
                        )

                    # Exit if the handler has failed
                    if not ok:
                        await self.producer.close()
                        return False
