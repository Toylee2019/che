import re

class BaseParser:
    def __init__(self):
        pass

    def parse_content_blocks(self, paragraphs):
        """
        接受一个段落列表，支持：
        1) 行内标签 [T]…[T/]、[D]…[D/]、[S]…[S/]
        2) 跨行标签 [T]…[T/]、[D]…[D/]、[S]…[S/]
        最后会 flush 未闭合的 buffer。
        返回 {'T':题干, 'D':答案, 'S':解析/评分标准}
        """
        result = {'T': '', 'D': '', 'S': ''}
        current = None
        buffer = []

        for para in paragraphs:
            text = para.text.strip() if hasattr(para, 'text') else str(para).strip()

            # 1. 优先行内标签
            for tag in ('T', 'D', 'S'):
                m = re.search(rf'\[{tag}\](.*?)\[{tag}/\]', text, re.S)
                if m:
                    result[tag] = m.group(1).strip()
                    current = None
                    buffer = []
                    break
            else:
                # 2. 跨行标签开始/结束
                if '[T]' in text:
                    current = 'T'
                    buffer = [text.replace('[T]', '').strip()]
                elif '[T/]' in text:
                    buffer.append(text.replace('[T/]', '').strip())
                    result['T'] = '\n'.join(buffer).strip()
                    current = None
                    buffer = []
                elif '[D]' in text:
                    current = 'D'
                    buffer = [text.replace('[D]', '').strip()]
                elif '[D/]' in text:
                    buffer.append(text.replace('[D/]', '').strip())
                    result['D'] = '\n'.join(buffer).strip()
                    current = None
                    buffer = []
                elif '[S]' in text:
                    current = 'S'
                    buffer = [text.replace('[S]', '').strip()]
                elif '[S/]' in text:
                    buffer.append(text.replace('[S/]', '').strip())
                    result['S'] = '\n'.join(buffer).strip()
                    current = None
                    buffer = []
                elif current:
                    buffer.append(text)

        # 3. flush 未闭合的多行 buffer
        if current and buffer:
            result[current] = '\n'.join(buffer).strip()

        return result
