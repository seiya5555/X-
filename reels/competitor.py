"""
競合リールの記録とパターン分析

Instagram の公式APIでは他人のアカウントの数値を取得できないため、
競合データは手動入力で蓄積する。件数が少なくても、フックと構成を
言語化して溜めるほど分析の精度が上がる。
"""

from datetime import date

from . import claude_api, obsidian, storage
from .config import COMPETITORS_FILE, PATTERNS_FILE

EMPTY_COMPETITORS = {"reels": []}
EMPTY_PATTERNS = {"analyzed_at": "", "source_count": 0, "patterns": [], "avoid": [], "summary": ""}

ANALYSIS_PROMPT = """あなたはショート動画（Instagramリール）の分析専門家です。
手動で収集された競合リールのデータを分析し、再現可能な「伸びパターン」を抽出します。

## 分析の原則

【原則1：数値ではなく構造を見る】
再生数が多い理由を「運が良かった」で終わらせない。
フックの言い回し・情報の出し方・尺の使い方など、
次に自分が再現できる「構造」として言語化する。

【原則2：最初の2秒を最重要視する】
リールは冒頭2秒で離脱するかどうかが決まる。
伸びているリールのフックが「なぜ指を止めさせたか」を必ず分析する。

【原則3：自分に適用できるかを冷静に判定する】
発信者の属性・リソース・撮影環境が違えば再現できないパターンもある。
「顔出し前提」「高額な機材が前提」「既に大きなフォロワーが前提」の
パターンは applicability を low とし、その理由を明記する。

【原則4：真似すべきでないものを明示する】
誇大表現・煽り・誤解を招く断定など、短期的に伸びても
アカウントの信頼を毀損するパターンは avoid に入れる。

【原則5：データが少ないときは正直に言う】
サンプルが少ない場合、断定を避けて「仮説」として提示し、
確度を上げるために次にどんなデータを集めるべきかを summary に書く。

## 出力形式
必ずJSON形式のみで出力。余計な説明文・マークダウン記法は一切不要。

{
  "patterns": [
    {
      "name": "パターン名（短く具体的に）",
      "evidence": "どのデータからそう言えるのか",
      "why_it_works": "視聴者心理の観点でなぜ機能するのか",
      "applicability": "high | mid | low",
      "applicability_reason": "自分のアカウントに適用できる/できない理由",
      "how_to_apply": "自分の発信でどう使うかの具体案"
    }
  ],
  "avoid": [
    {"pattern": "真似すべきでないパターン", "reason": "理由"}
  ],
  "summary": "全体の要約と、次に集めるべきデータ"
}"""


def load() -> dict:
    return storage.load(COMPETITORS_FILE, EMPTY_COMPETITORS)


def add(record: dict) -> int:
    """競合リールを1件追加し、追加後の総件数を返す。"""
    data = load()
    reels = data.setdefault("reels", [])

    record["added_at"] = str(date.today())
    record["id"] = len(reels) + 1
    reels.append(record)

    storage.save(COMPETITORS_FILE, data)
    return len(reels)


def load_patterns() -> dict:
    return storage.load(PATTERNS_FILE, EMPTY_PATTERNS)


def _format_reels(reels: list[dict]) -> str:
    lines = []
    for reel in reels:
        lines.append(
            f"---\n"
            f"アカウント: {reel.get('account', '不明')}\n"
            f"ジャンル: {reel.get('genre', '不明')}\n"
            f"再生数: {reel.get('views', 0):,} / いいね: {reel.get('likes', 0):,} / "
            f"保存: {reel.get('saves', 0):,}\n"
            f"尺: {reel.get('duration_sec', 0)}秒\n"
            f"冒頭2秒のフック: {reel.get('hook', '')}\n"
            f"構成: {reel.get('structure', '')}\n"
            f"最後まで見てしまった理由: {reel.get('why_watched', '')}\n"
            f"メモ: {reel.get('note', '')}"
        )
    return "\n".join(lines)


def analyze(my_context: str = "") -> dict:
    """蓄積した競合データから伸びパターンを抽出し、patterns.json に保存する。"""
    data = load()
    reels = data.get("reels", [])

    if not reels:
        raise RuntimeError(
            "エラー: 競合データが1件もありません。\n"
            "先に `python -m reels.main competitor` で競合リールを登録してください。"
        )

    user_content = (
        f"## 収集した競合リール（{len(reels)}件）\n"
        f"{_format_reels(reels)}\n\n"
        f"## 自分のアカウントの情報\n"
        f"{my_context if my_context else '（情報なし）'}\n\n"
        "このデータを分析し、再現可能な伸びパターンと、"
        "自分のアカウントへの適用可否を判定してください。"
    )

    result = claude_api.ask_json(ANALYSIS_PROMPT, user_content)

    patterns = {
        "analyzed_at": str(date.today()),
        "source_count": len(reels),
        "patterns": result.get("patterns", []),
        "avoid": result.get("avoid", []),
        "summary": result.get("summary", ""),
    }
    storage.save(PATTERNS_FILE, patterns)

    return patterns


def patterns_as_prompt_context() -> str:
    """台本生成に渡すための、分析済みパターンのテキスト。"""
    data = load_patterns()
    patterns = data.get("patterns", [])
    if not patterns:
        return ""

    lines = [f"（{data.get('source_count', 0)}件の競合データから分析）"]
    for pattern in patterns:
        lines.append(
            f"- 【{pattern.get('name', '')}】適用度: {pattern.get('applicability', '?')}\n"
            f"  機能する理由: {pattern.get('why_it_works', '')}\n"
            f"  適用方法: {pattern.get('how_to_apply', '')}"
        )

    avoid = data.get("avoid", [])
    if avoid:
        lines.append("\n【真似してはいけないパターン】")
        for item in avoid:
            lines.append(f"- {item.get('pattern', '')}（理由: {item.get('reason', '')}）")

    return "\n".join(lines)


def to_markdown(patterns: dict) -> str:
    """分析結果を Obsidian ノート用の Markdown に整形する。"""
    lines = [
        f"# 競合分析レポート {patterns.get('analyzed_at', '')}",
        "",
        f"分析元データ: {patterns.get('source_count', 0)}件",
        "",
        "## 抽出された伸びパターン",
        "",
    ]

    applicability_label = {"high": "そのまま使える", "mid": "調整すれば使える", "low": "今は使いにくい"}

    for pattern in patterns.get("patterns", []):
        level = pattern.get("applicability", "")
        lines.extend(
            [
                f"### {pattern.get('name', '')}",
                "",
                f"- **適用度**: {level}（{applicability_label.get(level, '不明')}）",
                f"- **根拠**: {pattern.get('evidence', '')}",
                f"- **機能する理由**: {pattern.get('why_it_works', '')}",
                f"- **適用可否の理由**: {pattern.get('applicability_reason', '')}",
                f"- **自分への適用方法**: {pattern.get('how_to_apply', '')}",
                "",
            ]
        )

    avoid = patterns.get("avoid", [])
    if avoid:
        lines.extend(["## 真似してはいけないパターン", ""])
        for item in avoid:
            lines.append(f"- **{item.get('pattern', '')}** — {item.get('reason', '')}")
        lines.append("")

    lines.extend(["## まとめ・次に集めるべきデータ", "", patterns.get("summary", ""), ""])
    lines.append("#リール #競合分析")

    return "\n".join(lines)


def save_report_to_vault(patterns: dict):
    return obsidian.save_note(
        title="競合分析レポート",
        body=to_markdown(patterns),
        subdir="競合分析",
    )
