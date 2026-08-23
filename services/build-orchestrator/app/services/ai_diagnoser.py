import json
import logging
from groq import AsyncGroq
from app.core.config import settings
from app.core.redis import redis_client

logger = logging.getLogger(__name__)

class AiDiagnoser:
    def __init__(self):
        self.groq_client = None
        if settings.GROQ_API_KEY:
            self.groq_client = AsyncGroq(api_key=settings.GROQ_API_KEY)
        else:
            logger.warning("GROQ_API_KEY not set. AI Diagnosis will be disabled.")

    def _build_prompt(self, log_lines: list[str], error: str) -> str:
        # Take the last 100 lines of logs to keep the context window reasonable
        log_tail = "\n".join(log_lines[-100:])
        return f"""You are an expert build engineer and CI/CD specialist.
A user's automated build has failed. Analyze the build logs below 
and provide a clear, developer-friendly diagnosis.

Your response must be structured exactly like this:
**Root Cause:** (1-2 sentences: what went wrong)
**Evidence:** (2-3 relevant log lines that confirm the issue)
**Fix:** (concrete, actionable steps — code changes or commands)

Keep the total response under 200 words. Be specific and direct.

--- ERROR ---
{error}

--- BUILD LOGS (last 100 lines) ---
{log_tail}
"""

    async def diagnose(self, deployment_id: str, log_lines: list[str], error: str):
        if not self.groq_client:
            logger.warning("Skipping AI diagnosis due to missing Groq API Key.")
            return

        channel = f"build:{deployment_id}:ai_diagnosis"
        
        try:
            logger.info(f"Starting AI diagnosis for deployment {deployment_id}")
            
            # Publish a "started" signal
            await redis_client.publish(channel, json.dumps({"type": "ai_start"}))
            
            prompt = self._build_prompt(log_lines, error)
            
            # Stream Groq response token by token
            stream = await self.groq_client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "user", "content": prompt}],
                stream=True,
            )
            
            async for chunk in stream:
                text = chunk.choices[0].delta.content or ""
                if text:
                    await redis_client.publish(channel, json.dumps({
                        "type": "ai_token",
                        "text": text
                    }))
                    
            logger.info(f"AI diagnosis completed for {deployment_id}")
                    
        except Exception as e:
            logger.error(f"AI diagnosis failed for {deployment_id}: {e}")
            await redis_client.publish(channel, json.dumps({
                "type": "ai_token",
                "text": f"\n\n*AI Diagnosis failed: {str(e)}*"
            }))
        finally:
            # Signal completion
            await redis_client.publish(channel, json.dumps({"type": "ai_done"}))

ai_diagnoser = AiDiagnoser()
