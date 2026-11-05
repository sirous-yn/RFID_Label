"""Optional interface to the existing M7E-Hecto RFID package.

The label application remains usable without the RFID wheel: operators can
enter a PID manually. On compatible Linux/Python systems, get_pid() reads the
TID returned by the existing rfid_reader package and exposes it as the label PID.
"""


def get_pid():
    """Return the identifier read from a nearby RFID tag.

    Raises a helpful RuntimeError if the optional RFID package is not installed,
    the reader is unavailable, or no tag is detected.
    """
    try:
        from rfid_reader import get_tid
    except ImportError as exc:
        raise RuntimeError(
            "RFID support is not installed in this Python environment. "
            "See README.md for the supported Linux/Python combination. "
            "You can still enter the PID manually."
        ) from exc

    try:
        identifier = get_tid()
    except Exception as exc:
        raise RuntimeError(f"The RFID reader could not read a tag: {exc}") from exc

    if not identifier:
        raise RuntimeError("No RFID tag was detected. Enter the PID manually.")

    return str(identifier).strip()
