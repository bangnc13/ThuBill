import os
import json
import glob
import re
import streamlit as st
import streamlit.components.v1 as components
import folium
from streamlit_folium import st_folium

# --- CẤU HÌNH TRANG STREAMLIT ---
st.set_page_config(
    page_title="Hệ thống tối ưu lộ trình TQGP",
    page_icon="🗺️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Tùy chỉnh CSS để xóa viền và giúp bản đồ hiển thị full màn hình bên phải
st.markdown("""
    <style>
        .block-container {
            padding-top: 1rem;
            padding-bottom: 0rem;
            padding-left: 1rem;
            padding-right: 1rem;
        }
        [data-testid="stSidebar"] {
            background-color: #1a1c23;
            color: white;
        }
        .stButton button {
            width: 100%;
        }
    </style>
""", unsafe_allow_html=True)

# --- THÔNG TIN TỔ CHỨC & TÁC GIẢ (SIDEBAR) ---
with st.sidebar:
    # Logo & Title
    st.markdown("<h1 style='color: #FF5722; margin-bottom:0;'>FPT Telecom</h1>", unsafe_allow_html=True)
    st.markdown("**Make by BangNC13**")
    st.markdown("---")

    # Hàm đọc các file TQGPxxx.json
    def load_tqgp_json_files():
        json_files = glob.glob("TQGP*.json")
        points = {}
        for file in json_files:
            try:
                with open(file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Giả định cấu trúc JSON chứa danh sách điểm có 'name', 'lat', 'lng'
                    # Hoặc dict dạng {"TQGP001.0001/HO": [lat, lng]}
                    if isinstance(data, list):
                        for item in data:
                            name = item.get("name", "")
                            if "/HO" in name and "TQGP" in name:
                                points[name] = (item["lat"], item["lng"])
                    elif isinstance(data, dict):
                        for k, v in data.items():
                            if "/HO" in k and "TQGP" in k:
                                points[k] = (v[0], v[1]) if isinstance(v, list) else (v["lat"], v["lng"])
            except Exception as e:
                pass
        return json_files, points

    json_files, tqgp_points = load_tqgp_json_files()

    # Cảnh báo file JSON
    if not json_files:
        st.warning("⚠️ Chưa tìm thấy file TQGPxxx.json nào trong thư mục!")
    else:
        st.success(f"Dữ liệu: Đã tải {len(json_files)} file JSON ({len(tqgp_points)} điểm /HO)")

    # Debug Log & API Key[cite: 1]
    with st.expander("🔍 Lịch sử kiểm tra (Debug Log)"):
        st.write(f"Số file phát hiện: {len(json_files)}")
        st.write(f"Danh sách file: {json_files}")

    api_key = st.text_input("🔑 Google API Key (Tùy chọn)", type="password")

    st.markdown("---")
    
    # Nhập điểm cuối & Chọn lộ trình[cite: 1]
    end_point_input = st.text_input("🎯 Nhập điểm cuối hành trình (nếu muốn)", placeholder="Chợ Tam Cờ...")
    
    selected_points = st.multiselect(
        "📱 Chọn lộ trình di chuyển",
        options=list(tqgp_points.keys()),
        help="Chọn các điểm TQGPxxx.xxxx/HO cần đi qua"
    )

    st.markdown("**Hoặc Upload file Excel:**")
    uploaded_file = st.file_uploader("Upload", type=["xlsx", "xls"], label_visibility="collapsed")
    st.caption("200MB per file • XLSX, XLS")

    st.markdown("---")

    # Các Checkbox Tùy chỉnh[cite: 1]
    show_labels = st.checkbox("📌 Hiện tên điểm (Label)", value=True)
    show_routes = st.checkbox("🛣️ Hiện đường vẽ lộ trình", value=True)

    col1, col2 = st.columns(2)
    with col1:
        btn_refresh = st.button("🔄 Làm mới bản đồ")
    with col2:
        btn_route = st.button("🚀 Lộ trình")

# --- NÚT LẤY ĐỊNH VỊ REALTIME TỪ ĐIỆN THOẠI/TRÌNH DUYỆT ---
st.sidebar.markdown("---")
st.sidebar.markdown("**📍 Vị trí hiện tại của bạn:**")

# Nhúng JavaScript lấy GPS
gps_code = """
<script>
function getLocation() {
  if (navigator.geolocation) {
    navigator.geolocation.getCurrentPosition(showPosition, showError);
  } else {
    alert("Geolocation không được hỗ trợ bởi trình duyệt này.");
  }
}
function showPosition(position) {
  const lat = position.coords.latitude;
  const lng = position.coords.longitude;
  document.getElementById("gps_status").innerText = "Tọa độ: " + lat.toFixed(5) + ", " + lng.toFixed(5);
}
function showError(error) {
  document.getElementById("gps_status").innerText = "Không thể lấy vị trí GPS.";
}
</script>
<button onclick="getLocation()" style="width:100%; padding:8px; background-color:#28a745; color:white; border:none; border-radius:4px; cursor:pointer;">
    📍 Định vị Realtime
</button>
<p id="gps_status" style="color:white; font-size:12px; margin-top:5px;"></p>
"""
with st.sidebar:
    components.html(gps_code, height=90)


# --- XỬ LÝ VẼ BẢN ĐỒ GOOGLE MAPS (MAIN AREA) ---

# Tọa độ trung tâm mặc định (Tuyên Quang như trên ảnh)[cite: 1]
default_center = [21.823, 105.215]
zoom_level = 13

# Khởi tạo bản đồ Folium với Layer Google Maps RoadMap (Lớp xem phố)
m = folium.Map(
    location=default_center,
    zoom_start=zoom_level,
    tiles=None
)

# Thêm Layer Google Maps Standard Roadmap (Mặc định layer xem phố)
folium.TileLayer(
    tiles="https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}",
    attr="Google Maps",
    name="Google Maps (Phố)",
    overlay=False,
    control=True
).add_to(m)

# Thêm điểm được chọn lên bản đồ
route_coords = []
if selected_points:
    for point_name in selected_points:
        if point_name in tqgp_points:
            coord = tqgp_points[point_name]
            route_coords.append(coord)
            
            # Thêm Marker
            folium.Marker(
                location=coord,
                popup=point_name,
                tooltip=point_name if show_labels else None,
                icon=folium.Icon(color="red", icon="info-sign")
            ).add_to(m)

    # Nếu chọn tùy chọn vẽ đường và có ít nhất 2 điểm
    if show_routes and len(route_coords) >= 2:
        # Thuật toán vẽ đường nối giữa các điểm (Tuyến đường di chuyển)
        folium.PolyLine(
            locations=route_coords,
            color="blue",
            weight=5,
            opacity=0.8,
            tooltip="Lộ trình di chuyển xe máy"
        ).add_to(m)
        
        # Căn chỉnh view bản đồ vừa với tất cả các điểm
        m.fit_bounds(route_coords)

# Hiển thị bản đồ Full Màn Hình
st_folium(m, width="100%", height=780, returned_objects=[])
