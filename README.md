# X 自動投稿システム
「SNSアフィリエイトで100万円稼ぐまでのリアル成長記録」を毎日24本、1時間ごとに自動投稿するシステムです。

> **Instagram リール台本生成システムも同梱しています。**
> Obsidian の知識を元に、競合分析 → 台本生成 → 実績記録で PDCA を回す仕組みです。
> 使い方は [`reels/README.md`](reels/README.md) を参照してください。

---

## 仕組みの概要

```
毎朝（手動）
  ↓ GitHub の daily.yml を手動トリガー
  ↓ フォロワー数・収益・気づきを入力
  ↓ Claude API が24本の投稿文を一括生成
  ↓ tweets_queue.json に保存してコミット

毎時間（自動）
  ↓ post.yml が自動起動（毎時:05）
  ↓ tweets_queue.json から対象時刻の投稿を取得
  ↓ Twitter API v2 で投稿
  ↓ キューを更新してコミット
```

---

## セットアップ

### 1. リポジトリのクローン

```bash
git clone https://github.com/your-username/your-repo.git
cd your-repo
```

### 2. 依存パッケージのインストール（ローカル動作確認用）

```bash
pip install -r requirements.txt
```

### 3. 環境変数の設定

`.env.example` をコピーして `.env` を作成します。

```bash
cp .env.example .env
```

`.env` を編集して各APIキーを入力します。

```
ANTHROPIC_API_KEY=sk-ant-...
TWITTER_API_KEY=...
TWITTER_API_SECRET=...
TWITTER_ACCESS_TOKEN=...
TWITTER_ACCESS_SECRET=...
```

### 4. GitHub Secrets の設定

GitHub リポジトリの **Settings → Secrets and variables → Actions** で以下を登録します。

| Secret 名 | 内容 |
|---|---|
| `ANTHROPIC_API_KEY` | Anthropic の APIキー |
| `TWITTER_API_KEY` | Twitter Consumer Key |
| `TWITTER_API_SECRET` | Twitter Consumer Secret |
| `TWITTER_ACCESS_TOKEN` | Twitter Access Token |
| `TWITTER_ACCESS_SECRET` | Twitter Access Token Secret |

### 5. Twitter API の権限確認

Twitter Developer Portal で **Read and Write** 権限が付与されていることを確認してください。  
Read Only の場合は投稿できません。

---

## 毎日の使い方

### 毎朝の操作（約2分）

1. GitHub リポジトリを開く
2. **Actions タブ** → 「X Daily Tweet Generator」を選択
3. **「Run workflow」** をクリック
4. 以下の3項目を入力して実行

| 入力項目 | 説明 | 例 |
|---|---|---|
| 今日のフォロワー数 | 現在のフォロワー数（数字） | `152` |
| 今日の収益額（円） | 本日の収益（数字） | `320` |
| 今日の出来事・気づき | 1〜2行の自由テキスト | `初めてクリックが出た。小さいけど嬉しかった` |

実行後、約30〜60秒で投稿が生成され `tweets_queue.json` にコミットされます。

### 自動投稿スケジュール

`post.yml` が毎時:05に自動起動し、スケジュールされた投稿を順次投稿します。  
投稿時刻は Claude が以下の時間帯に自動分配します。

| 時間帯 | 時刻 |
|---|---|
| 朝 | 7時・8時・9時 |
| 昼 | 12時・13時 |
| 夕方〜夜 | 17時・18時・19時・20時 |
| 深夜 | 21時・22時・23時 |
| 早朝 | 0時・1時・6時 |

---

## ローカルでのテスト

```bash
# 対話入力モード
python main.py

# 環境変数で入力（CI相当）
FOLLOWERS=100 REVENUE=500 TODAY_MEMO="今日は初リプをもらった" AUTO_CONFIRM=true python main.py

# キューの確認（投稿は実行しない）
cat tweets_queue.json | python -m json.tool

# 次の投稿を手動実行
python scheduler.py
```

---

## ファイル構成

```
.
├── main.py              # 起動・入力受付・全体制御
├── generator.py         # Claude API で24本の投稿文を生成
├── poster.py            # Twitter API v2 で投稿を実行
├── scheduler.py         # キュー管理・スケジュール投稿
├── memory.py            # 昨日の予告内容を保存・読込
├── tweets_queue.json    # 本日の投稿キュー（自動更新）
├── memory.json          # 前日の予告内容（自動更新）
├── requirements.txt     # Python 依存パッケージ
├── .env.example         # 環境変数テンプレート
└── .github/
    └── workflows/
        ├── daily.yml    # 投稿生成ワークフロー（手動トリガー）
        └── post.yml     # 毎時投稿ワークフロー（自動）
```

---

## 投稿の種類と配分

| タイプ | 本数 | 内容 |
|---|---|---|
| リアル報告型 | 4本 | フォロワー数・収益の正直な報告 |
| 葛藤・本音型 | 5本 | 不安・しんどさをそのまま言語化 |
| 共感・あるある型 | 4本 | 副業初心者の悩みを代弁 |
| 学び・気づき型 | 5本 | 今日の等身大の発見 |
| 予告・伏線型 | 3本 | 翌日への伏線・期待を作る |
| 読者巻き込み型 | 2本 | 読者への感謝・共犯者意識 |
| CTA型 | 1本 | プロフィール・LINE誘導 |

---

## 注意事項

- Twitter API の無料プランは月1,500ツイートまでです（24本/日 × 30日 = 720本 → 余裕あり）
- 同一内容の重複投稿は Twitter API がエラーを返します。再生成してください
- `tweets_queue.json` と `memory.json` はリポジトリに含めてください（Actions 間でデータを共有するため）
- `.env` ファイルは絶対に Git にコミットしないでください（`.gitignore` に含まれています）
