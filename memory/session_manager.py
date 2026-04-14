"""
Session Manager Module - Phase 4

Implements session and memory management using:
- In-memory session service for managing conversation state
- Context management for agent operations
- History tracking and retrieval
- Session persistence and recovery

Provides the session layer for agent continuity.
"""

import logging
import json
from typing import Optional, Dict, List, Any
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
import uuid

logger = logging.getLogger(__name__)


class SessionState(str, Enum):
    """Session state enumeration."""
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class Message:
    """A single message in a conversation."""
    
    role: str  # "user" or "assistant"
    content: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Session:
    """
    Represents a conversation session.
    
    Tracks messages, context, and state across a conversation.
    """
    
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = "Untitled Session"
    state: SessionState = SessionState.ACTIVE
    
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    messages: List[Message] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_message(self, role: str, content: str, metadata: Optional[Dict] = None):
        """Add a message to the session."""
        msg = Message(role=role, content=content, metadata=metadata or {})
        self.messages.append(msg)
        self.updated_at = datetime.now().isoformat()
    
    def get_conversation_history(self) -> List[Dict[str, str]]:
        """Get conversation history as list of dicts."""
        return [{"role": m.role, "content": m.content} for m in self.messages]
    
    def get_context(self, key: str, default: Any = None) -> Any:
        """Get a value from session context."""
        return self.context.get(key, default)
    
    def set_context(self, key: str, value: Any):
        """Set a value in session context."""
        self.context[key] = value
        self.updated_at = datetime.now().isoformat()
    
    def to_dict(self) -> Dict:
        """Convert session to dictionary."""
        return {
            "session_id": self.session_id,
            "title": self.title,
            "state": self.state.value,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "message_count": len(self.messages),
            "context": self.context,
            "metadata": self.metadata
        }


class InMemorySessionService:
    """
    In-memory session management service.
    
    Features:
    - Create and manage multiple sessions
    - Store conversation history
    - Maintain context across interactions
    - Session lifecycle management
    - Query and filtering capabilities
    
    Example:
        >>> service = InMemorySessionService()
        >>> session = service.create_session("My Chat")
        >>> session.add_message("user", "Hello!")
        >>> session.add_message("assistant", "Hi there!")
        >>> history = session.get_conversation_history()
    """
    
    def __init__(self):
        """Initialize the session service."""
        self.sessions: Dict[str, Session] = {}
        self.active_session_id: Optional[str] = None
        
        logger.info("✅ InMemorySessionService initialized")
    
    def create_session(self, title: str = "Untitled Session") -> Session:
        """
        Create a new session.
        
        Args:
            title (str): Session title
            
        Returns:
            Session: New session object
        """
        session = Session(title=title)
        self.sessions[session.session_id] = session
        self.active_session_id = session.session_id
        
        logger.info(f"✅ Created session: {session.session_id} - {title}")
        return session
    
    def get_session(self, session_id: str) -> Optional[Session]:
        """
        Get a session by ID.
        
        Args:
            session_id (str): Session ID
            
        Returns:
            Session or None
        """
        return self.sessions.get(session_id)
    
    def get_active_session(self) -> Optional[Session]:
        """
        Get the currently active session.
        
        Returns:
            Session or None
        """
        if self.active_session_id:
            return self.sessions.get(self.active_session_id)
        return None
    
    def set_active_session(self, session_id: str) -> bool:
        """
        Set the active session.
        
        Args:
            session_id (str): Session ID to activate
            
        Returns:
            bool: True if successful
        """
        if session_id in self.sessions:
            self.active_session_id = session_id
            logger.info(f"✅ Activated session: {session_id}")
            return True
        return False
    
    def list_sessions(self) -> List[Dict]:
        """
        List all sessions.
        
        Returns:
            List[Dict]: List of session summaries
        """
        return [s.to_dict() for s in self.sessions.values()]
    
    def delete_session(self, session_id: str) -> bool:
        """
        Delete a session.
        
        Args:
            session_id (str): Session ID to delete
            
        Returns:
            bool: True if successful
        """
        if session_id in self.sessions:
            del self.sessions[session_id]
            if self.active_session_id == session_id:
                self.active_session_id = None
            logger.info(f"✅ Deleted session: {session_id}")
            return True
        return False
    
    def save_session_state(self, session_id: str, filepath: str) -> bool:
        """
        Save session state to a JSON file.
        
        Args:
            session_id (str): Session ID
            filepath (str): Path to save file
            
        Returns:
            bool: True if successful
        """
        session = self.get_session(session_id)
        if not session:
            return False
        
        try:
            data = {
                "session_id": session.session_id,
                "title": session.title,
                "state": session.state.value,
                "created_at": session.created_at,
                "updated_at": session.updated_at,
                "messages": [
                    {
                        "role": m.role,
                        "content": m.content,
                        "timestamp": m.timestamp,
                        "metadata": m.metadata
                    }
                    for m in session.messages
                ],
                "context": session.context,
                "metadata": session.metadata
            }
            
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.info(f"✅ Saved session to: {filepath}")
            return True
        except Exception as e:
            logger.error(f"Error saving session: {str(e)}")
            return False
    
    def load_session_state(self, filepath: str) -> Optional[Session]:
        """
        Load session state from a JSON file.
        
        Args:
            filepath (str): Path to load file
            
        Returns:
            Session or None
        """
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            
            session = Session(
                session_id=data["session_id"],
                title=data["title"],
                state=SessionState(data["state"]),
                created_at=data["created_at"],
                updated_at=data["updated_at"],
                context=data.get("context", {}),
                metadata=data.get("metadata", {})
            )
            
            # Restore messages
            for msg_data in data.get("messages", []):
                session.messages.append(Message(
                    role=msg_data["role"],
                    content=msg_data["content"],
                    timestamp=msg_data.get("timestamp", datetime.now().isoformat()),
                    metadata=msg_data.get("metadata", {})
                ))
            
            self.sessions[session.session_id] = session
            logger.info(f"✅ Loaded session from: {filepath}")
            return session
        except Exception as e:
            logger.error(f"Error loading session: {str(e)}")
            return None
    
    def clear_all_sessions(self):
        """Clear all sessions."""
        self.sessions.clear()
        self.active_session_id = None
        logger.info("✅ Cleared all sessions")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get session statistics."""
        total_messages = sum(len(s.messages) for s in self.sessions.values())
        active_sessions = sum(1 for s in self.sessions.values() if s.state == SessionState.ACTIVE)
        
        return {
            "total_sessions": len(self.sessions),
            "active_sessions": active_sessions,
            "total_messages": total_messages,
            "average_messages_per_session": total_messages / len(self.sessions) if self.sessions else 0
        }


class ContextManager:
    """
    Manages context and state for agent operations.
    
    Features:
    - Store and retrieve operational context
    - Manage scoped contexts
    - Variable substitution
    - Context inheritance
    """
    
    def __init__(self):
        """Initialize context manager."""
        self.global_context: Dict[str, Any] = {}
        self.scoped_contexts: Dict[str, Dict[str, Any]] = {}
        self.current_scope: Optional[str] = None
    
    def set_global(self, key: str, value: Any):
        """Set a global context value."""
        self.global_context[key] = value
    
    def get_global(self, key: str, default: Any = None) -> Any:
        """Get a global context value."""
        return self.global_context.get(key, default)
    
    def create_scope(self, scope_name: str) -> Dict[str, Any]:
        """
        Create a new context scope.
        
        Args:
            scope_name (str): Name of the scope
            
        Returns:
            Dict: The scope context
        """
        self.scoped_contexts[scope_name] = {}
        self.current_scope = scope_name
        return self.scoped_contexts[scope_name]
    
    def set_scoped(self, key: str, value: Any, scope: Optional[str] = None):
        """Set a scoped context value."""
        scope = scope or self.current_scope
        if scope and scope in self.scoped_contexts:
            self.scoped_contexts[scope][key] = value
    
    def get_scoped(self, key: str, scope: Optional[str] = None, default: Any = None) -> Any:
        """Get a scoped context value."""
        scope = scope or self.current_scope
        if scope and scope in self.scoped_contexts:
            return self.scoped_contexts[scope].get(key, default)
        return default
    
    def get_merged_context(self) -> Dict[str, Any]:
        """
        Get merged context (global + current scope).
        
        Returns:
            Dict: Merged context
        """
        merged = self.global_context.copy()
        if self.current_scope and self.current_scope in self.scoped_contexts:
            merged.update(self.scoped_contexts[self.current_scope])
        return merged
