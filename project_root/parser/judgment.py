# parser/judgment.py

import re
import logging

def parse(content_lines):
    """
    支持格式：
      803.[T]AA002	2	3	1
      (   )题干文字。[T/]
      [D]×[D/]
      [S]正确答案内容[S/]
    """
    questions = []
    question_index = 0
    i = 0
    n = len(content_lines)

    header_pat = re.compile(r"\[T\]([A-Z]{2}\d{3})\s+(\d)\s+(\d)\s+(\d)")
    answer_pat = re.compile(r"\[D\]([√×])\[D/\]")
    correct_pat = re.compile(r"\[S\](.+?)\[S/\]")

    while i < n:
        line = content_lines[i].strip()
        if "[T]" in line:
            question_index += 1
            header_match = header_pat.search(line)
            if not header_match:
                logging.error(f"判断题 第{question_index}题 题头格式错误: {line}")
                i += 1
                continue
            code, level_code, type_code, difficulty = header_match.groups()

            # 提取题干直到 [T/] 出现
            question_text_parts = []
            if "[T/]" in line:
                content_after_header = line.split("]")[-1].replace("[T/]", "").strip()
                if content_after_header:
                    question_text_parts.append(content_after_header)
            else:
                i += 1
                while i < n and "[T/]" not in content_lines[i]:
                    question_text_parts.append(content_lines[i].strip())
                    i += 1
                if i < n:
                    last_line = content_lines[i].replace("[T/]", "").strip()
                    if last_line:
                        question_text_parts.append(last_line)
            question_text = " ".join(question_text_parts)
            i += 1

            # 答案
            answer = ""
            if i < n:
                ans_match = answer_pat.search(content_lines[i])
                if ans_match:
                    answer = ans_match.group(1)
                else:
                    logging.error(f"判断题 第{question_index}题 答案格式错误，未提取到 [D]√[D/] 或 [D]×[D/]，行: {content_lines[i]}")
                i += 1
            else:
                logging.error(f"判断题 第{question_index}题 缺失答案标记行")

            # 正确答案（当答案为 × 时必须有）
            correct_answer = ""
            if answer == "×":
                if i < n:
                    smatch = correct_pat.search(content_lines[i])
                    if smatch:
                        correct_answer = smatch.group(1).strip()
                        i += 1
                    else:
                        logging.error(f"判断题 第{question_index}题 答案为×但未识别到正确答案 [S] 标签，行: {content_lines[i]}")
                else:
                    logging.error(f"判断题 第{question_index}题 答案为×但缺失正确答案部分")

            # 保存
            questions.append({
                "code": code,
                "level_code": level_code,
                "type_code": type_code,
                "difficulty_code": difficulty,
                "question_text": question_text,
                "answer": answer,
                "correct_answer": correct_answer
            })
        else:
            i += 1

    # 校验每个认定点是否含两个答案（√ 和 ×）
    group = {}
    for q in questions:
        group.setdefault(q["code"], []).append(q)
    for code, lst in group.items():
        if len(lst) != 2:
            logging.error(f"判断题 认定点 {code} 必须有 2 道题, 当前数量: {len(lst)}")
        else:
            answers = [q["answer"] for q in lst]
            if set(answers) != {"√", "×"}:
                if len(set(answers)) == 1:
                    only_answer = answers[0]
                    logging.error(f"判断题 认定点 {code} 下出题要求答案应为1对1错，但当前两题答案都为：{only_answer}。")
                else:
                    logging.error(f"判断题 认定点 {code} 答案配对异常，当前答案为：{answers}")

    return questions
