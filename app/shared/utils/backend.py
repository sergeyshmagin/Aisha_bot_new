def get_backend_headers(api_key: str) -> dict:
    """Формирует headers для Backend API"""
    if api_key:
        return {"X-API-Key": api_key}
    return {} 