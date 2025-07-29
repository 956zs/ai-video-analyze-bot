import re

async def splitmsg(text: str, max_length: int = 2000):
    """
    將長訊息分割成多個較短的區塊，同時避免在程式碼區塊內分割。

    Args:
        text (str): 要分割的原始文字。
        max_length (int): 每個區塊的最大長度。

    Returns:
        list[str]: 分割後的訊息區塊列表。
    """
    chunks = []
    current_chunk = ""
    in_code_block = False
    lines = text.split('\n')

    for line in lines:
        # 檢查是否為程式碼區塊的開頭或結尾
        if line.strip().startswith('```'):
            in_code_block = not in_code_block
        
        # 如果將此行加入目前的區塊會超過最大長度，且不在程式碼區塊內
        if len(current_chunk) + len(line) + 1 > max_length and not in_code_block:
            if current_chunk:
                chunks.append(current_chunk)
            current_chunk = line
        else:
            if current_chunk:
                current_chunk += '\n' + line
            else:
                current_chunk = line

    # 加入最後剩餘的區塊
    if current_chunk:
        chunks.append(current_chunk)

    return chunks