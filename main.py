"""
X 自動投稿システム - メインスクリプト

使い方:
  python main.py              # ターミナルで対話入力
  FOLLOWERS=100 REVENUE=500 TODAY_MEMO="..." python main.py  # 環境変数で入力（CI用）
"""

import os
import sys

from dotenv import load_dotenv

load_dotenv()

import generator
import memory
import scheduler


def _get_inputs() -> tuple[int, int, str]:
    followers_env = os.environ.get("FOLLOWERS")
    revenue_env = os.environ.get("REVENUE")
    memo_env = os.environ.get("TODAY_MEMO")

    if followers_env is not None and revenue_env is not None and memo_env is not None:
        try:
            return int(followers_env), int(revenue_env), memo_env
        except ValueError:
            print("エラー: FOLLOWERS・REVENUE は整数で指定してください。")
            sys.exit(1)

    print("=" * 45)
    print("  X 自動投稿システム - 毎日の入力")
    print("=" * 45)

    while True:
        try:
            followers = int(input("\n今日のフォロワー数: ").strip())
            if followers < 0:
                print("エラー: 0以上の数値を入力してください。")
                continue
            break
        except ValueError:
            print("エラー: 数値を入力してください。")
        except (KeyboardInterrupt, EOFError):
            print("\nキャンセルしました。")
            sys.exit(0)

    while True:
        try:
            revenue = int(input("今日の収益額（円）: ").strip())
            if revenue < 0:
                print("エラー: 0以上の数値を入力してください。")
                continue
            break
        except ValueError:
            print("エラー: 数値を入力してください。")
        except (KeyboardInterrupt, EOFError):
            print("\nキャンセルしました。")
            sys.exit(0)

    memo = ""
    while not memo:
        try:
            memo = input("今日の出来事・気づき（1〜2行）: ").strip()
            if not memo:
                print("エラー: 気づきを入力してください。")
        except (KeyboardInterrupt, EOFError):
            print("\nキャンセルしました。")
            sys.exit(0)

    return followers, revenue, memo


def _display_tweets(tweets: list[dict]) -> None:
    print("\n" + "=" * 50)
    print("  生成された投稿一覧（全24本）")
    print("=" * 50)

    for i, tweet in enumerate(tweets, 1):
        hour = tweet.get("scheduled_hour", "?")
        tweet_type = tweet.get("type", "不明")
        content = tweet.get("content", "")
        print(f"\n[{i:02d}] {tweet_type}  /  {hour}時投稿予定")
        print("─" * 40)
        print(content)


def main() -> None:
    followers, revenue, memo = _get_inputs()

    print(f"\n入力確認:")
    print(f"  フォロワー数 : {followers:,}人")
    print(f"  収益         : {revenue:,}円")
    print(f"  気づき       : {memo}")

    yesterday_preview = memory.load_preview()
    if yesterday_preview:
        print(f"\n昨日の予告内容を読み込みました。")

    is_ci = os.environ.get("GITHUB_ACTIONS") == "true" or os.environ.get("AUTO_CONFIRM") == "true"

    while True:
        print("\nClaude API で24本の投稿文を生成中...")
        print("（30〜60秒ほどお待ちください）\n")

        try:
            tweets = generator.generate_tweets(
                today_followers=followers,
                today_revenue=revenue,
                today_memo=memo,
                yesterday_preview=yesterday_preview,
            )
        except RuntimeError as e:
            print(e)
            sys.exit(1)

        _display_tweets(tweets)

        if is_ci:
            print("\n（CI環境のため確認をスキップします）")
            break

        print("\n" + "=" * 50)
        try:
            answer = input("この内容で投稿しますか？ (y/n): ").strip().lower()
        except (KeyboardInterrupt, EOFError):
            print("\nキャンセルしました。")
            sys.exit(0)

        if answer == "y":
            break
        elif answer == "n":
            print("\n再生成します...")
            continue
        else:
            print("y または n を入力してください。")

    preview_contents = [t["content"] for t in tweets if t.get("type") == "予告・伏線型"]
    if preview_contents:
        memory.save_preview(preview_contents)
        print(f"\n明日用の予告内容を保存しました（{len(preview_contents)}本）")

    try:
        scheduler.save_queue(tweets)
    except OSError as e:
        print(f"エラー: キューの保存に失敗しました。詳細: {e}")
        sys.exit(1)

    print("\n" + "=" * 50)
    print("  完了！")
    print("=" * 50)
    print(f"24本の投稿をスケジュールしました。")
    print("GitHub Actions が毎時間スケジュール通りに自動投稿します。")


if __name__ == "__main__":
    main()
