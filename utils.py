from typing import Optional


def is_all_nines_api_key(api_key: Optional[str]) -> bool:
    """Return True if the API key (after removing any prefix) is all 9s."""
    if not api_key:
        return False
    key_part = api_key.split('-')[-1] if '-' in api_key else api_key
    return all(c == '9' for c in key_part)
