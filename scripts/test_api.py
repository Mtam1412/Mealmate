"""MealMate – test_api.py

Kiểm thử API (chạy khi server đang hoạt động).

Cách chạy (từ thư mục gốc dự án):
    1) Mở một cửa sổ lệnh và chạy server:  uvicorn api.main:app --port 8000
    2) Mở cửa sổ lệnh khác và chạy:        python scripts/test_api.py

Mỗi trường hợp in một dòng [OK] hoặc [LỖI]; cuối cùng in tổng số trường hợp đạt.
Mã 503 chấp nhận được khi chưa đặt GEMINI_API_KEY (server chạy nhưng chưa bật AI).

Mục lục: 1) Cấu hình  2) Danh sách trường hợp kiểm thử  3) Chạy + báo kết quả
"""
import requests


# =====================================================================
# 1) CẤU HÌNH
# =====================================================================
B = "http://127.0.0.1:8000"                       # địa chỉ server
turn = lambda r, c: {"role": r, "content": c}     # tạo một lượt hội thoại


# =====================================================================
# 2) DANH SÁCH TRƯỜNG HỢP KIỂM THỬ
#    (tên, phương thức, đường dẫn, dữ liệu gửi, các mã HTTP chấp nhận)
# =====================================================================
CASES = [
    # --- Server và file tĩnh ---
    ("Health", "get", "/api/health", None, (200,)),
    ("Trang chủ", "get", "/", None, (200,)),
    ("Dữ liệu nén", "get", "/data/recipes.json.gz", None, (200,)),

    # --- /api/generate: dữ liệu hợp lệ ---
    ("Câu lệnh hợp lệ", "post", "/api/generate", {"input": "Giải thích protein là gì, 2 câu"}, (200, 503)),
    ("Hội thoại hợp lệ", "post", "/api/generate", {"input": [turn("user", "Natri là gì?")]}, (200, 503)),

    # --- /api/generate: dữ liệu sai (phải bị từ chối bằng 422) ---
    ("Input rỗng", "post", "/api/generate", {"input": "   "}, (422,)),
    ("Input quá dài", "post", "/api/generate", {"input": "a" * 9000}, (422,)),
    ("Thiếu trường input", "post", "/api/generate", {}, (422,)),
    ("Hội thoại kết thúc bằng assistant", "post", "/api/generate", {"input": [turn("user", "hi"), turn("assistant", "hello")]}, (422,)),
    ("Vai trò sai", "post", "/api/generate", {"input": [turn("admin", "hi")]}, (422,)),
]


# =====================================================================
# 3) CHẠY + BÁO KẾT QUẢ
# =====================================================================
def run_case(name, method, path, data, want):
    """Chạy một trường hợp, in kết quả, trả về 1 nếu đạt, 0 nếu không."""
    try:
        send = getattr(requests, method)
        r = send(B + path, json=data, timeout=60) if data is not None else send(B + path, timeout=60)
        good = r.status_code in want
        print(f"[{'OK ' if good else 'LỖI'}] {name}: HTTP {r.status_code} (mong đợi {want})")
        return int(good)
    except requests.RequestException as e:
        print(f"[LỖI] {name}: không kết nối được ({e})")
        return 0


def main():
    ok = sum(run_case(*case) for case in CASES)
    print(f"{ok}/{len(CASES)} trường hợp đạt (503 là chấp nhận được khi chưa đặt GEMINI_API_KEY)")


if __name__ == "__main__":
    main()