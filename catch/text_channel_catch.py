from typing import Optional
from cogs.redis_cog import RedisCog

class TextChannelCache:
    def __init__(self, redis_cog: RedisCog):
        self.redis_cog = redis_cog

    async def get_latest_message_id(self, guild_id: str, channel_id: str, user_id: int) -> Optional[int]:
        key = self.redis_cog.get_prefixed_key(
            "text_channel",
            f"latest_message_id:{guild_id}:{channel_id}:{user_id}"
        )
        value = await self.redis_cog.redis_get(key)
        return int(value) if value else None

    async def update_latest_message_id(self, guild_id: str, channel_id: str, user_id: int, message_id: int):
        key = self.redis_cog.get_prefixed_key(
            "text_channel",
            f"latest_message_id:{guild_id}:{channel_id}:{user_id}"
        )
        await self.redis_cog.redis_set(key, str(message_id))

    async def delete_latest_message_id(self, guild_id: str, channel_id: str, user_id: int):
        key = self.redis_cog.get_prefixed_key(
            "text_channel",
            f"latest_message_id:{guild_id}:{channel_id}:{user_id}"
        )
        await self.redis_cog.redis_delete(key)