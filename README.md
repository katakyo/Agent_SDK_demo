# OpenAI Agents SDK サンプルプロジェクト

このプロジェクトは、OpenAI Agents SDKを使用した簡単なデモアプリケーションです。Streamlit UIを通じて複数のエージェントを設定・実行できます。

## 概要

OpenAI Agents SDKを使用して、GPT-4やGPT-3.5-turboモデルを活用したインタラクティブなエージェントを作成できます。Streamlit UIでエージェントの設定を簡単にカスタマイズすることができます。

## 特徴

- Docker/Docker Composeを使用した簡単なセットアップ
- 環境変数を使用したAPIキーの安全な管理
- Python 3.11環境
- Streamlit UIでエージェント設定の簡単カスタマイズ
  - エージェント名の設定
  - 指示（プロンプト）の編集
  - モデルの選択（GPT-3.5-turbo、GPT-4など）
  - 複数のエージェントプリセット

## セットアップ方法

### 前提条件

- Docker
- Docker Compose

### 実行方法

1. `.env`ファイルにOpenAI APIキーを設定します：

```
OPENAI_API_KEY=your_api_key_here
```

2. Docker Composeでアプリケーションを起動します：

```bash
docker-compose up --build
```

3. ブラウザで以下のURLにアクセスしてStreamlit UIを開きます：

```
http://localhost:8501
```

## プロジェクト構成

```
.
├── Dockerfile          # Python 3.11のDockerイメージ設定
├── README.md           # プロジェクト説明（このファイル）
├── app.py              # Streamlit UIアプリケーション
├── docker-compose.yml  # Docker Compose設定
├── .env                # 環境変数設定（APIキーなど）
└── main.py             # コマンドライン用のサンプルスクリプト
```

## Streamlit UIの使用方法

1. サイドバーでエージェントの設定を行います：
   - エージェント名
   - 指示（システムプロンプト）
   - 使用するモデル

2. プリセットから選択するか、カスタム設定を行います

3. チャット入力欄にメッセージを入力してエージェントと対話します

## OpenAI Agents SDKについて

OpenAI Agents SDKは、マルチエージェントワークフローを構築するための軽量かつ強力なフレームワークです。詳細については[公式ドキュメント](https://openai.github.io/openai-agents-python/)を参照してください。 