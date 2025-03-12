import os
from dotenv import load_dotenv

def load_config():
    """
    .envファイルから設定を読み込み、APIキーを取得する
    
    Returns:
        str: OpenAI APIキー
    """
    # .envファイルのパスを指定して読み込む
    dotenv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env')
    load_dotenv(dotenv_path)
    
    # 環境変数からAPIキーを取得
    api_key = os.getenv("OPENAI_API_KEY")
    return api_key

# 利用可能なモデルのリスト
AVAILABLE_MODELS = ["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo"]

# デフォルト設定
DEFAULT_INSTRUCTIONS = "You are a helpful assistant, always respond in Japanese"
DEFAULT_AGENT_NAME = "Assistant"

# エージェントプリセット
AGENT_PRESETS = {
    "日本語アシスタント": {
        "name": "日本語アシスタント",
        "instructions": "あなたは役立つアシスタントです。常に日本語で応答してください。",
        "model": "gpt-3.5-turbo"
    },
    "英語翻訳者": {
        "name": "英語翻訳者",
        "instructions": "あなたは日本語を英語に翻訳するエキスパートです。自然で流暢な英語に翻訳してください。",
        "model": "gpt-3.5-turbo"
    },
    "プログラミングヘルパー": {
        "name": "プログラミングヘルパー",
        "instructions": "あなたはプログラミングの専門家です。コードの説明、デバッグ、最適化のアドバイスを日本語で提供してください。",
        "model": "gpt-3.5-turbo"
    }
} 