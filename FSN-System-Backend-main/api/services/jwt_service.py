"""
JWT Service for Agent Authentication
"""
import jwt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from fastapi import HTTPException, status
import structlog

from core.config import settings

logger = structlog.get_logger()

class JWTService:
    """JWT token service for agent authentication"""
    
    def __init__(self):
        self.secret_key = settings.secret_key
        self.algorithm = settings.algorithm
        self.access_token_expire_minutes = settings.access_token_expire_minutes
    
    def create_agent_token(self, agent_id: int, license_id: str) -> str:
        """
        Create JWT token for agent authentication
        
        Args:
            agent_id: Agent ID
            license_id: License ID the agent belongs to
            
        Returns:
            str: JWT token
        """
        try:
            # Token payload
            payload = {
                "agent_id": agent_id,
                "license_id": license_id,
                "type": "agent_token",
                "iat": datetime.utcnow(),
                "exp": datetime.utcnow() + timedelta(days=30)  # Agent tokens last 30 days
            }
            
            # Create token
            token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
            
            logger.info("✅ Created agent token", agent_id=agent_id, license_id=license_id)
            return token
            
        except Exception as e:
            logger.error("❌ Failed to create agent token", error=str(e), agent_id=agent_id)
            raise HTTPException(
                status_code=500,
                detail="Failed to create agent token"
            )
    
    def verify_agent_token(self, token: str) -> Dict[str, Any]:
        """
        Verify and decode agent JWT token
        
        Args:
            token: JWT token to verify
            
        Returns:
            Dict containing token payload
            
        Raises:
            HTTPException: If token is invalid or expired
        """
        try:
            # Decode token
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            
            # Verify token type
            if payload.get("type") != "agent_token":
                raise HTTPException(
                    status_code=401,
                    detail="Invalid token type"
                )
            
            # Check if token is expired
            exp = payload.get("exp")
            if exp and datetime.utcnow().timestamp() > exp:
                raise HTTPException(
                    status_code=401,
                    detail="Token expired"
                )
            
            logger.debug("✅ Agent token verified", agent_id=payload.get("agent_id"))
            return payload
            
        except jwt.ExpiredSignatureError:
            logger.warning("⚠️ Agent token expired", token=token[:20] + "...")
            raise HTTPException(
                status_code=401,
                detail="Token expired"
            )
        except jwt.InvalidTokenError as e:
            logger.warning("⚠️ Invalid agent token", error=str(e), token=token[:20] + "...")
            raise HTTPException(
                status_code=401,
                detail="Invalid token"
            )
        except Exception as e:
            logger.error("❌ Token verification failed", error=str(e))
            raise HTTPException(
                status_code=500,
                detail="Token verification failed"
            )
    
    def create_pair_token(self, license_id: str) -> str:
        """
        Create short-lived pair token for agent pairing
        
        Args:
            license_id: License ID
            
        Returns:
            str: Pair token
        """
        try:
            # Token payload
            payload = {
                "license_id": license_id,
                "type": "pair_token",
                "iat": datetime.utcnow(),
                "exp": datetime.utcnow() + timedelta(minutes=10)  # Pair tokens last 10 minutes
            }
            
            # Create token
            token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
            
            logger.info("✅ Created pair token", license_id=license_id)
            return token
            
        except Exception as e:
            logger.error("❌ Failed to create pair token", error=str(e), license_id=license_id)
            raise HTTPException(
                status_code=500,
                detail="Failed to create pair token"
            )
    
    def verify_pair_token(self, token: str) -> Dict[str, Any]:
        """
        Verify and decode pair token
        
        Args:
            token: Pair token to verify
            
        Returns:
            Dict containing token payload
            
        Raises:
            HTTPException: If token is invalid or expired
        """
        try:
            # Decode token
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            
            # Verify token type
            if payload.get("type") != "pair_token":
                raise HTTPException(
                    status_code=401,
                    detail="Invalid token type"
                )
            
            # Check if token is expired
            exp = payload.get("exp")
            if exp and datetime.utcnow().timestamp() > exp:
                raise HTTPException(
                    status_code=401,
                    detail="Pair token expired"
                )
            
            logger.debug("✅ Pair token verified", license_id=payload.get("license_id"))
            return payload
            
        except jwt.ExpiredSignatureError:
            logger.warning("⚠️ Pair token expired", token=token[:20] + "...")
            raise HTTPException(
                status_code=401,
                detail="Pair token expired"
            )
        except jwt.InvalidTokenError as e:
            logger.warning("⚠️ Invalid pair token", error=str(e), token=token[:20] + "...")
            raise HTTPException(
                status_code=401,
                detail="Invalid pair token"
            )
        except Exception as e:
            logger.error("❌ Pair token verification failed", error=str(e))
            raise HTTPException(
                status_code=500,
                detail="Pair token verification failed"
            )

# Create global instance
jwt_service = JWTService()
