# format_utils.py

import re
from clean_utils import clean_inline_blocks

def format_question_preview(q, job, level):
    type_map = {
        "single_choice": "单项选择题",
        "multiple_choice": "多项选择题",
        "judgment": "判断题",
        "short_answer": "简答题",
        "calculation": "计算题"
    }

    zh_type = type_map.get(q.get("类别", ""), q.get("类别", "未知"))
    raw_text = q.get("question_text", "")
    raw_text = clean_inline_blocks(raw_text)

    code = q.get("code", "N/A")
    answer = q.get("answer", "未设置")
    rubric = q.get("rubric", "")

    if q.get("类别") in ("single_choice", "multiple_choice"):
        # 提取题干与选项
        option_start_index = -1
        for token in ["A、", "A.", "A．", "A)", "[A]"]:
            option_start_index = raw_text.find(token)
            if option_start_index != -1:
                break

        if option_start_index != -1:
            question_stem = raw_text[:option_start_index].strip()
            options_part = raw_text[option_start_index:]
            option_lines = re.findall(r"[A-D][、\.\．\)]\s?.*?(?=(?:[A-D][、\.\．\)]|$))", options_part)
            options_text = "\n".join(option_lines).strip()
        else:
            question_stem = raw_text.strip()
            options_text = "(未检测到选项)"

        return (
            f"认定点: {code}\n"
            f"工种: {job}\n"
            f"级别: {level}\n"
            f"题型: {zh_type}\n"
            f"题干: {question_stem}\n"
            f"选项:\n{options_text}\n"
            f"答案: {answer}"
        )

    elif q.get("类别") == "judgment":
        return (
            f"认定点: {code}\n"
            f"工种: {job}\n"
            f"级别: {level}\n"
            f"题型: {zh_type}\n"
            f"题干: {raw_text.strip()}\n"
            f"答案: {answer}"
        )

    elif q.get("类别") in ("short_answer", "calculation"):
        correct_answer = q.get("correct_answer", "(未提供参考答案)")
        return (
            f"认定点: {code}\n"
            f"工种: {job}\n"
            f"级别: {level}\n"
            f"题型: {zh_type}\n"
            f"题干: {raw_text.strip()}\n"
            f"参考答案: {correct_answer}"
        )

    else:
        return (
            f"认定点: {code}\n"
            f"工种: {job}\n"
            f"级别: {level}\n"
            f"题型: {zh_type}\n"
            f"题干: {raw_text.strip()}\n"
            f"答案: {answer}"
        )
