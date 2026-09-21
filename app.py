import json
import math
import os
from concurrent.futures import ThreadPoolExecutor

import folium
from folium.plugins import LocateControl
import pandas as pd
import requests
import streamlit as st
import streamlit.components.v1 as components
from streamlit_folium import st_folium

# -------------------------------------------------------------
# CẤU HÌNH TRANG STREAMLIT
# -------------------------------------------------------------
st.set_page_config(
    page_title="Tối ưu đường di chuyển xe máy - Tuyên Quang",
    layout="wide",
    initial_sidebar_state="expanded",
)

# -------------------------------------------------------------
# 1. LOGO & CSS HIỆU ỨNG
# -------------------------------------------------------------
logo_path = "FPT_Telecom_logo.png"
if os.path.exists(logo_path):
    st.sidebar.image(logo_path, use_container_width=True)

st.markdown(
    """
    <style>
    html, body, [data-testid="stAppViewContainer"], .main, .block-container {
        padding: 0 !important; 
        margin: 0 !important; 
        height: 100vh !important; 
        overflow: hidden !important;
    }
    [data-testid="stVerticalBlock"] { gap: 0rem !important; }
    header[data-testid="stHeader"] { 
        height: 0px !important; 
        background: transparent !important; 
        z-index: 99999 !important; 
    }
    @keyframes neonBlinkGlow {
        0% { background-color: #00ffcc !important; box-shadow: 0 0 10px #00ffcc; border: 2px solid #00ffcc; transform: scale(1); }
        50% { background-color: #00b386 !important; box-shadow: 0 0 25px #00ffcc, 0 0 45px #00ffcc; border: 2px solid #ffffff; transform: scale(1.15); }
        100% { background-color: #00ffcc !important; box-shadow: 0 0 10px #00ffcc; border: 2px solid #00ffcc; transform: scale(1); }
    }
    [data-testid="collapsedControl"], 
    [data-testid="stSidebarCollapsedControl"], 
    button[aria-label="Open sidebar"], 
    button[aria-label="Close sidebar"] {
        position: fixed !important; top: 14px !important; left: 14px !important; z-index: 99999999 !important;
        background-color: #00ffcc !important; border-radius: 50% !important; width: 44px !important; height: 44px !important;
        display: flex !important; align-items: center !important; justify-content: center !important;
        animation: neonBlinkGlow 1.2s infinite ease-in-out !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# -------------------------------------------------------------
# 2. LẤY TỌA ĐỘ GPS REALTIME TỪ ĐIỆN THOẠI/TRÌNH DUYỆT
# -------------------------------------------------------------
# Đặt mặc định tạm thời nếu thiết bị chưa bắt được GPS
if "user_gps" not in st.session_state:
    st.session_state.user_gps = {"lat": 21.82714, "lon": 105.19952}

# Nhúng HTML/JS lấy tọa độ GPS thực tế từ thiết bị di động
gps_component = components.html(
    """
    <script>
    function sendLocation() {
        if ("geolocation" in navigator) {
            navigator.geolocation.getCurrentPosition(
                function(position) {
                    window.parent.postMessage({
                        type: "streamlit:setComponentValue",
                        value: {
                            lat: position.coords.latitude,
                            lon: position.coords.longitude
                        }
                    }, "*");
                },
                function(error) {
                    console.log("GPS Error: ", error.message);
                },
                {
                    enableHighAccuracy: true,
                    timeout: 10000,
                    maximumAge: 0
                }
            );
        }
    }
    sendLocation();
    </script>
    """,
    height=0,
)

if gps_component and isinstance(gps_component, dict) and "lat" in gps_component:
    st.session_state.user_gps = gps_component

curr_lat = st.session_state.user_gps["lat"]
curr_lon = st.session_state.user_gps["lon"]


# -------------------------------------------------------------
# 3. LOAD DATA TỪ FILE EXCEL GỐC (Data.xlsx / data.xlsx)
# -------------------------------------------------------------
@st.cache_data(show_spinner=False)
def load_excel_data():
    """Tự động đọc file Excel và tách cột 'Lat - Lng' dạng '21.81...,105.20...'"""
    target_file = None
    for name in ["Data.xlsx", "data.xlsx", "Data.xls", "data.xls"]:
        if os.path.exists(name):
            target_file = name
            break

    if not target_file:
        return {}

    try:
        df = pd.read_excel(target_file)
        points = {}

        # 1. Tìm cột Tên / Mã đối tượng
        name_col = None
        for col in df.columns:
            col_str = str(col).strip().lower()
            if any(
                k in col_str
                for k in [
                    "tên",
                    "ten",
                    "đối tượng",
                    "doi tuong",
                    "mã",
                    "ma",
                    "name",
                    "point",
                ]
            ):
                name_col = col
                break
        if not name_col:
            name_col = df.columns[1] if len(df.columns) > 1 else df.columns[0]

        # 2. Tìm cột tọa độ
        coord_col = None
        lat_col, lon_col = None, None

        for col in df.columns:
            col_str = str(col).strip().lower()
            if "lat" in col_str and "lng" in col_str or "lat - lng" in col_str:
                coord_col = col
                break

        if not coord_col:
            for col in df.columns:
                col_str = str(col).strip().lower()
                if "lat" in col_str or "vĩ" in col_str:
                    lat_col = col
                elif "lng" in col_str or "lon" in col_str or "kinh" in col_str:
                    lon_col = col

        # 3. Trích xuất dữ liệu
        for _, row in df.iterrows():
            raw_name = str(row[name_col]).strip()
            if not raw_name or raw_name.lower() in ["nan", "none", "null"]:
                continue

            lat_val, lon_val = None, None

            if coord_col and pd.notna(row[coord_col]):
                parts = str(row[coord_col]).split(",")
                if len(parts) == 2:
                    try:
                        lat_val = float(parts[0].strip())
                        lon_val = float(parts[1].strip())
                    except ValueError:
                        continue
            elif lat_col and lon_col:
                try:
                    lat_val = float(row[lat_col])
                    lon_val = float(row[lon_col])
                except (ValueError, TypeError):
                    continue

            if lat_val is not None and lon_val is not None:
                if not math.isnan(lat_val) and not math.isnan(lon_val):
                    points[raw_name] = {"lat": lat_val, "lon": lon_val}

        return points
    except Exception as e:
        st.sidebar.error(f"Lỗi đọc file Excel: {e}")
        return {}


all_points = load_excel_data()
unique_keys = sorted(list(all_points.keys()))

if not unique_keys:
    st.sidebar.error(
        "⚠️ Không tìm thấy tập điểm nào trong file Data.xlsx! Vui lòng kiểm tra lại file dữ liệu."
    )

normalized_all_points = {k.strip().upper(): k for k in all_points.keys()}


# -------------------------------------------------------------
# 4. SIDEBAR & ĐỊA ĐIỂM
# -------------------------------------------------------------
st.sidebar.header("Make by BangNC13")

# Hiển thị thông báo vị trí GPS Realtime hiện tại
st.sidebar.info(
    f"📍 **Vị trí GPS điện thoại:**\n`Lat: {curr_lat:.5f}, Lon: {curr_lon:.5f}`"
)

search_query = st.sidebar.text_input(
    "Nhập điểm cuối hành trình (nếu muốn)", placeholder="Chợ Tam Cờ..."
)
end_location = None

if search_query:
    try:
        url = f"https://nominatim.openstreetmap.org/search?q={search_query}, Tuyên Quang, Việt Nam&format=json&limit=3"
        res = requests.get(
            url, headers={"User-Agent": "TQ_App"}, timeout=3
        ).json()
        if res:
            end_location = {
                "name": f"ĐÍCH ĐẾN: {search_query}",
                "lat": float(res[0]["lat"]),
                "lon": float(res[0]["lon"]),
            }
            st.sidebar.success(f"📍 Đã chọn đích: {search_query}")
        else:
            st.sidebar.error("Không tìm thấy địa điểm này ở Tuyên Quang!")
    except Exception as e:
        st.sidebar.error(f"Lỗi tìm kiếm: {e}")

st.sidebar.header("📋 Chọn lộ trình di chuyển")
selected_from_list = st.sidebar.multiselect(
    "Chọn điểm cần đi:", options=unique_keys
)

uploaded_file = st.sidebar.file_uploader(
    "Hoặc Upload danh sách điểm từ Excel:", type=["xlsx", "xls"]
)

excel_points = []
if uploaded_file:
    try:
        df_uploaded = pd.read_excel(uploaded_file, header=None).astype(str)
        flat_values = df_uploaded.values.flatten()

        for val in flat_values:
            val_clean = str(val).strip().upper()
            if val_clean in normalized_all_points:
                excel_points.append(normalized_all_points[val_clean])

        matched_unique = list(set(excel_points))
        if matched_unique:
            st.sidebar.info(
                f"✅ Đã map thành công {len(matched_unique)} điểm từ file upload."
            )
        else:
            st.sidebar.warning(
                "⚠️ Không tìm thấy mã điểm nào khớp với cơ sở dữ liệu hệ thống."
            )
    except Exception as e:
        st.sidebar.error(f"Lỗi xử lý file Upload: {e}")

final_selected_names = list(set(selected_from_list + excel_points))

st.sidebar.markdown("---")
show_labels = st.sidebar.checkbox("🏷️ Hiện tên điểm (Label)", value=True)
show_route_line = st.sidebar.checkbox("🛣️ Hiện đường vẽ lộ trình", value=True)

if st.sidebar.button("🔄 Làm mới bản đồ"):
    st.session_state.calculated_route = None
    st.session_state.route_cache = None
    st.rerun()


# -------------------------------------------------------------
# 5. THUẬT TOÁN TỐI ƯU LỘ TRÌNH TỪ ĐIỂM GPS REALTIME
# -------------------------------------------------------------
def haversine_distance(lat1, lon1, lat2, lon2):
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlon / 2) ** 2
    )
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def fetch_smart_segment(pair):
    p1, p2 = pair
    url = (
        f"http://router.project-osrm.org/route/v1/driving/"
        f"{p1[1]},{p1[0]};{p2[1]},{p2[0]}"
        f"?overview=full&geometries=geojson&radiuses=2500;2500"
    )

    try:
        res = requests.get(url, timeout=4).json()
        if res.get("code") == "Ok":
            route_data = res["routes"][0]
            osrm_dist = route_data["distance"] / 1000.0
            geom = [
                [lat, lon]
                for lon, lat in route_data["geometry"]["coordinates"]
            ]
            return geom, osrm_dist
    except Exception:
        pass

    direct_dist = haversine_distance(p1[0], p1[1], p2[0], p2[1])
    return [[p1[0], p1[1]], [p2[0], p2[1]]], direct_dist


def solve_tsp_google_style(start_coord, points, end_coord=None):
    all_coords = [start_coord] + [(p["lat"], p["lon"]) for p in points]
    if end_coord:
        all_coords.append((end_coord["lat"], end_coord["lon"]))

    n = len(all_coords)
    dist_matrix = [[0] * n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            dist_matrix[i][j] = haversine_distance(
                all_coords[i][0],
                all_coords[i][1],
                all_coords[j][0],
                all_coords[j][1],
            )

    unvisited = set(range(1, len(points) + 1))
    curr = 0
    path = [0]
    while unvisited:
        nxt = min(unvisited, key=lambda x: dist_matrix[curr][x])
        path.append(nxt)
        unvisited.remove(nxt)
        curr = nxt

    if end_coord:
        path.append(n - 1)

    ordered_points = []
    for idx in path[1:]:
        if end_coord and idx == n - 1:
            ordered_points.append(end_coord)
        else:
            ordered_points.append(points[idx - 1])

    return ordered_points


def get_accurate_route_geometry_parallel(coords_list):
    pairs = [
        (coords_list[i], coords_list[i + 1])
        for i in range(len(coords_list) - 1)
    ]
    road_lines = []
    total_dist = 0.0

    with ThreadPoolExecutor(max_workers=10) as executor:
        results = list(executor.map(fetch_smart_segment, pairs))

    for geom, dist in results:
        road_lines.append(geom)
        total_dist += dist

    return road_lines, total_dist


# -------------------------------------------------------------
# 6. TÍNH TOÁN & DỰNG BẢN ĐỒ
# -------------------------------------------------------------
if "calculated_route" not in st.session_state:
    st.session_state.calculated_route = None
if "route_cache" not in st.session_state:
    st.session_state.route_cache = None

if st.sidebar.button("🚀 Lộ trình"):
    if not final_selected_names and not end_location:
        st.sidebar.warning(
            "Vui lòng chọn điểm di chuyển hoặc nhập Điểm Kết Thúc!"
        )
    else:
        with st.spinner("Đang tính toán từ vị trí GPS Realtime của bạn..."):
            # Lấy tọa độ GPS realtime mới nhất từ điện thoại
            gps_start = (curr_lat, curr_lon)

            pts = [
                {
                    "name": name,
                    "lat": all_points[name]["lat"],
                    "lon": all_points[name]["lon"],
                }
                for name in final_selected_names
                if name in all_points
            ]

            opt_route = solve_tsp_google_style(gps_start, pts, end_location)
            stop_coords = [gps_start] + [
                (p["lat"], p["lon"]) for p in opt_route
            ]

            road_lines, real_dist = get_accurate_route_geometry_parallel(
                stop_coords
            )

            st.session_state.calculated_route = opt_route
            st.session_state.start_coords = gps_start
            st.session_state.route_cache = {
                "road_lines": road_lines,
                "real_dist": real_dist,
                "stop_coords": stop_coords,
            }


def build_map(center):
    m = folium.Map(
        location=center,
        zoom_start=15,
        tiles="https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}",
        attr="Google Maps",
    )
    # Nút định vị vị trí người dùng trực tiếp trên bản đồ
    LocateControl(
        auto_start=False,
        flyTo=True,
        strings={"title": "Định vị vị trí hiện tại"},
    ).add_to(m)
    return m


# RENDER BẢN ĐỒ MAIN VIEW
if st.session_state.calculated_route and st.session_state.route_cache:
    route = st.session_state.calculated_route
    s_lat, s_lon = st.session_state.start_coords

    cache = st.session_state.route_cache
    road_lines = cache["road_lines"]
    real_dist = cache["real_dist"]
    stop_coords = cache["stop_coords"]

    st.sidebar.success(f"📊 Tổng quãng đường xe máy: **~ {real_dist:.2f} km**")

    m = build_map([s_lat, s_lon])

    # Đánh dấu Vị trí GPS Realtime (Điểm bắt đầu)
    folium.Marker(
        [s_lat, s_lon],
        popup="🟢 Xuất phát (Vị trí GPS thực tế)",
        tooltip="Vị trí hiện tại của bạn",
        icon=folium.Icon(color="green", icon="user", prefix="fa"),
    ).add_to(m)

    num_pts = len(route)
    for idx, pt in enumerate(route, start=1):
        is_end = idx == num_pts and end_location is not None
        bg_color = "#e63946" if is_end else "#1A73E8"

        label_html = ""
        if show_labels:
            label_html = f"""
            <span style="margin-left: 6px; background: rgba(255, 255, 255, 0.95); color: #1f2937; font-weight: 700; 
            font-size: 11px; padding: 2px 6px; border-radius: 4px; border: 1px solid #d1d5db; 
            box-shadow: 0 2px 4px rgba(0,0,0,0.15); pointer-events: none; white-space: nowrap;">
                {pt['name']}
            </span>
            """

        marker_html = f"""
        <div style="display: flex; flex-direction: row; align-items: center; justify-content: center;">
            <div style="font-size: 10pt; font-weight: bold; color: white; background-color: {bg_color}; 
            border: 2px solid #ffffff; border-radius: 50%; width: 26px; height: 26px; text-align: center; 
            line-height: 22px; box-shadow: 0 2px 5px rgba(0,0,0,0.3); flex-shrink: 0;">
                {idx}
            </div>
            {label_html}
        </div>
        """

        folium.Marker(
            [pt["lat"], pt["lon"]],
            popup=f"{idx}. {pt['name']}",
            icon=folium.DivIcon(
                html=marker_html, icon_size=(150, 40), icon_anchor=(13, 13)
            ),
        ).add_to(m)

    if show_route_line:
        for line in road_lines:
            folium.PolyLine(
                line, color="#1A73E8", weight=5, opacity=0.85
            ).add_to(m)

    m.fit_bounds(stop_coords)
    st_folium(m, use_container_width=True, height=1000, key="optimized_map")
else:
    m_default = build_map([curr_lat, curr_lon])
    folium.Marker(
        [curr_lat, curr_lon],
        popup="🟢 Vị trí hiện tại của bạn",
        icon=folium.Icon(color="green", icon="user", prefix="fa"),
    ).add_to(m_default)
    st_folium(
        m_default, use_container_width=True, height=1000, key="default_map"
    )
