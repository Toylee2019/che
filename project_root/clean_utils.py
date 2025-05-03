# clean_utils.py

import re

def clean_inline_blocks(text: str) -> str:
    """
    清理 [A] xxx [/A] 中的水平空白（空格、tab、全角空格），保留标签
    """
    def clean_inner(m):
        code = m.group(1)
        content = m.group(2)
        cleaned = re.sub(r"[ \t\u3000]+", "", content)
        return f"[{code}]{cleaned}[/{code}]"

    return re.sub(r"\[([A-D])\](.*?)\[\/\1\]", clean_inner, text, flags=re.DOTALL)


def extract_clean_answer(text: str) -> str:
    """
    提取 [D]...[/D] 中的内容，并移除其中的所有水平空白字符
    """
    match = re.search(r"\[D\](.*?)\[D/\]", text, re.DOTALL)
    if match:
        return re.sub(r"[ \t\u3000\r\n]+", "", match.group(1)).strip()
    return ""
