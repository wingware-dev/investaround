"""``python -m investaround``: start the local web app and open a browser."""

from __future__ import annotations

import argparse
import threading
import webbrowser

from .app import create_app


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(prog="investaround", description="Paper-investing practice app")
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--source", choices=["yahoo", "fake"], help="price source (default from INVESTAROUND_PRICE_SOURCE)")
    ap.add_argument("--data-dir", help="where portfolios and the price cache live (default ./data)")
    ap.add_argument("--no-browser", action="store_true", help="don't open a browser window")
    ap.add_argument("--debug", action="store_true")
    args = ap.parse_args(argv)

    config = {}
    if args.source:
        config["PRICE_SOURCE"] = args.source
    if args.data_dir:
        config["DATA_DIR"] = args.data_dir
    app = create_app(config)

    url = f"http://{args.host}:{args.port}/"
    print(f"investaround running at {url}  (Ctrl-C to stop)")
    if not args.no_browser:
        threading.Timer(1.0, webbrowser.open, args=(url,)).start()
    app.run(host=args.host, port=args.port, debug=args.debug, use_reloader=False)


if __name__ == "__main__":
    main()
