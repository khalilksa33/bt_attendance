#!/bin/bash

# Path to your project directory (use the script's location)
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"

# Activate virtual environment
source .venv/bin/activate

# Execute the Python script
echo "Starting Attendance Report Generation for $(date +%B)..."
python daily_checkin_log.py

if [ $? -eq 0 ]; then
    echo "Report sent successfully."
else
    echo "Error: Report generation failed." >&2
fi

# Cron schedule:
# Daily at 9:30 AM
# 30 9 * * * /bin/bash /home/frappe/bt_attendance/run_report.sh >> /home/frappe/bt_attendance/log.txt 2>&1