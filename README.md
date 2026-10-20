# Lộ trình tối ưu cho xe máy (Streamlit)

Chọn hoặc import danh sách đối tượng (sheet "Tọa độ"), lấy vị trí điện thoại làm điểm xuất phát,
tính thứ tự tối ưu và vẽ lộ trình theo đường bộ thật.

## Chạy trên Streamlit Community Cloud
1. Tạo repo GitHub, đưa vào: `app.py`, `requirements.txt`, `Template.xlsx`, `README.md`, `.gitignore`, `.streamlit/config.toml`, thư mục `route_map/`.
2. Vào https://share.streamlit.io → New app → chọn repo, nhánh `main`, file `app.py` → Deploy.
3. Mở link app (https) trên điện thoại, bấm nút định vị và cho phép truy cập vị trí.

## Dùng thuật toán Google Maps (tùy chọn)
Trong Streamlit Cloud: App settings → Secrets, thêm:

    GOOGLE_MAPS_API_KEY = "khóa-của-bạn"

Cần bật Routes API cho khóa. Có khóa thì app dùng chế độ xe máy (TWO_WHEELER) và tối ưu thứ tự
(tối đa 25 điểm giữa). Không có khóa hoặc Google báo lỗi thì app dùng OSRM miễn phí (đường ô tô).

## Lưu ý
- Google Sheet phải chia sẻ "Bất kỳ ai có đường liên kết đều xem được".
- Máy chủ OSRM công cộng chỉ phù hợp dùng nhẹ; dùng nhiều nên tự dựng OSRM hoặc dùng khóa Google.

## Chạy thử trên máy
    pip install -r requirements.txt
    streamlit run app.py
