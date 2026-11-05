# Portable Label Printer

A small Python label-printing project for Linux, designed around the Brother
QL-1100 and the 103 mm DK-2246 continuous roll. It includes a graphical
application, an interactive command-line label program, and a printer-test
script. The main data-taking program is not connected to this application;
labels are printed only when an operator explicitly requests one.

## Project contents

- `label_gui.py` — graphical form with preview, editable title/date, Run ID,
  PID, board type (A or B), optional information, RFID-read button, logo
  checkbox, Clear Form, Default Form, and Print Label. Board type has no
  default selection and is required whenever a PID is provided.
- `label_cli.py` — interactive command-line label creation/printing for systems
  where the GUI is not wanted or available.
- `printer_test.py` — prints one short test label to check printing and cutting.
- `label_printer.py` — shared label rendering and printing functions.
- `rfid_interface.py` — small interface to the existing `rfid_reader` package.
- `fonts/` — fonts used by the label, so system fonts are not required.
- `vendor/` — the optional M7E-Hecto RFID wheel that was tested on Linux x86-64
  with CPython 3.14.

The project does not carry a virtual environment. Each computer creates its
own `.venv` because Python virtual environments contain machine-specific paths
and installed native libraries and should not be copied between computers.

## Install on Linux

Internet access is required during setup to install Python dependencies from
PyPI/GitHub. After installation, the scripts can run without internet access.

1. Extract this folder to a location where the user has write access.
2. The University logo `UR_Logo.jpg`  should be beside `label_printer.py`.
3. Open a terminal in this folder and run:

   ```bash
   bash setup_linux.sh
   ```

The installer supports common Debian/Ubuntu (`apt`), Fedora (`dnf`), and Arch
Linux (`pacman`) package managers. It creates a local `.venv`, installs Pillow
and the maintained `brother_ql` fork, and installs the bundled RFID wheel only
if the Python/platform combination matches the wheel.

## Launch the application

### GUI mode

```bash
./run_gui.sh
```

Alternatively:

```bash
.venv/bin/python label_gui.py
```

### Command-line mode

```bash
./run_cli.sh
```

or:

```bash
.venv/bin/python label_cli.py
```

The command-line program asks for a title, date, Run ID, PID, board type when a
PID is present, optional information, and whether to include the logo. It can try to read the PID from
the RFID reader, and allows manual entry if RFID reading is unavailable. It asks
for confirmation before printing.

### Printer and cutter test

```bash
./run_printer_test.sh
```

Then confirm the prompt. To skip the confirmation intentionally:

```bash
./run_printer_test.sh --yes
```

The test does not use the RFID reader. It prints a small `PRINTER TEST` label
without the logo so that the printer and automatic cutter can be checked
independently.

## Printer settings on another computer

The defaults match the tested setup:

- Model: `QL-1100`
- Linux backend: `linux_kernel`
- Device: `/dev/usb/lp0`
- Media: `103` (DK-2246 continuous roll)
- Automatic cutting: enabled by the Brother QL command's default behavior

If another computer uses a different device path, set an environment variable
before launching the GUI or a command-line tool. For example:

```bash
export LABEL_PRINTER_DEVICE=/dev/usb/lp1
./run_gui.sh
```

Available overrides are:

```text
LABEL_PRINTER_MODEL
LABEL_PRINTER_DEVICE
LABEL_PRINTER_BACKEND
LABEL_MEDIA_TYPE
```

Use the actual device path and media type for that computer/printer. The
printer user must have permission to access the device. On Ubuntu systems where
the device belongs to group `lp`, an administrator can add the current user via
`sudo usermod -aG lp "$USER"`; log out and back in for group membership to take
 effect. If the device permissions are managed differently on that machine,
follow that distribution's USB printer permission configuration. See
`TROUBLESHOOTING.md` for USB detection, permission checks, and recovery steps.

## RFID compatibility is platform-dependent

The included file
`vendor/rfid_m7e_hecto-1.0.0-cp314-none-linux_x86_64.whl` is a native package
for **CPython 3.14 on Linux x86-64**. The installer does not install it on other
Python versions or CPU architectures. In those cases, the label printer and
manual PID entry still work, but RFID reading requires a compatible build of
the existing M7E-Hecto package for that system.

The GUI treats RFID as optional. If the reader package is not available, the
operator can still enter a PID manually. For hardware access, the RFID user also
needs appropriate serial/USB permissions.

## Portability notes

This is a portable source package, not a universal executable. Linux hardware
paths, device permissions, OS packages, CPU architecture, and Python ABI differ
between computers. The installer handles common Linux distributions, but it
cannot make a native RFID wheel compatible with every architecture or Python
version. Test the printer and RFID reader separately on a new computer before
using them in an experiment.
