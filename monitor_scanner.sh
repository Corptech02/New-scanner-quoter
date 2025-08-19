#!/bin/bash

echo "Monitoring GEICO Scanner for Commercial Auto detection..."
echo "Press Ctrl+C to stop"
echo "========================================"

tail -f /home/corp06/software_projects/New-scanner-quoter/geico_scanner.log | grep -E "(MAIN LOOP|Commercial Auto|EMERGENCY|FORCE|LOGIN|DEBUG|SUCCESS|CLICKED)" --line-buffered