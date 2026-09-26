"""
Gunicorn config — currently exists for exactly one reason: wiring
prometheus_client's multiprocess mode (see app/observability.py's
module docstring for why this isn't optional with multiple workers).

PROMETHEUS_MULTIPROC_DIR must be set in the environment before the
app is imported (prometheus_client reads it at import time), and
child_exit must clean up each worker's metric files when gunicorn
recycles it — both handled here rather than left for whoever deploys
this to discover by reading prometheus_client's docs themselves.
"""

import os
import shutil

bind = "0.0.0.0:5000"
worker_class = "gevent"
workers = 4

_multiproc_dir = os.environ.setdefault("PROMETHEUS_MULTIPROC_DIR", "/tmp/prometheus-multiproc")


def on_starting(server):
    # Fresh directory on boot — stale files from a previous run (e.g.
    # a container restart that reused the same /tmp) would otherwise
    # get counted as if the current process had produced them.
    shutil.rmtree(_multiproc_dir, ignore_errors=True)
    os.makedirs(_multiproc_dir, exist_ok=True)


def child_exit(server, worker):
    from prometheus_client import multiprocess

    multiprocess.mark_process_dead(worker.pid)
