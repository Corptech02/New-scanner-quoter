#!/usr/bin/env python3
"""
Claude wrapper with memory - maintains conversation context
"""
import subprocess
import uuid
import time
import json
from typing import Dict, Optional, List
from datetime import datetime
from terminal_monitor import terminal_monitor

class ClaudeMemorySession:
    """Session that maintains conversation history"""
    
    def __init__(self, session_id: str, tab_id: str = None):
        self.session_id = session_id
        self.tab_id = tab_id
        self.message_count = 0
        self.conversation_history: List[Dict[str, str]] = []
        self.max_context_messages = 10  # Keep last 10 exchanges
        
        # Initialize terminal monitor for this tab
        if self.tab_id:
            terminal_monitor.initialize_buffer(self.tab_id)
        
    def send_message(self, message: str, retry_count: int = 0) -> str:
        """Send a message to Claude with conversation context and retry mechanism"""
        max_retries = 2
        
        try:
            self.message_count += 1
            start_time = time.time()
            print(f"[SESSION {self.session_id[:8]}] Sending message #{self.message_count}: {message}")
            if retry_count > 0:
                print(f"[SESSION {self.session_id[:8]}] Retry attempt {retry_count}")
            
            # Build context from conversation history
            context_prompt = self._build_context_prompt(message)
            
            # Add command to terminal monitor
            if self.tab_id:
                terminal_monitor.add_command(self.tab_id, f"claude {message[:50]}...")
            
            # Call Claude with full context
            cmd = ['claude', '--dangerously-skip-permissions', '--print', context_prompt]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True
            )
            
            elapsed_time = time.time() - start_time
            print(f"[SESSION {self.session_id[:8]}] Request took {elapsed_time:.1f} seconds")
            
            if result.returncode == 0 and result.stdout:
                response = result.stdout.strip()
                
                # Add output to terminal monitor
                if self.tab_id:
                    terminal_monitor.add_output(self.tab_id, response)
                
                # Check for execution error in response
                if "execution error" in response.lower() and retry_count < max_retries:
                    print(f"[SESSION {self.session_id[:8]}] Detected execution error, retrying...")
                    return self._retry_with_message(message, retry_count + 1)
                
                # Store the exchange in history (only if successful)
                if retry_count == 0 or "execution error" not in response.lower():
                    self.conversation_history.append({
                        'role': 'user',
                        'content': message,
                        'timestamp': datetime.now().isoformat()
                    })
                    self.conversation_history.append({
                        'role': 'assistant',
                        'content': response,
                        'timestamp': datetime.now().isoformat()
                    })
                    
                    # Trim history if too long
                    if len(self.conversation_history) > self.max_context_messages * 2:
                        # Keep only the most recent messages
                        self.conversation_history = self.conversation_history[-(self.max_context_messages * 2):]
                
                print(f"[SESSION {self.session_id[:8]}] Got response ({len(response)} chars): {response[:200]}...")
                return response
            else:
                print(f"[SESSION {self.session_id[:8]}] Error: returncode={result.returncode}, stderr={result.stderr}")
                
                # Add error to terminal monitor
                if self.tab_id and result.stderr:
                    terminal_monitor.add_output(self.tab_id, f"ERROR: {result.stderr}")
                
                # Check if this looks like an execution error and retry
                error_message = result.stderr or "Unknown error"
                if ("execution" in error_message.lower() or result.returncode != 0) and retry_count < max_retries:
                    print(f"[SESSION {self.session_id[:8]}] Process error detected, retrying...")
                    return self._retry_with_message(message, retry_count + 1)
                
                return "Sorry, I couldn't process that request after multiple attempts."
                
        except Exception as e:
            print(f"[SESSION {self.session_id[:8]}] Exception: {e}")
            
            # Retry on exception if we haven't exceeded max retries
            if retry_count < max_retries:
                print(f"[SESSION {self.session_id[:8]}] Exception occurred, retrying...")
                return self._retry_with_message(message, retry_count + 1)
            
            return f"Sorry, an error occurred after multiple attempts: {str(e)}"
    
    def _retry_with_message(self, original_message: str, retry_count: int) -> str:
        """Handle retry with user-visible feedback"""
        # Add a small delay before retrying
        time.sleep(1)
        
        # Create retry message for the user to see
        if retry_count == 1:
            retry_response = "⚠️ Execution error - Trying again..."
        else:
            retry_response = f"⚠️ Execution error - Trying again (attempt {retry_count})..."
        
        print(f"[SESSION {self.session_id[:8]}] Showing retry message to user: {retry_response}")
        
        # Try the request again
        actual_response = self.send_message(original_message, retry_count)
        
        # If we got another error response, combine them
        if "execution error" in actual_response.lower() or "sorry" in actual_response.lower():
            return f"{retry_response}\n\n{actual_response}"
        else:
            # Success on retry - show the retry message followed by the actual response
            return f"{retry_response}\n\n{actual_response}"
    
    def _build_context_prompt(self, new_message: str) -> str:
        """Build a prompt that includes conversation history"""
        if not self.conversation_history:
            # First message, no context needed
            return new_message
        
        # Build context from history
        context_parts = []
        context_parts.append("Continue this conversation, maintaining context from our previous messages:")
        context_parts.append("")
        
        # Add conversation history
        for msg in self.conversation_history[-self.max_context_messages:]:
            if msg['role'] == 'user':
                context_parts.append(f"Human: {msg['content']}")
            else:
                context_parts.append(f"Assistant: {msg['content']}")
            context_parts.append("")
        
        # Add the new message
        context_parts.append(f"Human: {new_message}")
        context_parts.append("")
        context_parts.append("Assistant:")
        
        full_prompt = "\n".join(context_parts)
        
        # Log the context being sent (truncated for readability)
        print(f"[SESSION {self.session_id[:8]}] Context prompt ({len(full_prompt)} chars):")
        print(full_prompt[:500] + "..." if len(full_prompt) > 500 else full_prompt)
        
        return full_prompt

class ClaudeMemoryOrchestrator:
    """Orchestrator for Claude sessions with memory"""
    
    def __init__(self):
        self.sessions: Dict[str, ClaudeMemorySession] = {}
        self.session_data: Dict[str, Dict] = {}  # Store additional session data
        print("[MEMORY ORCHESTRATOR] Initialized with conversation memory")
        
    def create_session(self, tab_id: str) -> str:
        """Create a new Claude session for a tab"""
        session_id = str(uuid.uuid4())
        session = ClaudeMemorySession(session_id, tab_id=tab_id)
        self.sessions[tab_id] = session
        self.session_data[tab_id] = {
            'created_at': datetime.now().isoformat(),
            'message_count': 0
        }
        print(f"[MEMORY ORCHESTRATOR] Created session {session_id[:8]} for tab {tab_id}")
        return session_id
        
    def send_message(self, tab_id: str, message: str) -> Optional[str]:
        """Send message to a session and get response"""
        if tab_id not in self.sessions:
            print(f"[MEMORY ORCHESTRATOR] No session for tab {tab_id}, creating one")
            self.create_session(tab_id)
            
        session = self.sessions[tab_id]
        response = session.send_message(message)
        
        # Update session data
        if tab_id in self.session_data:
            self.session_data[tab_id]['message_count'] += 1
            self.session_data[tab_id]['last_activity'] = datetime.now().isoformat()
        
        return response
    
    def send_message_with_retry_feedback(self, tab_id: str, message: str, callback=None) -> Optional[str]:
        """Send message with real-time retry feedback"""
        if tab_id not in self.sessions:
            print(f"[MEMORY ORCHESTRATOR] No session for tab {tab_id}, creating one")
            self.create_session(tab_id)
            
        session = self.sessions[tab_id]
        
        # Custom wrapper to provide feedback during retries
        class RetryFeedbackSession:
            def __init__(self, original_session, feedback_callback):
                self.original_session = original_session
                self.feedback_callback = feedback_callback
                
            def send_message(self, msg, retry_count=0):
                if retry_count > 0 and self.feedback_callback:
                    # Send immediate feedback to user
                    if retry_count == 1:
                        self.feedback_callback("⚠️ Execution error - Trying again...")
                    else:
                        self.feedback_callback(f"⚠️ Execution error - Trying again (attempt {retry_count})...")
                
                return self.original_session.send_message(msg, retry_count)
        
        if callback:
            wrapped_session = RetryFeedbackSession(session, callback)
            response = wrapped_session.send_message(message)
        else:
            response = session.send_message(message)
        
        # Update session data
        if tab_id in self.session_data:
            self.session_data[tab_id]['message_count'] += 1
            self.session_data[tab_id]['last_activity'] = datetime.now().isoformat()
        
        return response
        
    def cleanup_session(self, tab_id: str):
        """Clean up a session"""
        if tab_id in self.sessions:
            print(f"[MEMORY ORCHESTRATOR] Cleaning up session for tab {tab_id}")
            # Save conversation history before cleanup (optional)
            session = self.sessions[tab_id]
            if session.conversation_history:
                print(f"[MEMORY ORCHESTRATOR] Session had {len(session.conversation_history)} messages")
            
            del self.sessions[tab_id]
            if tab_id in self.session_data:
                del self.session_data[tab_id]
            
    def get_session_id(self, tab_id: str) -> Optional[str]:
        """Get session ID for a tab"""
        if tab_id in self.sessions:
            return self.sessions[tab_id].session_id
        return None
    
    def get_conversation_history(self, tab_id: str) -> List[Dict[str, str]]:
        """Get conversation history for a tab"""
        if tab_id in self.sessions:
            return self.sessions[tab_id].conversation_history
        return []

# Create global instance
simple_orchestrator = ClaudeMemoryOrchestrator()

if __name__ == "__main__":
    # Test
    print("Testing Claude memory wrapper...")
    
    session_id = simple_orchestrator.create_session("test_tab")
    print(f"Created session: {session_id}")
    
    # Test conversation with context
    response = simple_orchestrator.send_message("test_tab", "Hi! My name is Bob and I like pizza.")
    print(f"Response 1: {response}\n")
    
    response = simple_orchestrator.send_message("test_tab", "What's my name?")
    print(f"Response 2: {response}\n")
    
    response = simple_orchestrator.send_message("test_tab", "What food do I like?")
    print(f"Response 3: {response}\n")
    
    simple_orchestrator.cleanup_session("test_tab")
    print("Test completed!")