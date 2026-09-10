import os
import ssl
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from OpenDEMON.database.config import db_config

# Supabase pooler: hostname-based OR IP-based URL (Windows async DNS workaround)
_url = db_config.url
_is_pooler = "pooler.supabase.com" in _url or (
    # IP-based URL set when Windows async DNS fails to resolve pooler hostname
    os.environ.get("SUPABASE_POOLER_IP") in _url
    if os.environ.get("SUPABASE_POOLER_IP") else False
)
# Auto-detect: if URL contains a raw IP and SUPABASE_POOLER_SNI is set, treat as pooler
_sni_host = os.environ.get("SUPABASE_POOLER_SNI", "aws-0-ap-northeast-2.pooler.supabase.com")
_is_ip_url = not any(c.isalpha() for c in _url.split("@")[-1].split(":")[0])
_connect_args = {}
if "pooler.supabase.com" in _url or _is_ip_url:
    _ssl_ctx = ssl.create_default_context()
    _ssl_ctx.check_hostname = False
    _ssl_ctx.verify_mode = ssl.CERT_NONE
    _connect_args = {
        "ssl": _ssl_ctx,
        "statement_cache_size": 0,
    }
    if _is_ip_url:
        _connect_args["server_settings"] = {"sni": _sni_host}

engine = create_async_engine(
    db_config.url,
    pool_size=db_config.pool_size,
    max_overflow=db_config.max_overflow,
    pool_timeout=db_config.pool_timeout,
    pool_recycle=db_config.pool_recycle,
    pool_pre_ping=db_config.pool_pre_ping,
    connect_args=_connect_args,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)
