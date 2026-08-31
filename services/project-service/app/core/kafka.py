from aiokafka import AIOKafkaProducer
import json
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

class KafkaProducerClient:
    def __init__(self):
        self.producer = None

    async def start(self):
        sasl_kwargs = {}
        if settings.KAFKA_SASL_USERNAME:
            sasl_kwargs = {
                "security_protocol": settings.KAFKA_SECURITY_PROTOCOL or "SASL_SSL",
                "sasl_mechanism": settings.KAFKA_SASL_MECHANISM or "PLAIN",
                "sasl_plain_username": settings.KAFKA_SASL_USERNAME,
                "sasl_plain_password": settings.KAFKA_SASL_PASSWORD,
            }
        self.producer = AIOKafkaProducer(
            bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            acks="all",
            enable_idempotence=True,
            **sasl_kwargs
        )
        await self.producer.start()
        logger.info("Kafka producer started")

    async def stop(self):
        if self.producer:
            await self.producer.stop()
            logger.info("Kafka producer stopped")

    async def send_event(self, topic: str, value: dict, key: str = None):
        if not self.producer:
            raise RuntimeError("Kafka producer not initialized")
        
        # Use key for partitioning (e.g. project_id) so events for same project are ordered
        key_bytes = key.encode('utf-8') if key else None
        await self.producer.send_and_wait(topic, value=value, key=key_bytes)

kafka_client = KafkaProducerClient()
