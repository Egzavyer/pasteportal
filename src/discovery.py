from contextlib import ExitStack, contextmanager

from zeroconf import IPVersion, ServiceInfo, Zeroconf


@contextmanager
def advertise_service(
    ip: str,
    port: int,
    hostname: str,
):
    info = ServiceInfo(
        type_="_http._tcp.local.",
        name="PastePortal._http._tcp.local.",
        server=hostname,
        parsed_addresses=[ip],
        port=port,
        properties={"path": "/clipboard"},
    )

    with ExitStack() as cleanup:
        zc = Zeroconf(
            interfaces=[ip],
            ip_version=IPVersion.V4Only,
        )
        cleanup.callback(zc.close)

        zc.register_service(info)
        cleanup.callback(zc.unregister_service, info)

        yield info
