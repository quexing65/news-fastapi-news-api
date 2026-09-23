# 用户信息缓存方法
from typing import Optional, Dict, Any

from config.cache_conf import get_json_cache, set_cache, delete_cache

USER_INFO_PREFIX = "user:info:"


# 获取用户信息缓存
async def get_cached_user_info(user_id: int) -> Optional[Dict[str, Any]]:
    key = f"{USER_INFO_PREFIX}{user_id}"
    return await get_json_cache(key)


# 写入用户信息缓存，用户信息相对稳定，缓存 10 分钟
async def set_cached_user_info(user_id: int, data: Dict[str, Any], expire: int = 600) -> bool:
    key = f"{USER_INFO_PREFIX}{user_id}"
    return await set_cache(key, data, expire)


# 清除用户信息缓存（用户信息更新或修改密码后调用）
async def invalidate_user_info(user_id: int):
    await delete_cache(f"{USER_INFO_PREFIX}{user_id}")
