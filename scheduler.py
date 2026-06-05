"""
スケジューラー: tweets_queue.json を読み込み、
現在時刻（JST）に予定された投稿を実行する。

GitHub Actions から `python scheduler.py` で毎時間呼び出される。
"""

import json
import os
import sys
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from poster import post_tweet

QUEUE_FILE = "tweets_queue.json"
JST = ZoneInfo("Asia/Tokyo")


def save_queue(tweets: list[dict]) -> None:
    now_jst = datetime.now(JST)

    queue_tweets = []
    for tweet in tweets:
        hour = tweet.get("scheduled_hour", 12)
        target = now_jst.replace(hour=hour, minute=0, second=0, microsecond=0)
        if target <= now_jst:
            target += timedelta(days=1)

        queue_tweets.append(
            {
                "type": tweet.get("type", "不明"),
                "content": tweet.get("content", ""),
                "scheduled_hour": hour,
                "target_datetime": target.isoformat(),
                "posted": False,
                "posted_at": None,
            }
        )

    queue_tweets.sort(key=lambda x: x["target_datetime"])

    data = {
        "generated_date": now_jst.strftime("%Y-%m-%d"),
        "generated_at": now_jst.isoformat(),
        "total": len(queue_tweets),
        "posted_count": 0,
        "tweets": queue_tweets,
    }

    with open(QUEUE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"キューを保存しました: {len(queue_tweets)}本 → {QUEUE_FILE}")


def post_due_tweets() -> int:
    if not os.path.exists(QUEUE_FILE):
        print(f"エラー: キューファイルが見つかりません（{QUEUE_FILE}）")
        print("先に main.py を実行して投稿を生成してください。")
        return 0

    with open(QUEUE_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    tweets = data.get("tweets", [])
    if not tweets:
        print("キューが空です。本日の投稿はすべて完了しているか、まだ生成されていません。")
        return 0

    now_jst = datetime.now(JST)
    print(f"現在時刻（JST）: {now_jst.strftime('%Y-%m-%d %H:%M')}")

    posted_count = 0
    errors = []

    for tweet in tweets:
        if tweet.get("posted"):
            continue

        target_str = tweet.get("target_datetime", "")
        try:
            target = datetime.fromisoformat(target_str)
        except (ValueError, TypeError):
            errors.append(f"日時の解析に失敗: {target_str}")
            continue

        if target > now_jst:
            continue

        tweet_type = tweet.get("type", "不明")
        content = tweet.get("content", "")
        print(f"\n[{tweet_type}] {target.strftime('%H:%M')} 予定")
        print(f"  {content[:50]}{'...' if len(content) > 50 else ''}")

        try:
            post_tweet(content)
            tweet["posted"] = True
            tweet["posted_at"] = now_jst.isoformat()
            posted_count += 1
        except RuntimeError as e:
            print(f"  {e}")
            errors.append(str(e))

    data["posted_count"] = sum(1 for t in tweets if t.get("posted"))
    remaining = sum(1 for t in tweets if not t.get("posted"))

    with open(QUEUE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"\n今回の投稿: {posted_count}本 / 残り: {remaining}本")
    for err in errors:
        print(f"警告: {err}")

    return posted_count


if __name__ == "__main__":
    post_due_tweets()
