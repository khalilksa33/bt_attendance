#!/usr/bin/env python3
import argparse
from datetime import datetime, timedelta
from pathlib import Path
import os
import pandas as pd

from attendance_bot import (
    get_erp_users,
    get_erp_attendance_data,
    get_biometric_data,
    get_remote_checkin_data,
    write_daily_checkin_log,
    send_email,
)

BASE_DIR = Path(__file__).resolve().parent


def parse_args():
    parser = argparse.ArgumentParser(
        description="Generate a daily-only human-readable check-in log and notify selected recipients."
    )
    parser.add_argument(
        "--date",
        help="Date for the log in YYYY-MM-DD format. Defaults to today.",
    )
    parser.add_argument(
        "--start",
        help="Start date for range in YYYY-MM-DD format. Overrides --date when both are provided.",
    )
    parser.add_argument(
        "--end",
        help="End date for range in YYYY-MM-DD format. Required when --start is provided.",
    )
    parser.add_argument(
        "--to",
        help="Comma-separated recipient numbers or identifiers.",
    )
    parser.add_argument(
        "--from",
        dest="from_number",
        help="Sender identifier or configuration.",
    )
    return parser.parse_args()


def parse_date_range(date_arg, start_arg, end_arg):
    if start_arg:
        if not end_arg:
            raise ValueError("When --start is set, --end must also be provided.")
        start = datetime.fromisoformat(start_arg)
        end = datetime.fromisoformat(end_arg)
        end = end.replace(hour=23, minute=59, second=59, microsecond=999999)
        return start, end

    if date_arg:
        report_date = datetime.fromisoformat(date_arg)
    else:
        report_date = datetime.now()
    start = datetime(report_date.year, report_date.month, report_date.day)
    end = start.replace(hour=23, minute=59, second=59, microsecond=999999)
    return start, end


def generate_report_for_date(report_date):
    """
    Fetches attendance sources and generates log file entries for a given date.
    Email execution has been decoupled from this function to avoid duplicate dispatches.
    """
    report_start = datetime(report_date.year, report_date.month, report_date.day)
    report_end = report_start.replace(hour=23, minute=59, second=59, microsecond=999999)
    report_name = report_start.strftime("%d-%m-%Y")

    print(f"Generating daily check-in log data for {report_name}")

    try:
        df_erp_attendance = get_erp_attendance_data(report_start, report_end)
        df_bio = get_biometric_data(report_start, report_end)
        df_users = get_erp_users()
        df_remote = get_remote_checkin_data(report_start, report_end)

        attendance_frames = []
        for frame in (df_erp_attendance, df_bio, df_remote):
            if not frame.empty:
                attendance_frames.append(frame)

        if attendance_frames:
            df_attendance = pd.concat(attendance_frames, ignore_index=True)
        else:
            df_attendance = pd.DataFrame(columns=['user_id', 'timestamp'])

        df_attendance = df_attendance.drop_duplicates(subset=['user_id', 'timestamp'])
        df_attendance['user_id'] = df_attendance['user_id'].astype(str)
        df_users['attendance_device_id'] = df_users['attendance_device_id'].astype(str)

        df_merged = pd.merge(df_attendance, df_users, left_on='user_id', right_on='attendance_device_id')
        df_merged['timestamp'] = pd.to_datetime(df_merged['timestamp'], errors='coerce')

        write_daily_checkin_log(df_merged, df_users, report_start, report_end)

    except Exception as exc:
        print(f"Report generation failed for {report_name}: {exc}")
        raise exc


def main():
    args = parse_args()
    log_path = BASE_DIR / "logs" / "daily_checkin_details.txt"
    email_sent = False
    email_label = None

    if args.start:
        report_start, report_end = parse_date_range(args.date, args.start, args.end)
        email_label = f"{report_start.strftime('%d-%m-%Y')} to {report_end.strftime('%d-%m-%Y')}"
        print(f"Generating daily check-in log range for {email_label}")

        df_erp_attendance = get_erp_attendance_data(report_start, report_end)
        df_bio = get_biometric_data(report_start, report_end)
        df_users = get_erp_users()
        df_remote = get_remote_checkin_data(report_start, report_end)

        attendance_frames = []
        for frame in (df_erp_attendance, df_bio, df_remote):
            if not frame.empty:
                attendance_frames.append(frame)

        if attendance_frames:
            df_attendance = pd.concat(attendance_frames, ignore_index=True)
        else:
            df_attendance = pd.DataFrame(columns=['user_id', 'timestamp'])

        df_attendance = df_attendance.drop_duplicates(subset=['user_id', 'timestamp'])
        df_attendance['user_id'] = df_attendance['user_id'].astype(str)
        df_users['attendance_device_id'] = df_users['attendance_device_id'].astype(str)

        df_merged = pd.merge(df_attendance, df_users, left_on='user_id', right_on='attendance_device_id')
        df_merged['timestamp'] = pd.to_datetime(df_merged['timestamp'], errors='coerce')

        write_daily_checkin_log(df_merged, df_users, report_start, report_end)
        email_sent = True

    elif args.date:
        report_date = datetime.fromisoformat(args.date)
        email_label = report_date.strftime("%d-%m-%Y")
        
        generate_report_for_date(report_date)
        email_sent = True

    else:
        # Default automated run execution path
        today = datetime.now()
        yesterday = today - timedelta(days=1)
        
        # 1. Process data calculations sequentially for both days
        for report_date in [yesterday, today]:
            generate_report_for_date(report_date)
        
        email_label = f"{yesterday.strftime('%d-%m-%Y')} and {today.strftime('%d-%m-%Y')}"
        email_sent = True

    # 2. Send exactly ONE email transaction (consolidated at end to prevent duplicates)
    if email_sent and email_label:
        try:
            print(f"Sending email for: {email_label}")
            send_email(str(log_path), email_label)
            print("Email sent successfully.")
        except Exception as exc:
            print(f"Email send failed: {exc}")
            raise


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"Fatal execution error occurred: {exc}")
        raise
