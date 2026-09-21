import streamlit as st
import json
import os
import pandas as pd
import re
import streamlit.components.v1 as components

st.set_page_config(page_title="Quản lý hạ tầng cáp - FPT Telecom", layout="wide")

# ---------------------------------------------------------
# HÀM HỖ TRỢ XỬ LÝ DỮ LIỆU
# ---------------------------------------------------------
def clean_code(code_str):
    """Chuẩn hóa mã điểm để so sánh linh hoạt"""
    if not code_str or pd.isna(code_str):
        return ""
    return str(code_str).strip().upper()

def extract_coords_from_string(str_val):
    """Trích xuất tọa độ từ chuỗi kiểu (lat, lng)"""
    if not str_val or not isinstance(str_val, str):
        return []
    coords = []
    matches = re.findall(r'\(?\s*([0-9.]+)\s*,\s*([0-9.]+)\s*\)?', str_val)
    for lat, lng in matches:
        try:
            coords.append([float(lat), float(lng)])
        except ValueError:
            continue
    return coords

def load_json_from_folder(folder_path="data"):
    """Thử đọc tất cả file JSON/GeoJSON từ thư mục chỉ định"""
    all_features = []
    # Thử tìm ở thư mục truyền vào hoặc thư mục hiện tại
    paths_to_check = [folder_path, ".", "./data"]
    
    for path in paths_to_check:
        if os.path.exists(path) and os.path.isdir(path):
            for file_name in os.listdir(path):
                if file_name.endswith('.json') or file_name.endswith('.geojson'):
                    file_path = os.path.join(path, file_name)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            features = data.get('features', [])
                            all_features.extend(features)
                    except Exception:
                        pass
            if len(all_features) > 0:
                break
    return all_features

# ---------------------------------------------------------
# SIDEBAR: GIAO DIỆN ĐIỀU KHIỂN BÊN TRÁI
# ---------------------------------------------------------
with st.sidebar:
    st.title("FPT Telecom")
    st.caption("Make by BangNC13")
    
    # 1. Tải dữ liệu JSON tự động hoặc qua Upload
    raw_features = load_json_from_folder("data")
    
    # Tùy chọn Upload file JSON trực tiếp nếu chưa tìm thấy trong thư mục
    uploaded_json_files = st.file_uploader("📂 Upload file JSON/GeoJSON:", type=["json", "geojson"], accept_multiple_files=True)
    if uploaded_json_files:
        raw_features = []
        for file in uploaded_json_files:
            try:
                data = json.load(file)
                raw_features.extend(data.get('features', []))
            except Exception:
                pass

    st.success(f"Dữ liệu: Đã tải {len(raw_features)} đối tượng")

    # 2. Ô nhập Google API Key & Điểm cuối
    st.text_input("🔑 Google API Key (Tùy chọn)", type="password")
    end_point = st.text_input("🎯 Nhập điểm cuối hành trình (nếu muốn)", placeholder="Chợ Tam Cờ...")

    # 3. Lấy danh sách tên điểm từ JSON để cho vào Dropdown
    all_names = sorted(list(set([
        f['properties'].get('name', '') for f in raw_features if f.get('properties', {}).get('name')
    ])))

    # 4. Chọn lộ trình di chuyển
    selected_options = st.multiselect("📋 Chọn lộ trình di chuyển:", options=all_names)

    # 5. Upload file Excel / CSV
    uploaded_excel = st.file_uploader("Hoặc Upload file Excel/CSV:", type=["xlsx", "xls", "csv"])

    # Option hiển thị
    st.checkbox("Hiện tên điểm (Label)", value=True)
    st.checkbox("Hiện đường và lộ trình", value=True)

# ---------------------------------------------------------
# XỬ LÝ LỌC DỮ LIỆU ĐỂ HIỂN THỊ LÊN BẢN ĐỒ
# ---------------------------------------------------------
target_codes = []

# Đọc mã từ Excel
if uploaded_excel:
    try:
        df = pd.read_csv(uploaded_excel) if uploaded_excel.name.endswith('.csv') else pd.read_excel(uploaded_excel)
        for col in df.columns:
            target_codes.extend([clean_code(val) for val in df[col].dropna().tolist()])
        target_codes = list(set([c for c in target_codes if c]))
        st.sidebar.info(f"Đã đọc {len(target_codes)} mã từ Excel")
    except Exception as e:
        st.sidebar.error(f"Lỗi đọc file Excel: {e}")

# Gộp các mã được chọn ở Dropdown
if selected_options:
    target_codes.extend([clean_code(x) for x in selected_options])
    target_codes = list(set(target_codes))

matched_features = []
matched_cables = []

if target_codes:
    for feat in raw_features:
        props = feat.get('properties', {})
        feat_name = clean_code(props.get('name', ''))
        head_point = clean_code(props.get('headPoint', ''))
        tail_point = clean_code(props.get('tailPoint', ''))

        # Lọc linh hoạt (Chấp nhận chứa chuỗi con)
        is_match = any(
            (code in feat_name) or (feat_name in code) or 
            (code in head_point) or (code in tail_point) 
            for code in target_codes if code
        )

        if is_match:
            if props.get('hasCable') == 1 or 'latlngCable' in props or 'tailHeadLatLng' in props:
                matched_cables.append(feat)
            else:
                matched_features.append(feat)

    st.sidebar.success(f"Khớp: {len(matched_features)} điểm, {len(matched_cables)} cáp")
else:
    st.sidebar.warning("Vui lòng chọn hoặc upload danh sách điểm để hiển thị lộ trình.")

# ---------------------------------------------------------
# BẢN ĐỒ LEAFLET
# ---------------------------------------------------------
filtered_data_json = json.dumps({
    "points": matched_features,
    "cables": matched_cables
}, ensure_ascii=False)

html_code = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <style>
        html, body, #map {{
            height: 100%;
            width: 100%;
            margin: 0;
            padding: 0;
        }}
    </style>
</head>
<body>
<div id="map"></div>

<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script>
    var map = L.map('map').setView([21.817, 105.207], 13);

    L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
        attribution: '&copy; OpenStreetMap'
    }}).addTo(map);

    var data = {filtered_data_json};
    var bounds = [];

    // Vẽ điểm
    data.points.forEach(function(feat) {{
        var props = feat.properties || {{}};
        var lat = null, lng = null;

        if (feat.geometry && feat.geometry.coordinates) {{
            lng = feat.geometry.coordinates[0];
            lat = feat.geometry.coordinates[1];
        }} else if (props.latLng) {{
            var match = props.latLng.match(/\(?\s*([0-9.]+)\s*,\s*([0-9.]+)\s*\)?/);
            if (match) {{
                lat = parseFloat(match[1]);
                lng = parseFloat(match[2]);
            }}
        }}

        if (lat && lng) {{
            var marker = L.circleMarker([lat, lng], {{
                radius: 8,
                fillColor: "#e74c3c",
                color: "#ffffff",
                weight: 2,
                fillOpacity: 0.9
            }}).addTo(map);

            marker.bindPopup("<b>" + (props.name || "Tập điểm") + "</b><br/>ID: " + (props.id || ""));
            marker.bindTooltip(props.name || "", {{permanent: false, direction: 'top'}});
            bounds.push([lat, lng]);
        }}
    }});

    function parseCoords(str) {{
        if (!str) return [];
        var res = [];
        var regex = /\(?\s*([0-9.]+)\s*,\s*([0-9.]+)\s*\)?/g;
        var match;
        while ((match = regex.exec(str)) !== null) {{
            res.push([parseFloat(match[1]), parseFloat(match[2])]);
        }}
        return res;
    }}

    // Vẽ cáp
    data.cables.forEach(function(feat) {{
        var props = feat.properties || {{}};
        var lineCoords = parseCoords(props.latlngCable) || parseCoords(props.tailHeadLatLng);

        if (lineCoords.length > 0) {{
            var polyline = L.polyline(lineCoords, {{
                color: props.color || "#0055ff",
                weight: 4,
                opacity: 0.8
            }}).addTo(map);

            polyline.bindPopup("<b>Cáp: " + (props.name || "") + "</b>");
            lineCoords.forEach(function(pt) {{ bounds.push(pt); }});
        }}
    }});

    if (bounds.length > 0) {{
        map.fitBounds(bounds, {{padding: [50, 50]}});
    }}
</script>
</body>
</html>
"""

components.html(html_code, height=800)
