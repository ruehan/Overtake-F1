import json
import asyncio
from typing import Optional, Any, Dict, Union
from datetime import datetime, timedelta
import hashlib
import pickle
import redis.asyncio as redis
from contextlib import asynccontextmanager

from app.config import settings
from app.models.user_models import CacheEntry

class CacheService:
    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
        self._connection_pool = None
        
    async def connect(self):
        """Connect to Redis"""
        try:
            self._connection_pool = redis.ConnectionPool.from_url(
                settings.redis_url,
                decode_responses=True,
                max_connections=20
            )
            self.redis_client = redis.Redis(connection_pool=self._connection_pool)
            
            # Test connection
            await self.redis_client.ping()
            print("✅ Redis connection established")
            
        except Exception as e:
            print(f"❌ Redis connection failed: {e}")
            # Fall back to in-memory cache if Redis is not available
            self.redis_client = None
            self._memory_cache = {}
            print("📝 Using in-memory cache as fallback")
    
    async def close(self):
        """Close Redis connection"""
        if self.redis_client:
            await self.redis_client.close()
        if self._connection_pool:
            await self._connection_pool.disconnect()
    
    def _generate_cache_key(self, namespace: str, **kwargs) -> str:
        """Generate a unique cache key"""
        # Create a sorted string from kwargs for consistent hashing
        key_parts = [f"{k}:{v}" for k, v in sorted(kwargs.items()) if v is not None]
        key_string = "|".join(key_parts)
        
        # Hash the key string to keep it short and consistent
        key_hash = hashlib.md5(key_string.encode()).hexdigest()
        
        return f"{namespace}:{key_hash}"
    
    async def get(self, namespace: str, **kwargs) -> Optional[Any]:
        """Get data from cache"""
        cache_key = self._generate_cache_key(namespace, **kwargs)
        
        if self.redis_client:
            try:
                cached_data = await self.redis_client.get(cache_key)
                if cached_data:
                    # Increment hit count
                    await self.redis_client.hincrby(f"{cache_key}:meta", "hit_count", 1)
                    return json.loads(cached_data)
            except Exception as e:
                print(f"Redis get error: {e}")
        else:
            # Fallback to memory cache
            cache_entry = self._memory_cache.get(cache_key)
            if cache_entry and not cache_entry.is_expired:
                cache_entry.hit_count += 1
                return cache_entry.data
            elif cache_entry and cache_entry.is_expired:
                del self._memory_cache[cache_key]
        
        return None
    
    async def set(
        self, 
        namespace: str, 
        data: Any, 
        ttl_seconds: int = 300,  # 5 minutes default
        **kwargs
    ) -> bool:
        """Set data in cache"""
        cache_key = self._generate_cache_key(namespace, **kwargs)
        
        if self.redis_client:
            try:
                # Store the data
                serialized_data = json.dumps(data, default=str)
                await self.redis_client.setex(cache_key, ttl_seconds, serialized_data)
                
                # Store metadata
                metadata = {
                    "created_at": datetime.utcnow().isoformat(),
                    "expires_at": (datetime.utcnow() + timedelta(seconds=ttl_seconds)).isoformat(),
                    "hit_count": 0
                }
                await self.redis_client.hmset(f"{cache_key}:meta", metadata)
                await self.redis_client.expire(f"{cache_key}:meta", ttl_seconds)
                
                return True
            except Exception as e:
                print(f"Redis set error: {e}")
        else:
            # Fallback to memory cache
            expires_at = datetime.utcnow() + timedelta(seconds=ttl_seconds)
            cache_entry = CacheEntry(
                key=cache_key,
                data=data,
                expires_at=expires_at
            )
            self._memory_cache[cache_key] = cache_entry
            return True
        
        return False
    
    async def delete(self, namespace: str, **kwargs) -> bool:
        """Delete data from cache"""
        cache_key = self._generate_cache_key(namespace, **kwargs)
        
        if self.redis_client:
            try:
                deleted_count = await self.redis_client.delete(cache_key, f"{cache_key}:meta")
                return deleted_count > 0
            except Exception as e:
                print(f"Redis delete error: {e}")
        else:
            # Fallback to memory cache
            if cache_key in self._memory_cache:
                del self._memory_cache[cache_key]
                return True
        
        return False
    
    async def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching a pattern"""
        if self.redis_client:
            try:
                keys = await self.redis_client.keys(pattern)
                if keys:
                    deleted_count = await self.redis_client.delete(*keys)
                    # Also delete metadata keys
                    meta_keys = [f"{key}:meta" for key in keys]
                    await self.redis_client.delete(*meta_keys)
                    return deleted_count
                return 0
            except Exception as e:
                print(f"Redis delete pattern error: {e}")
        else:
            # Fallback to memory cache
            import fnmatch
            keys_to_delete = [
                key for key in self._memory_cache.keys() 
                if fnmatch.fnmatch(key, pattern)
            ]
            for key in keys_to_delete:
                del self._memory_cache[key]
            return len(keys_to_delete)
        
        return 0
    
    async def get_cache_stats(self, namespace: str) -> Dict[str, Any]:
        """Get cache statistics for a namespace"""
        if self.redis_client:
            try:
                pattern = f"{namespace}:*"
                keys = await self.redis_client.keys(pattern)
                meta_keys = [f"{key}:meta" for key in keys if not key.endswith(":meta")]
                
                total_keys = len([key for key in keys if not key.endswith(":meta")])
                total_hits = 0
                
                for meta_key in meta_keys:
                    hit_count = await self.redis_client.hget(meta_key, "hit_count")
                    if hit_count:
                        total_hits += int(hit_count)
                
                return {
                    "namespace": namespace,
                    "total_keys": total_keys,
                    "total_hits": total_hits,
                    "hit_rate": total_hits / max(total_keys, 1)
                }
            except Exception as e:
                print(f"Redis stats error: {e}")
        else:
            # Fallback to memory cache
            namespace_keys = [
                key for key in self._memory_cache.keys() 
                if key.startswith(f"{namespace}:")
            ]
            total_hits = sum(
                entry.hit_count 
                for entry in self._memory_cache.values() 
                if entry.key in namespace_keys
            )
            
            return {
                "namespace": namespace,
                "total_keys": len(namespace_keys),
                "total_hits": total_hits,
                "hit_rate": total_hits / max(len(namespace_keys), 1)
            }
        
        return {"namespace": namespace, "total_keys": 0, "total_hits": 0, "hit_rate": 0}
    
    async def clear_expired(self):
        """Clear expired entries from memory cache"""
        if not self.redis_client and hasattr(self, '_memory_cache'):
            expired_keys = [
                key for key, entry in self._memory_cache.items() 
                if entry.is_expired
            ]
            for key in expired_keys:
                del self._memory_cache[key]
            return len(expired_keys)
        return 0

# Create a singleton instance
cache_service = CacheService()

# Decorator for caching function results
def cached(namespace: str, ttl_seconds: int = 300):
    """Decorator to cache function results"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Generate cache key from function arguments
            cache_key_kwargs = {}
            
            # Include non-self arguments in cache key
            if args:
                if hasattr(args[0], '__class__'):  # Skip 'self' for methods
                    cache_key_kwargs.update({f"arg_{i}": arg for i, arg in enumerate(args[1:])})
                else:
                    cache_key_kwargs.update({f"arg_{i}": arg for i, arg in enumerate(args)})
            
            cache_key_kwargs.update(kwargs)
            
            # Try to get from cache first
            cached_result = await cache_service.get(namespace, **cache_key_kwargs)
            if cached_result is not None:
                return cached_result
            
            # If not in cache, execute function and cache result
            result = await func(*args, **kwargs)
            await cache_service.set(namespace, result, ttl_seconds, **cache_key_kwargs)
            
            return result
        return wrapper
    return decorator

@asynccontextmanager
async def get_cache_service():
    """Context manager for cache service"""
    try:
        if not cache_service.redis_client and not hasattr(cache_service, '_memory_cache'):
            await cache_service.connect()
        yield cache_service
    finally:
        pass  # Keep connection alive for reuse