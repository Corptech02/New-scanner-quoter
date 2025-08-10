# Installation Guide

## Prerequisites

- Python 3.8 or higher
- Claude CLI installed and configured
- Modern web browser with WebRTC support (Chrome/Edge recommended)
- SSL certificates for HTTPS (self-signed or valid)

## Step 1: Clone the Repository

```bash
git clone https://github.com/Corptech02/Multi-voice-bot.git
cd Multi-voice-bot
```

## Step 2: Set Up Python Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # On Linux/Mac
# or
venv\Scripts\activate  # On Windows

# Install dependencies
pip install -r requirements.txt
```

## Step 3: Install Claude CLI

If you haven't installed Claude CLI yet:

```bash
# Download and install Claude CLI from Anthropic
# Follow the official installation guide at:
# https://docs.anthropic.com/claude/docs/claude-cli
```

## Step 4: Generate SSL Certificates

For local development, create self-signed certificates:

```bash
# Generate private key
openssl genrsa -out key.pem 2048

# Generate certificate
openssl req -new -x509 -key key.pem -out cert.pem -days 365 \
  -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost"
```

## Step 5: Configure the Application

1. Update IP addresses in the Python files if needed:
   - Default: `192.168.40.232`
   - Change to your local IP or `127.0.0.1` for localhost

2. Update port numbers if conflicts exist:
   - Main app: `8444`
   - TTS server: `5001`

## Step 6: Run the Application

1. Start the TTS server:
```bash
python3 edge_tts_server_https.py
```

2. In a new terminal, start the main application:
```bash
python3 multi_tab_voice_exact_replica.py
```

3. Access the interface at:
```
https://192.168.40.232:8444
```

## Step 7: Browser Configuration

1. Accept the self-signed certificate warning
2. Allow microphone permissions when prompted
3. For best results, use Chrome or Edge browser

## Troubleshooting

- **Certificate errors**: Make sure cert.pem and key.pem exist in the project directory
- **Port conflicts**: Change port numbers in the Python files
- **Claude CLI not found**: Ensure Claude is in your PATH
- **No audio**: Check browser microphone permissions

## Optional: Auto-Approval Setup

To enable automatic bash command approval:

```bash
# Set environment variable
export CLAUDE_AUTO_APPROVE_BASH=1

# Or use the auto-approval script
python3 multi_tab_auto_approve.py
```