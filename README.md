# RFID Label Printing with Python

This project is being developed to automate the creation and printing of labels for RFID-tagged components.

The intended system will read an RFID tag, obtain the required component information, generate a label containing the RFID information, PID, and date, and send the label to a Brother QL-1100 label printer.

## Project Status

### Current status

The initial label-generation program is working on Windows.

The current Python program:

- Uses Python
- Uses Pillow for label generation
- Creates a 4 × 2 inch label at 300 DPI
- Adds a PID number
- Automatically adds the current date
- Saves the generated label as a PNG image

### Current example

The generated label currently contains:

```text
RFID COMPONENT

PID: PMT-0042
Date: 2026-10-06
