# Instagram リール台本生成システム

Obsidian に溜めた自分の知識・実績を土台に、競合の伸びパターンを踏まえた
リール台本を生成し、投稿後の実績で PDCA を回すためのシステムです。

---

## 全体の流れ

```
[Obsidian Vault：あなたの全知識・過去実績]
        │
        ▼
① 競合リールを記録        competitor
        │
        ▼
② 伸びパターンを分析      analyze     → Vault に分析レポートを保存
        │
        ▼
③ リール台本を生成        script      → Vault に台本ノートを保存
        │
        ▼
④ 撮影・編集・投稿（手動）
        │
        ▼
⑤ 投稿実績を記録          record
        │
        ▼
⑥ 振り返りで改善点を出す  review
        │
        └──────→ ②③ に自動で反映（PDCA）
```

②の分析結果と⑤の実績は、③の台本生成時に**自動で読み込まれます**。
使い続けるほど「自分のアカウントで何が効くか」に最適化されていきます。

---

## VS Code での始め方

初回だけ以下を順番に実行します。2回目以降は「4. 実行する」だけで動きます。

### 0. リポジトリを手元に落とす

VS Code のターミナル（`Ctrl + @` / Mac は `Cmd + @`）を開いて実行します。

```bash
git clone https://github.com/seiya5555/x-.git
cd x-
git checkout claude/cloud-code-usage-03lju6
```

すでに clone 済みなら、最新を取り込むだけで構いません。

```bash
git pull origin claude/cloud-code-usage-03lju6
```

### 1. 仮想環境を作る

プロジェクト専用の Python 環境を作ります。パソコン全体を汚さずに済みます。

```bash
python -m venv .venv
```

**Mac / Linux**

```bash
source .venv/bin/activate
```

**Windows（PowerShell）**

```powershell
.venv\Scripts\Activate.ps1
```

ターミナルの行頭に `(.venv)` と出れば成功です。

> VS Code 右下に「この仮想環境を選択しますか？」と出たら「はい」を押してください。
> 出ない場合は `Ctrl + Shift + P` →「Python: Select Interpreter」→ `.venv` を選びます。

### 2. パッケージを入れる

```bash
pip install -r requirements.txt
```

### 3. `.env` を作る

```bash
cp .env.example .env
```

VS Code のサイドバーから `.env` を開き、最低限この2つを埋めます。

```
ANTHROPIC_API_KEY=sk-ant-...
OBSIDIAN_VAULT_PATH=/Users/あなたの名前/Documents/Vault名
```

- **API キー** は https://console.anthropic.com の「API Keys」で発行します
- **Vault のパス** は Obsidian で Vault を右クリック →「フォルダで表示」から辿れます
  - Windows は区切りを `/` にしてください（例: `C:/Users/yourname/Documents/MyVault`）

`.env` は `.gitignore` に入っているので、GitHub には上がりません。

### 4. 実行する

```bash
python -m reels.main script
```

テーマを聞かれるので入力すれば、台本が生成されて Obsidian に保存されます。

---

## つまずいたときは

| 症状 | 原因と対処 |
|---|---|
| `ModuleNotFoundError: No module named 'anthropic'` | 仮想環境が有効になっていません。`(.venv)` が行頭にあるか確認し、なければ有効化コマンドを再実行してください |
| `ANTHROPIC_API_KEY が設定されていません` | `.env` が未作成か、キーが空です。`.env`（`.env.example` ではない）を確認してください |
| `OBSIDIAN_VAULT_PATH のフォルダが見つかりません` | パスの打ち間違いです。Windows は区切りを `/` にしてください |
| `python` が見つからない | `python3` に置き換えて実行してください（Mac に多いです） |
| 実行はできるが「Vault が未設定」と警告が出る | Vault なしでも動きますが、過去ノートを参照できないため台本の精度が大きく落ちます。設定を強く推奨します |

コマンド一覧は以下で確認できます。

```bash
python -m reels.main --help
```

---

## 使い方

### ① 競合リールを記録する

```bash
python -m reels.main competitor
```

伸びている競合リールの情報を対話形式で入力します。
数値が分からない項目は空欄で Enter を押せばスキップできます。

**入力のコツ**：`冒頭2秒で何を言っていたか` と `なぜ最後まで見てしまったか`
が分析の質を決めます。ここだけは丁寧に埋めてください。

5件以上たまると分析の精度が上がります。

### ② 伸びパターンを分析する

```bash
python -m reels.main analyze
```

蓄積した競合データから、再現可能な「伸びパターン」を抽出します。
各パターンには**自分のアカウントに適用できるか**の判定（high / mid / low）と
その理由が付きます。分析レポートは Vault の `競合分析` フォルダに保存されます。

適用度が low のパターンと、`真似してはいけないパターン` は
台本生成時に自動で除外されます。

### ③ リール台本を生成する

```bash
python -m reels.main script
```

テーマを入力すると、以下を含む台本が生成されます。

| 出力 | 内容 |
|---|---|
| フック候補 | 異なる型で3案。それぞれ「なぜ指が止まるか」付き |
| シーン割 | 秒数・ナレーション・テロップ・映像指示の表 |
| ループ設計 | 最後から最初へどうつなげるか |
| キャプション | 投稿本文とハッシュタグ |
| 設計の根拠 | どの伸びパターン・どの過去ノートを使ったか |
| 自己採点 | フック強度（10点満点）・離脱リスク・改善案 |

台本は Vault の `リール台本` フォルダに Markdown で保存されます。
ノート末尾には投稿後の実績を書き込む欄が付いています。

引数で直接指定することもできます。

```bash
python -m reels.main script --theme "副業を始めて最初にやるべきこと" --duration 30
```

### ④ 投稿実績を記録する

```bash
python -m reels.main record
```

投稿したリールの結果を記録します。この実績は次回以降の台本生成に
自動で反映されます。

### ⑤ 振り返って改善点を出す

```bash
python -m reels.main review
```

蓄積した実績から、伸びた要因・伸びなかった要因を分析し、
**次の投稿で試すべき最優先の1点**を提示します。

---

## ファイル構成

```
reels/
├── main.py               # CLI エントリポイント
├── script_generator.py   # リール台本の生成（中核）
├── competitor.py         # 競合データの記録・伸びパターン分析
├── performance.py        # 投稿実績の記録・振り返り
├── obsidian.py           # Vault の検索とノート書き出し
├── claude_api.py         # Claude API 呼び出しの共通処理
├── storage.py            # JSON ファイルの読み書き
├── config.py             # 設定・パス
└── data/
    ├── competitors.json  # 競合リールの記録
    ├── patterns.json     # 分析済みの伸びパターン（自動生成）
    └── performance.json  # 自分の投稿実績
```

---

## Obsidian 連携の仕組み

Obsidian の Vault は**ただの Markdown フォルダ**なので、MCP サーバーを
使わずに直接読み書きしています。追加の設定は不要です。

台本生成時は、テーマから抽出したキーワードで Vault 全体を検索し、
関連度の高いノート（最大12件）を材料として渡します。
日本語は助詞で区切ってキーワード化するため、
「副業を始めて最初にやるべきこと」→ `副業` `最初` のように分解されます。

`.obsidian` `.trash` などの管理用フォルダは検索対象外です。

---

## 注意事項

- **競合データは手動入力です。** Instagram の公式 API では他人のアカウントの
  数値を取得できません。非公式なスクレイピングは利用規約違反となり
  アカウント凍結のリスクがあるため、このシステムでは行いません。
- 生成された台本は**そのまま使わず必ず確認してください。** 特に数字や実績に
  関する記述は、事実と合っているかを投稿前にチェックしてください。
- `data/` 配下の JSON は蓄積データです。消すと学習内容が失われます。
- `.env` は絶対に Git にコミットしないでください（`.gitignore` に含まれています）。
