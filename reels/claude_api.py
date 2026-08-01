"""Claude API 呼び出しの共通処理（エラー処理・JSON抽出）。"""

import json
import os
import re

import anthropic

from . import config


def _get_client() -> anthropic.Anthropic:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError(
            "エラー: ANTHROPIC_API_KEY が設定されていません。"
            ".env ファイルを確認してください。"
        )
    return anthropic.Anthropic(api_key=api_key)


def ask_json(system_prompt: str, user_content: str) -> dict:
    """Claude に問い合わせて JSON を辞書で返す。"""
    client = _get_client()

    try:
        message = client.messages.create(
            model=config.MODEL,
            max_tokens=config.MAX_TOKENS,
            system=system_prompt,
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
            "テーマや追加指示の表現を変えてもう一度試してください。"
        )

    # 思考ブロックが先頭に来ることがあるため、テキストブロックだけを拾う。
    response_text = "".join(
        block.text for block in message.content if block.type == "text"
    ).strip()

    if not response_text:
        raise RuntimeError(
            "エラー: AIの応答が空でした。もう一度試してください。"
        )

    json_match = re.search(r"\{[\s\S]*\}", response_text)
    if not json_match:
        raise RuntimeError(
            "エラー: AIの応答からJSONを取得できませんでした。もう一度試してください。"
        )

    try:
        return json.loads(json_match.group())
    except json.JSONDecodeError as e:
        raise RuntimeError(f"エラー: JSONの解析に失敗しました。詳細: {e}")
