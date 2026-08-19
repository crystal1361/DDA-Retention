"""
logging_setup.py

A single get_logger() helper every script calls instead of hand-rolling
its own logging.basicConfig().

WHY THIS FILE EXISTS, AND WHY print() STATEMENTS STILL STAY IN EVERY
SCRIPT (this is deliberate, not an oversight):
This project's scripts print a narrated, human-readable walkthrough as
they run ("Step 1: loading data...", "RDD estimate: -10.7pp [-14.8,
-6.6]...") -- that narration is genuinely useful for a demo/interview
context, where a human is watching the terminal and the whole point is
to see the story unfold. Ripping that out in favor of logger.info() would
make the scripts less readable for exactly the audience they're built
for. What print() can't do, and what a production system needs, is:
structured, leveled, timestamped, greppable, persisted-to-disk output --
e.g. "show me every WARNING from the last 30 days of runs" isn't
answerable from stdout scrollback. So this file adds logging ALONGSIDE
the existing print() narration, not instead of it: print() stays for the
human-facing story, logger.info/warning/error calls get added around the
handful of moments that matter for auditing a production run (pipeline
start/end, validation failures, key metrics, exceptions) and write to
both the console and a per-script rotating-by-run log file under
logs/.
"""

import logging
import os

from config import LOG_DIR


def get_logger(name):
    """Return a logger named `name` (pass __name__ from the calling
    script) that writes INFO+ to both the console and
    logs/<name>.log. Calling this more than once with the same name is
    safe -- handlers are only attached the first time, so re-importing a
    module (e.g. in tests) won't duplicate every log line."""
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger  # already configured -- avoid duplicate handlers

    logger.setLevel(logging.INFO)
    fmt = logging.Formatter(
        "%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(fmt)
    console_handler.setLevel(logging.WARNING)  # console stays quiet; print() carries the narration
    logger.addHandler(console_handler)

    log_path = os.path.join(LOG_DIR, f"{name}.log")
    file_handler = logging.FileHandler(log_path, mode="a", encoding="utf-8")
    file_handler.setFormatter(fmt)
    file_handler.setLevel(logging.INFO)
    logger.addHandler(file_handler)

    logger.propagate = False
    return logger
