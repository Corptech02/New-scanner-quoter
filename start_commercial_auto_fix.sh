#!/bin/bash

# Kill any existing scanner processes
echo "Stopping existing scanner..."
pkill -f "geico_scanner"
sleep 2

# Start the new commercial auto fix scanner
echo "Starting Commercial Auto Fix Scanner..."
cd /home/corp06/software_projects/New-scanner-quoter/
python3 geico_scanner_commercial_auto_fix.py &

echo "Scanner started! Access it at: https://localhost:5558"
echo "The scanner now includes:"
echo "  - Auto-detection and clicking of Commercial Auto/Trucking tab"
echo "  - Force Commercial Auto Click button for manual override"
echo "  - Better click persistence and verification"
echo "  - Status tracking for commercial auto clicks"