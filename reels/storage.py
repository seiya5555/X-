"""JSON データファイルの読み書き。"""

import json
from pathlib import Path

from . import config


def load(path: Path, default: dict) -> dict:
    if not path.exists():
        return dict(default)
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        print(f"警告: {path.name} を読み込めませんでした。空の状態で続行します。")
        return dict(default)


def save(path: Path, data: dict) -> None:
    config.ensure_data_dir()
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except OSError as e:
        raise RuntimeError(f"エラー: {path.name} の保存に失敗しました。詳細: {e}")
