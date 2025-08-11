#!/usr/bin/env python3
"""
Simple orchestrator using the simple Claude wrapper
"""
import json
import time
import uuid
from dataclasses import dataclass, field
from typing import Dict, Optional, List
from datetime import datetime
import threading
import queue
from claude_memory_wrapper import simple_orchestrator

@dataclass
class BotSession:
    """Represents a single Claude bot session"""
    session_id: str
    tab_id: str
    created_at: datetime
    project_name: str
    is_active: bool = True
    last_activity: datetime = None
    messages: List[dict] = field(default_factory=list)
    # Per-request metrics (reset after each response)
    current_request_tokens: int = 0
    current_request_duration: float = 0.0
    current_request_start: datetime = None
    # Cumulative metrics (for history)
    total_tokens: int = 0
    total_duration: float = 0.0

class SimpleOrchestrator:
    """
    Simple orchestrator that uses the simple Claude wrapper
    """
    
    def __init__(self):
        self.sessions: Dict[str, BotSession] = {}
        self.active_tab_id: Optional[str] = None
        self.max_sessions = 4
        self.event_queue = queue.Queue()
        self.last_responses: Dict[str, str] = {}  # Store last response for each tab
        print(f"[ORCHESTRATOR] Initialized with simple wrapper")
        
    def create_session(self, tab_id: str, project_name: str) -> BotSession:
        """Create a new Claude session for a tab"""
        print(f"[ORCHESTRATOR] create_session called with tab_id={tab_id}, project_name={project_name}")
        
        if len(self.sessions) >= self.max_sessions:
            # Try to clean up old sessions first
            self._cleanup_old_sessions()
            
            # Check again after cleanup
            if len(self.sessions) >= self.max_sessions:
                raise Exception(f"Maximum number of sessions ({self.max_sessions}) reached")
        
        try:
            # Use simple orchestrator to create the actual Claude session
            session_id = simple_orchestrator.create_session(tab_id)
            
            # Create session object
            session = BotSession(
                session_id=session_id,
                tab_id=tab_id,
                created_at=datetime.now(),
                project_name=project_name,
                last_activity=datetime.now()
            )
            
            # Store session
            self.sessions[tab_id] = session
            
            print(f"[ORCHESTRATOR] Session created successfully. Total sessions: {len(self.sessions)}")
            
            return session
            
        except Exception as e:
            print(f"[ORCHESTRATOR] Error creating session: {e}")
            raise
    
    def route_message(self, tab_id: str, message: str) -> str:
        """Route a message to the appropriate Claude instance"""
        print(f"[ORCHESTRATOR] route_message called: tab_id={tab_id}, message={message}")
        
        if tab_id not in self.sessions:
            print(f"[ORCHESTRATOR] No session for tab {tab_id}, creating one")
            self.create_session(tab_id, f"Tab {tab_id}")
        
        session = self.sessions[tab_id]
        session.last_activity = datetime.now()
        
        # Reset per-request metrics
        session.current_request_tokens = 0
        session.current_request_duration = 0.0
        
        # Track request start time
        request_start = datetime.now()
        session.current_request_start = request_start
        
        # Send message using simple orchestrator
        print(f"[ORCHESTRATOR] Sending message to simple_orchestrator")
        response = simple_orchestrator.send_message(tab_id, message)
        
        # Calculate request duration
        request_duration = (datetime.now() - request_start).total_seconds()
        session.current_request_duration = request_duration
        session.current_request_start = None  # Clear to stop timer
        
        # Add to cumulative metrics
        session.total_duration += request_duration
        
        if response:
            print(f"[ORCHESTRATOR] Got response: {response[:100]}...")
            # Store the response
            self.last_responses[tab_id] = response
            
            # Update token count (estimate based on response length)
            # This is a rough estimate - 1 token ≈ 4 characters
            estimated_tokens = len(message) // 4 + len(response) // 4
            session.current_request_tokens = estimated_tokens
            
            # Add to cumulative metrics
            session.total_tokens += estimated_tokens
            
            # Store message and response
            session.messages.append({
                'type': 'user',
                'text': message,
                'timestamp': datetime.now().isoformat()
            })
            
            session.messages.append({
                'type': 'bot',
                'text': response,
                'timestamp': datetime.now().isoformat()
            })
        else:
            print(f"[ORCHESTRATOR] No response received")
        
        return session.session_id
    
    def capture_response(self, session_id) -> Optional[str]:
        """Get the last response for a session"""
        # Handle both string session_id and BotSession object
        if isinstance(session_id, BotSession):
            actual_session_id = session_id.session_id
            print(f"[ORCHESTRATOR] capture_response called with BotSession object, extracting session_id: {actual_session_id}")
        else:
            actual_session_id = session_id
            print(f"[ORCHESTRATOR] capture_response called for session {actual_session_id}")
        
        # Find the tab_id for this session
        tab_id = None
        for tid, sess in self.sessions.items():
            if sess.session_id == actual_session_id:
                tab_id = tid
                break
                
        if not tab_id:
            print(f"[ORCHESTRATOR] No tab found for session {actual_session_id}")
            return None
            
        session = self.sessions[tab_id]
        
        # Return the last response if available
        if tab_id in self.last_responses:
            response = self.last_responses[tab_id]
            # Don't clear it immediately - let it be available for a few calls
            # This ensures the capture thread has time to get it
            print(f"[ORCHESTRATOR] Returning response: {response[:100]}...")
            
            # Add a counter to track how many times this response has been returned
            if not hasattr(self, '_response_counters'):
                self._response_counters = {}
            
            if tab_id not in self._response_counters:
                self._response_counters[tab_id] = 0
            
            self._response_counters[tab_id] += 1
            
            # Clear after 3 returns to avoid duplicate sends
            if self._response_counters[tab_id] >= 3:
                del self.last_responses[tab_id]
                del self._response_counters[tab_id]
            
            return f"● {response}"
        
        return None
    
    def switch_tab(self, tab_id: str):
        """Switch active tab"""
        if tab_id not in self.sessions:
            # Create session if it doesn't exist
            print(f"[ORCHESTRATOR] Creating session for tab {tab_id} on switch")
            self.create_session(tab_id, f"Tab {tab_id}")
        
        self.active_tab_id = tab_id
    
    def get_active_session(self) -> Optional[BotSession]:
        """Get the currently active session"""
        if self.active_tab_id and self.active_tab_id in self.sessions:
            return self.sessions[self.active_tab_id]
        return None
    
    def cleanup_session(self, tab_id: str):
        """Clean up a session when tab is closed"""
        if tab_id not in self.sessions:
            return
        
        # Clean up simple orchestrator session
        simple_orchestrator.cleanup_session(tab_id)
        
        # Remove from active sessions
        del self.sessions[tab_id]
        
        # Remove any stored responses
        if tab_id in self.last_responses:
            del self.last_responses[tab_id]
    
    def get_session_info(self, tab_id: str) -> Optional[dict]:
        """Get information about a specific session"""
        if tab_id not in self.sessions:
            return None
        
        session = self.sessions[tab_id]
        
        # Get current request metrics
        current_duration = session.current_request_duration
        current_tokens = session.current_request_tokens
        is_processing = False
        
        if session.current_request_start:
            # Currently processing - calculate live duration
            time_diff = (datetime.now() - session.current_request_start).total_seconds()
            current_duration = time_diff
            is_processing = True
        
        return {
            'session_id': session.session_id,
            'tab_id': session.tab_id,
            'project_name': session.project_name,
            'created_at': session.created_at.isoformat(),
            'last_activity': session.last_activity.isoformat() if session.last_activity else None,
            'is_active': session.is_active,
            'message_count': len(session.messages),
            # Current request metrics (what we display)
            'tokens': current_tokens,
            'duration': current_duration,
            # Cumulative metrics (for history)
            'total_tokens': session.total_tokens,
            'total_duration': session.total_duration,
            'total_duration_formatted': self._format_duration(session.total_duration),
            'is_processing': is_processing
        }
    
    def _format_duration(self, seconds: float) -> str:
        """Format duration in seconds to human readable format"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        
        if hours > 0:
            return f"{hours}h {minutes}m {secs}s"
        elif minutes > 0:
            return f"{minutes}m {secs}s"
        else:
            return f"{secs}s"
    
    def _cleanup_old_sessions(self):
        """Clean up the oldest inactive sessions"""
        print(f"[ORCHESTRATOR] Cleaning up old sessions. Current count: {len(self.sessions)}")
        
        # Sort sessions by last activity
        sorted_sessions = sorted(
            self.sessions.items(), 
            key=lambda x: x[1].last_activity if x[1].last_activity else x[1].created_at
        )
        
        # Remove the oldest 25% of sessions
        to_remove = max(1, len(sorted_sessions) // 4)
        
        for tab_id, session in sorted_sessions[:to_remove]:
            print(f"[ORCHESTRATOR] Removing old session: tab_id={tab_id}, last_activity={session.last_activity}")
            self.cleanup_session(tab_id)
    
    def list_active_sessions(self) -> list:
        """List all active sessions"""
        return [self.get_session_info(tab_id) for tab_id in self.sessions.keys()]
    
    def store_bot_response(self, tab_id: str, response: str):
        """Store bot response in session history"""
        if tab_id in self.sessions:
            self.sessions[tab_id].messages.append({
                'type': 'bot',
                'text': response,
                'timestamp': datetime.now().isoformat()
            })
    
    def publish_event(self, event_type: str, data: dict):
        """Publish event to event queue"""
        event = {
            'type': event_type,
            'timestamp': datetime.now().isoformat(),
            'data': data
        }
        self.event_queue.put(event)
    
    def get_events(self) -> List[dict]:
        """Get all pending events"""
        events = []
        while not self.event_queue.empty():
            try:
                events.append(self.event_queue.get_nowait())
            except queue.Empty:
                break
        return events


# Singleton instance
orchestrator = SimpleOrchestrator()