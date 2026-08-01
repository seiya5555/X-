"""
リール台本の生成

Obsidian の過去ノート（自分の知識・実績・言葉づかい）と、
競合分析で抽出した伸びパターン、そして過去投稿の実績を材料に、
撮影・編集にそのまま使えるリール台本を生成する。
"""

import re
from datetime import date

from . import claude_api, competitor, obsidian, performance

SYSTEM_PROMPT = """あなたはInstagramリールの構成作家です。
発信者本人の過去の知識・実績と、競合分析から得られた伸びパターンを元に、
撮影と編集にそのまま使えるリール台本を作ります。

## リールという媒体の絶対的な前提

【前提1：勝負は最初の2秒】
スクロールを止められなければ、中身がどれだけ良くても意味がない。
冒頭2秒は「続きが気になる状態」を作ることだけに使う。
自己紹介・挨拶・前置きを冒頭に置くことは絶対に禁止。

【前提2：音声オフで見られる】
多くの視聴者は音を出さずに見る。
話している内容は必ず画面上のテロップでも伝わるようにする。
テロップだけを追っても意味が通る構成にする。

【前提3：離脱は常に起きている】
3〜5秒ごとに「次を見る理由」を作り直す。
話題の切り替え・数字の提示・映像の変化などで飽きさせない。

【前提4：保存とコメントが伸びを決める】
再生数よりも保存率・コメント率がアルゴリズム上の評価につながる。
「後で見返したい情報密度」か「言いたくなる余白」のどちらかを必ず入れる。

【前提5：ループさせる】
最後のカットが最初のカットに自然につながると、
再生数が実質的に倍増する。可能な限りループ構造を狙う。

## 台本を作るときの原則

【原則1：発信者本人の言葉を使う】
提供された過去ノートに出てくる語彙・言い回し・実体験を優先して使う。
一般論やネットで拾えるような内容だけで構成してはいけない。
本人しか言えない具体的な数字・失敗・固有の体験を必ず入れる。

【原則2：伸びパターンは「構造」だけ借りる】
競合の伸びパターンは構成の型として使い、内容をそのまま真似しない。
適用度が low のパターンは使わない。
avoid に挙げられたパターンは絶対に使わない。

【原則3：過去実績から学習する】
過去投稿の実績が提供された場合、伸びた投稿の共通点を踏襲し、
伸びなかった投稿の失敗要因を繰り返さない。
どこを反映したかを design_reason に明記する。

【原則4：誇張しない】
断定できないことを断定しない。誇大な数字・煽り表現は使わない。
再現性のない成功談を「誰でもできる」と表現しない。

【原則5：撮影者が迷わない粒度で書く】
各シーンには「何を話すか」だけでなく
「画面に何を出すか」「どんな映像か」まで書く。
台本を見た人がそのまま撮影できる状態にする。

## フックの型（3案は必ず異なる型で作る）
- 逆説型：「〇〇は実はやらない方がいい」
- 数字型：「3ヶ月で〇〇円になった方法」
- 失敗開示型：「これで〇〇円溶かしました」
- 疑問提起型：「なんで伸びないか分かる？」
- 実演型：いきなり作業・結果を見せる
- 共感型：「〇〇な人、これ絶対やってる」

## 出力形式
必ずJSON形式のみで出力。余計な説明文・マークダウン記法は一切不要。

{
  "title": "台本のタイトル（管理用）",
  "theme": "この動画のテーマ",
  "target": "誰に向けた動画か",
  "duration_sec": 想定尺（秒・整数）,
  "hooks": [
    {"type": "フックの型", "text": "冒頭2秒のセリフとテロップ", "why": "なぜ指が止まるのか"}
  ],
  "selected_hook": "3案のうち最も強いものの text をそのまま記載",
  "selected_reason": "その案を選んだ理由",
  "scenes": [
    {
      "no": 1,
      "start_sec": 0,
      "end_sec": 2,
      "narration": "話す内容",
      "on_screen_text": "画面に出すテロップ",
      "visual": "どんな映像・カットか",
      "purpose": "このシーンの役割（掴み/展開/転換/結論など）"
    }
  ],
  "loop_note": "最後から最初へどうつなげるか",
  "caption": "投稿キャプション本文（改行含む）",
  "hashtags": ["#タグ1", "#タグ2"],
  "cta": "視聴者に取ってほしい行動と、その促し方",
  "bgm": "BGMの雰囲気・テンポの指示",
  "patterns_used": ["使った伸びパターン名"],
  "source_notes": ["参考にした過去ノートのファイル名"],
  "design_reason": "なぜこの構成にしたのかの説明",
  "self_check": {
    "hook_strength": 1〜10の整数,
    "retention_risk": "離脱しそうな箇所と理由",
    "improvement": "さらに良くするなら何を変えるか"
  }
}"""


# 日本語はスペースで区切られないため、漢字・カタカナ・英数字のまとまりを語として取り出す。
# 助詞や活用語尾はひらがななので、そこが自然な区切りになる。
# （例: 「副業を始めて最初にやるべきこと」→ 副業 / 最初）
_TOKEN_PATTERN = re.compile(
    r"[一-龥々]{2,}"  # 漢字2文字以上
    r"|[ァ-ヴー]{3,}"  # カタカナ3文字以上
    r"|[A-Za-z][A-Za-z0-9]{1,}"  # 英数字
    r"|[ぁ-ん]{4,}"  # ひらがなのみの語（長めのものだけ拾う）
)


def _keywords_from(theme: str, extra: str = "") -> list[str]:
    """テーマ文から Vault 検索用のキーワードを作る。"""
    tokens = _TOKEN_PATTERN.findall(f"{theme} {extra}")

    # 順序を保ったまま重複を除く
    seen = set()
    keywords = []
    for token in tokens:
        if token not in seen:
            seen.add(token)
            keywords.append(token)

    return keywords or [theme]


def generate(theme: str, duration_sec: int = 30, extra_note: str = "") -> dict:
    """リール台本を生成して返す。"""
    keywords = _keywords_from(theme, extra_note)

    vault_context = obsidian.build_context(keywords)
    pattern_context = competitor.patterns_as_prompt_context()
    performance_context = performance.as_prompt_context()

    user_content = (
        f"## 今回のテーマ\n{theme}\n\n"
        f"## 想定尺\n{duration_sec}秒\n\n"
        f"## 追加の指示・入れたい要素\n{extra_note if extra_note else '（特になし）'}\n\n"
        f"## 発信者の過去ノート（Obsidian より抜粋）\n"
        f"{vault_context if vault_context else '（過去ノートが見つかりませんでした）'}\n\n"
        f"## 競合分析から抽出された伸びパターン\n"
        f"{pattern_context if pattern_context else '（未分析。一般的なリール構成の原則で作成してください）'}\n\n"
        f"## 自分の過去投稿の実績\n"
        f"{performance_context if performance_context else '（実績データなし）'}\n\n"
        "以上を踏まえて、リール台本を1本作成してください。\n"
        "過去ノートに出てくる本人の具体的な体験・数字・言葉づかいを必ず活かしてください。"
    )

    result = claude_api.ask_json(SYSTEM_PROMPT, user_content)
    result["generated_at"] = str(date.today())
    result.setdefault("theme", theme)
    result.setdefault("duration_sec", duration_sec)

    return result


def to_markdown(script: dict) -> str:
    """台本を Obsidian ノート用の Markdown に整形する。"""
    lines = [
        f"# {script.get('title', 'リール台本')}",
        "",
        f"- **作成日**: {script.get('generated_at', '')}",
        f"- **テーマ**: {script.get('theme', '')}",
        f"- **ターゲット**: {script.get('target', '')}",
        f"- **想定尺**: {script.get('duration_sec', '')}秒",
        "",
        "## フック候補",
        "",
    ]

    for i, hook in enumerate(script.get("hooks", []), 1):
        lines.extend(
            [
                f"{i}. **【{hook.get('type', '')}】** {hook.get('text', '')}",
                f"   - 効く理由: {hook.get('why', '')}",
            ]
        )

    lines.extend(
        [
            "",
            f"**採用フック**: {script.get('selected_hook', '')}",
            "",
            f"理由: {script.get('selected_reason', '')}",
            "",
            "## 台本（シーン割）",
            "",
            "| 秒数 | 役割 | ナレーション | テロップ | 映像 |",
            "|---|---|---|---|---|",
        ]
    )

    for scene in script.get("scenes", []):
        # 表が崩れないよう、セル内の改行とパイプを置き換える
        def cell(value: str) -> str:
            return str(value).replace("|", "\\|").replace("\n", "<br>")

        lines.append(
            f"| {scene.get('start_sec', '')}〜{scene.get('end_sec', '')}秒 "
            f"| {cell(scene.get('purpose', ''))} "
            f"| {cell(scene.get('narration', ''))} "
            f"| {cell(scene.get('on_screen_text', ''))} "
            f"| {cell(scene.get('visual', ''))} |"
        )

    hashtags = " ".join(script.get("hashtags", []))
    check = script.get("self_check", {})

    lines.extend(
        [
            "",
            f"**ループ設計**: {script.get('loop_note', '')}",
            "",
            f"**BGM**: {script.get('bgm', '')}",
            "",
            "## キャプション",
            "",
            "```",
            script.get("caption", ""),
            "",
            hashtags,
            "```",
            "",
            f"**CTA**: {script.get('cta', '')}",
            "",
            "## 設計の根拠",
            "",
            f"- **使った伸びパターン**: {', '.join(script.get('patterns_used', [])) or 'なし'}",
            f"- **参考にした過去ノート**: {', '.join(script.get('source_notes', [])) or 'なし'}",
            "",
            script.get("design_reason", ""),
            "",
            "## 自己採点",
            "",
            f"- **フック強度**: {check.get('hook_strength', '?')} / 10",
            f"- **離脱リスク**: {check.get('retention_risk', '')}",
            f"- **改善案**: {check.get('improvement', '')}",
            "",
            "## 投稿後の記録（投稿したら埋める）",
            "",
            "- 再生数: ",
            "- いいね: ",
            "- 保存: ",
            "- コメント: ",
            "- 気づき: ",
            "",
            "#リール #台本",
        ]
    )

    return "\n".join(lines)


def save_to_vault(script: dict):
    return obsidian.save_note(
        title=script.get("title", "リール台本"),
        body=to_markdown(script),
    )
