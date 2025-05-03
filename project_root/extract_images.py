import os
import docx
import shutil
from database.db_manager import insert_image_record  # 调用写库函数

def extract_images_from_docx(docx_path, question_id_prefix="Q"):
    doc = docx.Document(docx_path)
    rels = doc.part._rels

    output_dir = "images"
    os.makedirs(output_dir, exist_ok=True)

    image_index = 1
    for rel in rels:
        rel_obj = rels[rel]
        if "image" in rel_obj.reltype:
            img_name = f"image_{image_index:03d}.png"
            img_path = os.path.join(output_dir, img_name)

            with open(img_path, "wb") as f:
                f.write(rel_obj.target_part.blob)

            print(f"保存图片：{img_path}")

            # 将图片与题目 ID 关联（这里假设与顺序相关）
            question_id = f"{question_id_prefix}{image_index}"
            insert_image_record(question_id, img_path)

            image_index += 1
