from typing import Dict


def build_storage_options(token: str) -> Dict:
    """
    Build fsspec-compatible storage options with Authorization header, to be used with
    datasets' DownloadConfig.storage_options. This works for non-HF endpoints as well.
    """
    if not token:
        return {}
    return {"headers": {"Authorization": f"Bearer {token}"}}


def mask_token(token: str, keep: int = 4) -> str:
    if not token:
        return ""
    if len(token) <= keep:
        return "*" * len(token)
    return "*" * (len(token) - keep) + token[-keep:]


