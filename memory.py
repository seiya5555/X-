import json
import os
from datetime import date

MEMORY_FILE = "memory.json"


def save_preview(preview_contents: list[str]) -> None:
    data = {
        "saved_date": str(date.today()),
        "yesterday_preview": preview_contents,
    }
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_preview() -> str:
    if not os.path.exists(MEMORY_FILE):
        return ""
    try:
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, IOError):
        return ""

    previews = data.get("yesterday_preview", [])
    if not previews:
        return ""
    return "\n".join(previews)
