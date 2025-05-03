# parser/calculation.py

import re
import logging

def parse(lines):
    questions = []
    i = 0
    n = len(lines)
    q_index = 1

    header_pat = re.compile(r"\[T\]([A-Z]{2}\d{3})\s+([1-5])\s+5\s+([135])")
    answer_pat = re.compile(r"\[D\](.*?)\[D/\]", re.DOTALL)

    while i < n:
        line = lines[i].strip()
        if "[T]" in line:
            header_match = header_pat.search(line)
            if not header_match:
                logging.warning(f"计算题 第{q_index}题 题头格式错误：{line}")
                i += 1
                continue

            code, level_code, difficulty_code = header_match.groups()
            q_lines = []

            # 处理题干是否在 [T]...[T/] 同一行
            if "[T/]" in line:
                start_idx = line.find("]") + 1
                end_idx = line.find("[T/]")
                inline = line[start_idx:end_idx].strip()
                if inline:
                    q_lines.append(inline)
                i += 1
            else:
                i += 1
                while i < n and "[T/]" not in lines[i]:
                    q_lines.append(lines[i].strip())
                    i += 1
                if i < n and "[T/]" in lines[i]:
                    end_line = lines[i].replace("[T/]", "").strip()
                    if end_line:
                        q_lines.append(end_line)
                    i += 1

            question_text = " ".join(q_lines).strip()

            # 提取计算答案
            correct_answer = ""
            if i < n:
                amatch = answer_pat.search(lines[i])
                if amatch:
                    correct_answer = amatch.group(1).strip()
                    i += 1
                else:
                    logging.warning(f"计算题 第{q_index}题 答案格式错误或缺失：{lines[i]}")
                    i += 1

            questions.append({
                "code": code,
                "level_code": level_code,
                "type_code": "5",
                "difficulty_code": difficulty_code,
                "question_text": question_text,
                "correct_answer": correct_answer
            })
            q_index += 1
        else:
            i += 1

    return questions
