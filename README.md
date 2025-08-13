# Geico Auto Quote Scanner

A web-based automation tool for scanning and monitoring Geico auto insurance quotes with real-time element detection and screenshot capture.

## Features

- **Browser Automation**: Selenium-based Chrome automation
- **Visual Element Detection**: Red overlay boxes on detected form elements
- **Screenshot Capture**: Automatic screenshots with timestamps
- **Process Management**: Automatic Chrome cleanup before each run
- **Web Interface**: Clean, responsive UI on port 5558

## Requirements

- Python 3.8+
- Chrome/Chromium browser
- Selenium WebDriver

## Installation

1. Clone the repository:
```bash
git clone https://github.com/Corptech02/New-scanner-quoter.git
cd New-scanner-quoter
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

1. Start the server:
```bash
python geico_scanner_fixed.py
```

2. Open your browser to:
```
http://localhost:5558
```

3. Click "Start Quote" to begin automation

## Technical Details

- **Port**: 5558
- **Framework**: Flask with Selenium
- **Browser**: Chrome in headless mode with custom window size
- **Element Detection**: XPath-based with visual overlays

## Files

- `geico_scanner_fixed.py` - Main scanner application
- `geico_auto_scanner.html` - Web interface
- `requirements.txt` - Python dependencies

## License

Private development project