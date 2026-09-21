import streamlit as st
import streamlit.components.v1 as components

# Cấu hình trang Streamlit
st.set_page_config(
    page_title="Quản lý cáp - FPT Telecom",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------------------------------------------------
# SIDEBAR: Giao diện điều khiển bên trái
# ---------------------------------------------------------
with st.sidebar:
    st.title("FPT Telecom")
    st.caption("Make by BangNC13")
    
    st.text_input("🔑 Google API Key (Tùy chọn)", type="password")
    st.text_input("Nhập điểm cuối hành trình (nếu muốn)", placeholder="Chợ Tam Cờ...")
    
    st.subheader("📋 Chọn lộ trình di chuyển")
    st.selectbox("Chọn điểm TQGP0xx:", ["Choose options", "TQGP001", "TQGP002", "TQGP003"])
    
    st.write("Hoặc Upload file Excel:")
    uploaded_file = st.file_uploader("Upload", type=["xlsx", "xls"], label_visibility="collapsed")
    st.caption("200MB per file • XLSX, XLS")
    
    st.checkbox("Hiện tên điểm (Label)", value=True)
    st.checkbox("Hiện đường và lộ trình", value=True)

# ---------------------------------------------------------
# MAIN: Hiển thị bản đồ Leaflet ở khu vực chính
# ---------------------------------------------------------
# Mã HTML, CSS và JS được đặt an toàn trong một chuỗi Python nhiều dòng (Multiline String)
map_html = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <!-- Leaflet CSS -->
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <style>
        html, body {
            margin: 0;
            padding: 0;
            height: 100%;
            width: 100%;
        }
        #map {
            /* Dòng height: 100vh gây lỗi trước đó giờ đã nằm an toàn bên trong chuỗi HTML */
            height: 100vh;
            width: 100%;
        }
    </style>
</head>
<body>

<div id="map"></div>

<!-- Leaflet JS -->
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script>
    // Khởi tạo bản đồ tại khu vực Tuyên Quang (Minh Xuân)
    var map = L.map('map').setView([21.817, 105.207], 14);

    // Thêm bản đồ nền OpenStreetMap
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; OpenStreetMap contributors'
    }).addTo(map);

    // Thêm ví dụ Marker điểm Bệnh viện Đa khoa Tuyên Quang
    var marker = L.marker([21.817, 105.207]).addTo(map);
    marker.bindPopup("<b>Bệnh Viện Đa Khoa Tỉnh Tuyên Quang</b>").openPopup();
</script>

</body>
</html>
"""

# Hiển thị khối HTML/JS trên giao diện Streamlit
components.html(map_html, height=800, scrolling=False)
