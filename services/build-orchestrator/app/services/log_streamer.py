import json
import logging
from datetime import datetime, timezone
from app.core.redis import redis_client

logger = logging.getLogger(__name__)

class LogStreamer:
    async def stream_logs(self, container, deployment_id: str) -> list[str]:
        """Streams stdout/stderr from aiodocker container to Redis Pub/Sub"""
        line_number = 0
        channel = f"build:{deployment_id}:logs"
        log_buffer = []
        
        logger.info(f"Started streaming logs to Redis channel {channel}")
        
        try:
            # aiodocker log streaming
            async for log in container.log(stdout=True, stderr=True, follow=True):
                # log might be bytes or string depending on TTY config
                if isinstance(log, bytes):
                    # aiodocker multiplexed format: 8 byte header + payload
                    if len(log) > 8:
                        text = log[8:].decode('utf-8', errors='replace').strip()
                    else:
                        continue
                else:
                    text = str(log).strip()
                    
                if not text:
                    continue
                    
                for line in text.splitlines():
                    line_number += 1
                    log_buffer.append(line)
                    payload = {
                        "line": line,
                        "line_number": line_number,
                        "ts": datetime.now(timezone.utc).isoformat()
                    }
                    await redis_client.publish(channel, json.dumps(payload))
                    # In a real app, also publish to Kafka for archival
                    
        except Exception as e:
            logger.error(f"Error streaming logs for {deployment_id}: {e}")
            error_line = f"Internal system error: {e}"
            log_buffer.append(error_line)
            await redis_client.publish(channel, json.dumps({
                "line": error_line,
                "line_number": line_number + 1,
                "ts": datetime.now(timezone.utc).isoformat()
            }))
            
        return log_buffer

log_streamer = LogStreamer()
