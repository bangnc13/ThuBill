import os
import json
import glob
import pandas as pd
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

# Tùy chỉnh CSS giao diện Sidebar
st.markdown("""
    <style>
        .block-container { padding-top: 1rem; padding-bottom: 0rem; padding-left: 1rem; padding-right: 1rem; }
        [data-testid="stSidebar"] { background-color: #1a1c23; color: white; }
        .stButton button { width: 100%; }
    </style>
""", unsafe_allow_html=True)

# --- THÔNG TIN TỔ CHỨC & TÁC GIẢ (SIDEBAR) ---
with st.sidebar:
    st.markdown("<h1 style='color: #FF5722; margin-bottom:0;'>FPT Telecom</h1>", unsafe_allow_html=True)
    st.markdown("**Make by BangNC13**")
    st.markdown("---")

    # --- HÀM ĐỌC DỮ LIỆU TỪ FILE JSON CẢI TIẾN ---
    def extract_points_from_json_data(data, points_dict):
        """Hàm đệ quy quét mọi cấu trúc JSON để tìm lat, lng và name"""
        if isinstance(data, dict):
            # Kiểm tra nếu object hiện tại chứa tên điểm và tọa độ
            name = data.get("name") or data.get("ten") or data.get("label") or data.get("id")
            lat = data.get("lat") or data.get("latitude") or data.get("y")
            lng = data.get("lng") or data.get("long") or data.get("longitude") or data.get("x")
            
            if name and lat is not None and lng is not None:
                if "TQGP" in str(name).upper():
                    points_dict[str(name)] = (float(lat), float(lng))
            
            for k, v in data.items():
                if isinstance(v, (dict, list)):
                    extract_points_from_json_data(v, points_dict)
                elif "TQGP" in str(k).upper() and isinstance(v, (list, tuple)) and len(v) >= 2:
                    points_dict[str(k)] = (float(v[0]), float(v[1]))

        elif isinstance(data, list):
            for item in data:
                extract_points_from_json_data(item, points_dict)

    def load_all_tqgp_json():
        json_files = glob.glob("*.json")
        points = {}
        for file in json_files:
            try:
                with open(file, 'r', encoding='utf-8') as f:
                    content = json.load(f)
                    extract_points_from_json_data(content, points)
            except Exception:
                pass
        return json_files, points

    json_files, tqgp_points = load_all_tqgp_json()

    # Khởi tạo state lưu trữ điểm được chọn
    if "selected_points_list" not in st.session_state:
        st.session_state.selected_points_list = []

    # Thông báo số lượng dữ liệu
    if not json_files:
        st.warning("⚠️ Chưa tìm thấy file .json nào trong thư mục!")
    else:
        st.success(f"Dữ liệu: Đã tải {len(json_files)} file JSON ({len(tqgp_points)} điểm TQGP)")

    # Debug Log & API Key
    with st.expander("🔍 Lịch sử kiểm tra (Debug Log)"):
        st.write(f"Tổng số file JSON tìm thấy: {len(json_files)}")
        st.write(f"Danh sách các điểm lọc được ({len(tqgp_points)}):")
        st.json(list(tqgp_points.keys())[:10])  # Hiển thị 10 điểm đầu tiên để test

    api_key = st.text_input("🔑 Google API Key (Tùy chọn)", type="password")
    st.markdown("---")
    
    # Nhập điểm cuối
    end_point_input = st.text_input("🎯 Nhập điểm cuối hành trình (nếu muốn)", placeholder="Chợ Tam Cờ...")
    
    # Selectbox chọn điểm thủ công
    manual_selected = st.multiselect(
        "📱 Chọn lộ trình di chuyển",
        options=list(tqgp_points.keys()),
        default=st.session_state.selected_points_list,
        help="Chọn các điểm TQGPxxx.xxxx/HO cần đi qua"
    )

    # UPLOAD FILE EXCEL / CSV
    st.markdown("**Hoặc Upload file Excel/CSV:**")
    uploaded_file = st.file_uploader("Upload file Excel danh sách điểm", type=["xlsx", "xls", "csv"], label_visibility="collapsed")

    excel_points = {}
    if uploaded_file is not None:
        try:
            if uploaded_file.name.endswith('.csv'):
                df = pd.read_csv(uploaded_file)
            else:
                df = pd.read_excel(uploaded_file)
            
            # Tìm các cột tương ứng
            name_col = next((col for col in df.columns if any(k in col.lower() for k in ['ten', 'name', 'diem', 'tqgp'])), df.columns[0])
            lat_col = next((col for col in df.columns if any(k in col.lower() for k in ['lat', 'y', 'toado_y'])), None)
            lng_col = next((col for col in df.columns if any(k in col.lower() for k in ['lng', 'long', 'x', 'toado_x'])), None)

            for _, row in df.iterrows():
                pt_name = str(row[name_col]).strip()
                if lat_col and lng_col and pd.notnull(row[lat_col]) and pd.notnull(row[lng_col]):
                    excel_points[pt_name] = (float(row[lat_col]), float(row[lng_col]))
                elif pt_name in tqgp_points:
                    excel_points[pt_name] = tqgp_points[pt_name]

            st.success(f"📌 Đã đọc {len(excel_points)} điểm từ file Excel upload!")
        except Exception as e:
            st.error(f"Lỗi đọc file Excel: {e}")

    st.markdown("---")

    # Các tùy chọn vẽ
    show_labels = st.checkbox("📌 Hiện tên điểm (Label)", value=True)
    show_routes = st.checkbox("🛣️ Hiện đường vẽ lộ trình", value=True)

    col1, col2 = st.columns(2)
    with col1:
        btn_refresh = st.button("🔄 Làm mới bản đồ")
    with col2:
        btn_route = st.button("🚀 Lộ trình", type="primary")

# --- XỬ LÝ KHI BẤM NÚT "LỘ TRÌNH" HOẶC CHỌN ĐIỂM ---
active_points = {}

if btn_route:
    # Ưu tiên lấy từ file Excel vừa upload, nếu không thì lấy từ Multiselect
    if excel_points:
        active_points = excel_points
    elif manual_selected:
        active_points = {k: tqgp_points[k] for k in manual_selected if k in tqgp_points}
    else:
        # Nếu không chọn gì, lấy tất cả điểm tìm được
        active_points = tqgp_points
else:
    if manual_selected:
        active_points = {k: tqgp_points[k] for k in manual_selected if k in tqgp_points}

# --- NÚT LẤY ĐỊNH VỊ REALTIME TỪ ĐIỆN THOẠI/TRÌNH DUYỆT ---
gps_code = """
<script>
function getLocation() {
  if (navigator.geolocation) {
    navigator.geolocation.getCurrentPosition(
        (pos) => { document.getElementById("gps_status").innerText = "Tọa độ GPS: " + pos.coords.latitude.toFixed(5) + ", " + pos.coords.longitude.toFixed(5); },
        (err) => { document.getElementById("gps_status").innerText = "Không thể lấy vị trí GPS."; }
    );
  }
}
</script>
<button onclick="getLocation()" style="width:100%; padding:8px; background-color:#28a745; color:white; border:none; border-radius:4px; cursor:pointer;">
    📍 Định vị Realtime
</button>
<p id="gps_status" style="color:#aaa; font-size:12px; margin-top:5px; text-align:center;"></p>
"""
with st.sidebar:
    components.html(gps_code, height=80)

# --- XỬ LÝ VẼ BẢN ĐỒ GOOGLE MAPS (MAIN VIEW) ---
default_center = [21.823, 105.215]  # Tuyên Quang
zoom_level = 13

if active_points:
    coords_list = list(active_points.values())
    default_center = [sum(p[0] for p in coords_list)/len(coords_list), sum(p[1] for p in coords_list)/len(coords_list)]

m = folium.Map(location=default_center, zoom_start=zoom_level, tiles=None)

# Layer xem phố Google Maps Roadmap (Chuẩn)
folium.TileLayer(
    tiles="https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}",
    attr="Google Maps",
    name="Google Maps Street",
    overlay=False
).add_to(m)

# Thêm điểm & đường nối lộ trình
route_coords = []
for name, coord in active_points.items():
    route_coords.append(coord)
    folium.Marker(
        location=coord,
        popup=name,
        tooltip=name if show_labels else None,
        icon=folium.Icon(color="red", icon="info-sign")
    ).add_to(m)

if show_routes and len(route_coords) >= 2:
    folium.PolyLine(
        locations=route_coords,
        color="#1E88E5",
        weight=5,
        opacity=0.8,
        tooltip="Lộ trình di chuyển xe máy"
    ).add_to(m)
    m.fit_bounds(route_coords)

# Hiển thị bản đồ Full màn hình
st_folium(m, width="100%", height=800, returned_objects=[])
