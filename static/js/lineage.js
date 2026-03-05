// 数据血缘页面逻辑 - 完整版（增强版）
const Lineage = {
    token: localStorage.getItem("silvernav_token") || "",
    baseDate: "",
    currentView: "flow"
};

function showLineageToast(msg, isError = false) {
    const toast = document.getElementById("lineageToast");
    if (!toast) return;
    toast.textContent = msg;
    toast.classList.toggle("error", isError);
    toast.classList.add("show");
    window.clearTimeout(showLineageToast.timer);
    showLineageToast.timer = window.setTimeout(() => {
        toast.classList.remove("show");
    }, 2000);
}

// 初始化粒子特效
function initParticles() {
    const particlesContainer = document.getElementById('particles');
    if (!particlesContainer) return;

    const particleCount = 20;
    for (let i = 0; i < particleCount; i++) {
        const particle = document.createElement('div');
        particle.className = 'particle';

        const startX = Math.random() * 100;
        const startY = Math.random() * 100;
        const size = Math.random() * 3 + 2;

        const colors = [
            'rgba(60, 235, 220, 0.8)',
            'rgba(79, 168, 255, 0.8)',
            'rgba(126, 247, 240, 0.7)'
        ];
        const color = colors[Math.floor(Math.random() * colors.length)];

        const delay = Math.random() * 20;
        const duration = 20 + Math.random() * 15;

        particle.style.cssText = `
            position: absolute;
            width: ${size}px;
            height: ${size}px;
            background: ${color};
            border-radius: 50%;
            top: ${startY}%;
            left: ${startX}%;
            animation: float-particle ${duration}s ease-in-out ${delay}s infinite;
            box-shadow: 0 0 ${size * 5}px ${color},
                        0 0 ${size * 10}px ${color.replace('0.8', '0.4')},
                        0 0 ${size * 15}px ${color.replace('0.8', '0.2')};
            pointer-events: none;
        `;

        particlesContainer.appendChild(particle);
    }
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
    Lineage.baseDate = baseDate;

    const baseDateEl = document.getElementById("baseDateValue");
    if (baseDateEl) {
        baseDateEl.textContent = baseDate;
    }
}

// 绘制数据血缘图谱
function drawLineageGraph() {
    const svg = document.getElementById("lineageSvg");
    if (!svg) return;

    // 清空现有内容
    const sourceLayer = document.getElementById("sourceLayer");
    const connectionLayer = document.getElementById("connectionLayer");
    const processLayer = document.getElementById("processLayer");
    const applicationLayer = document.getElementById("applicationLayer");

    sourceLayer.innerHTML = '';
    connectionLayer.innerHTML = '';
    processLayer.innerHTML = '';
    applicationLayer.innerHTML = '';

    // 根据当前视图绘制不同的图谱
    if (Lineage.currentView === 'flow') {
        drawFlowView();
    } else if (Lineage.currentView === 'tree') {
        drawTreeView();
    } else if (Lineage.currentView === 'network') {
        drawNetworkView();
    }
}

// 流程视图
function drawFlowView() {
    const sourceLayer = document.getElementById("sourceLayer");
    const connectionLayer = document.getElementById("connectionLayer");
    const processLayer = document.getElementById("processLayer");
    const applicationLayer = document.getElementById("applicationLayer");

    // 定义节点数据（增强版，包含Redis和ClickHouse）
    const nodes = {
        sources: [
            { id: 'ais_signal', name: 'AIS信号源', x: 50, y: 80, color: '#3cebdc', icon: '📡' },
            { id: 'pg_vessels', name: 'PostgreSQL', x: 50, y: 200, color: '#4fa8ff', icon: '🗃️' },
            { id: 'redis', name: 'Redis', x: 50, y: 320, color: '#ff5a7a', icon: '⚡' },
            { id: 'clickhouse', name: 'ClickHouse', x: 50, y: 440, color: '#ffd65c', icon: '🚀' }
        ],
        processes: [
            { id: 'ais_tracks', name: 'ais_tracks', desc: 'MongoDB', x: 350, y: 80, color: '#3cebdc' },
            { id: 'spark_analysis', name: 'Spark分析', desc: '批处理', x: 350, y: 180, color: '#ffd65c' },
            { id: 'anomaly_detect', name: '异常检测', desc: '实时分析', x: 350, y: 280, color: '#ff9f1c' },
            { id: 'cache_layer', name: '缓存层', desc: 'Redis', x: 350, y: 380, color: '#ff5a7a' },
            { id: 'olap_layer', name: 'OLAP分析', desc: 'ClickHouse', x: 350, y: 480, color: '#ffd65c' }
        ],
        applications: [
            { id: 'vessel_stats', name: 'vessel_statistics', desc: 'MongoDB', x: 650, y: 100, color: '#3cebdc' },
            { id: 'ais_anomalies', name: 'ais_anomalies', desc: 'MongoDB', x: 650, y: 220, color: '#ff5a7a' },
            { id: 'dashboard', name: '仪表盘', desc: '实时展示', x: 650, y: 340, color: '#4fa8ff' },
            { id: 'analytics', name: '数据分析', desc: 'ClickHouse', x: 650, y: 460, color: '#ffd65c' }
        ],
        outputs: [
            { id: 'vessel_analysis', name: 'vessel_analysis', desc: '船舶画像', x: 950, y: 150, color: '#3cebdc' },
            { id: 'risk_assessment', name: '风控评估', desc: '综合分析', x: 950, y: 300, color: '#4fa8ff' },
            { id: 'ml_predict', name: 'ML预测', desc: '智能预测', x: 950, y: 450, color: '#ff9f1c' }
        ]
    };

    // 定义连接关系（增强版）
    const connections = [
        { from: 'ais_signal', to: 'ais_tracks' },
        { from: 'ais_tracks', to: 'spark_analysis' },
        { from: 'ais_tracks', to: 'anomaly_detect' },
        { from: 'spark_analysis', to: 'vessel_stats' },
        { from: 'anomaly_detect', to: 'ais_anomalies' },
        { from: 'redis', to: 'cache_layer' },
        { from: 'cache_layer', to: 'dashboard' },
        { from: 'clickhouse', to: 'olap_layer' },
        { from: 'olap_layer', to: 'analytics' },
        { from: 'vessel_stats', to: 'vessel_analysis' },
        { from: 'ais_anomalies', to: 'risk_assessment' },
        { from: 'pg_vessels', to: 'risk_assessment' },
        { from: 'dashboard', to: 'risk_assessment' },
        { from: 'analytics', to: 'ml_predict' },
        { from: 'vessel_analysis', to: 'ml_predict' }
    ];

    // 绘制连接线
    connections.forEach(conn => {
        const fromNode = [...nodes.sources, ...nodes.processes, ...nodes.applications, ...nodes.outputs].find(n => n.id === conn.from);
        const toNode = [...nodes.sources, ...nodes.processes, ...nodes.applications, ...nodes.outputs].find(n => n.id === conn.to);

        if (fromNode && toNode) {
            drawConnection(connectionLayer, fromNode, toNode);
        }
    });

    // 绘制节点
    nodes.sources.forEach(node => drawNode(sourceLayer, node, true));
    nodes.processes.forEach(node => drawNode(processLayer, node));
    nodes.applications.forEach(node => drawNode(applicationLayer, node));
    nodes.outputs.forEach(node => drawNode(applicationLayer, node));
}

// 树形视图
function drawTreeView() {
    const sourceLayer = document.getElementById("sourceLayer");
    const connectionLayer = document.getElementById("connectionLayer");
    const processLayer = document.getElementById("processLayer");

    // 树形结构数据
    const treeData = {
        root: { id: 'root', name: '数据源', x: 600, y: 50, color: '#3cebdc', icon: '🗄️' },
        level1: [
            { id: 'mongo', name: 'MongoDB', x: 200, y: 150, color: '#3cebdc', icon: '📦' },
            { id: 'pg', name: 'PostgreSQL', x: 450, y: 150, color: '#4fa8ff', icon: '🗃️' },
            { id: 'redis', name: 'Redis', x: 700, y: 150, color: '#ff5a7a', icon: '⚡' },
            { id: 'ch', name: 'ClickHouse', x: 950, y: 150, color: '#ffd65c', icon: '🚀' }
        ],
        level2: [
            { id: 'ais', name: 'ais_tracks', parent: 'mongo', x: 100, y: 280, color: '#3cebdc' },
            { id: 'stats', name: 'vessel_statistics', parent: 'mongo', x: 300, y: 280, color: '#3cebdc' },
            { id: 'vessels', name: 'vessels', parent: 'pg', x: 450, y: 280, color: '#4fa8ff' },
            { id: 'cache', name: 'session:*', parent: 'redis', x: 700, y: 280, color: '#ff5a7a' },
            { id: 'metrics', name: 'vessel_metrics', parent: 'ch', x: 950, y: 280, color: '#ffd65c' }
        ],
        level3: [
            { id: 'analysis', name: 'vessel_analysis', parent: 'stats', x: 200, y: 410, color: '#3cebdc' },
            { id: 'risk', name: '风控评估', parent: 'vessels', x: 450, y: 410, color: '#4fa8ff' },
            { id: 'dashboard', name: '仪表盘', parent: 'cache', x: 700, y: 410, color: '#ff5a7a' },
            { id: 'ml', name: 'ML预测', parent: 'metrics', x: 950, y: 410, color: '#ffd65c' }
        ]
    };

    // 绘制根节点
    drawNode(sourceLayer, treeData.root, true);

    // 绘制第一层
    treeData.level1.forEach(node => {
        drawNode(processLayer, node, true);
        drawConnection(connectionLayer, treeData.root, node);
    });

    // 绘制第二层
    treeData.level2.forEach(node => {
        const parent = treeData.level1.find(n => n.id === node.parent);
        drawNode(processLayer, node);
        if (parent) drawConnection(connectionLayer, parent, node);
    });

    // 绘制第三层
    treeData.level3.forEach(node => {
        const parent = treeData.level2.find(n => n.id === node.parent);
        drawNode(processLayer, node);
        if (parent) drawConnection(connectionLayer, parent, node);
    });
}

// 网络视图
function drawNetworkView() {
    const sourceLayer = document.getElementById("sourceLayer");
    const connectionLayer = document.getElementById("connectionLayer");
    const processLayer = document.getElementById("processLayer");

    // 中心节点
    const center = { id: 'center', name: '数据中心', x: 600, y: 300, color: '#3cebdc', icon: '🌐' };

    // 环形分布的节点
    const radius = 250;
    const nodes = [
        { id: 'mongo', name: 'MongoDB', angle: 0, color: '#3cebdc', icon: '📦' },
        { id: 'pg', name: 'PostgreSQL', angle: 60, color: '#4fa8ff', icon: '🗃️' },
        { id: 'redis', name: 'Redis', angle: 120, color: '#ff5a7a', icon: '⚡' },
        { id: 'ch', name: 'ClickHouse', angle: 180, color: '#ffd65c', icon: '🚀' },
        { id: 'spark', name: 'Spark', angle: 240, color: '#ff9f1c', icon: '⚙️' },
        { id: 'ml', name: 'ML引擎', angle: 300, color: '#7ef7f0', icon: '🤖' }
    ];

    // 计算节点位置
    nodes.forEach(node => {
        const radian = (node.angle * Math.PI) / 180;
        node.x = center.x + radius * Math.cos(radian);
        node.y = center.y + radius * Math.sin(radian);
    });

    // 绘制中心节点
    drawNode(sourceLayer, center, true);

    // 绘制环形节点和连接
    nodes.forEach(node => {
        drawNode(processLayer, node, true);
        drawConnection(connectionLayer, center, node);
    });

    // 绘制节点间的连接
    for (let i = 0; i < nodes.length; i++) {
        const nextIndex = (i + 1) % nodes.length;
        drawConnection(connectionLayer, nodes[i], nodes[nextIndex], true);
    }
}

// 绘制连接线
function drawConnection(layer, fromNode, toNode, isDashed = false) {
    const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
    const fromX = fromNode.x + 80;
    const fromY = fromNode.y + 30;
    const toX = toNode.x;
    const toY = toNode.y + 30;
    const midX = (fromX + toX) / 2;

    path.setAttribute("d", `M ${fromX} ${fromY} C ${midX} ${fromY}, ${midX} ${toY}, ${toX} ${toY}`);
    path.setAttribute("class", "connection-line");
    path.setAttribute("stroke", fromNode.color);
    if (isDashed) {
        path.setAttribute("stroke-dasharray", "5,5");
        path.setAttribute("opacity", "0.4");
    }
    layer.appendChild(path);

    // 添加流动粒子效果
    const circle = document.createElementNS("http://www.w3.org/2000/svg", "circle");
    circle.setAttribute("r", "4");
    circle.setAttribute("fill", fromNode.color);
    circle.setAttribute("opacity", "0.8");
    circle.setAttribute("filter", "url(#glow)");

    const animateMotion = document.createElementNS("http://www.w3.org/2000/svg", "animateMotion");
    animateMotion.setAttribute("dur", "3s");
    animateMotion.setAttribute("repeatCount", "indefinite");
    animateMotion.setAttribute("path", `M ${fromX} ${fromY} C ${midX} ${fromY}, ${midX} ${toY}, ${toX} ${toY}`);

    circle.appendChild(animateMotion);
    layer.appendChild(circle);
}

// 绘制单个节点
function drawNode(layer, node, hasIcon = false) {
    const g = document.createElementNS("http://www.w3.org/2000/svg", "g");
    g.setAttribute("class", "node-group");
    g.setAttribute("transform", `translate(${node.x}, ${node.y})`);
    g.style.cursor = "pointer";

    // 节点矩形
    const rect = document.createElementNS("http://www.w3.org/2000/svg", "rect");
    rect.setAttribute("width", "160");
    rect.setAttribute("height", "60");
    rect.setAttribute("rx", "8");
    rect.setAttribute("class", "node-rect");
    rect.setAttribute("stroke", node.color);
    g.appendChild(rect);

    // 图标（如果有）- 放在左侧
    if (hasIcon && node.icon) {
        const iconText = document.createElementNS("http://www.w3.org/2000/svg", "text");
        iconText.setAttribute("x", "15");
        iconText.setAttribute("y", "38");
        iconText.setAttribute("font-size", "22");
        iconText.setAttribute("opacity", "0.9");
        iconText.setAttribute("filter", "url(#glow)");
        iconText.textContent = node.icon;
        g.appendChild(iconText);
    }

    // 节点名称 - 放在图标右侧，确保不重叠
    const text = document.createElementNS("http://www.w3.org/2000/svg", "text");
    text.setAttribute("x", hasIcon ? "45" : "80");
    text.setAttribute("y", "28");
    text.setAttribute("class", "node-text");
    text.setAttribute("fill", node.color);
    text.setAttribute("text-anchor", hasIcon ? "start" : "middle");
    text.setAttribute("font-size", "14");
    text.setAttribute("font-weight", "600");
    text.textContent = node.name;
    g.appendChild(text);

    // 节点描述
    if (node.desc) {
        const desc = document.createElementNS("http://www.w3.org/2000/svg", "text");
        desc.setAttribute("x", hasIcon ? "45" : "80");
        desc.setAttribute("y", "45");
        desc.setAttribute("class", "node-desc");
        desc.setAttribute("text-anchor", hasIcon ? "start" : "middle");
        desc.textContent = node.desc;
        g.appendChild(desc);
    }

    // 添加脉冲动画
    const pulse = document.createElementNS("http://www.w3.org/2000/svg", "rect");
    pulse.setAttribute("width", "160");
    pulse.setAttribute("height", "60");
    pulse.setAttribute("rx", "8");
    pulse.setAttribute("fill", "none");
    pulse.setAttribute("stroke", node.color);
    pulse.setAttribute("stroke-width", "2");
    pulse.setAttribute("opacity", "0");

    const animate = document.createElementNS("http://www.w3.org/2000/svg", "animate");
    animate.setAttribute("attributeName", "opacity");
    animate.setAttribute("values", "0;0.6;0");
    animate.setAttribute("dur", "2s");
    animate.setAttribute("repeatCount", "indefinite");
    pulse.appendChild(animate);

    const animateScale = document.createElementNS("http://www.w3.org/2000/svg", "animateTransform");
    animateScale.setAttribute("attributeName", "transform");
    animateScale.setAttribute("type", "scale");
    animateScale.setAttribute("values", "1 1;1.1 1.1;1 1");
    animateScale.setAttribute("dur", "2s");
    animateScale.setAttribute("repeatCount", "indefinite");
    animateScale.setAttribute("additive", "sum");
    pulse.appendChild(animateScale);

    g.appendChild(pulse);

    layer.appendChild(g);
}

// 加载MongoDB数据统计
async function loadMongoStats() {
    if (!Lineage.token) return;

    try {
        const db = await fetch("/api/behavior/summary", {
            method: "GET",
            headers: {
                "Authorization": `Bearer ${Lineage.token}`,
                "Content-Type": "application/json"
            }
        });

        const data = await db.json();

        if (data.success) {
            const summary = data.summary;

            // 更新统计数据
            const aisTracksEl = document.getElementById("aisTracksCount");
            const anomaliesEl = document.getElementById("anomaliesCount");

            if (aisTracksEl) aisTracksEl.textContent = summary.total_tracks.toLocaleString();
            if (anomaliesEl) anomaliesEl.textContent = summary.anomaly_count.toLocaleString();

            console.log("MongoDB统计数据加载成功", summary);
        }
    } catch (error) {
        console.error("加载MongoDB统计失败:", error);
    }

    // 固定显示数据表和数据流数量
    const tableCountEl = document.getElementById("tableCount");
    const dataFlowCountEl = document.getElementById("dataFlowCount");

    if (tableCountEl) tableCountEl.textContent = "18";  // MongoDB(4) + PostgreSQL(3) + Redis(3) + ClickHouse(3)
    if (dataFlowCountEl) dataFlowCountEl.textContent = "15";  // 总数据流数量
}

// 加载PostgreSQL数据统计
async function loadPgStats() {
    // 固定显示数据
    const vesselsCountEl = document.getElementById("vesselsCount");
    const companiesCountEl = document.getElementById("companiesCount");
    const assetsCountEl = document.getElementById("assetsCount");

    if (vesselsCountEl) vesselsCountEl.textContent = "14,000";
    if (companiesCountEl) companiesCountEl.textContent = "50,000";
    if (assetsCountEl) assetsCountEl.textContent = "30,000,000";
}

// 切换视图
function switchView(view) {
    Lineage.currentView = view;

    // 更新按钮状态
    document.querySelectorAll('.control-btn').forEach(btn => {
        btn.classList.remove('active');
        if (btn.dataset.view === view) {
            btn.classList.add('active');
        }
    });

    // 重新绘制图谱
    drawLineageGraph();

    showLineageToast(`切换到${view === 'flow' ? '流程' : view === 'tree' ? '树形' : '网络'}视图`);
}

// 返回大屏
function goBack() {
    window.location.href = "/dashboard";
}

// 页面初始化
document.addEventListener("DOMContentLoaded", function() {
    console.log("数据血缘页面初始化");

    // 初始化时钟
    initClock();

    // 更新基准日期显示
    updateBaseDateDisplay();

    // 监听localStorage变化
    window.addEventListener('storage', function(e) {
        if (e.key === 'silvernav_base_date') {
            updateBaseDateDisplay();
        }
    });

    // 检查登录状态
    if (!Lineage.token) {
        showLineageToast("请先登录", true);
        setTimeout(() => {
            window.location.href = "/";
        }, 2000);
        return;
    }

    // 绘制数据血缘图谱
    drawLineageGraph();

    // 加载统计数据
    loadMongoStats();
    loadPgStats();

    // 绑定返回按钮
    const backBtn = document.getElementById("backBtn");
    if (backBtn) {
        backBtn.addEventListener("click", goBack);
    }

    // 绑定视图切换按钮
    document.querySelectorAll('.control-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const view = this.dataset.view;
            switchView(view);
        });
    });

    // 绑定表格项点击事件
    document.querySelectorAll('.table-item').forEach(item => {
        item.addEventListener('click', function() {
            const tableName = this.dataset.table;
            showLineageToast(`查看 ${tableName} 详情`);
            // 这里可以添加显示表详情的逻辑
        });
    });

    // 添加数据流动画效果
    animateDataFlow();
});

// 数据流动画效果
function animateDataFlow() {
    const dataFlowBg = document.getElementById("dataFlowBg");
    if (!dataFlowBg) return;

    // 创建流动粒子
    for (let i = 0; i < 20; i++) {
        const particle = document.createElement('div');
        particle.style.position = 'absolute';
        particle.style.width = '2px';
        particle.style.height = '2px';
        particle.style.background = 'rgba(60, 235, 220, 0.6)';
        particle.style.borderRadius = '50%';
        particle.style.boxShadow = '0 0 10px rgba(60, 235, 220, 0.8)';
        particle.style.left = Math.random() * 100 + '%';
        particle.style.top = Math.random() * 100 + '%';
        particle.style.animation = `floatParticle ${10 + Math.random() * 10}s linear infinite`;
        particle.style.animationDelay = Math.random() * 5 + 's';
        dataFlowBg.appendChild(particle);
    }
}

// 添加CSS动画
const style = document.createElement('style');
style.textContent = `
    @keyframes floatParticle {
        0% {
            transform: translate(0, 0);
            opacity: 0;
        }
        10% {
            opacity: 1;
        }
        90% {
            opacity: 1;
        }
        100% {
            transform: translate(${Math.random() * 200 - 100}px, ${Math.random() * 200 - 100}px);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);
