from __future__ import annotations


def resolve_return_to(return_to: str, default_url: str) -> str:
    if return_to.startswith("/") and not return_to.startswith("//"):
        return return_to
    return default_url
