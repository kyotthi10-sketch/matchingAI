# Discord AI マッチングサービス

複数カテゴリー（友達/恋愛/ゲーム/ビジネス）に対応した、AIを活用した高度なマッチングサービスです。

## 🎯 主な機能

### ✅ 実装済み
1. **複数カテゴリー対応**
   - 👥 友達探し
   - 💕 恋愛マッチング
   - 🎮 ゲーム仲間
   - 💼 ビジネス・スキル

2. **質問ベース診断システム**
   - カテゴリーごとに30問の質問
   - A〜E の5段階評価
   - ランダム順序での質問提示

3. **AI分析（2つのオプション）**
   - 🤖 **Google Gemini API版**（推奨：無料枠が大きい）
     - Gemini 2.0 Flash 使用
     - 高速レスポンス（1-3秒）
     - 60 requests/minute（無料枠）
   - 🧠 **Anthropic Claude API版**
     - Claude Sonnet 4 使用
     - 高品質な分析
     - 従量課金制
   
   どちらも以下の機能に対応：
   - 性格・価値観の自動分析
   - 詳細なプロフィール生成
   - 相性度の高度計算
   - アイスブレイクメッセージ生成

4. **データベース管理**
   - SQLiteベースの永続化
   - カテゴリー別プロフィール管理
   - マッチング履歴の記録

### 🚧 開発中
- マッチング候補の自動検索
- マッチング受諾/拒否システム
- プライベートチャンネル自動作成
- マッチング通知機能
- レコメンデーションアルゴリズム

## 📋 必要要件

- Python 3.10 以上
- Discord Bot Token
- Anthropic API Key（オプション：AI機能用）

## 🚀 セットアップ

### 1. リポジトリのクローンと依存関係のインストール

```bash
# 仮想環境の作成
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 依存関係のインストール
pip install discord.py anthropic aiosqlite
```

### 2. Discord Bot の作成

1. [Discord Developer Portal](https://discord.com/developers/applications) にアクセス
2. "New Application" をクリック
3. Bot タブから Bot を追加
4. TOKEN をコピー
5. Privileged Gateway Intents で以下を有効化:
   - SERVER MEMBERS INTENT
   - MESSAGE CONTENT INTENT
6. OAuth2 → URL Generator で以下を選択:
   - Scopes: `bot`, `applications.commands`
   - Bot Permissions: `Send Messages`, `Manage Channels`, `Read Message History`
7. 生成されたURLでBotをサーバーに招待

### 3. AI APIキーの取得（オプション）

**どちらか一方、または両方を取得できます:**

#### オプションA: Google Gemini API（推奨：無料枠が大きい）

1. [Google AI Studio](https://aistudio.google.com/) にアクセス
2. Googleアカウントでログイン
3. 左メニューから「Get API key」をクリック
4. 「Create API key」をクリック
5. APIキーをコピー

**無料枠:** 60 requests/minute、1500 requests/day

#### オプションB: Anthropic Claude API

1. [Anthropic Console](https://console.anthropic.com/) にアクセス
2. API Keys からキーを生成
3. キーをコピー

**料金:** 従量課金制（$3-15 per million tokens）

※ API Keyがない場合でも基本的なマッチングは動作しますが、AI分析機能は制限されます。

### 4. 環境変数の設定

`.env` ファイルを作成:

```bash
# 必須
DISCORD_TOKEN=your_discord_bot_token_here

# AI API（どちらか一方、または両方を設定可能）
# Google Gemini API（推奨：無料枠が大きい）
GEMINI_API_KEY=your_gemini_api_key_here

# Anthropic Claude API（オプション）
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# その他の設定
GUILD_ID=0  # 特定のサーバーIDを指定（0で全サーバー）
AUTO_CLOSE_SECONDS=300  # 診断完了後のチャンネル自動削除時間
ADMIN_ROLE_ID=0  # 管理者ロールID
```

### 5. Bot の起動

#### 既存のシステム（ゲーム診断のみ）を使う場合:
```bash
python bot.py
```

#### 新しい統合マッチングシステムを使う場合:

**Gemini API版（推奨：無料枠が大きい）:**
```bash
python bot_multi_gemini.py
```

**Claude API版:**
```bash
python bot_multi.py
```

## 📖 使い方

### ユーザー向けコマンド

#### `/start`
診断を開始します。カテゴリーを選択して質問に回答していきます。

#### `/profile [category]`
自分のプロフィールを表示します。カテゴリーを指定しない場合は全カテゴリーを表示します。

#### `/match <category>`
指定したカテゴリーでマッチング相手を検索します。

### 管理者向けコマンド

#### `/stats`
サービスの利用統計を表示します。

## 🗂️ ファイル構成

```
.
├── bot.py                          # 既存のゲーム診断Bot
├── bot_multi.py                    # 統合マッチングBot（Claude版）
├── bot_multi_gemini.py             # 統合マッチングBot（Gemini版）★
├── db.py                           # 既存のDB（ゲーム診断用）
├── db_multi.py                     # 新しいDB（複数カテゴリー対応）
├── question.py                     # 既存の質問データ
├── questions_multi_category.py     # 新しい質問データ（全カテゴリー）
├── ai_matching.py                  # AIマッチングエンジン（Claude版）
├── ai_matching_gemini.py           # AIマッチングエンジン（Gemini版）★
├── app.db                          # 既存のデータベースファイル
├── app_multi.db                    # 新しいデータベースファイル
├── README.md                       # このファイル
└── GEMINI_SETUP.md                 # Gemini版セットアップガイド★
```

★ = Gemini API対応ファイル

## 🔧 カスタマイズ

### 質問の追加・変更

`questions_multi_category.py` を編集してください。各カテゴリーに30問ずつ定義されています。

```python
QUESTIONS_FRIENDSHIP = [
    {
        "id": 101,  # 一意のID
        "category": "communication_style",  # サブカテゴリー
        "text": "質問文",
        "choices": CHOICES_5  # A〜Eの5段階
    },
    # ...
]
```

### カテゴリーの追加

1. `CATEGORY_META` に新しいカテゴリーのメタデータを追加
2. `QUESTIONS_XXX` リストを作成
3. `CATEGORY_QUESTIONS` に登録

### マッチングアルゴリズムの調整

`ai_matching.py` の `AIMatchingEngine` クラスを編集してください。

## 🧪 テスト

AIマッチングエンジンのテスト:
```bash
python ai_matching.py
```

## 📊 データベーススキーマ

### users
- user_id (PK)
- discord_id (UNIQUE)
- username
- created_at
- reputation_score
- is_active

### user_profiles
- id (PK)
- user_id (FK)
- category
- bio
- interests (JSON)
- personality_traits (JSON)
- active_status
- created_at, updated_at

### answers
- user_id, category, question_id (PK)
- answer
- answered_at

### matches
- id (PK)
- user1_id, user2_id (FK)
- category
- match_score
- status (pending/accepted/rejected/closed)
- created_at, updated_at

## 🔐 セキュリティとプライバシー

- ユーザーデータは暗号化せずにローカルDBに保存されます
- 本番環境では適切な暗号化とアクセス制御を実装してください
- Discord IDは外部に公開しないでください
- 恋愛カテゴリーなど機密性の高いデータは特に注意が必要です

## 🚀 今後の実装予定

1. **マッチング機能の完成**
   - 自動マッチング検索
   - マッチング提案の通知
   - 受諾/拒否システム

2. **会話機能**
   - マッチング成立時のプライベートチャンネル作成
   - AIによる会話サポート
   - アイスブレイク提案

3. **高度な機能**
   - ユーザー評価システム
   - ブロック・報告機能
   - マッチング履歴の閲覧
   - プロフィール編集機能

4. **UI改善**
   - Webダッシュボード
   - グラフィカルなプロフィール表示
   - マッチング相手のプレビュー

## 🤝 貢献

プルリクエストは大歓迎です！大きな変更の場合は、まずissueを開いて変更内容を議論してください。

## 📄 ライセンス

MIT License

## 🙏 謝辞

- [discord.py](https://github.com/Rapptz/discord.py)
- [Anthropic Claude API](https://www.anthropic.com/)

## 📞 サポート

質問やバグ報告は Issue でお願いします。
