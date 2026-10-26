#!/usr/bin/env python3
"""
Example: run the full lookup suite against one TikTok username and choose
which parts of the result to print.

The default lookup (creation date + basic profile) always runs. The two extra
views are opt-in:

    SHOW_PIVOTS  OSINT pivot links  (bio links, cross-platform handles,
                 reverse-image / Wayback finders) — makes network calls.
    SHOW_FLAGS   integrity heuristics (bought-followers / takeover / rebrand
                 signals) — no extra network calls, inferred from data on hand.

Pick what you want in the config block below, then run:

    python example_full_lookup.py

Or override per-run from the command line (these win over the config block):

    python example_full_lookup.py charlidamelio            # default only
    python example_full_lookup.py charlidamelio --flags    # + integrity flags
    python example_full_lookup.py charlidamelio --pivots    # + OSINT pivots
    python example_full_lookup.py charlidamelio --all       # both

Keyless and free, like the rest of TokIntel — no API key, signup, or login.
"""

import argparse

from tiktok_created import (
    new_session,
    lookup,
    integrity_flags,
    resolve_pivots,
    human_age,
)

# ---------------------------------------------------------------------------
# Config — edit these, or override them with the command-line flags above.
# ---------------------------------------------------------------------------
USERNAME = "tiktok"      # the account to look up (handle, @handle, or URL also work)
SHOW_PIVOTS = False      # print OSINT pivot links
SHOW_FLAGS = False       # print integrity flags
# ---------------------------------------------------------------------------


def print_default(data):
    """The always-on view: creation date and headline profile numbers."""
    print("── Account ───────────────────────────────────────────")
    if "error" in data:
        print(f"  ⚠️  {data['error']}")
        return
    if data.get("type") == "limited":
        # A real account TikTok won't return full details for (e.g. gated).
        print(f"  🔵 @{data.get('username')} is a real account, but TikTok "
              "returned only limited details.")
        return
    if data.get("type") != "account":
        # This example is written for usernames; a video/ID target lands here.
        print(f"  {data}")
        return

    print(f"  username:  @{data.get('username')}")
    if data.get("nickname"):
        print(f"  name:      {data['nickname']}")
    if data.get("account_created"):
        age = human_age(data.get("account_created_unix"))
        age_str = f"  ({age})" if age else ""
        print(f"  created:   {data['account_created']}{age_str}")
    elif data.get("created_estimate_from_id"):
        print(f"  created:   no exact date from TikTok; "
              f"estimate from user ID: {data['created_estimate_from_id']}")
    else:
        print("  created:   not available")
    for label, key in (("followers", "followers"),
                        ("following", "following"),
                        ("videos", "videos")):
        val = data.get(key)
        if isinstance(val, int):
            print(f"  {label + ':':11}{val:,}")
    if data.get("bio"):
        print(f"  bio:       {data['bio']}")
    if data.get("bio_link"):
        print(f"  bio link:  {data['bio_link']}")


def print_flags(data):
    """Integrity heuristics. No extra network calls; inference, not proof."""
    print("\n── Integrity flags ───────────────────────────────────")
    if data.get("type") != "account":
        print("  (only available for a resolved account)")
        return
    icon = {"warn": "🚩", "info": "ℹ️ ", "ok": "✅"}
    for severity, message in integrity_flags(data):
        print(f"  {icon.get(severity, '•')} {message}")


def print_pivots(data, session):
    """OSINT pivots. Makes network calls to check cross-platform handles etc."""
    print("\n── OSINT pivots ──────────────────────────────────────")
    if data.get("type") != "account":
        print("  (only available for a resolved account)")
        return
    finders, shared, web = resolve_pivots(data, session=session)

    def dump(title, rows):
        if not rows:
            return
        print(f"  {title}:")
        for row in rows:
            # `web` rows are (label, url, note); the others are (label, url).
            label, url = row[0], row[1]
            note = f"  — {row[2]}" if len(row) > 2 and row[2] else ""
            print(f"    • {label}: {url}{note}")

    dump("Confirmed theirs", shared)
    dump("Same handle elsewhere (verify)", web)
    dump("Tools to confirm yourself", finders)
    if not (finders or shared or web):
        print("  no pivots available for this result")


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("username", nargs="?", default=USERNAME,
                   help="account to look up (defaults to the USERNAME in the file)")
    p.add_argument("--pivots", action="store_true", help="also show OSINT pivot links")
    p.add_argument("--flags", action="store_true", help="also show integrity flags")
    p.add_argument("--all", action="store_true", help="show both pivots and flags")
    args = p.parse_args()

    # A command-line flag turns a view ON; with no flags at all we fall back to
    # the SHOW_* config above, so editing the file and running bare both work.
    show_pivots = args.pivots or args.all
    show_flags = args.flags or args.all
    if not (args.pivots or args.flags or args.all):
        show_pivots, show_flags = SHOW_PIVOTS, SHOW_FLAGS

    session = new_session()
    print(f"\nLooking up @{args.username.lstrip('@')} …\n")
    _, data = lookup(args.username, session)

    print_default(data)
    if show_flags:
        print_flags(data)
    if show_pivots:
        print_pivots(data, session)
    print()


if __name__ == "__main__":
    main()
