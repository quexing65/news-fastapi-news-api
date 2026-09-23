# 收藏列表缓存方法
from typing import Optional, Dict, Any

from config.cache_conf import get_json_cache, set_cache, delete_pattern_cache

FAVORITE_LIST_PREFIX = "favorite:list:"


# 获取收藏列表缓存 key = favorite:list:用户id:页码:每页数量
async def get_cached_favorite_list(user_id: int, page: int, page_size: int) -> Optional[Dict[str, Any]]:
    key = f"{FAVORITE_LIST_PREFIX}{user_id}:{page}:{page_size}"
    return await get_json_cache(key)


# 写入收藏列表缓存，用户维度数据，缓存 5 分钟
async def set_cached_favorite_list(user_id: int, page: int, page_size: int, data: Dict[str, Any], expire: int = 300) -> bool:
    key = f"{FAVORITE_LIST_PREFIX}{user_id}:{page}:{page_size}"
    return await set_cache(key, data, expire)


# 清除该用户的所有收藏列表缓存（收藏增删改后调用）
async def invalidate_favorite_cache(user_id: int):
    await delete_pattern_cache(f"{FAVORITE_LIST_PREFIX}{user_id}:*")
