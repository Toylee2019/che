# preprocessor.py

from docx import Document
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
import os
import logging

def get_paragraph_text_with_line_breaks(para):
    """
    遍历段落底层 XML 节点，将 <w:t> 文本、<w:br> 换行符、<w:tab> 制表符拼接成字符串。
    """
    texts = []
    for child in para._element.iter():
        tag = child.tag
        if tag.endswith("}t"):
            if child.text:
                texts.append(child.text)
        elif tag.endswith("}br"):
            texts.append("\r")
        elif tag.endswith("}tab"):
            texts.append("\t")
    return "".join(texts)

def generate_new_doc_with_paragraph_splits(input_path, output_path):
    """
    读取输入文档，对每个段落根据换行符拆分，然后生成新的文档。
    """
    if not os.path.exists(input_path):
        logging.error(f"预处理：文件不存在: {input_path}")
        return False

    doc = Document(input_path)
    new_doc = Document()
    # 清除默认内容
    new_doc._body.clear_content()

    for para in doc.paragraphs:
        full_text = get_paragraph_text_with_line_breaks(para)
        parts = full_text.split("\r")
        for part in parts:
            if part != "":
                new_doc.add_paragraph(part)
    new_doc.save(output_path)
    logging.info(f"预处理：新文件生成成功: {output_path}")
    return True

def preprocess_document(input_path):
    """
    读取 input_path 指定的 docx 文档，
    对每个段落调用 get_paragraph_text_with_line_breaks，
    按回车符 ("\r") 拆分为多个部分，将所有非空部分构造为一个列表，
    返回这个预处理后的段落列表。
    """
    if not os.path.exists(input_path):
        logging.error(f"预处理：文件不存在: {input_path}")
        return []
    doc = Document(input_path)
    new_paragraphs = []
    for para in doc.paragraphs:
        full_text = get_paragraph_text_with_line_breaks(para)
        parts = full_text.split("\r")
        for part in parts:
            if part != "":
                new_paragraphs.append(part)
    logging.info(f"预处理：共生成 {len(new_paragraphs)} 个段落")
    return new_paragraphs

if __name__ == "__main__":
    input_file = "all_questions.docx"
    output_file = "all_questions_replaced.docx"
    if generate_new_doc_with_paragraph_splits(input_file, output_file):
        print(f"预处理完成，新文件：{output_file}")
    else:
        print("预处理失败。")
