# Troubleshooting Guide

## Common Issues and Solutions

### 🎤 Microphone Not Working

**Symptoms:**
- No red recording indicator
- "Speech recognition not supported" error
- No voice input detected

**Solutions:**
1. **Check browser compatibility**
   - Use Chrome, Edge, or other Chromium-based browsers
   - Firefox has limited Web Speech API support

2. **Verify HTTPS connection**
   - Must access via HTTPS (not HTTP)
   - Accept self-signed certificate if prompted

3. **Check microphone permissions**
   - Click the lock icon in address bar
   - Ensure microphone is set to "Allow"
   - Refresh the page after changing permissions

4. **Test microphone**
   ```bash
   # Linux
   arecord -l
   
   # Test recording
   arecord -d 5 test.wav && aplay test.wav
   ```

### 🤖 No Bot Response

**Symptoms:**
- Messages sent but no reply
- "Bot is typing..." never completes
- Empty response bubbles

**Solutions:**
1. **Check Claude CLI**
   ```bash
   # Test Claude directly
   claude --version
   claude "Hello, are you working?"
   ```

2. **Verify orchestrator is running**
   - Check server logs for errors
   - Look for `[ORCHESTRATOR] Initialized` message

3. **Session limit reached**
   ```bash
   # Clear sessions and restart
   pkill -f "claude"
   python3 multi_tab_voice_exact_replica.py
   ```

4. **Check logs**
   ```bash
   tail -f server_*.log | grep -E "ERROR|WARN|Failed"
   ```

### 🔊 No Audio/TTS Not Working

**Symptoms:**
- No voice playback
- TTS server errors
- Silent responses

**Solutions:**
1. **Verify TTS server is running**
   ```bash
   # Check if running
   ps aux | grep edge_tts_server
   
   # Check port 5001
   netstat -tlnp | grep 5001
   ```

2. **Check mute button**
   - Ensure speaker icon shows 🔊 (not 🔇)
   - Click to toggle if muted

3. **Browser audio permissions**
   - Some browsers block autoplay
   - Click anywhere on page to enable audio

4. **Test TTS directly**
   ```bash
   curl -k https://localhost:5001/tts \
     -d "text=Hello world" \
     -o test.mp3
   ```

### 🔐 SSL Certificate Errors

**Symptoms:**
- "NET::ERR_CERT_AUTHORITY_INVALID"
- "Your connection is not private"
- Cannot access HTTPS URLs

**Solutions:**
1. **Generate new certificates**
   ```bash
   # Remove old certificates
   rm cert.pem key.pem
   
   # Generate new ones
   openssl req -x509 -newkey rsa:4096 \
     -keyout key.pem -out cert.pem \
     -days 365 -nodes \
     -subj "/CN=localhost"
   ```

2. **Accept certificate in browser**
   - Click "Advanced" → "Proceed to localhost"
   - Or type `thisisunsafe` on the error page

3. **Add certificate exception**
   - Chrome: Settings → Privacy → Manage certificates
   - Firefox: Settings → Privacy → View Certificates

### 📡 WebSocket Connection Failed

**Symptoms:**
- "WebSocket connection failed"
- Real-time updates not working
- Chat appears frozen

**Solutions:**
1. **Check Socket.IO version**
   ```bash
   pip show python-socketio flask-socketio
   ```

2. **Firewall/proxy issues**
   - Disable proxy temporarily
   - Check firewall rules for WebSocket

3. **Browser console errors**
   - Press F12 → Console tab
   - Look for WebSocket errors
   - Clear cache and cookies

### 💬 Messages Truncated

**Symptoms:**
- Only first line of response shown
- Multi-line responses cut off
- Lists appear incomplete

**Solutions:**
1. **Update to latest version**
   ```bash
   git pull origin main
   ```

2. **Check response capture**
   - Look for `[CAPTURE] Emitting complete response` in logs
   - Verify multi-line capture is working

### 🎵 Chime Not Playing

**Symptoms:**
- No notification sound
- Bell icon shows enabled but no sound

**Solutions:**
1. **Check bell button**
   - Should show 🔔 (not 🔕)
   - Click to toggle

2. **Browser audio context**
   - Click anywhere on page first
   - Some browsers require user interaction

3. **Volume settings**
   - Check system volume
   - Check browser tab not muted

### 🏷️ Tab Issues

**Symptoms:**
- Cannot rename tabs
- Tab highlighting not working
- Wrong tab receiving messages

**Solutions:**
1. **Double-click to rename**
   - Must double-click on tab text
   - Press Enter to save, Escape to cancel

2. **Clear browser cache**
   - Ctrl+Shift+R (hard refresh)
   - Clear site data if needed

3. **Check JavaScript errors**
   - F12 → Console
   - Look for errors when switching tabs

### 🚨 High CPU/Memory Usage

**Symptoms:**
- Browser becoming slow
- System lagging
- Memory warnings

**Solutions:**
1. **Limit active sessions**
   - Close unused tabs
   - Restart application periodically

2. **Clear conversation history**
   - Refresh browser to reset
   - Long conversations use more memory

3. **Check for memory leaks**
   ```bash
   # Monitor Python processes
   htop
   # or
   ps aux | grep python | grep multi_tab
   ```

## Debug Mode

Enable detailed logging:

```python
# In multi_tab_voice_exact_replica.py
app.config['DEBUG'] = True
logging.basicConfig(level=logging.DEBUG)
```

## Log Files

Check these logs for detailed error information:
- `server_*.log` - Main application logs
- `edge_tts_*.log` - TTS server logs
- Browser console - Client-side errors

## Getting Help

If issues persist:
1. Check [GitHub Issues](https://github.com/Corptech02/Multi-voice-bot/issues)
2. Create detailed bug report with:
   - Error messages
   - Browser/OS versions
   - Steps to reproduce
   - Relevant log excerpts