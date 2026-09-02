"""Desktop client, tkinter. Runs on a Mac, Windows or Linux desktop.

    python3 -m agentic_network.gui
    python3 -m agentic_network.gui --config config/config_agency.xml

Not usable in Colab or any headless environment, which have no display. The
notebook and the Colab link use agentic_network.cli instead.
"""

from __future__ import annotations

import argparse
import queue
import re
import sys
import threading
import tkinter as tk
from tkinter import ttk, scrolledtext

from .channels import QueueChannel
from .cli import DEFAULT_CONFIG, load_env
from .config import load_config
from .graph import build_network

THEME = {
    "font_family": "Helvetica",
    "font_size_chat": 13,
    "font_size_log": 11,
    "bg": "#F4F6F9",
    "chat_bg": "#FFFFFF",
    "text": "#2C3E50",
    "ai_label": "#E74C3C",
    "you_label": "#2980B9",
    "log_bg": "#1E1E1E",
    "log_fg": "#4CAF50",
    "status": "#F1C40F",
    "send": "#27AE60",
    "approve": "#F39C12",
}


class AgentClientApp:
    def __init__(self, root: tk.Tk, network):
        self.root = root
        self.network = network
        self.channel: QueueChannel = network.channel
        self.awaiting_approval = False

        root.title("Agentic Network")
        root.geometry("900x700")

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TNotebook", background=THEME["bg"])
        style.configure("TFrame", background=THEME["bg"])

        self.notebook = ttk.Notebook(root)
        self.notebook.pack(expand=True, fill="both")
        self.chat_frame = ttk.Frame(self.notebook)
        self.log_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.chat_frame, text="   How can I help?   ")
        self.notebook.add(self.log_frame, text="   Agent Trace Log   ")

        self._build_chat_tab()
        self._build_log_tab()
        self._poll()

    def _build_chat_tab(self) -> None:
        self.status_var = tk.StringVar(value="Ready")
        tk.Label(
            self.chat_frame, textvariable=self.status_var, fg=THEME["you_label"],
            bg=THEME["bg"], anchor="w", font=(THEME["font_family"], 10, "bold"),
        ).pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)

        self.chat = scrolledtext.ScrolledText(
            self.chat_frame, wrap=tk.WORD, state="disabled",
            font=(THEME["font_family"], THEME["font_size_chat"]),
            bg=THEME["chat_bg"], fg=THEME["text"], padx=15, pady=15,
        )
        self.chat.pack(expand=True, fill="both", padx=10, pady=(0, 10))
        f = THEME["font_family"], THEME["font_size_chat"]
        self.chat.tag_config("normal", font=f)
        self.chat.tag_config("bold", font=(*f, "bold"))
        self.chat.tag_config("ai_label", foreground=THEME["ai_label"], font=(*f, "bold"))
        self.chat.tag_config("you_label", foreground=THEME["you_label"], font=(*f, "bold"))

        bar = tk.Frame(self.chat_frame, bg=THEME["bg"])
        bar.pack(fill=tk.X, padx=10, pady=(0, 10))
        self.entry = tk.Entry(
            bar, font=(THEME["font_family"], THEME["font_size_chat"]),
            relief=tk.FLAT, highlightbackground="#CCCCCC", highlightthickness=1,
        )
        self.entry.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 10), ipady=5)
        self.entry.bind("<Return>", lambda _e: self.send())
        self.send_btn = tk.Button(
            bar, text="Send", command=self.send, width=12, bg=THEME["send"], fg="black",
            font=(THEME["font_family"], 11, "bold"), relief=tk.FLAT, cursor="hand2",
        )
        self.send_btn.pack(side=tk.RIGHT, ipady=3)

    def _build_log_tab(self) -> None:
        self.log = scrolledtext.ScrolledText(
            self.log_frame, wrap=tk.WORD, state="disabled",
            font=("Courier", THEME["font_size_log"]),
            bg=THEME["log_bg"], fg=THEME["log_fg"], padx=10, pady=10,
        )
        self.log.pack(expand=True, fill="both", padx=10, pady=10)

    def _append_log(self, text: str, colour: str | None = None) -> None:
        self.log.config(state="normal")
        if colour:
            self.log.tag_config(colour, foreground=colour)
            self.log.insert(tk.END, text + "\n", colour)
        else:
            self.log.insert(tk.END, text + "\n")
        self.log.yview(tk.END)
        self.log.config(state="disabled")

    def _insert_markdown(self, text: str) -> None:
        """Render **bold** spans; everything else goes in as-is."""
        self.chat.config(state="normal")
        for part in re.split(r"(\*\*.*?\*\*)", text, flags=re.DOTALL):
            if part.startswith("**") and part.endswith("**"):
                self.chat.insert(tk.END, part[2:-2], "bold")
            else:
                self.chat.insert(tk.END, part, "normal")
        self.chat.insert(tk.END, "\n")
        self.chat.yview(tk.END)
        self.chat.config(state="disabled")

    def _poll(self) -> None:
        try:
            while True:
                item = self.channel.queue.get_nowait()
                kind, msg = item["type"], item["msg"]
                if kind == "status":
                    self.status_var.set(msg)
                    self._append_log(f"[STATUS] {msg}", THEME["status"])
                elif kind == "log":
                    self._append_log(f"[TRACE] {msg}", THEME["log_fg"])
                elif kind == "chat":
                    self.chat.config(state="normal")
                    self.chat.insert(tk.END, "\nAI:\n", "ai_label")
                    self.chat.config(state="disabled")
                    self._insert_markdown(msg)
                elif kind == "system" and msg == "requires_input":
                    self.awaiting_approval = True
                    self.send_btn.config(text="Approve (Y/N)", bg=THEME["approve"])
        except queue.Empty:
            pass
        finally:
            self.root.after(100, self._poll)

    def send(self) -> None:
        text = self.entry.get().strip()
        if not text:
            return
        self.entry.delete(0, tk.END)
        self.chat.config(state="normal")
        self.chat.insert(tk.END, "\nYou: ", "you_label")
        self.chat.insert(tk.END, text + "\n", "normal")
        self.chat.yview(tk.END)
        self.chat.config(state="disabled")

        if self.awaiting_approval:
            self.awaiting_approval = False
            self.send_btn.config(text="Send", bg=THEME["send"])
            self.status_var.set("Processing your decision ...")
            self.channel.submit_approval(text)
        else:
            self.status_var.set("Analysing ...")
            self._append_log(f"\n--- NEW REQUEST: {text} ---", "#FFFFFF")
            threading.Thread(target=self.network.run, args=(text,), daemon=True).start()


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Desktop client for the agent network.")
    p.add_argument("-c", "--config", default=DEFAULT_CONFIG)
    args = p.parse_args(argv)

    load_env()
    try:
        network = build_network(load_config(args.config), channel=QueueChannel())
    except (FileNotFoundError, ValueError, RuntimeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    try:
        root = tk.Tk()
    except tk.TclError as exc:
        print(
            f"error: no display available ({exc}).\n"
            "The GUI needs a desktop. In a notebook or Colab use agentic_network.cli.",
            file=sys.stderr,
        )
        return 2

    AgentClientApp(root, network)
    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
