import logging
from contextlib import ExitStack, contextmanager
from threading import Event, Thread

from winrt.windows.networking.connectivity import NetworkInformation

from .discovery import advertise_service


@contextmanager
def watch_network(get_ip, port: int, hostname: str):
    stopping = Event()
    changed = Event()
    changed.set()  # Perform the initial registration immediately.

    def on_network_changed(sender):
        # Keep the Windows callback short. The worker does the work.
        changed.set()

    def run():
        current_ip = None

        with ExitStack() as advertisement:
            while not stopping.is_set():
                # Notifications wake immediately. Periodic checks also catch IP changes and retry failed registrations.
                notified = changed.wait(timeout=1.0)
                changed.clear()

                if stopping.is_set():
                    break

                # Briefly allow the network config to settle
                if notified and stopping.wait(0.2):
                    break

                try:
                    new_ip = get_ip()

                    if not notified and new_ip == current_ip:
                        continue

                    # Release sockets and records for the old network.
                    advertisement.close()
                    current_ip = None

                    if new_ip is None:
                        logging.info("Waiting for a network connection")
                        continue

                    advertisement.enter_context(
                        advertise_service(
                            ip=new_ip,
                            port=port,
                            hostname=hostname,
                        )
                    )

                    current_ip = new_ip
                    logging.info(
                        "Advertising %s at %s:%s",
                        hostname,
                        new_ip,
                        port,
                    )

                except Exception:
                    # Leave the worker running so it can retry.
                    current_ip = None
                    logging.exception("Could not refresh network discovery")

    worker = Thread(target=run, name="network-discovery", daemon=True)

    token = NetworkInformation.add_network_status_changed(on_network_changed)

    try:
        worker.start()
        yield
    finally:
        stopping.set()
        changed.set()

        try:
            NetworkInformation.remove_network_status_changed(token)
        finally:
            if worker.ident is not None:
                worker.join()
