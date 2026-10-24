"""MealMate – test_api.py

Kiểm thử API (chạy khi server đang hoạt động).

Cách chạy trên máy (từ thư mục gốc dự án):
    1) Mở một cửa sổ lệnh và chạy server:  uvicorn api.main:app --port 8000
    2) Mở cửa sổ lệnh khác và chạy:        python scripts/test_api.py

Cách chạy trên link web đã deploy (PowerShell):
    $env:BASE_URL="https://mealmate-bim9.onrender.com"
    python scripts/test_api.py

Mỗi trường hợp in một dòng [OK] hoặc [LỖI]; cuối cùng in tổng số trường hợp đạt.
Mã 503 chấp nhận được khi chưa đặt GEMINI_API_KEY (server chạy nhưng chưa bật AI).

Mục lục: 1) Cấu hình  2) Dữ liệu mẫu  3) Danh sách trường hợp kiểm thử  4) Chạy + báo kết quả
"""
import os
import time

import requests


# =====================================================================
# 1) CẤU HÌNH
# =====================================================================
# Địa chỉ server. Mặc định là máy của bạn; muốn thử trên web đã deploy thì đặt biến môi trường BASE_URL.
B = os.environ.get("BASE_URL", "http://127.0.0.1:8000").rstrip("/")
turn = lambda r, c: {"role": r, "content": c}     # tạo một lượt hội thoại (dùng cho /api/generate)


# =====================================================================
# 2) DỮ LIỆU MẪU
# =====================================================================
# Tên tài khoản kèm số giây hiện tại => mỗi lần chạy test ra một tên mới, không bị báo "đã tồn tại".
uname = f"test_{int(time.time())}"
OK_USER = {"username": uname, "email": f"{uname}@example.com", "password": "abc12345"}   # tài khoản hợp lệ

# Một công thức hợp lệ (tên món, số khẩu phần, danh sách nguyên liệu) để thử /api/recipe-ai-stream.
RECIPE = {"name": "Test", "servings": 2,
          "ingredients": [{"food": "egg", "quantity": 2, "measure": None}]}


# =====================================================================
# 3) DANH SÁCH TRƯỜNG HỢP KIỂM THỬ
#    (tên, phương thức, đường dẫn, dữ liệu gửi, các mã HTTP chấp nhận)
#    Mã thường gặp: 200 = thành công, 400 = dữ liệu sai nội dung, 401 = chưa đăng nhập / sai mật khẩu,
#    409 = trùng (tên, email), 422 = dữ liệu sai cấu trúc (thiếu trường, quá ngắn, quá dài).
# =====================================================================
CASES = [
    # --- Server và file tĩnh: kiểm tra server đã lên và phục vụ đúng file ---
    ("Health", "get", "/api/health", None, (200,)),
    ("Trang chủ", "get", "/", None, (200,)),
    ("Dữ liệu nén", "get", "/data/recipes.json.gz", None, (200,)),

    # --- /api/generate: dữ liệu hợp lệ (có gọi Gemini nên tốn một ít quota) ---
    ("Câu lệnh hợp lệ", "post", "/api/generate", {"input": "Giải thích protein là gì, 2 câu"}, (200, 503)),
    ("Hội thoại hợp lệ", "post", "/api/generate", {"input": [turn("user", "Natri là gì?")]}, (200, 503)),

    # --- /api/generate: dữ liệu sai (phải bị từ chối bằng 422, không gọi Gemini) ---
    ("Input rỗng", "post", "/api/generate", {"input": "   "}, (422,)),
    ("Input quá dài", "post", "/api/generate", {"input": "a" * 9000}, (422,)),
    ("Thiếu trường input", "post", "/api/generate", {}, (422,)),
    ("Hội thoại kết thúc bằng assistant", "post", "/api/generate", {"input": [turn("user", "hi"), turn("assistant", "hello")]}, (422,)),
    ("Vai trò sai", "post", "/api/generate", {"input": [turn("admin", "hi")]}, (422,)),

    # --- Đăng ký: một trường hợp đúng, các trường hợp còn lại phải bị từ chối ---
    ("Đăng ký hợp lệ", "post", "/api/register", OK_USER, (200,)),
    ("Đăng ký trùng tên", "post", "/api/register", OK_USER, (409,)),
    ("Mật khẩu quá ngắn", "post", "/api/register", {**OK_USER, "username": uname + "a", "password": "123"}, (422,)),
    ("Tên có ký tự đặc biệt", "post", "/api/register", {**OK_USER, "username": "a b!"}, (400,)),
    ("Email sai định dạng", "post", "/api/register", {**OK_USER, "username": uname + "b", "email": "abcdef"}, (400,)),

    # --- Đăng nhập và kiểm tra phiên ---
    ("Đăng nhập đúng", "post", "/api/login", {"username": uname, "password": "abc12345"}, (200,)),
    ("Đăng nhập sai mật khẩu", "post", "/api/login", {"username": uname, "password": "saisai"}, (401,)),
    ("Kiểm tra phiên khi chưa đăng nhập", "get", "/api/me", None, (200,)),     # vẫn 200, nhưng nội dung báo logged_in = false

    # --- AI recipe: chưa đăng nhập hoặc dữ liệu sai thì bị từ chối trước khi gọi Gemini (không tốn quota) ---
    ("AI recipe khi chưa đăng nhập", "post", "/api/recipe-ai-stream", RECIPE, (401,)),
    ("AI recipe số khẩu phần = 0", "post", "/api/recipe-ai-stream", {**RECIPE, "servings": 0}, (422,)),
    ("AI recipe thiếu nguyên liệu", "post", "/api/recipe-ai-stream", {**RECIPE, "ingredients": []}, (422,)),
]


# =====================================================================
# 4) CHẠY + BÁO KẾT QUẢ
# =====================================================================
def run_case(name, method, path, data, want):
    """Chạy một trường hợp, in kết quả, trả về 1 nếu đạt, 0 nếu không."""
    try:
        send = getattr(requests, method)          # requests.get hoặc requests.post
        r = send(B + path, json=data, timeout=60) if data is not None else send(B + path, timeout=60)
        good = r.status_code in want              # đạt nếu mã trả về nằm trong danh sách mã chấp nhận
        print(f"[{'OK ' if good else 'LỖI'}] {name}: HTTP {r.status_code} (mong đợi {want})")
        return int(good)
    except requests.RequestException as e:
        print(f"[LỖI] {name}: không kết nối được ({e})")      # server chưa chạy hoặc sai địa chỉ
        return 0


def main():
    print(f"Kiểm thử trên: {B}\n")
    ok = sum(run_case(*case) for case in CASES)
    print(f"\n{ok}/{len(CASES)} trường hợp đạt (503 là chấp nhận được khi chưa đặt GEMINI_API_KEY)")


if __name__ == "__main__":
    main()