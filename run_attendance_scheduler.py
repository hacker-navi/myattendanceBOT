from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

from check_attendance_once import run_check
from erp_automation.config import CHECK_INTERVAL_HOURS, CHECK_TIMES, TIMEZONE


def _job() -> None:
    try:
        print("Running scheduled attendance check...")
        run_check()
    except Exception as exc:
        print(f"Scheduled check failed: {exc}")


def main() -> None:
    scheduler = BlockingScheduler(timezone=TIMEZONE)

    parsed_times = [item.strip() for item in CHECK_TIMES.split(",") if item.strip()]
    if parsed_times:
        for value in parsed_times:
            hour_str, minute_str = value.split(":")
            scheduler.add_job(_job, CronTrigger(hour=int(hour_str), minute=int(minute_str)))
            print(f"Scheduled at {value} ({TIMEZONE})")
    else:
        scheduler.add_job(_job, "interval", hours=CHECK_INTERVAL_HOURS)
        print(f"Scheduled every {CHECK_INTERVAL_HOURS} hour(s)")

    print("Scheduler started. Press Ctrl+C to stop.")
    _job()
    scheduler.start()


if __name__ == "__main__":
    main()
