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
    提取所有图片和公式，并在段落文本中插入占位符 [IMAGE_id] / [MATH_id]，
    返回：
      {
        'paragraphs': [ '段落1文本…[IMAGE_1]…', … ],
        'media': [
          {'temp_id':1, 'type':'image', 'path':'media/images/img_1.png', 'used':False},
          {'temp_id':2, 'type':'mathml', 'content':'<m:oMath>…</m:oMath>', 'used':False},
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

    # 1. 提取图片到 media 列表
    image_dir = os.path.join("media", "images")
    os.makedirs(image_dir, exist_ok=True)
    for rel in doc.part._rels.values():
        if "image" in rel.reltype:
            blob = rel.target_part.blob
            ext = os.path.splitext(rel.target_ref)[-1] or ".png"
            img_name = f"img_{temp_id}{ext}"
            img_path = os.path.join(image_dir, img_name)
            with open(img_path, "wb") as f:
                f.write(blob)
            media.append({
                'temp_id': temp_id,
                'type': 'image',
                'path': img_path,
                'used': False
            })
            logging.info(f"[preprocessor] 提取图片 temp_id={temp_id}, path={img_path}")
            temp_id += 1

    # 2. 提取 MathML 公式到 media 列表
    body = doc.element.body
    for oMath in body.iterfind(f".//{qn('m:oMath')}"):
        mathml = etree.tostring(oMath, encoding="unicode")
        media.append({
            'temp_id': temp_id,
            'type': 'mathml',
            'content': mathml,
            'used': False
        })
        logging.info(f"[preprocessor] 提取公式 temp_id={temp_id}")
        temp_id += 1

    # 3. 构建带占位符的段落列表
    paragraphs = []
    for para in doc.paragraphs:
        parts = []
        for child in para._element.iter():
            tag = child.tag.lower()
            # 文本节点
            if tag.endswith("}t") and child.text:
                parts.append(child.text)
            # 换行
            elif tag.endswith("}br"):
                parts.append("\n")
            # 图片占位符 —— 这里改为更宽泛地匹配 drawing
            elif "drawing" in tag or "pict" in tag:
                unused_imgs = [m for m in media if m['type']=='image' and not m['used']]
                if unused_imgs:
                    img = unused_imgs[0]
                    img['used'] = True
                    parts.append(f"[IMAGE_{img['temp_id']}]")
            # 公式占位符
            elif tag.endswith("}omath"):
                unused_math = [m for m in media if m['type']=='mathml' and not m['used']]
                if unused_math:
                    mm = unused_math[0]
                    mm['used'] = True
                    parts.append(f"[MATH_{mm['temp_id']}]")
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
