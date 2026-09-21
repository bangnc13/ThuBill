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

    # --- HÀM ĐỌC VÀ TRÍCH XUẤT ĐIỂM TỪ FILE JSON BẰNG REGEX & DEEP PARSE ---
    def extract_tqgp_from_json():
        json_files = glob.glob("*.json") + glob.glob("*.JSON")
        json_files = list(set(json_files))
        points = {}
        sample_json_content = None

        for file_path in json_files:
            raw_text = ""
            for enc in ['utf-8-sig', 'utf-8', 'latin-1', 'cp1252']:
                try:
                    with open(file_path, 'r', encoding=enc) as f:
                        raw_text = f.read()
                        if not sample_json_content:
                            sample_json_content = raw_text[:500]  # Lưu mẫu 500 ký tự đầu để Debug
                        break
                except Exception:
                    continue
            
            if not raw_text:
                continue

            # Phương pháp 1: Thử parse dạng JSON chuẩn
            try:
                data = json.loads(raw_text)
                
                def walk_data(obj):
                    if isinstance(obj, dict):
                        # Bóc tách tên và tọa độ từ dict
                        name, lat, lng = None, None
                        for k, v in obj.items():
                            if isinstance(v, str) and "TQGP" in v.upper():
                                name = v.strip()
                            elif "TQGP" in str(k).upper():
                                name = str(k).strip()

                        # Tìm Lat/Lng
                        for k, v in obj.items():
                            k_lower = str(k).lower()
                            if k_lower in ['lat', 'latitude', 'y', 'toado_y'] and isinstance(v, (int, float)):
                                lat = float(v)
                            elif k_lower in ['lng', 'long', 'longitude', 'x', 'toado_x'] and isinstance(v, (int, float)):
                                lng = float(v)

                        # Dạng GeoJSON
                        if 'coordinates' in obj and isinstance(obj['coordinates'], (list, tuple)) and len(obj['coordinates']) >= 2:
                            c1, c2 = float(obj['coordinates'][0]), float(obj['coordinates'][1])
                            lng, lat = (c1, c2) if c1 > c2 else (c2, c1)

                        if name and lat is not None and lng is not None:
                            points[name] = (lat, lng)

                        for v in obj.values():
                            if isinstance(v, (dict, list)):
                                walk_data(v)

                    elif isinstance(obj, list):
                        for item in obj:
                            walk_data(item)

                walk_data(data)
            except Exception:
                pass

            # Phương pháp 2: Quét Regex trực tiếp nếu JSON bị đóng gói chuỗi/không chuẩn
            if len(points) == 0:
                # Tìm tất cả mã TQGP
                tqgp_matches = re.findall(r'TQGP[A-Za-z0-9\./\-_]+', raw_text)
                # Tìm tất cả tọa độ dạng (21.xxxx, 105.xxxx)
                coord_matches = re.findall(r'(\d{2}\.\d+)\s*,\s*(\d{3}\.\d+)', raw_text)
                
                if tqgp_matches and coord_matches:
                    for i in range(min(len(tqgp_matches), len(coord_matches))):
                        m_lat, m_lng = float(coord_matches[i][0]), float(coord_matches[i][1])
                        points[tqgp_matches[i]] = (m_lat, m_lng)

        return json_files, points, sample_json_content

    json_files, tqgp_database, sample_json_content = extract_tqgp_from_json()

    # Trạng thái dữ liệu JSON
    if not json_files:
        st.warning("⚠️ Chưa tìm thấy file .json nào trong thư mục chạy code!")
    else:
        st.success(f"Dữ liệu: Đã tải {len(json_files)} file JSON ({len(tqgp_database)} điểm TQGP)")

    # Debug Log mở rộng
    with st.expander("🔍 Lịch sử kiểm tra (Debug Log)"):
        st.write(f"📁 Tổng file JSON phát hiện: {len(json_files)}")
        st.write(f"📍 Tổng điểm trích xuất được: {len(tqgp_database)}")
        if sample_json_content:
            st.markdown("**Mẫu nội dung trong file JSON:**")
            st.code(sample_json_content, language="json")

    api_key = st.text_input("🔑 Google API Key (Tùy chọn)", type="password")
    st.markdown("---")
    
    end_point_input = st.text_input("🎯 Nhập điểm cuối hành trình (nếu muốn)", placeholder="Chợ Tam Cờ...")

    # Dropdown Chọn lộ trình thủ công
    selected_manual = st.multiselect(
        "📱 Chọn lộ trình di chuyển",
        options=list(tqgp_database.keys()),
        help="Chọn các điểm TQGPxxx.xxxx/HO cần đi qua"
    )

    # UPLOAD FILE EXCEL
    st.markdown("**Hoặc Upload file Excel/CSV:**")
    uploaded_file = st.file_uploader("Upload file Excel", type=["xlsx", "xls", "csv"], label_visibility="collapsed")

    excel_points = {}
    if uploaded_file is not None:
        try:
            df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
            
            # Lấy toàn bộ danh sách mã điểm từ file Excel
            excel_names = []
            for col in df.columns:
                for val in df[col].dropna():
                    val_clean = str(val).strip()
                    if "TQGP" in val_clean.upper():
                        excel_names.append(val_clean)

            # Đọc tọa độ trực tiếp từ Excel nếu Excel có chứa cột Tọa độ
            col_lat = next((c for c in df.columns if any(k in str(c).lower() for k in ['lat', 'y', 'toado_y'])), None)
            col_lng = next((c for c in df.columns if any(k in str(c).lower() for k in ['lng', 'long', 'x', 'toado_x'])), None)
            col_name = next((c for c in df.columns if any(k in str(c).lower() for k in ['name', 'ten', 'diem', 'tqgp'])), df.columns[0])

            matched_count = 0
            if col_lat and col_lng:
                for _, row in df.iterrows():
                    p_name = str(row[col_name]).strip()
                    try:
                        excel_points[p_name] = (float(row[col_lat]), float(row[col_lng]))
                        matched_count += 1
                    except: pass
            else:
                # Nếu Excel chỉ có tên mã điểm -> So sánh với database JSON
                for name in excel_names:
                    # Chuẩn hóa chuỗi so sánh
                    norm_name = re.sub(r'[^A-ZA-Z0-9]', '', name.upper())
                    
                    found = False
                    for db_name, coords in tqgp_database.items():
                        norm_db = re.sub(r'[^A-ZA-Z0-9]', '', db_name.upper())
                        if norm_name in norm_db or norm_db in norm_name:
                            excel_points[name] = coords
                            matched_count += 1
                            found = True
                            break

            st.success(f"📌 Đã đọc {len(excel_names)} mã điểm từ Excel. Khớp được {matched_count} tọa độ!")
            if len(excel_names) > 0 and matched_count == 0:
                st.error("⚠️ File JSON chưa trích xuất được tọa độ của các điểm này. Vui lòng mở Debug Log để kiểm tra cấu trúc JSON.")

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

# --- XỬ LÝ DỮ LIỆU ĐỂ HỌA ĐỒ ---
points_to_render = {}

if uploaded_file is not None and excel_points:
    points_to_render = excel_points
elif selected_manual:
    points_to_render = {k: tqgp_database[k] for k in selected_manual if k in tqgp_database}
elif btn_route and tqgp_database:
    points_to_render = tqgp_database

# --- NÚT ĐỊNH VỊ REALTIME ---
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

# --- VẼ BẢN ĐỒ GOOGLE MAPS ---
default_center = [21.823, 105.215]  # Tuyên Quang

if points_to_render:
    coords = list(points_to_render.values())
    default_center = [sum(p[0] for p in coords)/len(coords), sum(p[1] for p in coords)/len(coords)]

m = folium.Map(location=default_center, zoom_start=13, tiles=None)

# Layer xem phố Google Maps
folium.TileLayer(
    tiles="https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}",
    attr="Google Maps",
    name="Google Maps Street",
    overlay=False
).add_to(m)

# Thêm Marker và Polyline
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
        tooltip="Lộ trình di chuyển"
    ).add_to(m)
    m.fit_bounds(route_coords)

# Hiển thị Full màn hình
st_folium(m, width="100%", height=800, returned_objects=[])
