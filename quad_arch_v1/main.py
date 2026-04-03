from __future__ import annotations

import tkinter as tk

if __package__ in {None, ""}:
    import sys
    from pathlib import Path

    package_root = Path(__file__).resolve().parent.parent
    if str(package_root) not in sys.path:
        sys.path.insert(0, str(package_root))

    from quad_arch_v1.app_runtime import AppRuntime
    from quad_arch_v1.gui import QuadArchGUI
else:
    from .app_runtime import AppRuntime
    from .gui import QuadArchGUI


def main() -> None:
    runtime = AppRuntime()
    root = tk.Tk()
    QuadArchGUI(root, runtime)
    root.mainloop()


if __name__ == "__main__":
    main()
