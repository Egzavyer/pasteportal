import pystray
from PIL import Image
import socket
from contextlib import ExitStack
from pathlib import Path
import logging

from src.server import Server
from src.network import watch_network

PORT = 43127
HOSTNAME = "pasteportal-a7f2.local."


def get_local_ip() -> str | None:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.connect(("8.8.8.8", 1))
            ip = sock.getsockname()[0]

        if ip == "0.0.0.0" or ip.startswith("127."):
            return None

        return ip
    except OSError:
        return None


def main():

    def on_quit(icon, item):
        icon.stop()

    icon_path = Path(__file__).resolve().parent / "paperclip.ico"
    image = Image.open(icon_path)

    menu = pystray.Menu(pystray.MenuItem("Quit", on_quit))
    icon = pystray.Icon("PaperclipIcon", image, "PastePortal", menu)

    with ExitStack() as cleanup:
        server = Server(host="0.0.0.0", port=PORT)
        cleanup.callback(server.stop)
        server.start()

        logging.info("HTTP server listening on port %s", PORT)

        cleanup.enter_context(
            watch_network(
                get_ip=get_local_ip,
                port=PORT,
                hostname=HOSTNAME,
            )
        )

        icon.run()


if __name__ == "__main__":
    logging.basicConfig(
        filename=Path(__file__).resolve().parent / "pasteportal.log",
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        encoding="utf-8",
    )

    try:
        main()
    except Exception:
        logging.exception("PastePortal failed")
