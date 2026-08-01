"""
リール台本生成システム - メインスクリプト

使い方:
  python -m reels.main script      # リール台本を生成する
  python -m reels.main competitor  # 競合リールを1件記録する
  python -m reels.main analyze     # 競合データから伸びパターンを分析する
  python -m reels.main record      # 自分の投稿実績を記録する
  python -m reels.main review      # 実績を振り返って改善点を出す
"""

import argparse
import sys

from . import competitor, config, obsidian, performance, script_generator


def _ask(label: str, required: bool = True, default: str = "") -> str:
    while True:
        try:
            value = input(f"{label}: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nキャンセルしました。")
            sys.exit(0)

        if value:
            return value
        if not required:
            return default
        print("エラー: 入力してください。")


def _ask_int(label: str, default: int = 0) -> int:
    while True:
        try:
            value = input(f"{label}: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nキャンセルしました。")
            sys.exit(0)

        if not value:
            return default
        try:
            number = int(value.replace(",", ""))
        except ValueError:
            print("エラー: 数値を入力してください。")
            continue
        if number < 0:
            print("エラー: 0以上の数値を入力してください。")
            continue
        return number


def _header(title: str) -> None:
    print("=" * 50)
    print(f"  {title}")
    print("=" * 50)


def _warn_if_no_vault() -> None:
    if config.get_vault_path() is None:
        print(
            "警告: OBSIDIAN_VAULT_PATH が未設定です。\n"
            "      過去ノートを参照せずに生成します（精度が落ちます）。\n"
            "      .env に Vault のパスを設定してください。\n"
        )


def cmd_script(args: argparse.Namespace) -> None:
    _header("リール台本の生成")
    _warn_if_no_vault()

    theme = args.theme or _ask("今回のテーマ（例: 副業を始めて最初にやるべきこと）")
    duration = args.duration or _ask_int("想定尺（秒・未入力なら30）", default=30)
    extra = args.note or _ask("入れたい要素・追加指示（任意）", required=False)

    print("\nClaude API で台本を生成中...")
    print("（30〜60秒ほどお待ちください）\n")

    try:
        script = script_generator.generate(theme, duration_sec=duration, extra_note=extra)
    except RuntimeError as e:
        print(e)
        sys.exit(1)

    print(script_generator.to_markdown(script))

    try:
        path = script_generator.save_to_vault(script)
    except RuntimeError as e:
        print(f"\n{e}")
        sys.exit(1)

    print("\n" + "=" * 50)
    if path:
        print(f"完了！ Obsidian に保存しました:\n  {path}")
    else:
        print("完了！（Vault 未設定のため、上記の内容をコピーして使ってください）")


def cmd_competitor(args: argparse.Namespace) -> None:
    _header("競合リールの記録")
    print("伸びている競合リールを1件ずつ記録します。")
    print("数値は分かる範囲で構いません（不明なら空欄でEnter）。\n")

    record = {
        "account": _ask("アカウント名（例: @example）"),
        "genre": _ask("ジャンル（例: 副業・投資）"),
        "url": _ask("投稿URL（任意）", required=False),
        "views": _ask_int("再生数"),
        "likes": _ask_int("いいね数"),
        "saves": _ask_int("保存数"),
        "comments": _ask_int("コメント数"),
        "duration_sec": _ask_int("尺（秒）"),
        "hook": _ask("冒頭2秒で何を言っていたか（できるだけ正確に）"),
        "structure": _ask("全体の構成（例: 問題提起→失敗談→解決策→CTA）"),
        "why_watched": _ask("なぜ最後まで見てしまったか（あなたの主観でOK）"),
        "note": _ask("その他メモ（任意）", required=False),
    }

    try:
        total = competitor.add(record)
    except RuntimeError as e:
        print(e)
        sys.exit(1)

    print(f"\n記録しました。（累計 {total} 件）")
    if total < 5:
        print("ヒント: 5件以上たまると、分析の精度が上がります。")
    else:
        print("`python -m reels.main analyze` で伸びパターンを分析できます。")


def cmd_analyze(args: argparse.Namespace) -> None:
    _header("競合の伸びパターン分析")

    if not competitor.load().get("reels"):
        print(
            "エラー: 競合データが1件もありません。\n"
            "先に `python -m reels.main competitor` で競合リールを登録してください。"
        )
        sys.exit(1)

    my_context = obsidian.build_context(["自分", "アカウント", "発信", "コンセプト"], max_notes=5)

    print("Claude API で分析中...")
    print("（30〜60秒ほどお待ちください）\n")

    try:
        patterns = competitor.analyze(my_context=my_context)
    except RuntimeError as e:
        print(e)
        sys.exit(1)

    print(competitor.to_markdown(patterns))

    try:
        path = competitor.save_report_to_vault(patterns)
    except RuntimeError as e:
        print(f"\n{e}")
        sys.exit(1)

    print("\n" + "=" * 50)
    if path:
        print(f"完了！ Obsidian に保存しました:\n  {path}")
    else:
        print("完了！（Vault 未設定のため、上記の内容をコピーして使ってください）")
    print("この分析結果は、次回以降の台本生成に自動で反映されます。")


def cmd_record(args: argparse.Namespace) -> None:
    _header("投稿実績の記録")
    print("投稿したリールの結果を記録します。\n")

    record = {
        "title": _ask("投稿のタイトル・内容"),
        "posted_at": _ask("投稿日（例: 2026-08-01）"),
        "hook": _ask("使ったフック（冒頭2秒）"),
        "duration_sec": _ask_int("尺（秒）"),
        "views": _ask_int("再生数"),
        "likes": _ask_int("いいね数"),
        "saves": _ask_int("保存数"),
        "comments": _ask_int("コメント数"),
        "note": _ask("所感・気づき（任意）", required=False),
    }

    try:
        total = performance.add(record)
    except RuntimeError as e:
        print(e)
        sys.exit(1)

    print(f"\n記録しました。（累計 {total} 件）")
    print("この実績は、次回以降の台本生成に自動で反映されます。")


def cmd_review(args: argparse.Namespace) -> None:
    _header("投稿実績の振り返り")

    if not performance.load().get("posts"):
        print(
            "エラー: 実績データが1件もありません。\n"
            "先に `python -m reels.main record` で投稿実績を記録してください。"
        )
        sys.exit(1)

    print("Claude API で分析中...")
    print("（30〜60秒ほどお待ちください）\n")

    try:
        result = performance.review()
    except RuntimeError as e:
        print(e)
        sys.exit(1)

    print("【伸びた要因】")
    for item in result.get("winning_factors", []):
        print(f"- {item.get('factor', '')}")
        print(f"  根拠: {item.get('evidence', '')}")

    print("\n【伸びなかった要因】")
    for item in result.get("losing_factors", []):
        print(f"- {item.get('factor', '')}")
        print(f"  根拠: {item.get('evidence', '')}")
        print(f"  直し方: {item.get('fix', '')}")

    print(f"\n【次に試すべき最優先の1点】\n{result.get('next_action', '')}")
    print(f"\n【仮説】\n{result.get('hypothesis', '')}")
    print(f"\n【まとめ】\n{result.get('summary', '')}")


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="reels",
        description="Instagram リール台本生成・競合分析・PDCA システム",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    p_script = subparsers.add_parser("script", help="リール台本を生成する")
    p_script.add_argument("--theme", help="今回のテーマ")
    p_script.add_argument("--duration", type=int, help="想定尺（秒）")
    p_script.add_argument("--note", help="追加の指示")
    p_script.set_defaults(func=cmd_script)

    p_competitor = subparsers.add_parser("competitor", help="競合リールを記録する")
    p_competitor.set_defaults(func=cmd_competitor)

    p_analyze = subparsers.add_parser("analyze", help="競合の伸びパターンを分析する")
    p_analyze.set_defaults(func=cmd_analyze)

    p_record = subparsers.add_parser("record", help="自分の投稿実績を記録する")
    p_record.set_defaults(func=cmd_record)

    p_review = subparsers.add_parser("review", help="実績を振り返って改善点を出す")
    p_review.set_defaults(func=cmd_review)

    args = parser.parse_args()

    try:
        args.func(args)
    except RuntimeError as e:
        print(e)
        sys.exit(1)


if __name__ == "__main__":
    main()
