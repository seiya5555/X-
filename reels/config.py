"""
リールシステム - 共通設定

必要な環境変数（.env に記載）:
  ANTHROPIC_API_KEY    Claude API キー
  OBSIDIAN_VAULT_PATH  Obsidian Vault のフォルダパス
"""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

MODEL = "claude-opus-5"
# 思考トークンと応答テキストの合計上限。台本1本ぶんの余裕を持たせる。
MAX_TOKENS = 16000

PACKAGE_DIR = Path(__file__).resolve().parent
DATA_DIR = PACKAGE_DIR / "data"
COMPETITORS_FILE = DATA_DIR / "competitors.json"
PATTERNS_FILE = DATA_DIR / "patterns.json"
PERFORMANCE_FILE = DATA_DIR / "performance.json"

# Vault 内に台本ノートを書き出すフォルダ名
VAULT_SCRIPTS_DIR = "リール台本"

# Vault 探索時に無視するフォルダ
SKIP_DIRS = {".obsidian", ".trash", ".git", ".claude", "node_modules", "__pycache__"}


def get_vault_path() -> Path | None:
    """Vault のパスを返す。未設定なら None（Vault なしでも動作させるため）。"""
    raw = os.environ.get("OBSIDIAN_VAULT_PATH", "").strip()
    if not raw:
        return None

    path = Path(raw).expanduser()
    if not path.is_dir():
        raise RuntimeError(
            f"エラー: OBSIDIAN_VAULT_PATH のフォルダが見つかりません: {path}\n"
            ".env の OBSIDIAN_VAULT_PATH を確認してください。"
        )
    return path


def ensure_data_dir() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
