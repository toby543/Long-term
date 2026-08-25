#!/usr/bin/env python3
"""
Generate a Kite Connect access_token for today.

Zerodha's login step cannot be automated (it requires your own browser
session and 2FA), so this has to be run interactively once per trading day:

    export KITE_API_KEY=your_api_key
    export KITE_API_SECRET=your_api_secret
    python kite_login.py

It prints a login URL — open it, log in, and Zerodha redirects you to your
app's redirect URL with a `request_token` in the query string. Paste that
token back in when prompted, and this exchanges it for an access_token
(valid until ~6am the next day) and prints the export command to run.
"""

import os
import sys


def main():
    api_key = os.environ.get("KITE_API_KEY")
    api_secret = os.environ.get("KITE_API_SECRET")
    if not api_key or not api_secret:
        print("Set KITE_API_KEY and KITE_API_SECRET first (see README.md).", file=sys.stderr)
        return 1

    try:
        from kiteconnect import KiteConnect
    except ImportError:
        print("kiteconnect isn't installed — run: pip install kiteconnect", file=sys.stderr)
        return 1

    kite = KiteConnect(api_key=api_key)
    print("1. Open this URL and log in with your Zerodha credentials:\n")
    print(f"   {kite.login_url()}\n")
    print("2. After login you'll be redirected to your app's redirect URL —")
    print("   copy the `request_token` value from that URL's query string.\n")

    request_token = input("Paste the request_token here: ").strip()
    if not request_token:
        print("No request_token provided.", file=sys.stderr)
        return 1

    session = kite.generate_session(request_token, api_secret=api_secret)
    access_token = session["access_token"]

    print("\nSuccess. Set this for the rest of today's session:\n")
    print(f"   export KITE_ACCESS_TOKEN={access_token}\n")
    print("(Access tokens expire around 6am IST the next day — re-run this then.)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
