from frontend_bot.config.external_services import ExternalServicesConfig
import redis.asyncio as aioredis

config = ExternalServicesConfig()
redis_client = aioredis.from_url(config.redis_url, decode_responses=False) 