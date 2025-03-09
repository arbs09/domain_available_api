from fastapi import FastAPI, HTTPException
from slowapi import Limiter
from slowapi.util import get_remote_address
import aiodns
import cachetools
import asyncio

limiter = Limiter(key_func=get_remote_address)
app = FastAPI()

resolver = aiodns.DNSResolver()

domain_cache = cachetools.TTLCache(maxsize=1000, ttl=600)

@app.get("/check")
@limiter.limit("10/minute")
async def check_domain(domain: str):
    if domain in domain_cache:
        return {"domain": domain, "available": domain_cache[domain]}

    try:
        result = await asyncio.wait_for(resolver.query(domain, 'NS'), timeout=3)
        domain_cache[domain] = False
        return {"domain": domain, "available": False}
    except aiodns.error.DNSError:
        domain_cache[domain] = True
        return {"domain": domain, "available": True}
    except asyncio.TimeoutError:
        raise HTTPException(status_code=408, detail="DNS query timeout")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
