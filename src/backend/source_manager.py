import requests
import os
from datetime import datetime
from typing import Dict, List

from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()


class NewsSource(Base):
    __tablename__ = "news_sources"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    url = Column(String, nullable=False)
    rss_feed = Column(String, nullable=True)
    political_bias = Column(String, default="Unclassified")
    last_scraped = Column(DateTime)
    active = Column(Integer, default=1)

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "url": self.url,
            "rss_feed": self.rss_feed,
            "political_bias": self.political_bias,
            "last_scraped": self.last_scraped.isoformat() if self.last_scraped else None,
            "active": self.active,
        }


class SourceManager:
    def __init__(self, db_path: str = None):
        # Use DATABASE_URL from environment if available, otherwise use SQLite
        database_url = os.getenv("DATABASE_URL")
        
        if database_url:
            # Use environment database URL (PostgreSQL or other)
            # Convert to sync URL if it's async
            if "postgresql+asyncpg://" in database_url:
                database_url = database_url.replace("postgresql+asyncpg://", "postgresql://")
            # Remove SSL query parameters for psycopg2
            if "?" in database_url:
                database_url = database_url.split("?")[0]
            self.engine = create_engine(database_url)
        else:
            # Fall back to SQLite
            db_path = db_path or "news_sources.db"
            self.engine = create_engine(f"sqlite:///{db_path}")
        
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

    def add_source(
        self,
        name: str,
        url: str,
        rss_feed: str = None,
        political_bias: str = "Unclassified",
    ) -> Dict:
        """Add a new news source to the database."""
        session = self.Session()
        try:
            response = requests.head(url, timeout=5, allow_redirects=True)
            if response.status_code >= 400:
                return {
                    "success": False,
                    "message": f"URL returned status {response.status_code}",
                }

            existing = session.query(NewsSource).filter_by(name=name).first()
            if existing:
                return {"success": False, "message": "Source already exists"}

            new_source = NewsSource(
                name=name,
                url=url,
                rss_feed=rss_feed,
                political_bias=political_bias,
                last_scraped=datetime.now(),
                active=1,
            )
            session.add(new_source)
            session.commit()

            return {
                "success": True,
                "message": f"Source '{name}' added successfully",
                "source_id": new_source.id,
            }

        except requests.RequestException as e:
            return {"success": False, "message": f"Connection error: {e}"}
        except Exception as e:
            session.rollback()
            return {"success": False, "message": f"Error adding source: {e}"}
        finally:
            session.close()

    def get_active_sources(self) -> List[Dict]:
        """Retrieve all active news sources."""
        session = self.Session()
        try:
            sources = session.query(NewsSource).filter_by(active=1).all()
            return [source.to_dict() for source in sources]
        finally:
            session.close()

    def get_all_sources(self) -> List[Dict]:
        """Retrieve all news sources regardless of status."""
        session = self.Session()
        try:
            sources = session.query(NewsSource).all()
            return [source.to_dict() for source in sources]
        finally:
            session.close()

    def update_source_status(self, source_id: int, active: bool) -> Dict:
        """Activate or deactivate a news source."""
        session = self.Session()
        try:
            source = session.query(NewsSource).filter_by(id=source_id).first()
            if not source:
                return {"success": False, "message": "Source not found"}

            source.active = 1 if active else 0
            session.commit()
            return {"success": True, "message": f"Source status updated"}
        except Exception as e:
            session.rollback()
            return {"success": False, "message": f"Error updating source: {e}"}
        finally:
            session.close()

    def remove_source(self, source_id: int) -> Dict:
        """Permanently remove a news source."""
        session = self.Session()
        try:
            source = session.query(NewsSource).filter_by(id=source_id).first()
            if not source:
                return {"success": False, "message": "Source not found"}

            name = source.name
            session.delete(source)
            session.commit()
            return {"success": True, "message": f"Source '{name}' removed"}
        except Exception as e:
            session.rollback()
            return {"success": False, "message": f"Error removing source: {e}"}
        finally:
            session.close()

    def update_last_scraped(self, source_id: int) -> None:
        """Update the last_scraped timestamp for a source."""
        session = self.Session()
        try:
            source = session.query(NewsSource).filter_by(id=source_id).first()
            if source:
                source.last_scraped = datetime.now()
                session.commit()
        finally:
            session.close()
