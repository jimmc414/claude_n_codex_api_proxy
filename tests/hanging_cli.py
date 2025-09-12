#!/usr/bin/env python3
import os
import time

pid_file = os.environ.get("PID_FILE")
if pid_file:
    with open(pid_file, "w") as f:
        f.write(str(os.getpid()))
        f.flush()

# Sleep long enough to trigger timeouts in callers
while True:
    time.sleep(1)
