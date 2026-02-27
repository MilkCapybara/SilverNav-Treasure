// 船舶行为分析页面逻辑
const Behavior = {
    token: localStorage.getItem("silvernav_token") || "",
    baseDate: "",
    map: null,
    trackLayer: null,
    currentVessel: null,
    tracks: []
};

function showBehaviorToast(msg, isError = false) {
    const toast = document.getElementById("behaviorToast");
    if (!toast) return;
    toast.textContent = msg;
    toast.classList.toggle("error", isError);
    toast.classList.add("show");
    window.clearTimeout(showBehaviorToast.timer);
    showBehaviorToast.timer = window.setTimeout(() => {
        toast.classList.remove("show");
    }, 2000);
}

// 初始化时钟
function initClock() {
    const clockEl = document.getElementById("cnClock");
    if (!clockEl) return;

    function updateClock() {
        const now = new Date();
        const timeStr = now.toLocaleTimeString("zh-CN", {
            hour: "2-digit",
            minute: "2-digit",
            second: "2-digit",
            hour12: false
        });
        clockEl.textContent = timeStr;
    }

    updateClock();
    setInterval(updateClock, 1000);
}

// 从localStorage获取基准日期
function getBaseDate() {
    const storedDate = localStorage.getItem("silvernav_base_date");
    if (storedDate) {
        return storedDate;
    }
    const today = new Date();
    return today.toISOString().split('T')[0];
}

// 更新基准日期显示
function updateBaseDateDisplay() {
    const baseDate = getBaseDate();
    Behavior.baseDate = baseDate;

    const baseDateEl = document.getElementById("baseDateValue");
    if (baseDateEl) {
        baseDateEl.textContent = baseDate;
    }
}

// 初始化地图
function initMap() {
    // 创建地图，中心点设置为上海
    Behavior.map = L.map('mapContainer').setView([31.2304, 121.4737], 6);

    // 添加地图底图 - 使用多个备选源以确保在中国可访问
    // 优先使用CartoDB的Voyager底图（在中国访问较稳定）
    L.tileLayer('https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
        subdomains: 'abcd',
        maxZoom: 20
    }).addTo(Behavior.map);

    // 创建轨迹图层组
    Behavior.trackLayer = L.layerGroup().addTo(Behavior.map);

    console.log("地图初始化完成");
}

// 加载总览统计
async function loadSummary() {
    if (!Behavior.token) {
        showBehaviorToast("请先登录", true);
        window.location.href = "/";
        return;
    }

    try {
        const response = await fetch("/api/behavior/summary", {
            method: "GET",
            headers: {
                "Authorization": `Bearer ${Behavior.token}`,
                "Content-Type": "application/json"
            }
        });

        const data = await response.json();

        if (data.success) {
            const summary = data.summary;

            // 更新统计卡片
            document.getElementById("totalTracks").textContent = summary.total_tracks.toLocaleString();
            document.getElementById("vesselCount").textContent = summary.vessel_count;
            document.getElementById("anomalyCount").textContent = summary.anomaly_count;

            // 计算时间跨度
            if (summary.time_range.start && summary.time_range.end) {
                const start = new Date(summary.time_range.start);
                const end = new Date(summary.time_range.end);
                const days = Math.floor((end - start) / (1000 * 60 * 60 * 24));
                document.getElementById("timeSpan").textContent = `${days}天`;
            }

            // 渲染船舶类型分布图
            renderShipTypeChart(summary.ship_type_distribution);

            console.log("总览统计加载成功", summary);
        } else {
            showBehaviorToast(data.msg || "加载失败", true);
        }
    } catch (error) {
        console.error("加载总览统计失败:", error);
        showBehaviorToast("加载失败: " + error.message, true);
    }
}

// 渲染船舶类型分布图
function renderShipTypeChart(distribution) {
    const chartContainer = document.getElementById("shipTypeChart");
    if (!chartContainer || !distribution || distribution.length === 0) {
        chartContainer.innerHTML = '<p style="text-align: center; padding: 40px; color: #999;">暂无数据</p>';
        return;
    }

    const maxCount = Math.max(...distribution.map(d => d.count));
    const chartHTML = distribution.map(d => {
        const percentage = maxCount > 0 ? (d.count / maxCount) * 100 : 0;
        return `
            <div style="margin-bottom: 15px;">
                <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                    <span style="color: #fff; font-size: 14px;">🚢 ${d.type}</span>
                    <span style="color: #4fc3f7; font-weight: bold;">${d.count.toLocaleString()}条</span>
                </div>
                <div style="background: rgba(255,255,255,0.1); height: 20px; border-radius: 10px; overflow: hidden;">
                    <div style="background: linear-gradient(90deg, #4fc3f7, #29b6f6); height: 100%; width: ${percentage}%; transition: width 0.3s;"></div>
                </div>
            </div>
        `;
    }).join('');

    chartContainer.innerHTML = chartHTML;
}

// 加载船舶列表
async function loadVesselList() {
    if (!Behavior.token) return;

    try {
        // 从MongoDB读取船舶列表
        const response = await fetch("/api/behavior/vessels", {
            method: "GET",
            headers: {
                "Authorization": `Bearer ${Behavior.token}`,
                "Content-Type": "application/json"
            }
        });

        const data = await response.json();

        if (data.success && data.vessels) {
            const select = document.getElementById("vesselSelect");
            select.innerHTML = '<option value="">请选择船舶...</option>';

            data.vessels.forEach(vessel => {
                const option = document.createElement("option");
                option.value = vessel.imo_number;
                option.textContent = `${vessel.vessel_name} (${vessel.imo_number})`;
                select.appendChild(option);
            });

            console.log("船舶列表加载成功", data.vessels.length);
        } else {
            const select = document.getElementById("vesselSelect");
            select.innerHTML = '<option value="">暂无船舶数据</option>';
            console.error("加载船舶列表失败:", data.msg);
        }
    } catch (error) {
        console.error("加载船舶列表失败:", error);
        const select = document.getElementById("vesselSelect");
        select.innerHTML = '<option value="">加载失败</option>';
    }
}

// 加载船舶轨迹
async function loadVesselTrack() {
    const vesselSelect = document.getElementById("vesselSelect");
    const timeRangeSelect = document.getElementById("timeRangeSelect");

    const imoNumber = vesselSelect.value;
    if (!imoNumber) {
        showBehaviorToast("请先选择船舶", true);
        return;
    }

    const timeRange = timeRangeSelect.value;

    // 计算时间范围
    let startDate = null;
    let endDate = new Date().toISOString();

    if (timeRange !== 'all') {
        const days = parseInt(timeRange);
        const start = new Date();
        start.setDate(start.getDate() - days);
        startDate = start.toISOString();
    }

    showBehaviorToast("加载轨迹中...", false);

    try {
        const response = await fetch("/api/behavior/tracks", {
            method: "POST",
            headers: {
                "Authorization": `Bearer ${Behavior.token}`,
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                imo_number: imoNumber,
                start_date: startDate,
                end_date: endDate,
                limit: 1000
            })
        });

        const data = await response.json();

        if (data.success) {
            Behavior.tracks = data.tracks;
            Behavior.currentVessel = imoNumber;

            // 渲染轨迹到地图
            renderTrackOnMap(data.tracks);

            // 渲染轨迹表格
            renderTrackTable(data.tracks);

            showBehaviorToast(`加载成功！共${data.count}个轨迹点`, false);
        } else {
            showBehaviorToast(data.msg || "加载失败", true);
        }
    } catch (error) {
        console.error("加载轨迹失败:", error);
        showBehaviorToast("加载失败: " + error.message, true);
    }
}

// 在地图上渲染轨迹
function renderTrackOnMap(tracks) {
    if (!Behavior.map || !Behavior.trackLayer) return;

    // 清除现有轨迹
    Behavior.trackLayer.clearLayers();

    if (!tracks || tracks.length === 0) {
        showBehaviorToast("该船舶暂无轨迹数据", true);
        return;
    }

    // 提取坐标点
    const latlngs = tracks.map(track => {
        const coords = track.position.coordinates;
        return [coords[1], coords[0]]; // Leaflet使用[lat, lng]格式
    });

    // 绘制轨迹线
    const polyline = L.polyline(latlngs, {
        color: '#3cebdc',
        weight: 3,
        opacity: 0.7
    }).addTo(Behavior.trackLayer);

    // 添加起点标记
    if (latlngs.length > 0) {
        L.circleMarker(latlngs[0], {
            radius: 8,
            fillColor: '#66bb6a',
            color: '#fff',
            weight: 2,
            opacity: 1,
            fillOpacity: 0.8
        }).bindPopup(`<b>起点</b><br>${tracks[0].timestamp}<br>速度: ${tracks[0].speed}节`).addTo(Behavior.trackLayer);
    }

    // 添加终点标记
    if (latlngs.length > 1) {
        const lastIdx = latlngs.length - 1;
        L.circleMarker(latlngs[lastIdx], {
            radius: 8,
            fillColor: '#ffd65c',
            color: '#fff',
            weight: 2,
            opacity: 1,
            fillOpacity: 0.8
        }).bindPopup(`<b>终点</b><br>${tracks[lastIdx].timestamp}<br>速度: ${tracks[lastIdx].speed}节`).addTo(Behavior.trackLayer);
    }

    // 添加中间点标记（每10个点一个）
    for (let i = 10; i < tracks.length - 1; i += 10) {
        const track = tracks[i];
        const coords = track.position.coordinates;
        L.circleMarker([coords[1], coords[0]], {
            radius: 4,
            fillColor: '#4fc3f7',
            color: '#fff',
            weight: 1,
            opacity: 0.8,
            fillOpacity: 0.6
        }).bindPopup(`
            <b>${track.vessel_name}</b><br>
            时间: ${track.timestamp}<br>
            速度: ${track.speed}节<br>
            航向: ${track.course}°<br>
            状态: ${track.status}
        `).addTo(Behavior.trackLayer);
    }

    // 调整地图视野以显示所有轨迹
    Behavior.map.fitBounds(polyline.getBounds(), { padding: [50, 50] });

    console.log(`轨迹渲染完成，共${tracks.length}个点`);
}

// 渲染轨迹表格
function renderTrackTable(tracks) {
    const tableBody = document.getElementById("trackTableBody");
    if (!tableBody) return;

    if (!tracks || tracks.length === 0) {
        tableBody.innerHTML = '<tr><td colspan="5" style="text-align: center; padding: 40px;">暂无轨迹数据</td></tr>';
        return;
    }

    // 只显示前50条
    const displayTracks = tracks.slice(0, 50);

    const rows = displayTracks.map(track => {
        const coords = track.position.coordinates;
        const timestamp = new Date(track.timestamp).toLocaleString('zh-CN');

        return `
            <tr>
                <td>${timestamp}</td>
                <td>${coords[0].toFixed(4)} / ${coords[1].toFixed(4)}</td>
                <td>${track.speed.toFixed(1)}</td>
                <td>${track.course.toFixed(0)}</td>
                <td>${track.status}</td>
            </tr>
        `;
    }).join('');

    tableBody.innerHTML = rows;

    if (tracks.length > 50) {
        tableBody.innerHTML += `
            <tr>
                <td colspan="5" style="text-align: center; padding: 20px; color: #ffd65c;">
                    仅显示前50条记录，共${tracks.length}条
                </td>
            </tr>
        `;
    }
}

// 清除轨迹
function clearTrack() {
    if (Behavior.trackLayer) {
        Behavior.trackLayer.clearLayers();
    }

    const tableBody = document.getElementById("trackTableBody");
    if (tableBody) {
        tableBody.innerHTML = '<tr><td colspan="5" style="text-align: center; padding: 40px;">请选择船舶并加载轨迹</td></tr>';
    }

    Behavior.tracks = [];
    Behavior.currentVessel = null;

    // 重置地图视野
    if (Behavior.map) {
        Behavior.map.setView([31.2304, 121.4737], 6);
    }

    showBehaviorToast("轨迹已清除", false);
}

// 初始化页面
function initBehaviorPage() {
    // 初始化时钟
    initClock();

    // 更新基准日期显示
    updateBaseDateDisplay();

    // 监听localStorage变化（当大屏修改基准日期时同步）
    window.addEventListener('storage', function(e) {
        if (e.key === 'silvernav_base_date') {
            updateBaseDateDisplay();
            // 重新加载数据
            loadSummary();
        }
    });

    // 初始化地图
    initMap();

    // 加载总览统计
    loadSummary();

    // 加载船舶列表
    loadVesselList();

    // 绑定返回按钮
    const backBtn = document.getElementById("backBtn");
    if (backBtn) {
        backBtn.addEventListener("click", () => {
            window.location.href = "/dashboard";
        });
    }

    // 绑定加载轨迹按钮
    const loadTrackBtn = document.getElementById("loadTrackBtn");
    if (loadTrackBtn) {
        loadTrackBtn.addEventListener("click", loadVesselTrack);
    }

    // 绑定清除轨迹按钮
    const clearTrackBtn = document.getElementById("clearTrackBtn");
    if (clearTrackBtn) {
        clearTrackBtn.addEventListener("click", clearTrack);
    }
}

// 页面加载完成后初始化
window.addEventListener("load", () => {
    if (document.body.classList.contains("behavior-page")) {
        initBehaviorPage();
    }
});
