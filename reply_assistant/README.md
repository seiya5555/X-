# X リプ案アシスタント（GitHub Actions × Gemini）

## できること
- `reply_assistant/candidates.json` に登録された公開Xポストの本文から、Gemini 2.5 Flash-Liteで**返信案を作成**する
- 毎時17分（UTC、JSTでも毎時17分）に最大20件を**1 APIリクエストでまとめて**処理する
- 重複するIDの再処理を防ぎ、`results.json` と `drafts.md` に保存する
- 返信案は人間が確認してXアプリから手動で送信する。**Xへの自動投稿は一切しない**

## 最初の設定（1回だけ）
1. https://aistudio.google.com/apikey でGemini APIキーを作る。無料で使うなら**請求先を登録していないFree Tierのプロジェクト**を使い、AI StudioのRate limitsで`gemini-2.5-flash-lite`のRPD/RPM/TPMを確認する（Google AI Proのアプリ枠とは別）。
2. このGitHubリポジトリの **Settings → Secrets and variables → Actions → New repository secret** で、Nameを`GEMINI_API_KEY`、ValueをAPIキーとして登録。**ソースコードや候補JSONには書かない。**
3. `reply_assistant/candidates.json`を編集。以下のように公開ポストのURLと本文を追加。
4. Actions → **X Reply Draft Assistant** → **Run workflow** でテスト。約定時刻の自動実行も有効。
5. `reply_assistant/drafts.md`で返信案を確認して、Xで**自分で送信**する。

候補の例（例文は実際のユーザーの投稿ではありません）:

```json
[
  {
    "id": "unique-post-001",
    "url": "https://x.com/example/status/1234567890123456789",
    "text": "生成AIを仕事に導入したいけど、最初に何から始めればいいのかわからない。",
    "topic": "AI・仕事効率化"
  }
]
```

- `id`は候補ごとに一意にする。
- URLのみでは本文を取得しないため、**text欄にポスト本文を貼ることが必要**。
- 候補が0件ならGemini APIは呼び出さない。
- 20件の候補は原則1回のGeminiリクエスト。上限超過時は失敗してキューを残す（課金に自動切替しない）。
- 公開リポジトリなので、候補JSONと生成結果は公開される。非公開運用したい場合は**プライベートリポジトリに移す**こと。

## 費用と制約
- GeminiのFree Tierは対象モデルの入力・出力が無料。ただしRPD/RPM/TPMはアカウントごとに異なる。
- 公開リポジトリでの標準GitHub-hosted Actionsは原則無料。非公開リポジトリではアカウントの無料枠と合算。
- X APIは使用しないため**X API利用料は0円**。Xの投稿を勝手に検索・取得したり、自動リプする機能はない。
- GitHubの定期実行は時間どおりの起動を保証せず、状況により遅延/スキップの可能性がある。
- Xの自動化規約を確認し、無差別な勧誘や大量リプ回りは行わない。

## 関連公式情報
- Gemini料金: https://ai.google.dev/gemini-api/docs/pricing
- Gemini枠: https://ai.google.dev/gemini-api/docs/rate-limits
- X自動化: https://help.x.com/en/rules-and-policies/x-automation
