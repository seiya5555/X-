"""
自分の投稿実績の記録（PDCA の C と A）

投稿したリールの結果を記録し、次回の台本生成にそのまま材料として渡す。
これが溜まるほど「自分のアカウントで何が効くか」の精度が上がる。
"""

from datetime import date

from . import claude_api, storage
from .config import PERFORMANCE_FILE

EMPTY_PERFORMANCE = {"posts": []}

# プロンプトに渡す上位・下位の件数
TOP_N = 5

REVIEW_PROMPT = """あなたはショート動画運用の分析担当です。
発信者本人の投稿実績データを分析し、次の投稿に活かせる改善点を出します。

## 分析の原則

【原則1：伸びた理由を構造で説明する】
「良かった」で終わらせず、フック・尺・テーマ・投稿時間のどれが
効いたのかを切り分けて説明する。

【原則2：伸びなかった投稿こそ丁寧に扱う】
失敗した投稿の要因を具体的に特定する。
「内容が悪い」ではなく「冒頭2秒が説明から入っていた」のように
次に直せる粒度で書く。

【原則3：サンプル数を踏まえる】
データが少ないうちは断定しない。仮説として提示し、
検証するために次に何を試すべきかを提案する。

【原則4：次のアクションを1つに絞る】
改善点を並べるだけでは実行されない。
次の投稿で試すべき最優先の1点を必ず明示する。

## 出力形式
必ずJSON形式のみで出力。余計な説明文・マークダウン記法は一切不要。

{
  "winning_factors": [{"factor": "伸びた要因", "evidence": "根拠となる投稿"}],
  "losing_factors": [{"factor": "伸びなかった要因", "evidence": "根拠となる投稿", "fix": "next回の直し方"}],
  "next_action": "次の投稿で試すべき最優先の1点",
  "hypothesis": "現時点での仮説と、検証方法",
  "summary": "全体の要約"
}"""


def load() -> dict:
    return storage.load(PERFORMANCE_FILE, EMPTY_PERFORMANCE)


def add(record: dict) -> int:
    """投稿実績を1件追加し、追加後の総件数を返す。"""
    data = load()
    posts = data.setdefault("posts", [])

    record["recorded_at"] = str(date.today())
    record["id"] = len(posts) + 1
    posts.append(record)

    storage.save(PERFORMANCE_FILE, data)
    return len(posts)


def _format(post: dict) -> str:
    return (
        f"- [{post.get('posted_at', '?')}] 「{post.get('title', '')}」\n"
        f"  フック: {post.get('hook', '')}\n"
        f"  尺: {post.get('duration_sec', 0)}秒 / "
        f"再生: {post.get('views', 0):,} / いいね: {post.get('likes', 0):,} / "
        f"保存: {post.get('saves', 0):,} / コメント: {post.get('comments', 0):,}\n"
        f"  所感: {post.get('note', '')}"
    )


def as_prompt_context() -> str:
    """台本生成に渡すための、実績サマリー。"""
    posts = load().get("posts", [])
    if not posts:
        return ""

    ranked = sorted(posts, key=lambda p: p.get("views", 0), reverse=True)

    lines = [f"（記録件数: {len(posts)}件）", "", "【伸びた投稿】"]
    lines.extend(_format(post) for post in ranked[:TOP_N])

    if len(ranked) > TOP_N:
        lines.extend(["", "【伸びなかった投稿】"])
        lines.extend(_format(post) for post in ranked[-TOP_N:])

    return "\n".join(lines)


def review() -> dict:
    """蓄積した実績から、次に活かす改善点を分析する。"""
    posts = load().get("posts", [])
    if not posts:
        raise RuntimeError(
            "エラー: 実績データが1件もありません。\n"
            "先に `python -m reels.main record` で投稿実績を記録してください。"
        )

    user_content = (
        f"## 投稿実績（{len(posts)}件）\n"
        + "\n".join(_format(post) for post in posts)
        + "\n\nこのデータを分析し、次の投稿に活かせる改善点を出してください。"
    )

    return claude_api.ask_json(REVIEW_PROMPT, user_content)
