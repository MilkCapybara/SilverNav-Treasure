// 数据血缘页面逻辑 - 完整版
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

    // 定义节点数据
    const nodes = {
        // 数据源层
        sources: [
            { id: 'ais_signal', name: 'AIS信号源', x: 100, y: 100, color: '#3cebdc' },
            { id: 'pg_vessels', name: 'PostgreSQL', x: 100, y: 250, color: '#4fa8ff' }
        ],
        // 处理层
        processes: [
            { id: 'ais_tracks', name: 'ais_tracks', desc: '轨迹数据', x: 400, y: 100, color: '#3cebdc' },
            { id: 'spark_analysis', name: 'Spark分析', desc: '批处理', x: 400, y: 200, color: '#ffd65c' },
            { id: 'anomaly_detect', name: '异常检测', desc: '实时分析', x: 400, y: 300, color: '#ff9f1c' },
            { id: 'vessel_stats', name: 'vessel_statistics', desc: '统计结果', x: 700, y: 150, color: '#3cebdc' },
            { id: 'ais_anomalies', name: 'ais_anomalies', desc: '异常记录', x: 700, y: 300, color: '#ff5a7a' }
        ],
        // 应用层
        applications: [
            { id: 'vessel_analysis', name: 'vessel_analysis', desc: '船舶画像', x: 1000, y: 150, color: '#3cebdc' },
            { id: 'risk_assessment', name: '风控评估', desc: '综合分析', x: 1000, y: 300, color: '#4fa8ff' }
        ]
    };

    // 定义连接关系
    const connections = [
        { from: 'ais_signal', to: 'ais_tracks' },
        { from: 'ais_tracks', to: 'spark_analysis' },
        { from: 'ais_tracks', to: 'anomaly_detect' },
        { from: 'spark_analysis', to: 'vessel_stats' },
        { from: 'anomaly_detect', to: 'ais_anomalies' },
        { from: 'vessel_stats', to: 'vessel_analysis' },
        { from: 'ais_anomalies', to: 'risk_assessment' },
        { from: 'pg_vessels', to: 'risk_assessment' }
    ];

    // 绘制连接线
    connections.forEach(conn => {
        const fromNode = [...nodes.sources, ...nodes.processes, ...nodes.applications].find(n => n.id === conn.from);
        const toNode = [...nodes.sources, ...nodes.processes, ...nodes.applications].find(n => n.id === conn.to);

        if (fromNode && toNode) {
            const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
            const fromX = fromNode.x + 80;
            const fromY = fromNode.y + 30;
            const toX = toNode.x;
            const toY = toNode.y + 30;
            const midX = (fromX + toX) / 2;

            path.setAttribute("d", `M ${fromX} ${fromY} C ${midX} ${fromY}, ${midX} ${toY}, ${toX} ${toY}`);
            path.setAttribute("class", "connection-line");
            path.setAttribute("stroke", fromNode.color);
            connectionLayer.appendChild(path);

            // 添加流动粒子效果
            const circle = document.createElementNS("http://www.w3.org/2000/svg", "circle");
            circle.setAttribute("r", "4");
            circle.setAttribute("fill", fromNode.color);
            circle.setAttribute("opacity", "0.8");

            const animateMotion = document.createElementNS("http://www.w3.org/2000/svg", "animateMotion");
            animateMotion.setAttribute("dur", "3s");
            animateMotion.setAttribute("repeatCount", "indefinite");
            animateMotion.setAttribute("path", `M ${fromX} ${fromY} C ${midX} ${fromY}, ${midX} ${toY}, ${toX} ${toY}`);

            circle.appendChild(animateMotion);
            connectionLayer.appendChild(circle);
        }
    });

    // 绘制数据源节点
    nodes.sources.forEach(node => {
        drawNode(sourceLayer, node);
    });

    // 绘制处理层节点
    nodes.processes.forEach(node => {
        drawNode(processLayer, node);
    });

    // 绘制应用层节点
    nodes.applications.forEach(node => {
        drawNode(applicationLayer, node);
    });
}

// 绘制单个节点
function drawNode(layer, node) {
    const g = document.createElementNS("http://www.w3.org/2000/svg", "g");
    g.setAttribute("class", "node-group");
    g.setAttribute("transform", `translate(${node.x}, ${node.y})`);

    // 节点矩形
    const rect = document.createElementNS("http://www.w3.org/2000/svg", "rect");
    rect.setAttribute("width", "160");
    rect.setAttribute("height", "60");
    rect.setAttribute("rx", "8");
    rect.setAttribute("class", "node-rect");
    rect.setAttribute("stroke", node.color);
    g.appendChild(rect);

    // 节点名称
    const text = document.createElementNS("http://www.w3.org/2000/svg", "text");
    text.setAttribute("x", "80");
    text.setAttribute("y", "28");
    text.setAttribute("class", "node-text");
    text.setAttribute("fill", node.color);
    text.textContent = node.name;
    g.appendChild(text);

    // 节点描述
    if (node.desc) {
        const desc = document.createElementNS("http://www.w3.org/2000/svg", "text");
        desc.setAttribute("x", "80");
        desc.setAttribute("y", "45");
        desc.setAttribute("class", "node-desc");
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
            document.getElementById("aisTracksCount").textContent = summary.total_tracks.toLocaleString();
            document.getElementById("anomaliesCount").textContent = summary.anomaly_count.toLocaleString();

            // 计算总表数
            const mongoTables = 4; // ais_tracks, vessel_statistics, ais_anomalies, vessel_analysis
            const pgTables = 3; // vessels, companies, assets
            document.getElementById("tableCount").textContent = mongoTables + pgTables;

            // 计算数据流数量
            document.getElementById("dataFlowCount").textContent = "8";

            console.log("MongoDB统计数据加载成功", summary);
        }
    } catch (error) {
        console.error("加载MongoDB统计失败:", error);
    }
}

// 加载PostgreSQL数据统计
async function loadPgStats() {
    // 这里可以添加PostgreSQL统计的API调用
    // 暂时使用模拟数据
    document.getElementById("vesselsCount").textContent = "1,234";
    document.getElementById("companiesCount").textContent = "567";
    document.getElementById("assetsCount").textContent = "890";
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
