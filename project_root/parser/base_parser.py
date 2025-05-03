import logging

def read_block(lines, start_index, end_marker, question_index, part_name):
    """
    从 lines 列表中，从 start_index 行开始读取，直到遇到包含 end_marker 的行结束，
    将所有读取的行合并为一个字符串返回，同时返回新的索引位置（结束行的下一行索引）。
    
    参数:
      lines: 所有文本行的列表
      start_index: 起始行索引
      end_marker: 结束标记，例如 "[D/]" 或 "[S/]"
      question_index: 当前题目序号（用于日志记录）
      part_name: 当前块名称（例如 "答案" 或 "评分标准"），用于日志提示
      
    返回：
      block_str: 合并后的字符串
      new_index: 结束行的下一行索引
    如果没有找到结束标记，则记录错误并返回已读部分及原始索引（便于后续处理）。
    """
    block_lines = []
    i = start_index
    n = len(lines)
    while i < n:
        line = lines[i]
        block_lines.append(line)
        if end_marker in line:
            return (" ".join(block_lines).strip(), i + 1)
        i += 1
    logging.error(f"题目 第{question_index}题 {part_name}块中缺少结束标记 {end_marker}. 已读取内容: {' '.join(block_lines).strip()}")
    return (" ".join(block_lines).strip(), start_index)
