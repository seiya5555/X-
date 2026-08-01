"""
Obsidian Vault 連携

Vault はただの Markdown フォルダなので、MCP を使わず直接読み書きする。
台本生成時に「関連する過去ノート」を検索してコンテキストとして渡し、
生成した台本は Vault にノートとして書き戻す。
"""

import re
from datetime import date
from pathlib import Path

from . import config

# 1ノートあたりの引用上限（コンテキストが膨らみすぎるのを防ぐ）
MAX_CHARS_PER_NOTE = 1500


def _iter_notes(vault: Path):
    for path in vault.rglob("*.md"):
        if any(part in config.SKIP_DIRS for part in path.parts):
            continue
        yield path


def _read(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None


def _score(path: Path, text: str, keywords: list[str]) -> int:
    """ファイル名と本文のキーワード一致でノートの関連度を採点する。"""
    score = 0
    name = path.stem.lower()
    body = text.lower()

    for keyword in keywords:
        kw = keyword.lower().strip()
        if not kw:
            continue
        # ファイル名の一致は本文より強いシグナルとして扱う
        if kw in name:
            score += 10
        score += min(body.count(kw), 5)

    return score


def search_notes(keywords: list[str], max_notes: int = 12) -> list[tuple[Path, str]]:
    """キーワードに関連するノートを関連度順に返す。

    一致するノートが無い場合は、最近更新されたノートを返す。
    """
    vault = config.get_vault_path()
    if vault is None:
        return []

    scored: list[tuple[int, float, Path, str]] = []
    fallback: list[tuple[float, Path, str]] = []

    for path in _iter_notes(vault):
        text = _read(path)
        if text is None or not text.strip():
            continue

        mtime = path.stat().st_mtime
        fallback.append((mtime, path, text))

        score = _score(path, text, keywords)
        if score > 0:
            scored.append((score, mtime, path, text))

    if scored:
        # 関連度が同じなら新しいノートを優先する
        scored.sort(key=lambda item: (-item[0], -item[1]))
        return [(path, text) for _, _, path, text in scored[:max_notes]]

    fallback.sort(key=lambda item: -item[0])
    return [(path, text) for _, path, text in fallback[:max_notes]]


def build_context(keywords: list[str], max_notes: int = 12) -> str:
    """検索結果を、プロンプトに渡せる1つのテキストにまとめる。"""
    vault = config.get_vault_path()
    if vault is None:
        return ""

    notes = search_notes(keywords, max_notes=max_notes)
    if not notes:
        return ""

    blocks = []
    for path, text in notes:
        rel = path.relative_to(vault)
        body = text.strip()
        if len(body) > MAX_CHARS_PER_NOTE:
            body = body[:MAX_CHARS_PER_NOTE] + "\n（以下省略）"
        blocks.append(f"### ノート: {rel}\n{body}")

    return "\n\n".join(blocks)


def _safe_filename(title: str) -> str:
    """ファイル名に使えない文字を除去する。"""
    cleaned = re.sub(r'[\\/:*?"<>|]', "", title).strip()
    cleaned = re.sub(r"\s+", "_", cleaned)
    return cleaned[:80] or "無題"


def save_note(title: str, body: str, subdir: str = config.VAULT_SCRIPTS_DIR) -> Path | None:
    """Vault にノートを書き出す。Vault 未設定なら None を返す。"""
    vault = config.get_vault_path()
    if vault is None:
        return None

    target_dir = vault / subdir
    try:
        target_dir.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        raise RuntimeError(f"エラー: Vault にフォルダを作成できませんでした。詳細: {e}")

    filename = f"{date.today()}_{_safe_filename(title)}.md"
    path = target_dir / filename

    # 同名ファイルがあれば連番を付けて上書きを避ける
    counter = 2
    while path.exists():
        path = target_dir / f"{date.today()}_{_safe_filename(title)}_{counter}.md"
        counter += 1

    try:
        path.write_text(body, encoding="utf-8")
    except OSError as e:
        raise RuntimeError(f"エラー: ノートの保存に失敗しました。詳細: {e}")

    return path
