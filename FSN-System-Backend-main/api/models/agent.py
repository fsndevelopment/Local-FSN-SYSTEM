"""
Agent model for local device agents
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, JSON, ForeignKey
from sqlalchemy.sql import func
from database.connection import Base

class Agent(Base):
    __tablename__ = "agents"
    
    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(String(100), unique=True, index=True, nullable=False)
    license_id = Column(String(100), nullable=False, index=True)  # Link to license
    agent_name = Column(String(100), nullable=False)  # Human-readable name
    platform = Column(String(50), nullable=False)  # macOS, Windows, Linux
    app_version = Column(String(20), nullable=False)  # Agent app version
    agent_token = Column(Text, nullable=True)  # JWT token for agent auth
    appium_base_path = Column(String(50), default="/wd/hub")  # Appium base path
    status = Column(String(20), default="offline")  # online, offline, error
    last_seen = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<Agent(id={self.id}, agent_id='{self.agent_id}', license_id='{self.license_id}', status='{self.status}')>"

class PairToken(Base):
    __tablename__ = "pair_tokens"
    
    id = Column(Integer, primary_key=True, index=True)
    pair_token = Column(String(100), unique=True, index=True, nullable=False)
    license_id = Column(String(100), nullable=False, index=True)
    qr_payload = Column(String(500), nullable=False)  # fsn://pair?token=...
    expires_at = Column(DateTime(timezone=True), nullable=False)
    used = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<PairToken(id={self.id}, pair_token='{self.pair_token}', license_id='{self.license_id}', used={self.used})>"
