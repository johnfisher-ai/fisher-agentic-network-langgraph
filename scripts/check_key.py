"""Confirm the API key loads and works, without ever printing it."""
import os

try:
    from dotenv import load_dotenv
    load_dotenv()
except ModuleNotFoundError:
    print("python-dotenv not installed — reading shell environment only.")

k = os.environ.get("OPENAI_API_KEY")
if not k:
    raise SystemExit("FAIL: OPENAI_API_KEY not set. Copy .env.example to .env and fill it in.")
if k.startswith("sk-proj-replace-me"):
    raise SystemExit("FAIL: .env still holds the placeholder value.")
print(f"loaded: {k[:11]}...{k[-4:]}  (length {len(k)})")

try:
    from langchain_openai import ChatOpenAI
    r = ChatOpenAI(model="gpt-4o", temperature=0).invoke("Reply with the single word: ok")
    print(f"live call: {r.content.strip()}")
    print("PASS — the new key works.")
except Exception as e:
    raise SystemExit(f"FAIL: key loaded but the API call failed: {type(e).__name__}: {e}")
