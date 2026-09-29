from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import uvicorn
from threading import Thread
import pyperclip
from time import monotonic, sleep


class ClipboardRequest(BaseModel):
    text: str = Field(min_length=1, max_length=65536)


class Server:
    def __init__(self, host: str, port: int = 43127) -> None:
        self.app = FastAPI()

        self.app.post("/clipboard")(self.receive_clipboard)

        config = uvicorn.Config(
            app=self.app,
            host=host,
            port=port,
            loop="asyncio:SelectorEventLoop",
            log_level="info",
            log_config=None,
            timeout_graceful_shutdown=5,
        )

        self._server = uvicorn.Server(config)
        self._worker = Thread(target=self._server.run, daemon=True)

    def receive_clipboard(self, payload: ClipboardRequest):
        try:
            pyperclip.copy(payload.text)
        except pyperclip.PyperclipException as exc:
            raise HTTPException(
                status_code=503,
                detail="Could not access the clipboard. Try again.",
            ) from exc

        return {"ok": True}

    def start(self, timeout: float = 5.0) -> None:
        self._worker.start()
        deadline = monotonic() + timeout

        try:
            while not self._server.started:
                if not self._worker.is_alive():
                    raise RuntimeError(
                        "HTTP server failed to start. Check the Uvicorn logs."
                    )
                if monotonic() >= deadline:
                    raise TimeoutError(
                        f"HTTP server did not start within {timeout} seconds."
                    )

                sleep(0.05)
        except BaseException:
            self._server.should_exit = True
            raise

    def stop(self):
        self._server.should_exit = True

        if self._worker.ident is not None:
            self._worker.join()
