<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Hiển thị Hạ tầng Mạng GeoJSON</title>
    
    <!-- Thư viện Leaflet CSS -->
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    
    <style>
        body, html {
            margin: 0;
            padding: 0;
            height: 100%;
            width: 100%;
            font-family: Arial, sans-serif;
        }
        #map {
            width: 100%;
            height: 100vh;
        }
        .info-legend {
            background: white;
            padding: 10px;
            line-height: 1.5;
            box-shadow: 0 0 15px rgba(0,0,0,0.2);
            border-radius: 5px;
            font-size: 13px;
        }
        .legend-item {
            margin-bottom: 3px;
        }
        .legend-color {
            display: inline-block;
            width: 12px;
            height: 12px;
            margin-right: 5px;
            border-radius: 50%;
        }
    </style>
</head>
<body>

<div id="map"></div>

<!-- Thư viện Leaflet JS -->
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>

<script>
    // 1. Dữ liệu GeoJSON cung cấp
    const geojsonData = {"type":"FeatureCollection","features":[{"type":"Feature","geometry":{"type":"Point","coordinates":[105.207314,21.818127]},"properties":{"id":6839682,"name":"TQGM001.0021/HO","latLng":"(21.81812691151417,105.20731374621391)","objectType":3,"totalPort":48,"portFree":48,"portUsed":0,"spliter":0,"hasTapdiem":1,"cabType":2}},{"type":"Feature","geometry":{"type":"Point","coordinates":[105.205674,21.818614]},"properties":{"id":6839702,"name":"TQGM001.0023/HO","latLng":"(21.818613720895037,105.20567424595356)","objectType":3,"totalPort":12,"portFree":12,"portUsed":0,"spliter":0,"hasTapdiem":1,"cabType":2}},{"type":"Feature","geometry":{"type":"Point","coordinates":[105.208171,21.81768]},"properties":{"id":21796122,"name":"TQGM001.0025/MO","latLng":"(21.817680434824318,105.208170793655)","objectType":4,"totalPort":24,"portFree":24,"portUsed":0,"spliter":1,"hasTapdiem":1,"cabType":2}},{"type":"Feature","geometry":{"type":"Point","coordinates":[105.208502,21.816681]},"properties":{"id":6839672,"name":"TQGM001.0001/FO","latLng":"(21.81668079152923,105.20850196480751)","objectType":1,"totalPort":24,"portFree":24,"portUsed":0,"spliter":1,"hasTapdiem":1,"cabType":2}},{"type":"Feature","geometry":{"type":"Point","coordinates":[105.208383,21.817538]},"properties":{"id":21796112,"name":"TQGM001.0024/MO","latLng":"(21.81753849987688,105.20838268816718)","objectType":4,"totalPort":24,"portFree":24,"portUsed":0,"spliter":1,"hasTapdiem":1,"cabType":2}},{"type":"Feature","geometry":{"type":"Point","coordinates":[105.206228,21.818712]},"properties":{"id":6839692,"name":"TQGM001.0022/HO","latLng":"(21.818711767341103,105.20622778683901)","objectType":3,"totalPort":12,"portFree":12,"portUsed":0,"spliter":0,"hasTapdiem":1,"cabType":2}},{"type":"Feature","geometry":{"type":"Point","coordinates":[105.208369,21.816711]},"properties":{"id":16912,"name":"TQGM001","latLng":"(21.816711295287163,105.20836919546127)","objectType":5,"totalPort":144,"portFree":144,"portUsed":0,"spliter":3,"hasTapdiem":0,"cabType":2}},{"type":"Feature","geometry":{"type":"Point","coordinates":[105.208173,21.81769]},"properties":{"id":7267472,"name":"TQGM001.0021/CO","hasCable":1,"capacity":48,"length":null,"color":"#06168F","latlngCable":"(21.81769021269109, 105.20817339720462);(21.81812691151417, 105.20731374621391)","method":"Treo","headId":6839672,"headPoint":"TQGM001.0001/FO","headType":1,"tailId":6839682,"tailPoint":"TQGM001.0021/HO","tailType":3,"tailHeadLatLng":"(21.81668079152923,105.20850196480751);(21.81812691151417,105.20731374621391)","midObject":null}},{"type":"Feature","geometry":{"type":"Point","coordinates":[105.207314,21.818127]},"properties":{"id":7788902,"name":"TQGM001.0022/CO","hasCable":1,"capacity":12,"length":null,"color":"#0B9753","latlngCable":null,"method":"Treo","headId":6839682,"headPoint":"TQGM001.0021/HO","headType":3,"tailId":6839692,"tailPoint":"TQGM001.0022/HO","tailType":3,"tailHeadLatLng":"(21.81812691151417,105.20731374621391);(21.818711767341103,105.20622778683901)","midObject":null}},{"type":"Feature","geometry":{"type":"Point","coordinates":[105.206228,21.818712]},"properties":{"id":7788912,"name":"TQGM001.0023/CO","hasCable":1,"capacity":12,"length":null,"color":"#0B9753","latlngCable":"(21.818711767341103,105.20622778683901);(21.81881961857068,105.20603684701065);(21.818900934711706,105.2087432183086);(21.818633641448244,105.20568497478962)","method":"Treo","headId":6839692,"headPoint":"TQGM001.0022/HO","headType":3,"tailId":6839702,"tailPoint":"TQGM001.0023/HO","tailType":3,"tailHeadLatLng":"(21.818711767341103,105.20622778683901);(21.818613720895037,105.20567424595356)","midObject":null}},{"type":"Feature","geometry":{"type":"Point","coordinates":[105.208502,21.816681]},"properties":{"id":11095652,"name":"TQGM001.0024/CO","hasCable":1,"capacity":48,"length":null,"color":"#06168F","latlngCable":"(21.81668079152923, 105.20850196480751);(21.8186063594783, 105.20861667025201);(21.81712984530659, 105.20810003034339);(21.81753849987688, 105.20838268816718)","method":"Treo","headId":6839672,"headPoint":"TQGM001.0001/FO","headType":1,"tailId":21796112,"tailPoint":"TQGM001.0024/MO","tailType":4,"tailHeadLatLng":"(21.81668079152923,105.20850196480751);(21.81753849987688,105.20838268816718)","midObject":null}},{"type":"Feature","geometry":{"type":"Point","coordinates":[105.208383,21.817538]},"properties":{"id":11095662,"name":"TQGM001.0025/CO","hasCable":1,"capacity":48,"length":null,"color":"#06168F","latlngCable":null,"method":"Treo","headId":21796112,"headPoint":"TQGM001.0024/MO","headType":4,"tailId":21796122,"tailPoint":"TQGM001.0025/MO","tailType":4,"tailHeadLatLng":"(21.81753849987688,105.20838268816718);(21.817680434824318,105.208170793655)","midObject":null}}]};

    // 2. Khởi tạo bản đồ tại vị trí mặc định
    const map = L.map('map').setView([21.817, 105.207], 16);

    // 3. Thêm lớp bản đồ nền OpenStreetMap
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; OpenStreetMap contributors'
    }).addTo(map);

    // Hàm chuyển đổi chuỗi "(lat1, lng1);(lat2, lng2)" thành mảng [[lat1, lng1], [lat2, lng2]]
    function parseLatLngString(str) {
        if (!str) return [];
        return str.split(';').map(item => {
            const cleanStr = item.replace('(', '').replace(')', '').trim();
            const parts = cleanStr.split(',');
            if (parts.length === 2) {
                return [parseFloat(parts[0]), parseFloat(parts[1])];
            }
            return null;
        }).filter(item => item !== null);
    }

    // Hàm lấy màu sắc theo loại thiết bị (objectType)
    function getPointColor(objectType) {
        switch (objectType) {
            case 1: return '#e74c3c'; // FO - Đỏ
            case 3: return '#3498db'; // HO - Xanh dương
            case 4: return '#f39c12'; // MO - Cam
            case 5: return '#9b59b6'; // Tủ cáp chính - Tím
            default: return '#2ecc71';
        }
    }

    const featureGroup = L.featureGroup();

    // 4. Duyệt qua danh sách đối tượng
    geojsonData.features.forEach(feature => {
        const props = feature.properties;

        // XỬ LÝ ĐƯỜNG CÁP (Nếu có chứa thông tin cáp)
        if (props.hasCable === 1) {
            const cableCoords = parseLatLngString(props.latlngCable) || parseLatLngString(props.tailHeadLatLng);
            
            if (cableCoords && cableCoords.length > 0) {
                const polyline = L.polyline(cableCoords, {
                    color: props.color || '#0000FF',
                    weight: 4,
                    opacity: 0.8
                });

                // Nội dung thông tin Cáp khi click
                const cablePopup = `
                    <b>CÁP QUANG: ${props.name}</b><br/>
                    <b>ID:</b> ${props.id}<br/>
                    <b>Dung lượng:</b> ${props.capacity || 'N/A'} sợi<br/>
                    <b>Cách thức:</b> ${props.method || 'N/A'}<br/>
                    <b>Từ:</b> ${props.headPoint} (Loại ${props.headType})<br/>
                    <b>Đến:</b> ${props.tailPoint} (Loại ${props.tailType})
                `;
                
                polyline.bindPopup(cablePopup);
                polyline.bindTooltip(props.name, { sticky: true });
                polyline.addTo(featureGroup);
            }
        } 
        
        // XỬ LÝ ĐIỂM / THIẾT BỊ
        if (feature.geometry && feature.geometry.type === "Point") {
            const coords = feature.geometry.coordinates; // [lng, lat]
            const latLng = [coords[1], coords[0]];

            const marker = L.circleMarker(latLng, {
                radius: 7,
                fillColor: getPointColor(props.objectType),
                color: "#ffffff",
                weight: 2,
                opacity: 1,
                fillOpacity: 0.9
            });

            // Nội dung thông tin Điểm khi click
            const pointPopup = `
                <b>THIẾT BỊ: ${props.name}</b><br/>
                <b>ID:</b> ${props.id}<br/>
                <b>Tổng số cổng:</b> ${props.totalPort ?? 'N/A'}<br/>
                <b>Cổng rảnh:</b> <span style="color:green;font-weight:bold">${props.portFree ?? 'N/A'}</span><br/>
                <b>Cổng đã dùng:</b> <span style="color:red;font-weight:bold">${props.portUsed ?? 'N/A'}</span><br/>
                <b>Bộ chia (Spliter):</b> ${props.spliter ?? 'N/A'}
            `;

            marker.bindPopup(pointPopup);
            marker.bindTooltip(props.name, { permanent: false, direction: 'top' });
            marker.addTo(featureGroup);
        }
    });

    // Thêm tất cả đối tượng vào bản đồ
    featureGroup.addTo(map);

    // Tự động căn chỉnh bản đồ vừa vặn với toàn bộ dữ liệu
    if (featureGroup.getLayers().length > 0) {
        map.fitBounds(featureGroup.getBounds(), { padding: [30, 30] });
    }

    // 5. Thêm Chú thích (Legend) vào góc bản đồ
    const legend = L.control({ position: 'bottomright' });
    legend.onAdd = function () {
        const div = L.DomUtil.create('div', 'info-legend');
        div.innerHTML = `
            <b>Chú giải:</b><br/>
            <div class="legend-item"><span class="legend-color" style="background:#e74c3c;"></span>Loại 1 (FO)</div>
            <div class="legend-item"><span class="legend-color" style="background:#3498db;"></span>Loại 3 (HO)</div>
            <div class="legend-item"><span class="legend-color" style="background:#f39c12;"></span>Loại 4 (MO)</div>
            <div class="legend-item"><span class="legend-color" style="background:#9b59b6;"></span>Loại 5 (Tủ)</div>
            <div class="legend-item"><span class="legend-color" style="background:#06168F; height:3px; border-radius:0;"></span>Cáp 48FO</div>
            <div class="legend-item"><span class="legend-color" style="background:#0B9753; height:3px; border-radius:0;"></span>Cáp 12FO</div>
        `;
        return div;
    };
    legend.addTo(map);
</script>

</body>
</html>
