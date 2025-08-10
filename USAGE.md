# Usage Guide

## Getting Started

Once the application is running, access it at `https://192.168.40.232:8444`

## Interface Overview

### Tabs
- **4 Independent Sessions**: Each tab maintains its own conversation with Claude
- **Tab Naming**: Double-click any tab to rename it
- **Visual Indicators**: 
  - Active tab: Green border
  - Unread messages: Yellow highlight
  - Recording: Red background on mic button

### Controls
- **🎤 Microphone Button**: Click to start/stop voice recording
- **🔊/🔇 Mute Button**: Toggle text-to-speech audio
- **🔔/🔕 Bell Button**: Toggle notification chimes
- **Text Input**: Type messages directly

## Voice Commands

### Recording
1. Click the microphone button or press spacebar
2. Speak your command
3. The system auto-stops after 2 seconds of silence
4. Or click the button again to stop manually

### Smart Tab Handling
- Start recording in Tab 1
- Switch to Tab 2 while speaking
- Your message goes to Tab 1 (where you started)
- Recording auto-stops when switching tabs

## Text Input

1. Click in the text box at the bottom
2. Type your message
3. Press Enter to send
4. Shift+Enter for new lines

## Features in Action

### Multi-Tab Conversations
```
Tab 1: "Help me write a Python script"
Tab 2: "Explain quantum computing"
Tab 3: "Debug this JavaScript code"
Tab 4: "Write a bash script"
```

### Voice Recognition Examples
- "What is the weather today?"
- "Write a function to sort an array"
- "Explain this error message"
- "Create a README file"

### Notification System
- **Yellow Tab**: Unread message in inactive tab
- **Chime Sound**: Plays for all responses
- **Visual Flash**: Brief highlight on new messages

## Keyboard Shortcuts

- **Space**: Start/stop recording
- **Enter**: Send text message
- **Shift+Enter**: New line in text input
- **Tab/Shift+Tab**: Navigate between tabs

## Tips and Tricks

1. **Batch Operations**: Open multiple tabs for parallel tasks
2. **Context Preservation**: Each tab maintains full conversation history
3. **Quick Switch**: Use keyboard to rapidly switch between conversations
4. **Voice Drafting**: Speak rough ideas, Claude will help refine them

## Advanced Usage

### Running Bash Commands
Claude can execute bash commands with auto-approval enabled:
```
"List all Python files in the current directory"
"Check the system memory usage"
"Create a new directory called 'project'"
```

### Code Writing
```
"Write a REST API in Flask"
"Create a React component for a todo list"
"Generate unit tests for this function"
```

### File Operations
```
"Read the contents of config.json"
"Create a new file called app.py"
"Edit the README to add installation steps"
```

## Common Workflows

### Development Session
1. Tab 1: Main coding task
2. Tab 2: Documentation writing
3. Tab 3: Debugging issues
4. Tab 4: Research and questions

### Content Creation
1. Tab 1: Blog post draft
2. Tab 2: Technical explanations
3. Tab 3: Code examples
4. Tab 4: Fact-checking

## Troubleshooting

### Voice Not Working
- Check microphone permissions
- Ensure HTTPS connection
- Try refreshing the page

### No Bot Response
- Check server logs
- Verify Claude CLI is working
- Ensure all services are running

### Audio Issues
- Check mute button status
- Verify TTS server is running
- Check browser audio permissions