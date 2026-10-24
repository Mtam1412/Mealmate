# Bếp thông minh (MealMate) – tìm món theo nguyên liệu, tính dinh dưỡng, AI tạo công thức

Web tìm món từ 31.183 công thức (`data/recipes_clean.xlsx`). Người dùng nhập nguyên liệu, số khẩu phần, bữa ăn và các bộ lọc; hệ thống trả về món phù hợp, tính lại lượng nguyên liệu theo khẩu phần, nhờ AI viết công thức và có chatbot giải thích thành phần, dinh dưỡng.

**Mục lục:** 1) Chức năng · 2) Cài đặt và chạy · 3) Cấu trúc thư mục · 4) Giao diện · 5) Tài khoản · 6) Kiểm thử · 7) Hạn chế

---

## 1) Chức năng

1. **Nguyên liệu:** nhập tiếng Anh giống ngôn ngữ của dataset (`chicken, carrot, potato`), đối chiếu với tên nguyên liệu `ingredients.food`. Nguyên liệu hiện thẳng trong ô tìm kiếm, tự thêm ", " sau mỗi món. Có các từ gợi ý bấm để thêm hoặc bỏ, và ô **Match ingredients** (bật: món phải có tất cả nguyên liệu; tắt: chỉ cần một).
2. **Số khẩu phần:** lấy món có khẩu phần gốc trong [n-2, n+2]. Khi mở món, lượng nguyên liệu được nhân hệ số n / khẩu phần gốc. Trong **Dish details** có ô Servings riêng (− / + / Reset) để xem lượng nguyên liệu theo số khẩu phần khác.
3. **Bữa ăn, chế độ ăn, ẩm thực, loại món:** lựa chọn lấy từ dữ liệu (`meal_type`, `diet_labels`, `cuisine_type`, `dish_type`).
4. **Sắp xếp calo:** tăng dần hoặc giảm dần theo tổng calo công thức gốc.
5. **Kết quả:** tên món, ảnh (`image_url`), calo mỗi khẩu phần, độ khớp nguyên liệu. Mỗi trang 12 món, có nút trang trước / sau và số trang; tìm kiếm hoặc đổi bộ lọc thì quay về trang 1.
6. **AI tạo công thức:** Gemini viết công thức từ danh sách nguyên liệu của món (không dùng `url`), hiện dần từng đoạn. **Cần đăng nhập.** Kết quả được lưu cache nên lần sau mở nhanh hơn.
7. **Chatbot nổi (góc phải dưới):** chỉ giải thích thành phần và dinh dưỡng của món đang xem, không tìm hay gợi ý món khác. Câu hỏi về lượng (protein, potassium, sodium, vitamin, calo...) được trả lời ngay từ dữ liệu, không cần AI. Câu hỏi giải thích được gửi cho AI.
8. **Favorites và History:** lưu bằng `localStorage` của trình duyệt.

---

## 2) Cài đặt và chạy

```bash
pip install -r requirements.txt
python scripts/build_data.py                 # tạo web/data/recipes.json.gz (đã có sẵn, chạy lại khi đổi dữ liệu)
export GEMINI_API_KEY="khoa_cua_ban"         # Windows PowerShell: $env:GEMINI_API_KEY="khoa_cua_ban"
uvicorn api.main:app --port 8000             # chạy từ thư mục gốc dự án
```

Mở http://localhost:8000.

- Khóa lấy tại Google AI Studio, chỉ nằm ở server (đặt trong `.env` ở thư mục gốc, không đưa lên git).
- Nếu **không đặt khóa**: tìm kiếm vẫn chạy, chatbot vẫn trả lời các câu hỏi về lượng từ dữ liệu; khung **AI Recipe** tự ẩn và chatbot không trả lời được câu hỏi giải thích.
- Đổi model bằng biến `GEMINI_MODEL` (và `GEMINI_FALLBACK_MODEL` cho model dự phòng). Nếu AI báo lỗi, thử đặt `GEMINI_MODEL=gemini-2.5-flash` trong `.env`.
- Có thể mở trang bằng Live Server (cổng 5500...): giao diện tự tìm server ở cổng 8000 và `api/main.py` đã bật CORS cho localhost.

---

## 3) Cấu trúc thư mục
api/
main.py FastAPI: tài khoản, /api/health, /api/generate, /api/recipe-ai-stream, phục vụ thư mục web/
llm.py gọi Gemini (stream) + cache công thức
cache/ cache công thức AI (tự tạo)
data/
recipes_clean.xlsx dữ liệu gốc
scripts/
build_data.py xlsx -> web/data/recipes.json.gz
test_api.py kiểm thử API
web/
index.html
css/style.css, css/chatbot.css
js/app.js, js/chatbot.js
data/recipes.json.gz
assets/images/
users.db tài khoản (SQLite, tự tạo)
.env khóa API
requirements.txt
README.md

## 4) Giao diện

- Ngôn ngữ: **Python** (server) + **HTML / CSS / JavaScript thuần** (giao diện), không cần framework.
- **Cột trái:** Home / Favorites / History, nút **Sign in** và **Create account**.
- **Giữa:** Ingredients, Servings, Meal type, Search by dish name, Match ingredients, bộ lọc Diet / Cuisine / Dish type / Calories, lưới món (4 món/hàng, tự giảm còn 3 hoặc 2 khi màn hình hẹp).
- **Phải:** Dish details (nguyên liệu nhân theo khẩu phần, AI Recipe). Cột này đóng lúc mở trang và chỉ hiện khi bấm vào một món; khi đóng, nội dung được căn giữa.
- Chữ dùng font Source Serif 4 và Lato tải từ Google Fonts (cần internet; không có thì dùng font dự phòng).
- Phân công file: `index.html` (khung), `style.css` và `chatbot.css` (kiểu dáng), `app.js` (tìm kiếm, chi tiết, đăng nhập), `chatbot.js` (chatbot).

---

## 5) Đăng ký / đăng nhập

- Bấm **Create account** ở cột trái để tạo tài khoản; **Sign in** để đăng nhập; **Sign out** để kết thúc phiên.
- Tài khoản lưu trong `users.db` (SQLite). Mật khẩu không lưu dạng văn bản mà được băm bằng PBKDF2-HMAC-SHA256.
- Phiên đăng nhập giữ bằng cookie HTTP-only trong 7 ngày.
- Server tạo sẵn một tài khoản demo khi khởi động (xem `seed_demo` trong `api/main.py`).
- Favorites / History vẫn lưu ở trình duyệt, đăng nhập chưa đồng bộ các dữ liệu này lên server.
- Nếu server chưa chạy, cửa sổ đăng nhập báo rõ cách chạy; lỗi cơ sở dữ liệu hiện đúng nội dung thay vì báo chung chung.

---

## 6) Kiểm thử

Khi server đang chạy: `python scripts/test_api.py`

- 10 trường hợp hợp lệ và không hợp lệ cho `/api/health`, trang chủ, dữ liệu nén và `/api/generate`.
- Mã 503 chấp nhận được khi chưa có khóa.

---

## 7) Hạn chế (nên nêu trong báo cáo)

- Toàn bộ giao diện, tên món, nguyên liệu, nhãn và câu trả lời AI dùng tiếng Anh để cùng ngôn ngữ với dataset; nguyên liệu phải nhập bằng tiếng Anh.
- Ảnh là link ngoài trong `image_url`, có thể hết hạn; khi lỗi, giao diện hiển thị biểu tượng theo loại món.
- Công thức và lời giải thích do AI tạo, có thể sai; giao diện đã ghi chú nhưng cần kiểm tra lại. Thông tin dinh dưỡng chỉ mang tính tham khảo, không thay lời khuyên của bác sĩ hoặc chuyên gia dinh dưỡng.
- Calo và dinh dưỡng là số liệu của cả công thức theo khẩu phần gốc; mỗi khẩu phần = tổng chia số khẩu phần gốc.
- Dữ liệu nén khoảng 8 MB được tải và giải nén ở trình duyệt (cần Chrome, Edge, Safari 16.4 trở lên hoặc Firefox mới), lần mở đầu hơi chậm.
- Chưa có model học máy tự huấn luyện; hệ thống dựa trên lọc dữ liệu và AI có sẵn.