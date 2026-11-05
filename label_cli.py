#!/usr/bin/env python3
"""Interactive command-line label creation and printing; no GUI required."""

from datetime import date

from label_printer import print_label
from rfid_interface import get_pid

DEFAULT_TITLE = "BOARD IDENTIFICATION"


def ask(prompt, default=""):
    value = input(prompt).strip()
    return default if value == "" else value


def yes_no(prompt, default_yes=True):
    hint = "Y/n" if default_yes else "y/N"
    answer = input(f"{prompt} [{hint}]: ").strip().lower()
    if not answer:
        return default_yes
    return answer in {"y", "yes"}


def optional_value(prompt, default=""):
    """Blank keeps the default; entering '-' deliberately omits the field."""
    value = input(prompt).strip()
    if value == "-":
        return ""
    if value == "":
        return default
    return value


def main():
    today = date.today().isoformat()
    print("Label Printer — command-line mode")
    print("Enter '-' to omit an optional title or date.")
    print("Printing only occurs after you confirm at the end.\n")

    title = optional_value(
        f"Title [{DEFAULT_TITLE}] (or '-' for no title): ",
        default=DEFAULT_TITLE,
    )
    label_date = optional_value(
        f"Date [{today}] (or '-' for no date): ",
        default=today,
    )
    run_id = input("Run ID (blank for none): ").strip()

    pid = ""
    if yes_no("Read PID from RFID tag now?", default_yes=False):
        print("Reading RFID tag...")
        try:
            pid = get_pid()
            print(f"RFID identifier: {pid}")
        except Exception as error:
            print(f"RFID reading was not successful: {error}")
            pid = input("Enter PID manually (blank to omit): ").strip()
    else:
        pid = input("PID (manual entry; blank for none): ").strip()

    board_type = ""
    if pid:
        while board_type not in {"A", "B"}:
            board_type = input("Board type for this PID (A or B): ").strip().upper()
            if board_type not in {"A", "B"}:
                print("Please enter A or B.")

    extra_info = input("Extra information (one line; blank for none): ").strip()
    include_logo = yes_no("Include the University of Regina logo?", default_yes=True)

    print("\nLabel details")
    print("-------------")
    print(f"Title: {title or '(omitted)'}")
    print(f"Date: {label_date or '(omitted)'}")
    print(f"Run ID: {run_id or '(omitted)'}")
    print(f"PID: {pid or '(omitted)'}")
    print(f"Board type: {board_type if pid else '(not needed)'}")
    print(f"Extra information: {extra_info or '(omitted)'}")
    print(f"Include logo: {'yes' if include_logo else 'no'}")

    if not any((title, label_date, run_id, pid, extra_info)):
        print("No information entered. Nothing was printed.")
        return

    if not yes_no("Print this label now?", default_yes=False):
        print("Cancelled. Nothing was printed.")
        return

    try:
        print_label(
            title=title,
            date=label_date,
            run_id=run_id,
            pid=pid,
            board_type=board_type,
            extra_info=extra_info,
            include_logo=include_logo,
        )
        print("Print command completed.")
    except Exception as error:
        print(f"Printing failed: {error}")
        raise SystemExit(1) from error


if __name__ == "__main__":
    main()
