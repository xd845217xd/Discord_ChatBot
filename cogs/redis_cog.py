import os
import redis.asyncio as redis
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

class RedisCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.redis_client = None

    async def redis_connect(self):
        redis_url = os.getenv('REDIS_URL')
        self.redis_client = await redis.from_url(redis_url, encoding="utf-8", decode_responses=True)
        
    async def redis_close(self):
        if self.redis_client:
            await self.redis_client.close()

    async def redis_set(self, key, value, ex=None):
        await self.redis_client.set(key, value, ex=ex)

    async def redis_get(self, key):
        return await self.redis_client.get(key)

    async def redis_delete(self, key):
        await self.redis_client.delete(key)

    async def redis_exists(self, key):
        return await self.redis_client.exists(key)

    def get_prefixed_key(self, cog_name: str, key: str) -> str:
        return f"{cog_name}:{key}"

    async def is_redis_connected(self) -> bool:
        try:
            await self.redis_client.ping()
            return True
        except:
            return False

async def setup(bot):
    redis_cog = RedisCog(bot)
    await redis_cog.redis_connect()
    await bot.add_cog(redis_cog)