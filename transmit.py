#!/usr/bin/env python3
"""Numbers station. Each run emits one encoded transmission and rebuilds the feed."""
import sys
import hashlib
from datetime import datetime, timezone, timedelta

FEED = "feed.log"
README = "README.md"
KEY = 0x5A
INTRUDER_KEY = 0x37  # a different hand on the dial — won't decode with the station key
WINDOW = 14  # transmissions shown in the README window

INTRUDER_PHRASES = [
    "you are not alone on this band",
    "who is transmitting",
    "we hear you too",
    "leave the frequency",
    "this band is ours",
]

PHRASES = [
    "stay quiet",
    "no names here",
    "after dark only",
    "the tower listens",
    "count the silence",
    "nothing is signed",
    "we watch the chain",
    "burn the ledger",
    "trust the noise",
    "leave before dawn",
    "the signal is clean",
    "they are not looking",
    "hold the frequency",
    "everything decays",
    "you were not here",
]


def encode(phrase: str) -> str:
    raw = [b ^ KEY for b in phrase.encode()]
    hexes = [f"{b:02X}" for b in raw]
    mid = len(hexes) // 2
    return " ".join(hexes[:mid]) + " ██ " + " ".join(hexes[mid:])


def line_for(dt: datetime) -> str:
    seed = dt.strftime("%Y%m%d")
    h = hashlib.sha256(seed.encode()).digest()
    phrase = PHRASES[h[0] % len(PHRASES)]
    callsign = f"{h[1]:02X}{h[2]:02X}"
    ts = dt.strftime("%Y-%m-%dT%H:%MZ")
    return f"{ts}  {callsign} ░ {encode(phrase)}"


def rebuild_readme() -> None:
    try:
        lines = [l.rstrip("\n") for l in open(FEED) if l.strip()]
    except FileNotFoundError:
        lines = []
    recent = lines[-WINDOW:][::-1]  # newest first
    body = "\n".join(recent)
    md = (
        "# ⟁ transmissions\n"
        "freq 4625 kHz · continuous\n\n"
        "```\n"
        f"{body}\n"
        "```\n\n"
        "<sub>updates on its own. don't ask who's sending.</sub>\n\n"
        "<sub>♄</sub>\n"
    )
    open(README, "w").write(md)


def is_intruder(dt: datetime) -> bool:
    # roughly once a week, someone else keys the frequency
    return hashlib.sha256((dt.strftime("%Y%m%d") + "x").encode()).digest()[0] % 7 == 0


def intruder_line(dt: datetime) -> str:
    h = hashlib.sha256((dt.strftime("%Y%m%d") + "intruder").encode()).digest()
    phrase = INTRUDER_PHRASES[h[0] % len(INTRUDER_PHRASES)]
    hexes = " ".join(f"{b ^ INTRUDER_KEY:02X}" for b in phrase.encode())
    return f"{dt.strftime('%Y-%m-%dT%H:%MZ')}  ∎∎∎∎ ∷ {hexes}"


def append(dt: datetime) -> None:
    with open(FEED, "a") as f:
        f.write(line_for(dt) + "\n")
        if is_intruder(dt):
            f.write(intruder_line(dt) + "\n")


def main() -> None:
    now = datetime.now(timezone.utc)
    if len(sys.argv) > 1 and sys.argv[1] == "--intrude":
        with open(FEED, "a") as f:
            f.write(intruder_line(now) + "\n")
        rebuild_readme()
        return
    if len(sys.argv) > 2 and sys.argv[1] == "--backfill":
        n = int(sys.argv[2])
        base = now.replace(hour=3, minute=14, second=0, microsecond=0)
        for d in range(n, 0, -1):
            append(base - timedelta(days=d))
    else:
        append(now)
    rebuild_readme()


if __name__ == "__main__":
    main()
