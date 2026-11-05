# Troubleshooting

This project was tested with a Brother QL-1100 using the DK-2246 103 mm continuous roll on Linux. Run commands from the project directory unless noted otherwise.

## 1. Check whether Linux recognizes the Brother printer

List the Brother QL-1100 USB device:

```bash
lsusb -d 04f9:20a7
```

Expected output includes a line similar to:

```text
Bus 001 Device 007: ID 04f9:20a7 Brother Industries, Ltd QL-1100 Label Printer
```

The bus and device numbers may differ. If there is no output, check the USB cable, printer power, and USB connection.

Check the Linux printer device:

```bash
ls -l /dev/usb/lp0
```

A typical result is similar to:

```text
crw-rw----. 1 root lp 180, 0 ... /dev/usb/lp0
```

The punctuation, date, and device numbers can vary. If `/dev/usb/lp0` does not exist, check the `lsusb` output and whether the Linux printer driver created a device node. If the printer appears under a different device path, configure `LABEL_PRINTER_DEVICE` accordingly.

## 2. Check user permissions for `/dev/usb/lp0`

Run:

```bash
groups
getent group lp
id "$USER"
test -w /dev/usb/lp0 && echo "Writable" || echo "Not writable"
```

The `groups` output for the user running the GUI should include `lp`, for example:

```text
mbarbi wheel dialout lp
```

The exact order and other groups may differ. `getent group lp` should show the `lp` group and the user, for example:

```text
lp:x:7:mbarbi
```

The group number may differ. `id "$USER"` should list `lp` among the user's groups. The write-access test should print:

```text
Writable
```

If the `lp` group does not include your username, an administrator can add the account. For the `mbarbi` account, run:

```bash
sudo usermod -aG lp mbarbi
getent group lp
id mbarbi
```

Confirm that `getent group lp` includes `mbarbi` and `id mbarbi` lists `lp`. Group membership changes do not update terminals and desktop sessions that are already running. Open a new terminal and check `groups` again. If the GUI session still does not have the updated group, log out of the desktop account and log back in. A new terminal opened under a different username will not fix permissions for `mbarbi`; run the application as the intended user.

Then retry:

```bash
test -w /dev/usb/lp0 && echo "Writable" || echo "Not writable"
```

## 3. Run a printer and cutter test

From the project directory, run the normal test first:

```bash
./run_printer_test.sh
```

Confirm when prompted. It should print and cut one small test label.

If the normal test fails with `PermissionError: [Errno 13] Permission denied: '/dev/usb/lp0'`, and you need to confirm that the problem is device permissions, you may run this **one-time diagnostic**:

```bash
sudo .venv/bin/python printer_test.py --yes
```

This prints a label immediately without confirmation. If it works with `sudo` but not as the normal user, the problem is almost certainly the user's device permissions. Do not use `sudo` as the regular way to launch the GUI; fix the group/session permissions above instead.

## 4. `brother_ql` command not found

Check the executable in the project's virtual environment:

```bash
ls -l .venv/bin/brother_ql
.venv/bin/brother_ql --help
.venv/bin/python -c 'import sys; from pathlib import Path; p=Path(sys.prefix)/"bin"/"brother_ql"; print("Python:", sys.executable); print("CLI:", p); print("Exists:", p.is_file()); print("Executable:", p.is_file() and __import__("os").access(p, __import__("os").X_OK))'
```

The CLI should exist and be executable. `shutil.which("brother_ql")` may return `None` if `.venv/bin` is not in `PATH`; this alone is not a problem when the application can find `.venv/bin/brother_ql` directly. If the executable is genuinely missing, rerun the project setup or install the declared dependency inside `.venv`.

## 5. RFID reader not found

Make sure the M7E-Hecto is connected by USB. The reader used in the tested setup appeared as:

```text
ID 1a86:7523 QinHeng Electronics CH340 serial converter
```

Check USB recognition:

```bash
lsusb
ls -l /dev/ttyUSB0
```

The serial device may be `/dev/ttyUSB1` or another number. The package detects the reader automatically. If the device is permission denied, check:

```bash
groups
```

On many Linux systems, the serial-device group is `dialout`. If you were added to that group, log out and back in (or start a new terminal and recheck `groups`) before trying again.

## 6. Python package or import problems

Use the project's virtual environment rather than the system Python:

```bash
.venv/bin/python -m pip show pillow pyserial brother-ql-inventree
.venv/bin/python -m pip show rfid-m7e-hecto
```

The RFID package is platform- and Python-version-dependent. The bundled wheel is for CPython 3.14 on Linux x86-64. If that wheel is not compatible with the computer, manual PID entry and label printing can still work, but RFID reading requires a compatible package build.

## 7. RFID tag is not detected

Make sure:

- The M7E-Hecto is connected.
- An RFID tag is within the reader's range.
- The tag is compatible with the configured GEN2 protocol.
- The tag is positioned close enough to the antenna.

The default read power is 2600 (26 dBm).

## 8. TID appears as unreadable characters

TID data is binary data. The RFID package converts it to an uppercase hexadecimal string. The application should use `get_tid()` and should not decode the TID as ordinary text.

## 9. Multiple CH340 devices

If more than one device with the same USB VID/PID is connected, the package may report multiple matching devices. Disconnect unrelated CH340 devices and try again.
