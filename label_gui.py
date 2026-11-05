"""Standalone GUI for creating and printing labels on a Brother QL-1100.

Printing only occurs when the operator clicks Print Label.
"""

import tkinter as tk
from datetime import date as system_date
from tkinter import messagebox, ttk
from PIL import Image, ImageTk

from label_printer import render_label, print_label

try:
    from rfid_interface import get_pid
except Exception:
    get_pid = None


DEFAULT_TITLE = "BOARD IDENTIFICATION"


class LabelPrinterGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Label Printer")
        self.root.geometry("980x850")
        self.root.minsize(760, 700)

        self.title_var = tk.StringVar(value=DEFAULT_TITLE)
        self.date_var = tk.StringVar(value=system_date.today().strftime("%Y-%m-%d"))
        self.run_id_var = tk.StringVar()
        self.pid_var = tk.StringVar()
        self.board_type_var = tk.StringVar(value="")
        self.include_logo_var = tk.BooleanVar(value=True)

        self.preview_photo = None
        self.preview_after_id = None

        self._build_interface()
        self._connect_live_preview()
        self.update_preview()

    def _build_interface(self):
        outer = ttk.Frame(self.root, padding=14)
        outer.pack(fill="both", expand=True)
        outer.columnconfigure(1, weight=1)
        outer.rowconfigure(8, weight=1)

        # Title and quick restore button.
        ttk.Label(outer, text="Title:").grid(
            row=0, column=0, sticky="w", padx=(0, 10), pady=5
        )
        self.title_entry = ttk.Entry(outer, textvariable=self.title_var)
        self.title_entry.grid(row=0, column=1, sticky="ew", pady=5)
        ttk.Button(
            outer,
            text="Restore Default Title",
            command=self.restore_default_title,
        ).grid(row=0, column=2, sticky="ew", padx=(8, 0), pady=5)

        # Date (defaults to today's date but remains editable).
        ttk.Label(outer, text="Date (YYYY-MM-DD):").grid(
            row=1, column=0, sticky="w", padx=(0, 10), pady=5
        )
        self.date_entry = ttk.Entry(outer, textvariable=self.date_var)
        self.date_entry.grid(
            row=1, column=1, sticky="ew", pady=5
        )
        ttk.Button(
            outer,
            text="Today's Date",
            command=self.set_current_date,
        ).grid(row=1, column=2, sticky="ew", padx=(8, 0), pady=5)

        # Run ID.
        ttk.Label(outer, text="Run ID:").grid(
            row=2, column=0, sticky="w", padx=(0, 10), pady=5
        )
        self.run_id_entry = ttk.Entry(outer, textvariable=self.run_id_var)
        self.run_id_entry.grid(
            row=2, column=1, columnspan=2, sticky="ew", pady=5
        )

        # PID and RFID reader.
        ttk.Label(outer, text="PID:").grid(
            row=3, column=0, sticky="w", padx=(0, 10), pady=5
        )
        self.pid_entry = ttk.Entry(outer, textvariable=self.pid_var)
        self.pid_entry.grid(row=3, column=1, sticky="ew", pady=5)
        self.read_rfid_button = ttk.Button(
            outer, text="Read RFID Tag", command=self.read_rfid
        )
        self.read_rfid_button.grid(
            row=3, column=2, sticky="ew", padx=(8, 0), pady=5
        )

        # Board type is deliberately blank by default. It is required only when
        # a PID is entered and is printed only alongside a PID.
        ttk.Label(outer, text="Board type (required with PID):").grid(
            row=4, column=0, sticky="w", padx=(0, 10), pady=5
        )
        self.board_type_combo = ttk.Combobox(
            outer,
            textvariable=self.board_type_var,
            values=("A", "B"),
            state="readonly",
            width=8,
        )
        self.board_type_combo.grid(row=4, column=1, sticky="w", pady=5)

        # Optional extra information.
        ttk.Label(outer, text="Extra information:").grid(
            row=5, column=0, sticky="nw", padx=(0, 10), pady=5
        )
        self.extra_info_text = tk.Text(outer, height=3, wrap="word", undo=True)
        self.extra_info_text.grid(
            row=5, column=1, columnspan=2, sticky="ew", pady=5
        )

        # Logo inclusion toggle. Enabled by default.
        self.logo_checkbox = ttk.Checkbutton(
            outer,
            text="Include University of Regina logo",
            variable=self.include_logo_var,
            command=self._schedule_preview,
        )
        self.logo_checkbox.grid(
            row=6, column=1, columnspan=2, sticky="w", pady=(5, 0)
        )

        ttk.Label(
            outer, text="Label Preview", font=("TkDefaultFont", 11, "bold")
        ).grid(row=7, column=0, columnspan=3, sticky="w", pady=(14, 5))

        self.preview_frame = ttk.LabelFrame(outer, text="", padding=10)
        self.preview_frame.grid(
            row=8, column=0, columnspan=3, sticky="nsew"
        )
        self.preview_frame.columnconfigure(0, weight=1)
        self.preview_frame.rowconfigure(0, weight=1)

        self.preview_label = ttk.Label(
            self.preview_frame,
            text="Preparing preview...",
            anchor="center",
        )
        self.preview_label.grid(row=0, column=0, sticky="nsew")

        bottom = ttk.Frame(outer)
        bottom.grid(row=9, column=0, columnspan=3, sticky="e", pady=(14, 0))

        ttk.Button(
            bottom, text="Clear Form", command=self.clear_form
        ).pack(side="left", padx=(0, 8))

        ttk.Button(
            bottom, text="Default Form", command=self.reset_default_form
        ).pack(side="left", padx=(0, 8))

        ttk.Button(
            bottom, text="Refresh Preview", command=self.update_preview
        ).pack(side="left", padx=(0, 8))

        self.print_button = ttk.Button(
            bottom, text="Print Label", command=self.print_current_label
        )
        self.print_button.pack(side="left")

        self.root.bind("<Configure>", self._on_window_resize)

    def _connect_live_preview(self):
        self.title_var.trace_add("write", self._schedule_preview)
        self.date_var.trace_add("write", self._schedule_preview)
        self.run_id_var.trace_add("write", self._schedule_preview)
        self.pid_var.trace_add("write", self._schedule_preview)
        self.board_type_var.trace_add("write", self._schedule_preview)
        self.extra_info_text.bind("<KeyRelease>", self._schedule_preview)
        self.extra_info_text.bind("<FocusOut>", self._schedule_preview)

    def _schedule_preview(self, *_):
        if self.preview_after_id is not None:
            try:
                self.root.after_cancel(self.preview_after_id)
            except tk.TclError:
                pass
        self.preview_after_id = self.root.after(250, self.update_preview)

    def _on_window_resize(self, event):
        if event.widget is self.root:
            self._schedule_preview()

    def _extra_info(self):
        return self.extra_info_text.get("1.0", "end-1c").strip()

    def update_preview(self):
        self.preview_after_id = None
        try:
            image = render_label(
                title=self.title_var.get(),
                date=self.date_var.get(),
                run_id=self.run_id_var.get(),
                pid=self.pid_var.get(),
                board_type=self.board_type_var.get(),
                extra_info=self._extra_info(),
                include_logo=self.include_logo_var.get(),
            )

            available_width = max(360, self.preview_frame.winfo_width() - 50)
            available_height = max(220, self.preview_frame.winfo_height() - 45)
            scale = min(
                available_width / image.width,
                available_height / image.height,
                1.0,
            )
            preview_size = (
                max(1, int(image.width * scale)),
                max(1, int(image.height * scale)),
            )
            preview_image = image.resize(
                preview_size, Image.Resampling.LANCZOS
            )
            self.preview_photo = ImageTk.PhotoImage(preview_image)
            self.preview_label.configure(image=self.preview_photo, text="")
        except Exception as error:
            self.preview_label.configure(
                image="", text=f"Preview error:\n{error}"
            )
            self.preview_photo = None

    def _refresh_preview_now(self):
        """Cancel a pending preview and refresh immediately."""
        if self.preview_after_id is not None:
            try:
                self.root.after_cancel(self.preview_after_id)
            except tk.TclError:
                pass
            self.preview_after_id = None
        self.update_preview()

    def set_current_date(self):
        """Restore today's date without changing the other fields."""
        self.date_var.set(system_date.today().strftime("%Y-%m-%d"))
        self.date_entry.icursor("end")
        self.date_entry.focus_set()
        self._schedule_preview()

    def clear_form(self):
        """Clear all text fields, including the date, and preserve the logo setting."""
        self.title_var.set("")
        self.date_var.set("")
        self.run_id_var.set("")
        self.pid_var.set("")
        self.board_type_var.set("")
        self.extra_info_text.delete("1.0", "end")
        self.title_entry.focus_set()
        self._refresh_preview_now()

    def reset_default_form(self):
        """Reset the form for a new label with standard defaults enabled."""
        self.title_var.set(DEFAULT_TITLE)
        self.date_var.set(system_date.today().strftime("%Y-%m-%d"))
        self.run_id_var.set("")
        self.pid_var.set("")
        self.board_type_var.set("")
        self.extra_info_text.delete("1.0", "end")
        self.include_logo_var.set(True)
        self.title_entry.focus_set()
        self._refresh_preview_now()

    def restore_default_title(self):
        """Restore the standard title with one click."""
        self.title_var.set(DEFAULT_TITLE)
        self.title_entry.icursor("end")
        self.title_entry.focus_set()
        self._schedule_preview()

    def read_rfid(self):
        if get_pid is None:
            messagebox.showerror(
                "RFID reader unavailable",
                "The RFID interface could not be imported. Check that "
                "rfid_interface.py and the existing RFID package are available.",
                parent=self.root,
            )
            return

        self.read_rfid_button.configure(state="disabled", text="Reading...")
        self.root.update_idletasks()
        try:
            pid = get_pid()
            if not pid:
                messagebox.showwarning(
                    "No PID received",
                    "The RFID reader did not return a PID. You can enter it manually.",
                    parent=self.root,
                )
                return
            self.pid_var.set(str(pid).strip())
        except Exception as error:
            messagebox.showerror(
                "RFID read failed",
                f"Could not read a PID from the RFID tag.\n\n{error}\n\n"
                "You can enter the PID manually instead.",
                parent=self.root,
            )
        finally:
            self.read_rfid_button.configure(
                state="normal", text="Read RFID Tag"
            )

    def print_current_label(self):
        title = self.title_var.get().strip()
        date = self.date_var.get().strip()
        run_id = self.run_id_var.get().strip()
        pid = self.pid_var.get().strip()
        board_type = self.board_type_var.get().strip()
        extra_info = self._extra_info()
        include_logo = self.include_logo_var.get()

        if pid and board_type not in {"A", "B"}:
            messagebox.showwarning(
                "Board type required",
                "Select board type A or B before printing a label with a PID.",
                parent=self.root,
            )
            self.board_type_combo.focus_set()
            return

        if not any((title, run_id, pid, extra_info)):
            messagebox.showwarning(
                "Empty label",
                "Enter a title or at least one field before printing.",
                parent=self.root,
            )
            return

        self.print_button.configure(state="disabled", text="Printing...")
        self.root.update_idletasks()
        try:
            print_label(
                title=title,
                date=date,
                run_id=run_id,
                pid=pid,
                board_type=board_type,
                extra_info=extra_info,
                include_logo=include_logo,
            )
            messagebox.showinfo(
                "Label sent to printer",
                "The label was sent to the Brother QL-1100.",
                parent=self.root,
            )
        except Exception as error:
            messagebox.showerror(
                "Printing failed",
                str(error),
                parent=self.root,
            )
        finally:
            self.print_button.configure(
                state="normal", text="Print Label"
            )


def main():
    root = tk.Tk()
    LabelPrinterGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
