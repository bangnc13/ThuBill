# -------------------------------------------------------------
# 3. LOAD DATA TỪ FILE EXCEL GỐC (ĐÃ TỐI ƯU CHO FILE DATA.XLSX)
# -------------------------------------------------------------
@st.cache_data(show_spinner=False)
def load_excel_data():
    """Tự động tìm file Excel và tách cột 'Lat - Lng' dạng '21.81...,105.20...'"""
    # Tìm file Data.xlsx hoặc data.xlsx trong thư mục
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
            if any(k in col_str for k in ["tên", "ten", "đối tượng", "doi tuong", "mã", "ma", "name", "point"]):
                name_col = col
                break
        if not name_col:
            name_col = df.columns[1] if len(df.columns) > 1 else df.columns[0]

        # 2. Tìm cột tọa độ (cột gộp 'Lat - Lng' hoặc 2 cột riêng)
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

            # Trường hợp 1: Tọa độ nằm chung 1 cột dạng "21.8166,105.2085"
            if coord_col and pd.notna(row[coord_col]):
                parts = str(row[coord_col]).split(",")
                if len(parts) == 2:
                    try:
                        lat_val = float(parts[0].strip())
                        lon_val = float(parts[1].strip())
                    except ValueError:
                        continue

            # Trường hợp 2: Tọa độ ở 2 cột riêng
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


# Load tập điểm từ file Excel
all_points = load_excel_data()
unique_keys = sorted(list(all_points.keys()))

if not unique_keys:
    st.sidebar.error("⚠️ Không tìm thấy tập điểm nào trong file Excel dữ liệu gốc! Vui lòng kiểm tra lại file Data.xlsx.")

# Tạo dictionary hỗ trợ map không phân biệt hoa/thường và khoảng trắng
normalized_all_points = {k.strip().upper(): k for k in all_points.keys()}
