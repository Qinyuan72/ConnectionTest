import tkinter as tk

from gui import TelemetryGUI


def main() -> None:
    root = tk.Tk()
    TelemetryGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
