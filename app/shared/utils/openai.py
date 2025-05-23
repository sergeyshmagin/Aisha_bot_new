def get_openai_headers(api_key: str) -> dict:
    """Формирует headers для OpenAI API"""
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    } 