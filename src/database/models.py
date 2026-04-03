"""
SQLAlchemy Models for MCP Context Server.

This module defines all database models for storing symbols, dependencies,
observations, and metadata.
"""

from sqlalchemy import (
    Column, String, Text, Integer, Boolean, DateTime, ForeignKey, Index
)
from sqlalchemy.orm import DeclarativeBase, relationship
from datetime import datetime
import uuid


class Base(DeclarativeBase):
    """Base class for all models."""
    pass


class Symbol(Base):
    """Represents a code symbol (class, function, or method)."""
    __tablename__ = 'symbols'

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False, index=True)
    file = Column(String, nullable=False, index=True)
    body = Column(Text)
    signature = Column(Text)
    type = Column(String)  # 'class', 'function', 'method'
    start_line = Column(Integer)
    end_line = Column(Integer)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    file_hash = Column(String)

    # Relationships
    outgoing_deps = relationship("Dependency", foreign_keys="Dependency.caller_id", back_populates="caller")
    incoming_deps = relationship("Dependency", foreign_keys="Dependency.callee_id", back_populates="callee")
    observations = relationship("Observation", back_populates="symbol", cascade="all, delete-orphan")

    __table_args__ = (
        Index('idx_symbols_name', 'name'),
        Index('idx_symbols_file', 'file'),
    )


class Dependency(Base):
    """Represents a dependency relationship between two symbols."""
    __tablename__ = 'dependencies'

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    caller_id = Column(String, ForeignKey('symbols.id'), nullable=False)
    callee_id = Column(String, ForeignKey('symbols.id'), nullable=False)
    call_site_line = Column(Integer)

    # Relationships
    caller = relationship("Symbol", foreign_keys=[caller_id], back_populates="outgoing_deps")
    callee = relationship("Symbol", foreign_keys=[callee_id], back_populates="incoming_deps")

    __table_args__ = (
        Index('idx_deps_caller', 'caller_id'),
        Index('idx_deps_callee', 'callee_id'),
    )


class Observation(Base):
    """Represents an observation/note about a symbol."""
    __tablename__ = 'observations'

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    symbol_id = Column(String, ForeignKey('symbols.id'), nullable=False)
    note = Column(Text, nullable=False)
    category = Column(String)  # 'bug', 'refactor', 'logic', 'architecture'
    priority = Column(Integer, default=3)
    is_stale = Column(Boolean, default=False, index=True)
    session_id = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship
    symbol = relationship("Symbol", back_populates="observations")

    __table_args__ = (
        Index('idx_obs_symbol', 'symbol_id'),
        Index('idx_obs_stale', 'is_stale'),
    )


class ProjectMetadata(Base):
    """Represents project-level metadata."""
    __tablename__ = 'project_metadata'

    key = Column(String, primary_key=True)
    value = Column(Text)
    last_modified = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class FileHash(Base):
    """Tracks file hashes for incremental indexing."""
    __tablename__ = 'file_hashes'

    file_path = Column(String, primary_key=True)
    hash = Column(String, nullable=False)
    last_indexed = Column(DateTime, default=datetime.utcnow)
