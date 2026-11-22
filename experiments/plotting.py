"""Tiny helper: every script SAVES its charts as PNG files.
Add --show to also open each chart in a window (like plt.show() in the notebook):
    python experiments/run_regression.py --show
"""
import sys

import matplotlib

SHOW = "--show" in sys.argv
if not SHOW:
    matplotlib.use("Agg")          # no window, just files
import matplotlib.pyplot as plt    # noqa: E402  (must come after the backend choice)


def save_figure(path, dpi=150):
    plt.tight_layout()
    plt.savefig(path, dpi=dpi)
    print("  chart saved:", getattr(path, "name", path))
    if SHOW:
        plt.show()
    plt.close()