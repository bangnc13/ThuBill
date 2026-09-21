import os
import json
import glob
import re
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

# CSS giao diện Sidebar
st.markdown("""
    <style>
        .block-container { padding-top: 1rem; padding-bottom: 0rem; padding-left: 1rem; padding-right: 1rem; }
        [data-testid="stSidebar"] { background-color: #1a1c23; color: white; }
        .stButton button { width: 100%; }
    </style>
""", unsafe_allow_html=True)

# --- SIDEBAR TÙY CHỈNH ---
with st.sidebar:
    st.markdown("<h1 style='color: #FF5722; margin-bottom:0;'>FPT Telecom</h1>", unsafe_allow_html=True)
    st.markdown("**Make by BangNC13**")
    st.markdown("---")

    # --- HÀM TRUY TÌM MÃ TQGP VÀ TỌA ĐỘ TRONG JSON ---
    def parse_item_for_tqgp(item, points_dict):
        """Quét sâu vào từng dict/list để lấy mã TQGP và Tọa độ"""
        if isinstance(item, dict):
            # 1. Tìm tên mã điểm có dạng TQGPxxx...
            point_name = None
            for val in item.values():
                if isinstance(val, str) and "TQGP" in val.upper():
                    point_name = val.strip()
                    break
            
            # Nếu key chính là tên mã điểm
            if not point_name:
                for k in item.keys():
                    if "TQGP" in str(k).upper():
                        point_name = str(k).strip()
                        break

            # 2. Tìm tọa độ (Lat, Lng)
            lat, lng = None, None

            # TH 1: GeoJSON format -> coordinates: [lng, lat]
            if 'geometry' in item and isinstance(item['geometry'], dict):
                coords = item['geometry'].get('coordinates', [])
                if len(coords) >= 2:
                    lng, lat = float(coords[0]), float(coords[1])
            
            # TH 2: Cột coordinates dạng [lng, lat] hoặc [lat, lng]
            if lat is None and 'coordinates' in item and isinstance(item['coordinates'], (list, tuple)):
                if len(item['coordinates']) >= 2:
                    c1, c2 = float(item['coordinates'][0]), float(item['coordinates'][1])
                    # Tuyên Quang / Việt Nam: Lat ~ 20-22, Lng ~ 105-106
                    if 10 < c1 < 30 and 100 < c2 < 110:
                        lat, lng = c1, c2
                    else:
                        lng, lat = c1, c2

            # TH 3: Lat/Lng hoặc Y/X nằm ở các key riêng
            if lat is None:
                for k_lat in ['lat', 'latitude', 'y', 'toado_y', 'lat_degree']:
                    if k_lat in item and item[k_lat] is not None:
                        try: lat = float(item[k_lat]); break
                        except: pass
                for k_lng in ['lng', 'long', 'longitude', 'x', 'toado_x', 'lng_degree']:
                    if k_lng in item and item[k_lng] is not None:
                        try: lng = float(item[k_lng]); break
                        except: pass

            # TH 4: Tọa độ là chuỗi "21.xxx, 105.xxx"
            if lat is None:
                for v in item.values():
                    if isinstance(v, str) and "," in v:
                        parts = v.split(",")
                        if len(parts) == 2:
                            try:
                                p1, p2 = float(parts[0].strip()), float(parts[1].strip())
                                if 10 < p1 < 30 and 100 < p2 < 110:
                                    lat, lng = p1, p2
                                elif 10 < p2 < 30 and 100 < p1 < 110:
                                    lat, lng = p2, p1
                            except: pass

            # Nếu tìm thấy cả tên và tọa độ hợp lệ
            if point_name and lat is not None and lng is not None:
                points_dict[point_name] = (lat, lng)

            # Đệ quy duyệt các dict/list con
            for k, v in item.items():
                if isinstance(v, (dict, list)):
                    parse_item_for_tqgp(v, points_dict)

        elif isinstance(item, list):
            for sub_item in item:
                parse_item_for_tqgp(sub_item, points_dict)

    # --- ĐỌC TẤT CẢ FILE JSON ---
    def load_tqgp_database():
        # Quét cả file hoa lẫn thường *.json, *.JSON
        json_files = glob.glob("*.json") + glob.glob("*.JSON")
        json_files = list(set(json_files))
        points = {}
        
        for file_path in json_files:
            content = None
            for enc in ['utf-8-sig', 'utf-8', 'latin-1', 'cp1252']:
                try:
                    with open(file_path, 'r', encoding=enc) as f:
                        content = json.load(f)
                        break
                except Exception:
                    continue
            
            if content:
                parse_item_for_tqgp(content, points)
                
        return json_files, points

    json_files, tqgp_database = load_tqgp_database()

    # Hiển thị trạng thái dữ liệu JSON
    if not json_files:
        st.warning("⚠️ Chưa tìm thấy file .json nào trong thư mục chạy code!")
    else:
        st.success(f"Dữ liệu: Đã tải {len(json_files)} file JSON ({len(tqgp_database)} điểm TQGP)")

    # Debug Log kiểm tra chi tiết
    with st.expander("🔍 Lịch sử kiểm tra (Debug Log)"):
        st.write(f"📁 Tổng file JSON tìm thấy: {len(json_files)}")
        st.write(f"📍 Tổng số điểm trích xuất được: {len(tqgp_database)}")
        if tqgp_database:
            st.write("Mẫu 5 điểm đầu tiên phát hiện:")
            st.json(dict(list(tqgp_database.items())[:5]))

    api_key = st.text_input("🔑 Google API Key (Tùy chọn)", type="password")
    st.markdown("---")
    
    end_point_input = st.text_input("🎯 Nhập điểm cuối hành trình (nếu muốn)", placeholder="Chợ Tam Cờ...")

    # Dropdown Chọn lộ trình thủ công
    selected_manual = st.multiselect(
        "📱 Chọn lộ trình di chuyển",
        options=list(tqgp_database.keys()),
        help="Chọn các điểm TQGPxxx.xxxx/HO cần đi qua"
    )

    # UPLOAD FILE EXCEL (Xử lý file book1.xlsx)
    st.markdown("**Hoặc Upload file Excel/CSV:**")
    uploaded_file = st.file_uploader("Upload file Excel", type=["xlsx", "xls", "csv"], label_visibility="collapsed")

    excel_points = {}
    if uploaded_file is not None:
        try:
            df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
            
            # Lấy danh sách tất cả các giá trị chuỗi trong file Excel có chứa chữ 'TQGP'
            excel_names = []
            for col in df.columns:
                for val in df[col].dropna():
                    val_str = str(val).strip()
                    if "TQGP" in val_str.upper():
                        excel_names.append(val_str)

            # Khớp tên từ Excel với Cơ sở dữ liệu Tọa độ từ JSON
            matched_count = 0
            for name in excel_names:
                # Tìm tương đối hoặc chính xác trong DB
                if name in tqgp_database:
                    excel_points[name] = tqgp_database[name]
                    matched_count += 1
                else:
                    # Thử tìm gần đúng
                    for db_name, coords in tqgp_database.items():
                        if name.upper() in db_name.upper() or db_name.upper() in name.upper():
                            excel_points[name] = coords
                            matched_count += 1
                            break

            if excel_names:
                st.success(f"📌 Đã đọc {len(excel_names)} mã điểm từ Excel. Khớp được {matched_count} tọa độ!")
                if matched_count == 0:
                    st.error("⚠️ File JSON chưa trích xuất được tọa độ của các điểm này. Hãy kiểm tra Debug Log!")
            else:
                st.error("⚠️ Không tìm thấy cột hoặc dữ liệu nào chứa mã 'TQGP' trong file Excel!")

        except Exception as e:
            st.error(f"Lỗi đọc file Excel: {e}")

    st.markdown("---")

    show_labels = st.checkbox("📌 Hiện tên điểm (Label)", value=True)
    show_routes = st.checkbox("🛣️ Hiện đường vẽ lộ trình", value=True)

    col1, col2 = st.columns(2)
    with col1:
        btn_refresh = st.button("🔄 Làm mới bản đồ")
    with col2:
        btn_route = st.button("🚀 Lộ trình", type="primary")

# --- LỰA CHỌN CÁC ĐIỂM SẼ VẼ TRÊN BẢN ĐỒ ---
points_to_render = {}

if uploaded_file is not None and excel_points:
    points_to_render = excel_points
elif selected_manual:
    points_to_render = {k: tqgp_database[k] for k in selected_manual if k in tqgp_database}
elif btn_route and tqgp_database:
    points_to_render = tqgp_database

# --- NÚT ĐỊNH VỊ GPS REALTIME ---
gps_code = """
<script>
function getLocation() {
  if (navigator.geolocation) {
    navigator.geolocation.getCurrentPosition(
        (pos) => { document.getElementById("gps_status").innerText = "GPS: " + pos.coords.latitude.toFixed(5) + ", " + pos.coords.longitude.toFixed(5); },
        (err) => { document.getElementById("gps_status").innerText = "Lỗi lấy GPS!"; }
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

# --- VẼ BẢN ĐỒ GOOGLE MAPS STREET VIEW ---
default_center = [21.823, 105.215] # Mặc định Tuyên Quang

if points_to_render:
    coords = list(points_to_render.values())
    default_center = [sum(p[0] for p in coords)/len(coords), sum(p[1] for p in coords)/len(coords)]

m = folium.Map(location=default_center, zoom_start=13, tiles=None)

# Lớp bản đồ Google Maps Xem phố
folium.TileLayer(
    tiles="https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}",
    attr="Google Maps",
    name="Google Maps Street",
    overlay=False
).add_to(m)

# Thêm Marker và Đường vẽ
route_coords = []
for name, coord in points_to_render.items():
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

# Hiển thị bản đồ Full View
st_folium(m, width="100%", height=800, returned_objects=[])
