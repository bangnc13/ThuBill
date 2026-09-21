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

# --- THÔNG TIN TỔ CHỨC & TÁC GIẢ ---
with st.sidebar:
    st.markdown("<h1 style='color: #FF5722; margin-bottom:0;'>FPT Telecom</h1>", unsafe_allow_html=True)
    st.markdown("**Make by BangNC13**")
    st.markdown("---")

    # --- HÀM TRUY XUẤT TỌA ĐỘ VÀ TÊN TỪ MỌI DẠNG OBJECT/LIST ---
    def find_points_recursive(item, points_dict):
        if isinstance(item, dict):
            # Tìm tên điểm
            name = None
            for key in ['name', 'ten', 'label', 'id', 'ma_diem', 'point_name', 'title']:
                if key in item and item[key]:
                    name = str(item[key]).strip()
                    break
            
            # Nếu key chính là tên điểm (dạng {"TQGP001.0001/HO": [21.8, 105.2]})
            if not name:
                for k, v in item.items():
                    if "TQGP" in str(k).upper():
                        if isinstance(v, (list, tuple)) and len(v) >= 2:
                            try:
                                points_dict[str(k).strip()] = (float(v[0]), float(v[1]))
                            except: pass
                        elif isinstance(v, dict):
                            find_points_recursive(v, points_dict)

            # Tìm tọa độ lat, lng
            lat, lng = None, None
            # Trường hợp 1: Có key lat/lng/x/y trực tiếp
            for k_lat in ['lat', 'latitude', 'y', 'toado_y', 'lat_degree']:
                if k_lat in item and item[k_lat] is not None:
                    try: lat = float(item[k_lat])
                    except: pass
                    break
            for k_lng in ['lng', 'long', 'longitude', 'x', 'toado_x', 'lng_degree']:
                if k_lng in item and item[k_lng] is not None:
                    try: lng = float(item[k_lng])
                    except: pass
                    break
            
            # Trường hợp 2: Dạng GeoJSON coordinates [lng, lat]
            if lat is None and 'coordinates' in item and isinstance(item['coordinates'], (list, tuple)):
                if len(item['coordinates']) >= 2:
                    try:
                        lng = float(item['coordinates'][0])
                        lat = float(item['coordinates'][1])
                    except: pass

            # Lưu vào dictionary nếu hợp lệ
            if name and lat is not None and lng is not None:
                # Lấy tất cả điểm hoặc lọc theo TQGP
                points_dict[name] = (lat, lng)

            # Tiếp tục duyệt đệ quy các key con
            for k, v in item.items():
                if isinstance(v, (dict, list)):
                    find_points_recursive(v, points_dict)

        elif isinstance(item, list):
            for sub_item in item:
                find_points_recursive(sub_item, points_dict)

    # --- HÀM ĐỌC FILE JSON VỚI NHIỀU CHẾ ĐỘ ENCODING ---
    def load_all_tqgp_json():
        json_files = glob.glob("*.json")
        points = {}
        for file in json_files:
            content = None
            # Thử nhiều chuẩn encoding khác nhau để tránh lỗi font/đọc file
            for enc in ['utf-8-sig', 'utf-8', 'latin-1', 'cp1252']:
                try:
                    with open(file, 'r', encoding=enc) as f:
                        content = json.load(f)
                        break
                except Exception:
                    continue
            
            if content:
                find_points_recursive(content, points)
                
        return json_files, points

    json_files, tqgp_points = load_all_tqgp_json()

    # Thống kê số lượng
    if not json_files:
        st.warning("⚠️ Chưa tìm thấy file .json nào trong thư mục!")
    else:
        st.success(f"Dữ liệu: Đã tải {len(json_files)} file JSON ({len(tqgp_points)} điểm TQGP)")

    # Debug Log
    with st.expander("🔍 Lịch sử kiểm tra (Debug Log)"):
        st.write(f"Tổng số file JSON phát hiện: {len(json_files)}")
        st.write(f"Tổng số điểm tìm thấy: {len(tqgp_points)}")
        if tqgp_points:
            st.write("Danh sách 5 điểm mẫu:")
            st.write(list(tqgp_points.items())[:5])

    api_key = st.text_input("🔑 Google API Key (Tùy chọn)", type="password")
    st.markdown("---")
    
    end_point_input = st.text_input("🎯 Nhập điểm cuối hành trình (nếu muốn)", placeholder="Chợ Tam Cờ...")
    
    # Danh sách chọn điểm thủ công
    options_list = list(tqgp_points.keys())
    selected_manual = st.multiselect(
        "📱 Chọn lộ trình di chuyển",
        options=options_list,
        help="Chọn các điểm TQGPxxx.xxxx/HO cần đi qua"
    )

    # XỬ LÝ UPLOAD FILE EXCEL / CSV
    st.markdown("**Hoặc Upload file Excel/CSV:**")
    uploaded_file = st.file_uploader("Upload file Excel/CSV", type=["xlsx", "xls", "csv"], label_visibility="collapsed")

    excel_points = {}
    if uploaded_file is not None:
        try:
            if uploaded_file.name.endswith('.csv'):
                df = pd.read_csv(uploaded_file)
            else:
                df = pd.read_excel(uploaded_file)
            
            # Ép tên cột về dạng chữ thường để dễ so sánh
            df.columns = [str(c).strip() for c in df.columns]
            
            # Tìm các cột Tên, Lat, Lng
            col_name = next((c for c in df.columns if any(k in c.lower() for k in ['ten', 'name', 'diem', 'tqgp', 'id', 'label'])), df.columns[0])
            col_lat = next((c for c in df.columns if any(k in c.lower() for k in ['lat', 'y', 'toado_y', 'latitude'])), None)
            col_lng = next((c for c in df.columns if any(k in c.lower() for k in ['lng', 'long', 'x', 'toado_x', 'longitude'])), None)

            for _, row in df.iterrows():
                pt_name = str(row[col_name]).strip()
                
                # Nếu file Excel có cả cột Tọa độ
                if col_lat and col_lng and pd.notnull(row[col_lat]) and pd.notnull(row[col_lng]):
                    try:
                        excel_points[pt_name] = (float(row[col_lat]), float(row[col_lng]))
                    except: pass
                # Nếu file Excel chỉ chứa tên điểm -> Khớp tên với tập điểm từ JSON
                elif pt_name in tqgp_points:
                    excel_points[pt_name] = tqgp_points[pt_name]

            st.success(f"📌 Đã đọc {len(excel_points)} điểm từ file Excel upload!")
            if len(excel_points) == 0:
                st.error("⚠️ Không tìm thấy tọa độ khớp trong Excel hay JSON! Kiểm tra lại tên cột hoặc tên điểm.")
        except Exception as e:
            st.error(f"Lỗi đọc file Excel: {e}")

    st.markdown("---")

    # Checkbox Tùy chỉnh
    show_labels = st.checkbox("📌 Hiện tên điểm (Label)", value=True)
    show_routes = st.checkbox("🛣️ Hiện đường vẽ lộ trình", value=True)

    col1, col2 = st.columns(2)
    with col1:
        btn_refresh = st.button("🔄 Làm mới bản đồ")
    with col2:
        btn_route = st.button("🚀 Lộ trình", type="primary")

# --- QUYẾT ĐỊNH DANH SÁCH ĐIỂM SẼ HỌA ĐỒ ---
points_to_draw = {}

if btn_route or uploaded_file is not None:
    if excel_points:
        points_to_draw = excel_points
    elif selected_manual:
        points_to_draw = {k: tqgp_points[k] for k in selected_manual if k in tqgp_points}
    else:
        points_to_draw = tqgp_points
else:
    if selected_manual:
        points_to_draw = {k: tqgp_points[k] for k in selected_manual if k in tqgp_points}

# --- NÚT ĐỊNH VỊ REALTIME ---
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

# --- VẼ BẢN ĐỒ GOOGLE MAPS ---
default_center = [21.823, 105.215]  # Tuyên Quang

if points_to_draw:
    coords_list = list(points_to_draw.values())
    default_center = [sum(p[0] for p in coords_list)/len(coords_list), sum(p[1] for p in coords_list)/len(coords_list)]

m = folium.Map(location=default_center, zoom_start=13, tiles=None)

# Lớp bản đồ đường phố Google Maps
folium.TileLayer(
    tiles="https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}",
    attr="Google Maps",
    name="Google Maps Street",
    overlay=False
).add_to(m)

# Thêm marker và vẽ đường
route_coords = []
for name, coord in points_to_draw.items():
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
        tooltip="Lộ trình di chuyển"
    ).add_to(m)
    m.fit_bounds(route_coords)

# Hiển thị Full Screen
st_folium(m, width="100%", height=800, returned_objects=[])
