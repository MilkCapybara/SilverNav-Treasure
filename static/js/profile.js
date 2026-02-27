// 船舶画像页面逻辑
const Profile = {
    token: localStorage.getItem("silvernav_token") || "",
    baseDate: window.Dash?.baseDate || "",
    overview: null,
    statistics: null
};

function showProfileToast(msg, isError = false) {
    const toast = document.getElementById("profileToast");
    if (!toast) return;
    toast.textContent = msg;
    toast.classList.toggle("error", isError);
    toast.classList.add("show");
    window.clearTimeout(showProfileToast.timer);
    showProfileToast.timer = window.setTimeout(() => {
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

// 从localStorage或URL获取基准日期
function getBaseDate() {
    // 尝试从localStorage获取
    const storedDate = localStorage.getItem("silvernav_base_date");
    if (storedDate) {
        return storedDate;
    }

    // 默认使用今天
    const today = new Date();
    return today.toISOString().split('T')[0];
}

// 更新基准日期显示
function updateBaseDateDisplay() {
    const baseDate = getBaseDate();
    Profile.baseDate = baseDate;

    const baseDateEl = document.getElementById("baseDateValue");
    if (baseDateEl) {
        baseDateEl.textContent = baseDate;
    }
}

// 加载总览数据
async function loadOverview() {
    if (!Profile.token) {
        showProfileToast("请先登录", true);
        window.location.href = "/";
        return;
    }

    try {
        const baseDate = getBaseDate();
        const response = await fetch(`/api/profile/overview?base_date=${baseDate}`, {
            method: "GET",
            headers: {
                "Authorization": `Bearer ${Profile.token}`,
                "Content-Type": "application/json"
            }
        });

        const data = await response.json();

        if (data.success) {
            Profile.overview = data.overview;

            // 更新统计卡片
            document.getElementById("totalVessels").textContent = data.overview.total_vessels.toLocaleString();
            document.getElementById("activeVessels").textContent = data.overview.active_vessels.toLocaleString();
            document.getElementById("shipTypeCount").textContent = data.overview.ship_type_distribution.length;
            document.getElementById("flagCount").textContent = data.overview.flag_distribution.length;

            // 渲染图表
            renderShipTypeChart(data.overview.ship_type_distribution);
            renderFlagChart(data.overview.flag_distribution);

            console.log("总览数据加载成功", data.overview);
        } else {
            showProfileToast(data.msg || "加载失败", true);
        }
    } catch (error) {
        console.error("加载总览数据失败:", error);
        showProfileToast("加载失败: " + error.message, true);
    }
}

// 加载统计数据
async function loadStatistics() {
    if (!Profile.token) return;

    try {
        const baseDate = getBaseDate();
        const response = await fetch(`/api/profile/statistics?base_date=${baseDate}`, {
            method: "GET",
            headers: {
                "Authorization": `Bearer ${Profile.token}`,
                "Content-Type": "application/json"
            }
        });

        const data = await response.json();

        if (data.success) {
            Profile.statistics = data.statistics;

            // 渲染活跃度表格
            renderActivityTable(data.statistics.vessel_activity_top10);

            // 渲染速度分布图
            renderSpeedChart(data.statistics.speed_distribution);

            console.log("统计数据加载成功", data.statistics);
        } else {
            showProfileToast(data.msg || "加载统计失败", true);
        }
    } catch (error) {
        console.error("加载统计数据失败:", error);
        showProfileToast("加载统计失败: " + error.message, true);
    }
}

// 渲染船舶类型分布图（饼图）
function renderShipTypeChart(distribution) {
    const chartContainer = document.getElementById("shipTypeChart");
    if (!chartContainer || !distribution || distribution.length === 0) {
        chartContainer.innerHTML = '<p style="text-align: center; padding: 40px; color: #999;">暂无数据</p>';
        return;
    }

    // 取前8个类型
    const topTypes = distribution.slice(0, 8);
    const total = topTypes.reduce((sum, item) => sum + item.count, 0);

    // 颜色方案
    const colors = [
        '#3cebdc', '#4fa8ff', '#ffd65c', '#ff9f1c',
        '#ff5a7a', '#7ef7f0', '#ffb703', '#4dd4ac'
    ];

    // 生成饼图SVG
    let currentAngle = 0;
    const radius = 80;
    const centerX = 100;
    const centerY = 100;

    const paths = topTypes.map((item, index) => {
        const percentage = item.count / total;
        const angle = percentage * 360;
        const endAngle = currentAngle + angle;

        const startX = centerX + radius * Math.cos((currentAngle - 90) * Math.PI / 180);
        const startY = centerY + radius * Math.sin((currentAngle - 90) * Math.PI / 180);
        const endX = centerX + radius * Math.cos((endAngle - 90) * Math.PI / 180);
        const endY = centerY + radius * Math.sin((endAngle - 90) * Math.PI / 180);

        const largeArc = angle > 180 ? 1 : 0;

        const path = `M ${centerX} ${centerY} L ${startX} ${startY} A ${radius} ${radius} 0 ${largeArc} 1 ${endX} ${endY} Z`;

        currentAngle = endAngle;

        return {
            path,
            color: colors[index % colors.length],
            type: item.type,
            count: item.count,
            percentage: (percentage * 100).toFixed(1)
        };
    });

    // 生成HTML
    const svgPaths = paths.map(p =>
        `<path d="${p.path}" fill="${p.color}" opacity="0.8" stroke="#0a1628" stroke-width="2" />`
    ).join('');

    const legendItems = paths.map(p => `
        <div class="pie-legend-item">
            <div class="pie-legend-color" style="background: ${p.color};"></div>
            <span class="pie-legend-label">${p.type}</span>
            <span class="pie-legend-value">${p.count} (${p.percentage}%)</span>
        </div>
    `).join('');

    chartContainer.innerHTML = `
        <div class="pie-chart">
            <svg class="pie-svg" viewBox="0 0 200 200">
                ${svgPaths}
            </svg>
            <div class="pie-legend">
                ${legendItems}
            </div>
        </div>
    `;
}

// 渲染船旗国分布图（饼图）
function renderFlagChart(distribution) {
    const chartContainer = document.getElementById("flagChart");
    if (!chartContainer || !distribution || distribution.length === 0) {
        chartContainer.innerHTML = '<p style="text-align: center; padding: 40px; color: #999;">暂无数据</p>';
        return;
    }

    // 取前8个国家
    const topFlags = distribution.slice(0, 8);
    const total = topFlags.reduce((sum, item) => sum + item.count, 0);

    // 颜色方案
    const colors = [
        '#ff5a7a', '#ff9f1c', '#ffd65c', '#4dd4ac',
        '#3cebdc', '#4fa8ff', '#7ef7f0', '#ffb703'
    ];

    // 生成饼图SVG
    let currentAngle = 0;
    const radius = 80;
    const centerX = 100;
    const centerY = 100;

    const paths = topFlags.map((item, index) => {
        const percentage = item.count / total;
        const angle = percentage * 360;
        const endAngle = currentAngle + angle;

        const startX = centerX + radius * Math.cos((currentAngle - 90) * Math.PI / 180);
        const startY = centerY + radius * Math.sin((currentAngle - 90) * Math.PI / 180);
        const endX = centerX + radius * Math.cos((endAngle - 90) * Math.PI / 180);
        const endY = centerY + radius * Math.sin((endAngle - 90) * Math.PI / 180);

        const largeArc = angle > 180 ? 1 : 0;

        const path = `M ${centerX} ${centerY} L ${startX} ${startY} A ${radius} ${radius} 0 ${largeArc} 1 ${endX} ${endY} Z`;

        currentAngle = endAngle;

        return {
            path,
            color: colors[index % colors.length],
            flag: item.flag,
            count: item.count,
            percentage: (percentage * 100).toFixed(1)
        };
    });

    // 生成HTML
    const svgPaths = paths.map(p =>
        `<path d="${p.path}" fill="${p.color}" opacity="0.8" stroke="#0a1628" stroke-width="2" />`
    ).join('');

    const legendItems = paths.map(p => `
        <div class="pie-legend-item">
            <div class="pie-legend-color" style="background: ${p.color};"></div>
            <span class="pie-legend-label">${p.flag}</span>
            <span class="pie-legend-value">${p.count} (${p.percentage}%)</span>
        </div>
    `).join('');

    chartContainer.innerHTML = `
        <div class="pie-chart">
            <svg class="pie-svg" viewBox="0 0 200 200">
                ${svgPaths}
            </svg>
            <div class="pie-legend">
                ${legendItems}
            </div>
        </div>
    `;
}

// 渲染活跃度表格
function renderActivityTable(vessels) {
    const tbody = document.getElementById("activityTableBody");
    if (!tbody) return;

    if (!vessels || vessels.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" style="text-align: center; padding: 40px;">暂无数据</td></tr>';
        return;
    }

    const rows = vessels.map((vessel, index) => `
        <tr>
            <td class="rank">#${index + 1}</td>
            <td>${vessel.imo_number}</td>
            <td>${vessel.vessel_name}</td>
            <td>${vessel.ship_type}</td>
            <td>${vessel.track_count.toLocaleString()}</td>
            <td>${vessel.avg_speed} 节</td>
        </tr>
    `).join('');

    tbody.innerHTML = rows;
}

// 渲染速度分布图（柱状图）
function renderSpeedChart(distribution) {
    const chartContainer = document.getElementById("speedChart");
    if (!chartContainer || !distribution || distribution.length === 0) {
        chartContainer.innerHTML = '<p style="text-align: center; padding: 40px; color: #999;">暂无数据</p>';
        return;
    }

    const maxCount = Math.max(...distribution.map(d => d.count));

    const bars = distribution.map(item => {
        const percentage = maxCount > 0 ? (item.count / maxCount) * 100 : 0;
        return `
            <div class="chart-bar">
                <div class="chart-label">${item.range} 节</div>
                <div class="chart-bar-container">
                    <div class="chart-bar-fill" style="width: ${percentage}%"></div>
                </div>
                <div class="chart-value">${item.count.toLocaleString()}</div>
            </div>
        `;
    }).join('');

    chartContainer.innerHTML = bars;
}

// 搜索船舶
async function searchVessel() {
    const searchInput = document.getElementById("vesselSearch");
    const imoNumber = searchInput.value.trim();

    if (!imoNumber) {
        showProfileToast("请输入IMO编号", true);
        return;
    }

    if (!Profile.token) {
        showProfileToast("请先登录", true);
        window.location.href = "/";
        return;
    }

    try {
        const baseDate = getBaseDate();
        const response = await fetch(`/api/profile/vessel/${imoNumber}?base_date=${baseDate}`, {
            method: "GET",
            headers: {
                "Authorization": `Bearer ${Profile.token}`,
                "Content-Type": "application/json"
            }
        });

        const data = await response.json();

        if (data.success) {
            renderVesselDetail(data.profile);
            showProfileToast("查询成功");
        } else {
            showProfileToast(data.msg || "查询失败", true);
        }
    } catch (error) {
        console.error("搜索船舶失败:", error);
        showProfileToast("查询失败: " + error.message, true);
    }
}

// 渲染船舶详情
function renderVesselDetail(profile) {
    const detailContainer = document.getElementById("vesselDetail");
    if (!detailContainer) return;

    const html = `
        <div class="vessel-info-grid">
            <div class="info-section">
                <h4>📋 基本信息</h4>
                <div class="info-row">
                    <span class="info-label">IMO编号</span>
                    <span class="info-value highlight">${profile.imo_number}</span>
                </div>
                <div class="info-row">
                    <span class="info-label">船名</span>
                    <span class="info-value">${profile.vessel_name}</span>
                </div>
                <div class="info-row">
                    <span class="info-label">船舶类型</span>
                    <span class="info-value">${profile.ship_type}</span>
                </div>
                <div class="info-row">
                    <span class="info-label">船旗国</span>
                    <span class="info-value">${profile.flag}</span>
                </div>
            </div>

            <div class="info-section">
                <h4>📊 航行统计（近30天）</h4>
                <div class="info-row">
                    <span class="info-label">轨迹点数</span>
                    <span class="info-value highlight">${profile.track_count_30d.toLocaleString()}</span>
                </div>
                <div class="info-row">
                    <span class="info-label">平均速度</span>
                    <span class="info-value">${profile.avg_speed} 节</span>
                </div>
                <div class="info-row">
                    <span class="info-label">最大速度</span>
                    <span class="info-value">${profile.max_speed} 节</span>
                </div>
            </div>

            <div class="info-section">
                <h4>📍 最新位置</h4>
                <div class="info-row">
                    <span class="info-label">经度</span>
                    <span class="info-value">${profile.latest_position.lng ? profile.latest_position.lng.toFixed(4) : '--'}</span>
                </div>
                <div class="info-row">
                    <span class="info-label">纬度</span>
                    <span class="info-value">${profile.latest_position.lat ? profile.latest_position.lat.toFixed(4) : '--'}</span>
                </div>
                <div class="info-row">
                    <span class="info-label">更新时间</span>
                    <span class="info-value">${profile.latest_position.timestamp ? new Date(profile.latest_position.timestamp).toLocaleString('zh-CN') : '--'}</span>
                </div>
            </div>

            ${profile.pg_info ? `
            <div class="info-section">
                <h4>💼 资产信息</h4>
                <div class="info-row">
                    <span class="info-label">船舶ID</span>
                    <span class="info-value">${profile.pg_info.vessel_id || '--'}</span>
                </div>
                <div class="info-row">
                    <span class="info-label">所属公司</span>
                    <span class="info-value">${profile.pg_info.company_name || '--'}</span>
                </div>
            </div>
            ` : ''}
        </div>
    `;

    detailContainer.innerHTML = html;
}

// 返回大屏
function goBack() {
    window.location.href = "/dashboard";
}

// 页面初始化
document.addEventListener("DOMContentLoaded", function() {
    console.log("船舶画像页面初始化");

    // 初始化时钟
    initClock();

    // 更新基准日期显示
    updateBaseDateDisplay();

    // 监听localStorage变化（当大屏修改基准日期时同步）
    window.addEventListener('storage', function(e) {
        if (e.key === 'silvernav_base_date') {
            updateBaseDateDisplay();
            // 重新加载数据
            loadOverview();
            loadStatistics();
        }
    });

    // 加载数据
    loadOverview();
    loadStatistics();

    // 绑定事件
    const backBtn = document.getElementById("backBtn");
    if (backBtn) {
        backBtn.addEventListener("click", goBack);
    }

    const searchBtn = document.getElementById("searchBtn");
    if (searchBtn) {
        searchBtn.addEventListener("click", searchVessel);
    }

    const searchInput = document.getElementById("vesselSearch");
    if (searchInput) {
        searchInput.addEventListener("keypress", function(e) {
            if (e.key === "Enter") {
                searchVessel();
            }
        });
    }
});
