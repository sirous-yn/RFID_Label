#!/usr/bin/env python3
"""Print a small test label to verify the printer and cutter."""

import argparse
from datetime import date

from label_printer import print_label, PRINTER_DEVICE, PRINTER_MODEL


def main():
    parser = argparse.ArgumentParser(
        description="Print a test label using the configured Brother QL printer."
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        help="skip the final confirmation prompt",
    )
    args = parser.parse_args()

    print("Printer test")
    print("------------")
    print("This will print and cut one test label.")
    print(f"Printer model: {PRINTER_MODEL}")
    print(f"Printer device: {PRINTER_DEVICE}")

    if not args.yes:
        answer = input("Print a test label now? [y/N]: ").strip().lower()
        if answer not in {"y", "yes"}:
            print("Test cancelled. Nothing was printed.")
            return

    try:
        print_label(
            title="PRINTER TEST",
            date=date.today().isoformat(),
            extra_info="Printer and cutter test",
            include_logo=False,
        )
        print("Print command completed. Check the label and automatic cut.")
    except Exception as error:
        print(f"Printer test failed: {error}")
        raise SystemExit(1) from error


if __name__ == "__main__":
    main()
