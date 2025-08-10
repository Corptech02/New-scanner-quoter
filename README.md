# Claude Multi-Tab Voice Bot

A sophisticated multi-tab voice interface for Claude AI with real-time speech recognition, text-to-speech, and session management.

## Features

- **4 Independent Claude Sessions**: Each tab maintains its own conversation context
- **Voice Recognition**: Real-time speech-to-text with 2-second silence detection
- **Text-to-Speech**: High-quality voice synthesis using Edge TTS
- **Visual Feedback**: 
  - Red recording indicator when microphone is active
  - Yellow tab highlighting for unread messages
  - Blue chat bubbles for bot responses
- **Smart Tab Management**:
  - Voice messages go to the tab where recording started
  - Auto-send when switching tabs while recording
  - Double-click to rename tabs
- **Cross-Tab Notifications**: Chime sounds for responses on any tab
- **Auto-Approval**: Bash commands are automatically approved via `--dangerously-skip-permissions`

## Architecture

- **Frontend**: Flask web server with Socket.IO for real-time communication
- **Backend**: Orchestrator pattern managing multiple Claude CLI sessions
- **TTS Server**: Separate HTTPS server for text-to-speech synthesis
- **Memory Wrapper**: Maintains conversation history for each session

## Running the Application

1. Start the TTS server:
   ```bash
   python3 edge_tts_server_https.py
   ```

2. Start the main application:
   ```bash
   python3 multi_tab_voice_exact_replica.py
   ```

3. Access the interface at: https://192.168.40.232:8444

## Files

- `multi_tab_voice_exact_replica.py` - Main web application
- `orchestrator_simple_v2.py` - Session management orchestrator
- `claude_memory_wrapper.py` - Claude CLI wrapper with memory
- `edge_tts_server_https.py` - Text-to-speech server

## UI Specifications

- **Theme**: Cyberpunk-inspired with neon green accents
- **Layout**: 4 tabs, voice controls, text input
- **Colors**: Dark background (#0a0a0a), neon green borders (#00ff00)
- **Animations**: Pulsing mic button, glowing effects

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>