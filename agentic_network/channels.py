"""Where the network's output goes, and where human answers come from.

The graph itself never prints and never calls input(). It talks to a Channel.
That is what lets the same graph drive a terminal session, a desktop window or a
notebook cell without the nodes knowing which.
"""

from __future__ import annotations

import queue
import threading


class Channel:
    """Interface between the running graph and whoever is watching it."""

    def status(self, message: str) -> None:
        """One-line progress, meant to be overwritten by the next one."""

    def log(self, message: str) -> None:
        """Detail for the trace log."""

    def chat(self, message: str) -> None:
        """A message addressed to the user."""

    def ask_approval(self, proposal: str) -> bool:
        """Block until a human approves or rejects. Return True to proceed."""
        raise NotImplementedError


class SilentChannel(Channel):
    """Discards everything and auto-rejects. Useful in tests."""

    def ask_approval(self, proposal: str) -> bool:
        return False


class ConsoleChannel(Channel):
    """Terminal and notebook output.

    `verbose` turns on the per-agent trace. `auto_approve` answers the
    human-in-the-loop gate without prompting, which is what lets a notebook run
    top to bottom unattended; leave it None to actually ask.
    """

    def __init__(self, verbose: bool = False, auto_approve: bool | None = None):
        self.verbose = verbose
        self.auto_approve = auto_approve

    def status(self, message: str) -> None:
        if self.verbose:
            print(f"[status] {message}")

    def log(self, message: str) -> None:
        if self.verbose:
            print(f"[trace]  {message}")

    def chat(self, message: str) -> None:
        print(message)

    def ask_approval(self, proposal: str) -> bool:
        print("\n" + "=" * 62)
        print("HUMAN APPROVAL REQUIRED")
        print("=" * 62)
        print(proposal)
        print("=" * 62)
        if self.auto_approve is not None:
            verdict = "approved" if self.auto_approve else "rejected"
            print(f"(auto_approve={self.auto_approve}: {verdict} without prompting)")
            return self.auto_approve
        return input(">> Authorize this change? (yes/no): ").strip().lower().startswith("y")


class QueueChannel(Channel):
    """Feeds a GUI running the graph on a worker thread.

    Messages go onto a queue the UI polls. `ask_approval` blocks the worker on an
    Event until the UI calls `submit_approval` from the main thread.
    """

    def __init__(self):
        self.queue: queue.Queue[dict] = queue.Queue()
        self._answered = threading.Event()
        self._answer = False

    def _put(self, kind: str, message: str) -> None:
        self.queue.put({"type": kind, "msg": message})

    def status(self, message: str) -> None:
        self._put("status", message)

    def log(self, message: str) -> None:
        self._put("log", message)

    def chat(self, message: str) -> None:
        self._put("chat", message)

    def ask_approval(self, proposal: str) -> bool:
        self._put("chat", f"**APPROVAL REQUIRED**\n\n{proposal}\n\n**Authorize? (yes/no)**")
        self._put("system", "requires_input")
        self._answered.clear()
        self._answered.wait()
        return self._answer

    def submit_approval(self, text: str) -> None:
        """Called from the UI thread with the human's answer."""
        self._answer = text.strip().lower().startswith("y")
        self._answered.set()
