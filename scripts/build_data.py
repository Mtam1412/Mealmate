"""MealMate – build_data.py

Đọc data/recipes_clean.xlsx, rút gọn và nén thành web/data/recipes.json.gz cho trang web.

Cách chạy (từ thư mục gốc dự án):
    python scripts/build_data.py
(File này nằm trong thư mục scripts/ của dự án, vì ROOT được tính
bằng cách lùi lên hai cấp từ vị trí file.)

Mỗi món gồm:
  i (số thứ tự)   n (tên)   s (khẩu phần gốc)   c (tổng calo gốc)   m (đuôi link ảnh)
  d / u / t / y   chế độ ăn / ẩm thực / bữa ăn / loại món
  g               nguyên liệu: [tên, lượng, đơn vị, gram]
  x               dinh dưỡng của cả món

Mục lục: 1) Cấu hình  2) Đọc từng dòng  3) Chạy + ghi file
"""
import gzip
import json
import os

import pandas as pd


# =====================================================================
# 1) CẤU HÌNH
# =====================================================================
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "data", "recipes_clean.xlsx")        # file đầu vào
OUT = os.path.join(ROOT, "web", "data", "recipes.json.gz")    # file đầu ra cho trang web

# Các chất dinh dưỡng giữ lại trong total_nutrients
NUTK = ("PROCNT FAT FASAT FAMS FAPU FATRN CHOLE CHOCDF SUGAR FIBTG WATER NA K CA FE MG P ZN "
        "VITA_RAE VITC VITD TOCPHA VITK1 THIA RIBF NIA VITB6A FOLDFE VITB12").split()

# Phần đầu chung của link ảnh (chỉ lưu phần đuôi cho nhẹ file)
PREFIX = "https://datahive-prod-dataset-products.s3.eu-central-1.amazonaws.com/dataset/346/"


# =====================================================================
# 2) ĐỌC TỪNG DÒNG
# =====================================================================
L = lambda s: json.loads(s) if isinstance(s, str) and s else []   # cột danh sách dạng JSON; trống -> []


def make_recipe(r, index):
    """Chuyển một dòng Excel thành dict của một món. Dòng hỏng thì ném lỗi để bỏ qua."""
    s = max(1, int(round(float(r.servings))))
    c = round(float(r.calories), 1)
    tn = json.loads(r.total_nutrients)
    ings = json.loads(r.ingredients)

    # Nguyên liệu: [tên, lượng (chỉ khi chia được theo khẩu phần), đơn vị, gram]
    ing = [[g.get("food") or "",
            round(g["quantity"], 2) if g.get("scalable") and g.get("quantity") else None,
            g.get("measure"),
            round(g["weight"]) if g.get("weight") else None] for g in ings]

    u = r.image_url if isinstance(r.image_url, str) else ""
    return {"i": index, "n": r.recipe_name, "s": s, "c": c,
            "m": u[len(PREFIX):] if u.startswith(PREFIX) else "",
            "d": L(r.diet_labels), "u": L(r.cuisine_type), "t": L(r.meal_type), "y": L(r.dish_type),
            "g": ing,
            "x": {k: round(tn[k]["quantity"], 2) for k in NUTK if k in tn}}


# =====================================================================
# 3) CHẠY + GHI FILE
# =====================================================================
def main():
    df = pd.read_excel(SRC, dtype=str)
    rows, bad = [], 0

    for r in df.itertuples():
        try:
            rows.append(make_recipe(r, len(rows)))
        except (ValueError, TypeError, KeyError):
            bad += 1                                  # bỏ dòng hỏng
            continue

    raw = json.dumps(rows, ensure_ascii=False, separators=(",", ":")).encode()
    with open(OUT, "wb") as f:
        f.write(gzip.compress(raw, 9))

    print("Đã ghi", len(rows), "món (bỏ", bad, "dòng hỏng) ->", "web/data/recipes.json.gz")


if __name__ == "__main__":
    main()