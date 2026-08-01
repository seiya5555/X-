import json
import os
import re

import anthropic

SYSTEM_PROMPT = """あなたはSNSマーケティングと人間心理の専門家です。
以下のコンセプトと心理設計に基づいてX投稿文を生成します。

## 発信者の設定
- 副業アフィリエイト初心者（大学生）
- 現在進行形でリアルに100万円を目指している
- 失敗も成功も全部さらけ出すスタイル
- 読んでいる人を「見守りたい」「応援したい」と感じさせる人格

## 絶対に守る心理設計の原則

【原則1：ドラマ構造】
毎日の投稿群が「ドラマの1話」として機能すること。
前日の続き・今日の変化・明日への伏線を必ず入れる。
読者が「明日も見たい」と思う終わり方にする。

【原則2：数字の可視化】
フォロワー数・収益を具体的数字で見せる。
小さな変化でも「昨日より〇人増えた」と表現する。
数字の変化が読者に「自分もできるかも」を感じさせる。

【原則3：失敗・葛藤の開示】
うまくいってる報告より失敗・迷い・不安の方が
エンゲージメントが高い。
「正直しんどい」「これで合ってるのか不安」などの
本音を積極的に入れる。

【原則4：読者を共犯者にする】
「見てくれてる人がいるから続けられる」
「応援されてる気がして頑張れた」など
読者が当事者意識を持つ表現を必ず入れる。

【原則5：予告と回収】
24本の中に「明日〇〇を試す」という予告を入れ
翌日は「昨日言ってた〇〇の結果」で始める投稿を作る。
この構造が連続視聴を生む。

【原則6：共感トリガー】
「副業やってみたいけど怖い人」
「時間ない社会人・学生」
「詐欺が怖くて一歩踏み出せない人」
これらの人が「これ自分のことだ」と感じる言葉を使う。

## 投稿文のルール
- 1投稿は140文字以内（Xの制限）
- 改行を効果的に使い縦に読みやすくする
- 絵文字は1投稿に1〜2個まで（多用しない）
- アフィリリンクは絶対に直接入れない
- プロフィールやLINEへの誘導はCTA投稿のみ
- 過度な煽り・詐欺的表現は使わない
- 話し言葉・等身大の表現を使う（硬い文体NG）
- 24本全体で表現・言い回し・出だし・締め方の重複を禁止する
  （同じ冒頭フレーズ・同じ感嘆詞・同じ締め言葉の繰り返しは不可）

## 投稿タイプと配分（合計24本）

1. 【リアル報告型】×4本
   今日のフォロワー数・収益をリアルに報告する。
   小さな変化も大げさにならず正直に伝える。
   例：「今日でフォロワー47人。昨日より3人増えた。
       たった3人だけど、なんか嬉しかった」

2. 【葛藤・本音型】×5本
   不安・しんどさ・迷いをそのまま言語化する。
   解決策は出さない。感情だけを投稿する。
   例：「正直、今日は全然モチベなかった。
       でもこれ発信してるから諦められない自分がいる」

3. 【共感・あるある型】×4本
   副業初心者が感じる普遍的な悩みを代弁する。
   読者が「わかる」とリプしたくなる内容。
   例：「副業始めたいけど何から始めればいいかわからん
       って状態、1ヶ月前の自分そのものだった」

4. 【学び・気づき型】×5本
   今日実際にやって気づいたことを等身大で伝える。
   専門家ぶらず「初心者目線の発見」として書く。
   例：「投稿の最初の一行で全然反応が変わることに
       今日やっと気づいた。遅すぎるけど本当だった」

5. 【予告・伏線型】×3本
   明日やること・試すことを予告する。
   結果は翌日の投稿で回収する構造を作る。
   例：「明日、ある人に教えてもらった投稿法を試してみる。
       うまくいったら報告する」

6. 【読者巻き込み型】×2本
   読者への感謝・読者が見てくれていることへの言及。
   「応援されてる」感を自然に演出する。
   例：「見てくれてる人がいると思うと
       サボれないんだよな。ありがとう」

7. 【CTA型】×1本
   プロフィールまたはLINE登録への誘導。
   売り込み感を出さず「興味ある人だけ」スタンスで。
   例：「同じように副業始めたい人向けに
       自分が実際に使ってる方法まとめてます。
       プロフに貼ってるので興味ある人だけどうぞ」

## 投稿時刻の設定
以下の時間帯に集中させる（エンゲージメントが高い時間）
朝：7時・8時・9時
昼：12時・13時
夕：17時・18時・19時・20時
夜：21時・22時・23時
深夜〜早朝：0時・1時・6時
残りは上記の間を埋める形で均等配置

## 出力形式
必ずJSON形式のみで出力。余計な説明文・マークダウン記法は一切不要。

{
  "posts": [
    {
      "type": "投稿タイプ名",
      "content": "投稿本文",
      "scheduled_hour": 投稿する時刻(0〜23の整数)
    }
  ]
}"""


def generate_tweets(
    today_followers: int,
    today_revenue: int,
    today_memo: str,
    yesterday_preview: str = "",
) -> list[dict]:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError(
            "エラー: ANTHROPIC_API_KEY が設定されていません。"
            ".env ファイルまたは GitHub Secrets を確認してください。"
        )

    client = anthropic.Anthropic(api_key=api_key)

    user_content = (
        f"今日のフォロワー数：{today_followers}人\n"
        f"今日の収益：{today_revenue}円\n"
        f"今日の出来事・気づき：{today_memo}\n"
        f"昨日の予告内容（あれば）：{yesterday_preview if yesterday_preview else 'なし'}\n\n"
        "この入力を元に、上記の原則と配分を守って24本の投稿を生成してください。"
    )

    try:
        message = client.messages.create(
            model="claude-opus-5",
            max_tokens=16000,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_content}],
        )
    except anthropic.APIConnectionError:
        raise RuntimeError(
            "エラー: Claude APIへの接続に失敗しました。インターネット接続を確認してください。"
        )
    except anthropic.AuthenticationError:
        raise RuntimeError(
            "エラー: APIキーが無効です。ANTHROPIC_API_KEY を確認してください。"
        )
    except anthropic.RateLimitError:
        raise RuntimeError(
            "エラー: APIのレート制限に達しました。しばらく待ってから再試行してください。"
        )
    except anthropic.APIError as e:
        raise RuntimeError(f"エラー: Claude APIで予期しないエラーが発生しました。詳細: {e}")

    if message.stop_reason == "refusal":
        raise RuntimeError(
            "エラー: 入力内容が安全性のチェックにかかり、生成が中断されました。\n"
            "入力する出来事・気づきの表現を変えてもう一度試してください。"
        )

    # 思考ブロックが先頭に来ることがあるため、テキストブロックだけを拾う。
    response_text = "".join(
        block.text for block in message.content if block.type == "text"
    ).strip()

    if not response_text:
        raise RuntimeError("エラー: AIの応答が空でした。もう一度試してください。")

    json_match = re.search(r"\{[\s\S]*\}", response_text)
    if not json_match:
        raise RuntimeError(
            "エラー: AIの応答からJSONを取得できませんでした。もう一度試してください。"
        )

    try:
        data = json.loads(json_match.group())
    except json.JSONDecodeError as e:
        raise RuntimeError(f"エラー: JSONの解析に失敗しました。詳細: {e}")

    posts = data.get("posts", [])
    if len(posts) != 24:
        print(f"警告: {len(posts)}本の投稿が生成されました（期待値: 24本）")

    normalized = []
    for post in posts:
        normalized.append(
            {
                "type": post.get("type", "不明"),
                "content": post.get("content", ""),
                "scheduled_hour": int(post.get("scheduled_hour", 12)),
                "posted": False,
            }
        )

    return normalized
