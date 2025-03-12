import asyncio

def run_async(coroutine):
    """
    新しいイベントループを作成してコルーチンを実行するヘルパー関数
    
    Args:
        coroutine: 実行するコルーチン
    
    Returns:
        コルーチンの実行結果
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coroutine)
    finally:
        loop.close() 