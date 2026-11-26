"""Shared rolling request budgets, persisted without keys or document content."""
import math
import sqlite3
import time
from contextlib import closing

from .errors import VendorWiseError


class UsageBudget:
    def __init__(self, settings):
        self.path = settings.data_dir / "usage.sqlite3"
        self.per_minute = settings.ai_requests_per_minute
        self.per_day = settings.ai_requests_per_day
        if min(self.per_minute, self.per_day) < 1:
            raise ValueError("AI request budgets must be positive.")

    def reserve(self):
        """Charge before each outbound request, including failures and retries.

        BEGIN IMMEDIATE makes check-and-insert atomic across threads/processes.
        A restart with the same data directory cannot reset the budget.
        """
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with closing(sqlite3.connect(self.path, timeout=5)) as db, db:
            db.execute("CREATE TABLE IF NOT EXISTS requests (at REAL NOT NULL)")
            db.execute("CREATE INDEX IF NOT EXISTS requests_at ON requests(at)")
            db.execute("BEGIN IMMEDIATE")
            now = time.time()
            db.execute("DELETE FROM requests WHERE at <= ?", (now - 86400,))
            for seconds, limit, label in ((60, self.per_minute, "minute"),
                                           (86400, self.per_day, "24-hour")):
                count, first = db.execute(
                    "SELECT COUNT(*), MIN(at) FROM requests WHERE at > ?", (now - seconds,)
                ).fetchone()
                if count >= limit:
                    retry = max(1, math.ceil(first + seconds - now))
                    raise VendorWiseError(
                        f"The shared AI {label} request limit has been reached. "
                        f"Try again in {retry} seconds. Comparison, what-if and reports remain available.",
                        429, retry_after=retry)
            db.execute("INSERT INTO requests(at) VALUES (?)", (now,))
