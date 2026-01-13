import subprocess
import sys

# Check if tkinter is available before importing UI
try:
    import tkinter as tk

    # Try to create a minimal Tk instance to verify it works
    try:
        test_root = tk.Tk()
        test_root.withdraw()
        test_root.destroy()
    except Exception as e:
        raise ImportError(f"Tkinter found but cannot initialize: {e}")
except ImportError as e:
    error_msg = (
        "ERROR: Tkinter/Tk is not available on this system.\n\n"
        "This application requires Tk to display the GUI.\n\n"
        "To install on Linux:\n"
        "  sudo apt install tk8.6        (Debian/Ubuntu)\n"
        "  sudo dnf install tk            (Fedora)\n"
        "  sudo pacman -S tk              (Arch)\n\n"
        f"Technical details: {e}"
    )

    print(error_msg, file=sys.stderr)

    # Try to show a system dialog if available (Linux)
    try:
        subprocess.run(
            ["zenity", "--error", "--text", error_msg.replace("\n", "\n\n")],
            timeout=0.5,
            capture_output=True,
        )
    except:
        try:
            subprocess.run(
                ["kdialog", "--error", error_msg], timeout=0.5, capture_output=True
            )
        except:
            pass  # No GUI dialog available, console message is sufficient

    sys.exit(1)

from ui.main import ExifTransferApp

if __name__ == "__main__":
    app = ExifTransferApp()
    app.mainloop()  # This is the "Event Loop" that keeps the window open
