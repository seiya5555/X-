import os

import tweepy


def _get_client() -> tweepy.Client:
    required = [
        "TWITTER_API_KEY",
        "TWITTER_API_SECRET",
        "TWITTER_ACCESS_TOKEN",
        "TWITTER_ACCESS_SECRET",
    ]
    missing = [v for v in required if not os.environ.get(v)]
    if missing:
        raise RuntimeError(
            f"エラー: 以下の環境変数が設定されていません → {', '.join(missing)}\n"
            ".env ファイルまたは GitHub Secrets を確認してください。"
        )
    return tweepy.Client(
        consumer_key=os.environ["TWITTER_API_KEY"],
        consumer_secret=os.environ["TWITTER_API_SECRET"],
        access_token=os.environ["TWITTER_ACCESS_TOKEN"],
        access_token_secret=os.environ["TWITTER_ACCESS_SECRET"],
    )


def post_tweet(content: str) -> dict:
    if not content.strip():
        raise ValueError("エラー: 投稿内容が空です。")
    if len(content) > 280:
        raise ValueError(
            f"エラー: 投稿が280文字を超えています（{len(content)}文字）。"
        )
    try:
        client = _get_client()
        response = client.create_tweet(text=content)
        tweet_id = response.data["id"]
        print(f"  投稿成功 → https://x.com/i/web/status/{tweet_id}")
        return response.data
    except tweepy.errors.Forbidden as e:
        if "duplicate" in str(e).lower():
            raise RuntimeError(
                "エラー: 重複投稿です。同一内容を24時間以内に再送できません。"
            )
        raise RuntimeError(f"エラー: アクセス拒否（403）。APIの権限を確認してください。詳細: {e}")
    except tweepy.errors.TooManyRequests:
        raise RuntimeError(
            "エラー: レートリミットに達しました。しばらく時間をおいて再試行してください。"
        )
    except tweepy.errors.Unauthorized:
        raise RuntimeError(
            "エラー: 認証失敗（401）。Twitter APIキーとアクセストークンを確認してください。"
        )
    except tweepy.errors.TweepyException as e:
        raise RuntimeError(f"エラー: Twitter API呼び出しに失敗しました。詳細: {e}")
