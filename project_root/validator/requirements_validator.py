# validator/requirements_validator.py

from config.requirements import EXPECT_COUNTS
from collections import defaultdict

def validate_recognition(qs, level_name):
    """
    针对同一认定点码（recognition_code）及指定级别，校验题量和判断题真/假及解析要求。
    qs: list of dict, each dict 包含 keys: recognition_code, question_type, answer, answer_explanation
    level_name: "初级工"、"中级工" 等
    返回错误信息列表。
    """
    errors = []
    rec = qs[0]["recognition_code"] if qs else "未知"
    # 1. 拿到期望配置
    exp = EXPECT_COUNTS.get(level_name)
    if exp is None:
        errors.append(f"未配置级别 {level_name} 的题量标准，跳过校验")
        return errors

    # 2. 统计各题型数量
    counts = defaultdict(int)
    for q in qs:
        counts[q["question_type"]] += 1

    # 3. 数量校验
    for qt in ["单选", "多选", "判断"]:
        actual = counts.get(qt, 0)
        expected = exp.get(qt, 0)
        if actual != expected:
            errors.append(f"认定点 {rec}: {qt} 数量不符，期望 {expected}，实际 {actual}")

    # 4. 判断题真/假及解析校验
    jd_expected = exp.get("判断", 0)
    if jd_expected > 0:
        jds    = [q for q in qs if q["question_type"] == "判断"]
        trues  = [q for q in jds if q.get("answer") == "√"]
        falses = [q for q in jds if q.get("answer") == "×"]

        if len(trues) < 1:
            errors.append(f"认定点 {rec}: 判断题中“√”题数不足")
        if len(falses) < 1:
            errors.append(f"认定点 {rec}: 判断题中“×”题数不足")
        for q in falses:
            if not q.get("answer_explanation"):
                errors.append(f"认定点 {rec}: 判断题“×”题缺少解析")

    return errors
