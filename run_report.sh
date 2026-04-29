#!/bin/bash

# Path to your project directory (use the script's location)
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"

# Activate virtual environment
source .venv/bin/activate

# Execute the Python script
echo "Starting Attendance Report Generation for $(date +%B)..."
python attendance_bot.py

if [ $? -eq 0 ]; then
    echo "Report sent successfully."
else
    echo "Error: Report generation failed." >&2
fi

# Cron schedule examples:
# Every Friday at 11:00 AM
# 0 11 * * 5 /bin/bash /home/frappe/bt_attendance/run_report.sh >> /home/frappe/bt_attendance/log.txt 2>&1
# On the 1st of each month at 11:00 AM
# 0 11 1 * * /bin/bash /home/frappe/bt_attendance/run_report.sh >> /home/frappe/bt_attendance/log.txt 2>&1