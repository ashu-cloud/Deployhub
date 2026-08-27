from __future__ import annotations

import inspect

import httpx


def asgi_transport(app) -> httpx.ASGITransport:
    kwargs = {}
    if "lifespan" in inspect.signature(httpx.ASGITransport.__init__).parameters:
        kwargs["lifespan"] = "off"
    return httpx.ASGITransport(app=app, **kwargs)
