from __future__ import annotations

import tkinter as tk

from kal_rotor_api import KALRotorRig
from kal_rotor_gui import KALRotorTestGUI


def main() -> None:
    root = tk.Tk()
    rig = KALRotorRig()
    KALRotorTestGUI(root, rig)
    root.mainloop()


if __name__ == "__main__":
    main()
