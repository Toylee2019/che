# parser/single_choice.py

import re
import logging

def parse(lines):
    results = []
    i = 0
    question_index = 1

    header_pat = re.compile(r"\[T\]([A-Z]{2}\d{3})\s+([1-5])\s+1\s+([135])")

    while i < len(lines):
        line = lines[i].strip()
        if "[T]" in line:
            match = header_pat.search(line)
            if not match:
                i += 1
                continue
            code, level_code, difficulty_code = match.groups()
            i += 1

            q_lines = []
            while i < len(lines) and "[T/]" not in lines[i]:
                q_lines.append(lines[i].strip())
                i += 1
            if i < len(lines) and "[T/]" in lines[i]:
                tail = lines[i].replace("[T/]", "").strip()
                if tail:
                    q_lines.append(tail)
                i += 1

            question_text = " ".join(q_lines).strip()

            answer = None
            while i < len(lines):
                ans_line = lines[i].strip()
                if "[D]" in ans_line and "[D/]" in ans_line:
                    match = re.search(r"\[D\](.*?)\[D/\]", ans_line)
                    if match:
                        answer = match.group(1).strip()
                    break
                i += 1

            if not answer or not re.fullmatch(r"[A-D]", answer):
                logging.error(f"单选题 编码 {code} {level_code} 1 {difficulty_code} 答案格式错误: {answer or ''}")
                answer = None

            results.append({
                "code": code,
                "level_code": level_code,
                "type_code": "1",
                "difficulty_code": difficulty_code,
                "question_text": question_text,
                "answer": answer
            })
            question_index += 1
        else:
            i += 1
    return results
