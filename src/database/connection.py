"""
Database connection manager for ILI system.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager
from typing import Generator
import os


class DatabaseManager:
    """Manages database connections and sessions"""

    def __init__(self, db_url: str = None):
        """
        Initialize database manager.

        Args:
            db_url: Database URL. Defaults to SQLite in data directory.
        """
        if db_url is None:
            # Default to SQLite in data directory
            data_dir = os.path.join(os.path.dirname(__file__), "../../data")
            os.makedirs(data_dir, exist_ok=True)
            db_url = f"sqlite:///{data_dir}/ili_system.db"

        self.db_url = db_url
        self.engine = create_engine(db_url, echo=False, pool_pre_ping=True)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """
        Get a database session with automatic cleanup.

        Yields:
            Session: SQLAlchemy session

        Example:
            with db_manager.get_session() as session:
                session.query(Anomaly).all()
        """
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def create_tables(self) -> None:
        """Create all database tables"""
        from src.database.schema import Base

        Base.metadata.create_all(self.engine)

    def drop_tables(self) -> None:
        """Drop all database tables"""
        from src.database.schema import Base

        Base.metadata.drop_all(self.engine)

    def reset_database(self) -> None:
        """Drop and recreate all tables"""
        self.drop_tables()
        self.create_tables()


# Global database manager instance
_db_manager = None


def get_db_manager(db_url: str = None) -> DatabaseManager:
    """
    Get or create the global database manager instance.

    Args:
        db_url: Database URL (only used on first call)

    Returns:
        DatabaseManager: Global database manager instance
    """
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager(db_url)
    return _db_manager


def init_database(db_url: str = None) -> DatabaseManager:
    """
    Initialize the database and create tables.

    Args:
        db_url: Database URL

    Returns:
        DatabaseManager: Initialized database manager
    """
    db_manager = get_db_manager(db_url)
    db_manager.create_tables()
    return db_manager
