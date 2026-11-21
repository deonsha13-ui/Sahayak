import inspect


def ws_connect(uri: str, headers: dict | None = None, **kwargs):
    """Universal websockets connector that supports websockets.asyncio (v13+) and legacy (v10-12)."""
    try:
        from websockets.asyncio.client import connect as asyncio_connect
        sig = inspect.signature(asyncio_connect)
        if "additional_headers" in sig.parameters:
            return asyncio_connect(uri, additional_headers=headers, **kwargs)
        if "extra_headers" in sig.parameters:
            return asyncio_connect(uri, extra_headers=headers, **kwargs)
    except (ImportError, AttributeError):
        pass

    import websockets
    sig = inspect.signature(websockets.connect)
    if "additional_headers" in sig.parameters:
        return websockets.connect(uri, additional_headers=headers, **kwargs)
    if "extra_headers" in sig.parameters:
        return websockets.connect(uri, extra_headers=headers, **kwargs)
    return websockets.connect(uri, **kwargs)
