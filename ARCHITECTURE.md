# Architecture Documentation

## System Overview

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   Web Browser   │────▶│   Flask Server   │────▶│  Orchestrator   │
│  (Frontend UI)  │◀────│   (WebSocket)    │◀────│  (Session Mgr)  │
└─────────────────┘     └──────────────────┘     └─────────────────┘
         │                       │                         │
         │                       │                         ▼
         ▼                       ▼                 ┌─────────────────┐
┌─────────────────┐     ┌──────────────────┐     │  Claude CLI     │
│  Web Speech API │     │   TTS Server     │     │  (4 Sessions)   │
│  (Microphone)   │     │  (Edge TTS)      │     └─────────────────┘
└─────────────────┘     └──────────────────┘

```

## Component Details

### 1. Frontend (Browser)
- **Technology**: HTML5, JavaScript, CSS
- **Key Features**:
  - Web Speech API for voice recognition
  - Socket.IO client for real-time communication
  - Web Audio API for notification sounds
  - Local storage for user preferences

### 2. Flask Web Server
- **File**: `multi_tab_voice_exact_replica.py`
- **Port**: 8444 (HTTPS)
- **Responsibilities**:
  - Serve web interface
  - Handle WebSocket connections
  - Route messages to orchestrator
  - Manage SSL/TLS encryption

### 3. Orchestrator
- **File**: `orchestrator_simple_v2.py`
- **Pattern**: Session Manager
- **Features**:
  - Manages 4 independent Claude sessions
  - Routes messages to correct sessions
  - Captures and forwards responses
  - Handles session lifecycle

### 4. Claude Memory Wrapper
- **File**: `claude_memory_wrapper.py`
- **Purpose**: Maintain conversation context
- **Features**:
  - Stores conversation history
  - Formats prompts with context
  - Manages token limits
  - Executes Claude CLI commands

### 5. TTS Server
- **File**: `edge_tts_server_https.py`
- **Port**: 5001 (HTTPS)
- **Technology**: Microsoft Edge TTS
- **Voice**: en-US-AriaNeural

## Data Flow

### User Input Flow
1. User speaks or types in browser
2. Browser sends via WebSocket to Flask
3. Flask routes to orchestrator
4. Orchestrator finds correct session
5. Memory wrapper adds context
6. Claude CLI processes request

### Response Flow
1. Claude generates response
2. Memory wrapper captures output
3. Orchestrator detects new content
4. Flask emits via WebSocket
5. Browser displays message
6. TTS server generates audio
7. Browser plays audio response

## Session Management

### Session Structure
```python
BotSession:
  - session_id: UUID
  - tab_id: "tab_1" to "tab_4"
  - created_at: timestamp
  - messages: conversation history
  - is_active: boolean
```

### Tab Management
- Each tab = one Claude session
- Sessions persist across tab switches
- Independent conversation contexts
- Concurrent request handling

## Security Considerations

### SSL/TLS
- Self-signed certificates for development
- HTTPS required for:
  - Microphone access
  - Secure WebSocket
  - Cross-origin requests

### Command Execution
- `--dangerously-skip-permissions` flag
- Auto-approval for bash commands
- Sandboxed execution environment

## Performance Optimizations

### Response Capture
- Line-by-line processing
- Hash-based deduplication
- Multi-line response assembly
- Efficient content diffing

### WebSocket Communication
- Binary message support
- Automatic reconnection
- Event-based architecture
- Minimal latency design

## Scalability Considerations

### Current Limitations
- 4 fixed sessions
- Single-server architecture
- In-memory session storage
- Local Claude CLI dependency

### Potential Improvements
- Dynamic session creation
- Redis for session storage
- Containerized deployment
- Load balancer support

## Error Handling

### Frontend
- Microphone permission errors
- WebSocket disconnection
- Audio playback failures
- Browser compatibility

### Backend
- Claude CLI timeouts
- Session creation failures
- Memory limit exceeded
- SSL certificate errors

## Monitoring Points

### Key Metrics
- Response time per session
- Active sessions count
- WebSocket connections
- TTS generation time

### Log Locations
- Main app: `server_*.log`
- TTS server: `edge_tts_*.log`
- Orchestrator: inline logs
- Claude wrapper: inline logs