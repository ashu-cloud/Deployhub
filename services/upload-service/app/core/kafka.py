import json
import logging
from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
from app.core.config import settings

logger = logging.getLogger(__name__)

class KafkaClient:
    def __init__(self):
        self.producer = None
        self.consumer = None
        self._consume_task = None

    async def start(self, message_handler=None):
        sasl_kwargs = {}
        if settings.KAFKA_SASL_USERNAME:
            import ssl
            sasl_kwargs = {
                "security_protocol": settings.KAFKA_SECURITY_PROTOCOL or "SASL_SSL",
                "sasl_mechanism": settings.KAFKA_SASL_MECHANISM or "PLAIN",
                "sasl_plain_username": settings.KAFKA_SASL_USERNAME,
                "sasl_plain_password": settings.KAFKA_SASL_PASSWORD,
            }
            if sasl_kwargs["security_protocol"] == "SASL_SSL":
                ctx = ssl.create_default_context()
                ctx.check_hostname = False
                ctx.verify_mode = ssl.CERT_NONE
                sasl_kwargs["ssl_context"] = ctx
        # Start Producer
        self.producer = AIOKafkaProducer(
            bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            acks="all",
            enable_idempotence=True,
            **sasl_kwargs
        )
        await self.producer.start()

        # Start Consumer
        if message_handler:
            self.consumer = AIOKafkaConsumer(
                "build.completed",
                bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
                group_id="upload-service-cg",
                enable_auto_commit=False,
                value_deserializer=lambda x: json.loads(x.decode('utf-8')),
                **sasl_kwargs
            )
            await self.consumer.start()
            import asyncio
            self._consume_task = asyncio.create_task(self._consume_loop(message_handler))
            
            # QUAL-02: Prevent garbage collection and log silent crashes
            def _on_task_done(t):
                if not t.cancelled() and t.exception():
                    logger.error(f"Kafka consumer task died: {t.exception()}")
            self._consume_task.add_done_callback(_on_task_done)

    async def _consume_loop(self, handler):
        try:
            async for msg in self.consumer:
                logger.info(f"Received build.completed event for project: {msg.key.decode('utf-8') if msg.key else 'None'}")
                try:
                    await handler(msg.value)
                    await self.consumer.commit()
                except Exception as e:
                    logger.error(f"Error processing upload: {e}")
        except Exception as e:
            logger.error(f"Kafka consumer error: {e}")

    async def stop(self):
        if self._consume_task:
            self._consume_task.cancel()
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
