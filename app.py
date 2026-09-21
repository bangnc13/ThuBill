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
    # Chuyển thành chữ hoa, xóa khoảng trắng thừa
    return str(code_str).strip().upper()

def extract_coords_from_string(str_val):
    """Trích xuất danh sách [lat, lng] từ các chuỗi chứa tọa độ như (21.x, 105.x);..."""
    if not str_val or not isinstance(str_val, str):
        return []
    coords = []
    # Tìm các cặp số dạng (lat, lng)
    matches = re.findall(r'\(?\s*([0-9.]+)\s*,\s*([0-9.]+)\s*\)?', str_val)
    for lat, lng in matches:
        try:
            coords.append([float(lat), float(lng)])
        except ValueError:
            continue
    return coords

@st.cache_data
def load_all_json_data(json_folder_path="data"):
    """Đọc tất cả file JSON/GeoJSON trong thư mục"""
    all_features = []
    if not os.path.exists(json_folder_path):
        return all_features

    for file_name in os.listdir(json_folder_path):
        if file_name.endswith('.json') or file_name.endswith('.geojson'):
            file_path = os.path.join(json_folder_path, file_name)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    features = data.get('features', [])
                    all_features.extend(features)
            except Exception as e:
                pass
    return all_features

# ---------------------------------------------------------
# GIAO DIỆN CHÍNH (SIDEBAR)
# ---------------------------------------------------------
st.sidebar.title("FPT Telecom")
st.sidebar.caption("Make by BangNC13")

# Tải toàn bộ dữ liệu JSON vào bộ nhớ
raw_features = load_all_json_data("data")  # Thay "data" bằng đường dẫn thư mục chứa 37 file JSON của bạn

st.sidebar.success(f"Dữ liệu: Đã tải {len(raw_features)} đối tượng từ JSON")

# 1. Chọn điểm từ Dropdown Selectbox
selected_options = st.sidebar.multiselect(
    "📋 Chọn lộ trình di chuyển:",
    options=list(set([f['properties'].get('name', '') for f in raw_features if f.get('properties', {}).get('name')]))
)

# 2. Upload file Excel
uploaded_file = st.sidebar.file_uploader("Hoặc Upload file Excel/CSV:", type=["xlsx", "xls", "csv"])

target_codes = []

# Đọc danh sách mã cần tìm từ Excel
if uploaded_file:
    try:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
        
        # Lấy tất cả giá trị dạng chuỗi từ file Excel
        for col in df.columns:
            target_codes.extend([clean_code(val) for val in df[col].dropna().tolist()])
        target_codes = list(set([c for c in target_codes if c]))
        st.sidebar.info(f"Đã đọc {len(target_codes)} mã từ Excel")
    except Exception as e:
        st.sidebar.error(f"Lỗi đọc file Excel: {e}")

# Gộp các mã chọn từ dropdown
if selected_options:
    target_codes.extend([clean_code(x) for x in selected_options])
    target_codes = list(set(target_codes))

# ---------------------------------------------------------
# LỌC DỮ LIỆU: CHỈ LẤY CÁC ĐIỂM THUỘC DANH SÁCH YÊU CẦU
# ---------------------------------------------------------
matched_features = []
matched_cables = []

if target_codes:
    for feat in raw_features:
        props = feat.get('properties', {})
        feat_name = clean_code(props.get('name', ''))
        head_point = clean_code(props.get('headPoint', ''))
        tail_point = clean_code(props.get('tailPoint', ''))

        # Kiểm tra xem tên điểm hoặc điểm đầu/cuối của cáp có khớp với danh sách không (Khớp linh hoạt)
        is_match = any(
            (code in feat_name) or (feat_name in code) or 
            (code in head_point) or (code in tail_point) 
            for code in target_codes if code
        )

        if is_match:
            #Phân loại Cáp hoặc Điểm
            if props.get('hasCable') == 1 or 'latlngCable' in props or 'tailHeadLatLng' in props:
                matched_cables.append(feat)
            else:
                matched_features.append(feat)

    st.sidebar.success(f"Khớp thành công: {len(matched_features)} điểm, {len(matched_cables)} đường cáp")
else:
    st.sidebar.warning("Vui lòng chọn hoặc upload danh sách điểm để hiển thị lộ trình.")

# ---------------------------------------------------------
# RENDER BẢN ĐỒ LEAFLET VIA HTML/JS
# ---------------------------------------------------------
# Chuyển đổi dữ liệu đã lọc sang JSON string để truyền vào Javascript
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

    // 1. Vẽ các điểm (Points/Tập điểm)
    data.points.forEach(function(feat) {{
        var props = feat.properties || {{}};
        var lat = null, lng = null;

        // Trích xuất tọa độ từ Geometry hoặc thuộc tính latLng
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
            marker.bindTooltip(props.name || "", {{permanent: true, direction: 'top', className: 'label-style'}});
            bounds.push([lat, lng]);
        }}
    }});

    // Hàm hỗ trợ tách chuỗi tọa độ cáp
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

    // 2. Vẽ tuyến cáp (Polylines)
    data.cables.forEach(function(feat) {{
        var props = feat.properties || {{}};
        var lineCoords = parseCoords(props.latlngCable) || parseCoords(props.tailHeadLatLng);

        if (lineCoords.length > 0) {{
            var polyline = L.polyline(lineCoords, {{
                color: props.color || "#0055ff",
                weight: 4,
                opacity: 0.8
            }}).addTo(map);

            polyline.bindPopup("<b>Cáp: " + (props.name || "") + "</b><br/>Dung lượng: " + (props.capacity || ""));
            lineCoords.forEach(function(pt) {{ bounds.push(pt); }});
        }}
    }});

    // Tự động Zoom đến khu vực có điểm/cáp được chọn
    if (bounds.length > 0) {{
        map.fitBounds(bounds, {{padding: [50, 50]}});
    }}
</script>
</body>
</html>
"""

components.html(html_code, height=800)
