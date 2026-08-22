import json
import logging
from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
from app.core.config import settings

logger = logging.getLogger(__name__)

class KafkaClient:
    def __init__(self):
        self.producer = None
        self.consumer = None

    async def start(self, message_handler=None):
        # Start Producer
        self.producer = AIOKafkaProducer(
            bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            acks="all",
            enable_idempotence=True
        )
        await self.producer.start()

        # Start Consumer
        if message_handler:
            self.consumer = AIOKafkaConsumer(
                "deployment.uploaded",
                bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
                group_id="deployment-service-cg",
                enable_auto_commit=False,
                value_deserializer=lambda x: json.loads(x.decode('utf-8'))
            )
            await self.consumer.start()
            import asyncio
            asyncio.create_task(self._consume_loop(message_handler))

    async def _consume_loop(self, handler):
        try:
            async for msg in self.consumer:
                logger.info(f"Received deployment.uploaded event for project: {msg.key.decode('utf-8') if msg.key else 'None'}")
                try:
                    await handler(msg.value)
                    await self.consumer.commit()
                except Exception as e:
                    logger.error(f"Error processing deployment: {e}")
        except Exception as e:
            logger.error(f"Kafka consumer error: {e}")

    async def stop(self):
        if self.consumer:
            await self.consumer.stop()
        if self.producer:
            await self.producer.stop()

    async def send_event(self, topic: str, value: dict, key: str = None):
        if not self.producer:
            raise RuntimeError("Kafka producer not initialized")
        key_bytes = key.encode('utf-8') if key else None
        await self.producer.send_and_wait(topic, value=value, key=key_bytes)

kafka_client = KafkaClient()
