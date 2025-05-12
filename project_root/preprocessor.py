# preprocessor.py

import os
import logging
from docx import Document
from docx.oxml.ns import qn
from lxml import etree

# 初始化日志
log_file = os.path.join("logs", "preprocessor.log")
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    filename=log_file,
    filemode="w",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    encoding="utf-8"
)

def preprocess_document(input_path):
    """
    读取 input_path 指定的 docx 文档，
    按段落提取图片和公式，并在段落文本中插入占位符 [IMAGE_id] / [MATH_id]，
    返回：
      {
        'paragraphs': ['段落1文本…[IMAGE_1]…', …],
        'media': [
          {'temp_id':1, 'type':'image', 'path':'media/images/img_1.png'},
          {'temp_id':2, 'type':'mathml', 'content':'<m:oMath>…</m:oMath>'},
          …
        ]
      }
    """
    if not os.path.exists(input_path):
        logging.error(f"预处理：文件不存在: {input_path}")
        return {'paragraphs': [], 'media': []}

    doc = Document(input_path)
    media = []
    temp_id = 1

    # 准备 media/images 目录
    image_dir = os.path.join("media", "images")
    os.makedirs(image_dir, exist_ok=True)

    # 先提取所有 MathML 公式到 media（与原逻辑一致）
    body = doc.element.body
    for oMath in body.iterfind(f".//{qn('m:oMath')}"):
        mathml = etree.tostring(oMath, encoding="unicode")
        media.append({
            'temp_id': temp_id,
            'type': 'mathml',
            'content': mathml
        })
        logging.info(f"[preprocessor] 提取公式 temp_id={temp_id}")
        temp_id += 1

    # 构建带占位符的段落列表
    paragraphs = []
    for para in doc.paragraphs:
        parts = []
        # 遍历段落 XML 节点
        for child in para._element.iter():
            tag = child.tag.lower()
            # 文本节点
            if tag.endswith("}t") and child.text:
                parts.append(child.text)
            # 换行
            elif tag.endswith("}br"):
                parts.append("\n")
            # 图片占位：检测 drawing 中的 <a:blip> 嵌入关系
            elif child.tag == qn('a:blip'):
                # 获取 relationship id
                rel_id = child.get(qn('r:embed'))
                if rel_id and rel_id in doc.part.rels:
                    rel = doc.part.rels[rel_id]
                    blob = rel.target_part.blob
                    # 根据 partname 获取扩展名
                    ext = os.path.splitext(rel.target_part.partname)[1] or ".png"
                    img_name = f"img_{temp_id}{ext}"
                    img_path = os.path.join(image_dir, img_name)
                    # 写入文件
                    with open(img_path, "wb") as f:
                        f.write(blob)
                    media.append({
                        'temp_id': temp_id,
                        'type': 'image',
                        'path': img_path
                    })
                    logging.info(f"[preprocessor] 提取图片 temp_id={temp_id}, path={img_path}")
                    # 在文本中插入占位符
                    parts.append(f"[IMAGE_{temp_id}]")
                    temp_id += 1
            # 公式占位符（如果有其它 MathML 场景）
            elif tag.endswith("}omath"):
                # 找到尚未用到的 mathml
                unused = [m for m in media if m['type']=='mathml' and 'used' not in m]
                if unused:
                    m = unused[0]
                    parts.append(f"[MATH_{m['temp_id']}]")
                    m['used'] = True
            # 制表符
            elif tag.endswith("}tab"):
                parts.append("\t")

        paragraph_text = "".join(parts).strip()
        if paragraph_text:
            paragraphs.append(paragraph_text)

    logging.info(f"预处理：生成 {len(paragraphs)} 个带占位符段落，提取媒体 {len(media)} 条")
    return {'paragraphs': paragraphs, 'media': media}


if __name__ == "__main__":
    result = preprocess_document("test_questions.docx")
    print(f"段落数量：{len(result['paragraphs'])}, 媒体数量：{len(result['media'])}")
