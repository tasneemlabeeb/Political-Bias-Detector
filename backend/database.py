"""
Database Configuration and Models

Async SQLAlchemy setup with SQLite/PostgreSQL support.
"""

from datetime import datetime
from typing import AsyncGenerator
from urllib.parse import urlparse, parse_qs

from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String, Text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from backend.config import get_settings

settings = get_settings()

# Create async engine (support both SQLite and PostgreSQL)
database_url = str(settings.DATABASE_URL)

# Convert database URL to async version and handle SSL parameters
connect_args = {}
if "sqlite" in database_url:
    # SQLite - use aiosqlite
    database_url = database_url.replace("sqlite:///", "sqlite+aiosqlite:///")
elif "postgresql" in database_url:
    # PostgreSQL - use asyncpg
    # Remove query parameters and add them as connect_args
    if "?" in database_url:
        base_url, query_string = database_url.split("?", 1)
        database_url = base_url.replace("postgresql://", "postgresql+asyncpg://")
        
        # Parse SSL parameters for asyncpg
        params = parse_qs(query_string)
        if "sslmode" in params:
            sslmode = params["sslmode"][0]
            if sslmode == "require":
                connect_args["ssl"] = True
    else:
        database_url = database_url.replace("postgresql://", "postgresql+asyncpg://")

engine = create_async_engine(
    database_url,
    echo=settings.DB_ECHO,
    pool_pre_ping=True,
    connect_args=connect_args,
)

# Create async session factory
AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

Base = declarative_base()


# Dependency to get database session
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Database session dependency."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


# Database Models
class NewsSource(Base):
    """News source model."""
    
    __tablename__ = "news_sources"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False, index=True)
    url = Column(String(512), nullable=False)
    rss_feed = Column(String(512), nullable=True)
    political_bias = Column(String(50), default="Unclassified")
    credibility_score = Column(Float, default=0.5)
    active = Column(Boolean, default=True)
    last_scraped = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Article(Base):
    """Article model."""
    
    __tablename__ = "articles"
    
    id = Column(Integer, primary_key=True, index=True)
    source_id = Column(Integer, nullable=False, index=True)
    title = Column(String(512), nullable=False, index=True)
    url = Column(String(1024), unique=True, nullable=False)
    summary = Column(Text, nullable=True)
    content = Column(Text, nullable=True)
    published_date = Column(DateTime, nullable=True, index=True)
    
    # Source-assigned bias
    source_bias = Column(String(50), nullable=True)
    
    # ML predictions
    ml_bias = Column(String(50), nullable=True)
    ml_confidence = Column(Float, nullable=True)
    ml_direction_score = Column(Float, nullable=True)
    ml_intensity_score = Column(Float, nullable=True)
    ml_prediction_date = Column(DateTime, nullable=True)
    
    # Metadata
    crawled_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class User(Base):
    """User model."""
    
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class UserPreference(Base):
    """User preferences and settings."""
    
    __tablename__ = "user_preferences"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    
    # Reading preferences
    preferred_sources = Column(Text, nullable=True)  # JSON array
    blacklisted_sources = Column(Text, nullable=True)  # JSON array
    bias_filter = Column(String(255), nullable=True)  # Comma-separated list
    
    # Notification settings
    email_notifications = Column(Boolean, default=False)
    daily_digest = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ReadingHistory(Base):
    """User reading history."""
    
    __tablename__ = "reading_history"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    article_id = Column(Integer, nullable=False, index=True)
    read_at = Column(DateTime, default=datetime.utcnow, index=True)
    reading_time_seconds = Column(Integer, nullable=True)
    
    # User feedback
    user_rating = Column(Integer, nullable=True)  # 1-5 stars
    user_bias_assessment = Column(String(50), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)


class APIKey(Base):
    """API keys for external access."""
    
    __tablename__ = "api_keys"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    key = Column(String(64), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    rate_limit_per_hour = Column(Integer, default=1000)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)
    last_used_at = Column(DateTime, nullable=True)


class BiasReport(Base):
    """Crowdsourced bias report for model training."""

    __tablename__ = "bias_reports"

    id = Column(Integer, primary_key=True, index=True)
    url = Column(String(1024), nullable=True)
    title = Column(String(512), nullable=True)
    article_text = Column(Text, nullable=True)
    bias_label = Column(String(50), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class CitationRecord(Base):
    """Persisted citation between two news sources."""

    __tablename__ = "citations"

    id = Column(Integer, primary_key=True, index=True)
    from_source = Column(String(255), nullable=False, index=True)
    to_source = Column(String(255), nullable=False, index=True)
    from_article_id = Column(Integer, nullable=True, index=True)
    to_url = Column(String(1024), nullable=True)
    context = Column(Text, nullable=True)
    citation_type = Column(String(50), default="hyperlink")  # hyperlink, mention, reference
    from_bias = Column(String(50), nullable=True)
    to_bias = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
