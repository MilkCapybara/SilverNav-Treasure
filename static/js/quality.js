// 数据质量监控 JavaScript

// 时钟更新
function updateClock() {
    const now = new Date();
    const timeStr = now.toLocaleTimeString('zh-CN', {
        hour12: false,
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
    });
    const dateStr = now.toLocaleDateString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit'
    });

    const clockEl = document.getElementById('cnClock');
    if (clockEl) {
        clockEl.textContent = `${dateStr} ${timeStr}`;
    }
}

// 返回按钮
document.getElementById('backBtn')?.addEventListener('click', () => {
    window.location.href = '/dashboard';
});

// 从API获取真实质量数据
async function updateQualityMetrics() {
    try {
        const response = await fetch('/api/quality/metrics');
        const result = await response.json();

        if (result.success) {
            const data = result.data;

            // 更新四维质量指标
            document.getElementById('completeness').textContent = `${data.completeness}%`;
            document.getElementById('accuracy').textContent = `${data.accuracy}%`;
            document.getElementById('timeliness').textContent = `${data.timeliness}%`;
            document.getElementById('consistency').textContent = `${data.consistency}%`;

            // 更新综合质量分
            document.getElementById('overallScore').textContent = data.overall_score;

            // 更新状态标签
            updateStatusBadge('completeness', data.completeness);
            updateStatusBadge('accuracy', data.accuracy);
            updateStatusBadge('timeliness', data.timeliness);
            updateStatusBadge('consistency', data.consistency);

            // 更新数据表质量
            updateTableQualityDisplay(data.tables);

            // 更新异常统计
            updateAnomalyDisplay(data.anomalies);

            // 更新质量趋势图
            updateQualityTrendChart(data);
        }
    } catch (error) {
        console.error('获取质量数据失败:', error);
    }
}

// 更新状态标签
function updateStatusBadge(metricId, value) {
    const element = document.getElementById(metricId);
    if (!element) return;

    const statusElement = element.parentElement.querySelector('.stat-status');
    if (!statusElement) return;

    statusElement.classList.remove('excellent', 'good', 'warning');

    if (value >= 95) {
        statusElement.textContent = '优秀';
        statusElement.classList.add('excellent');
    } else if (value >= 85) {
        statusElement.textContent = '良好';
        statusElement.classList.add('good');
    } else {
        statusElement.textContent = '待优化';
        statusElement.classList.add('warning');
    }
}

// 更新数据表质量显示
function updateTableQualityDisplay(tables) {
    if (!tables || tables.length === 0) return;

    // 更新表格中的数据
    const tableRows = document.querySelectorAll('.table-row');
    tables.forEach((table, index) => {
        if (tableRows[index]) {
            const row = tableRows[index];
            row.querySelector('.col-name').textContent = table.name;
            row.querySelector('.col-records').textContent = table.records >= 1000000
                ? `${(table.records / 1000000).toFixed(1)}M+`
                : table.records.toLocaleString();
            row.querySelector('.col-null').textContent = `${table.null_rate}%`;
            row.querySelector('.col-duplicate').textContent = `${table.dup_rate}%`;

            const scoreEl = row.querySelector('.col-score');
            scoreEl.textContent = table.score;
            scoreEl.className = 'col-score';
            if (table.score >= 95) {
                scoreEl.classList.add('excellent');
            } else if (table.score >= 85) {
                scoreEl.classList.add('good');
            } else {
                scoreEl.classList.add('warning');
            }

            const statusBadge = row.querySelector('.status-badge');
            statusBadge.className = 'status-badge';
            if (table.score >= 95) {
                statusBadge.classList.add('excellent');
                statusBadge.textContent = '优秀';
            } else if (table.score >= 85) {
                statusBadge.classList.add('good');
                statusBadge.textContent = '良好';
            } else {
                statusBadge.classList.add('warning');
                statusBadge.textContent = '待优化';
            }
        }
    });
}

// 更新异常统计显示
function updateAnomalyDisplay(anomalies) {
    if (!anomalies) return;

    const anomalyItems = document.querySelectorAll('.anomaly-item');
    const anomalyData = [
        { key: 'null_values', label: '空值异常' },
        { key: 'format_errors', label: '格式错误' },
        { key: 'duplicates', label: '重复记录' },
        { key: 'logic_conflicts', label: '逻辑冲突' }
    ];

    anomalyData.forEach((item, index) => {
        if (anomalyItems[index]) {
            const countEl = anomalyItems[index].querySelector('.anomaly-count');
            if (countEl) {
                countEl.textContent = anomalies[item.key].toLocaleString();
            }
        }
    });
}

// 更新质量趋势图（简化版Canvas绘制）
let qualityHistory = [];
function updateQualityTrendChart(data) {
    const canvas = document.getElementById('qualityTrendChart');
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    const width = canvas.width = canvas.offsetWidth;
    const height = canvas.height = canvas.offsetHeight;

    // 添加当前数据点
    qualityHistory.push({
        time: new Date().getTime(),
        completeness: data.completeness,
        accuracy: data.accuracy,
        timeliness: data.timeliness,
        consistency: data.consistency
    });

    // 只保留最近30个数据点
    if (qualityHistory.length > 30) {
        qualityHistory.shift();
    }

    // 清空画布
    ctx.clearRect(0, 0, width, height);

    // 绘制网格
    ctx.strokeStyle = 'rgba(60, 235, 220, 0.1)';
    ctx.lineWidth = 1;
    for (let i = 0; i <= 4; i++) {
        const y = (height / 4) * i;
        ctx.beginPath();
        ctx.moveTo(0, y);
        ctx.lineTo(width, y);
        ctx.stroke();
    }

    if (qualityHistory.length < 2) return;

    // 绘制四条质量线
    const metrics = [
        { key: 'completeness', color: '#4ade80' },
        { key: 'accuracy', color: '#4fa8ff' },
        { key: 'timeliness', color: '#fbbf24' },
        { key: 'consistency', color: '#a78bfa' }
    ];

    metrics.forEach(metric => {
        ctx.strokeStyle = metric.color;
        ctx.lineWidth = 2;
        ctx.beginPath();

        qualityHistory.forEach((point, i) => {
            const x = (width / (qualityHistory.length - 1)) * i;
            const y = height - (point[metric.key] / 100) * height * 0.9;
            if (i === 0) {
                ctx.moveTo(x, y);
            } else {
                ctx.lineTo(x, y);
            }
        });
        ctx.stroke();
    });
}

// 从API获取时效性数据
async function updateTimelinessMonitoring() {
    try {
        const response = await fetch('/api/quality/timeliness');
        const result = await response.json();

        if (result.success) {
            const timelinessItems = document.querySelectorAll('.timeliness-item');
            const data = result.data;

            data.forEach((item, index) => {
                if (timelinessItems[index]) {
                    const timeValue = timelinessItems[index].querySelector('.time-value');
                    const timeStatus = timelinessItems[index].querySelector('.time-status');
                    const timeBar = timelinessItems[index].querySelector('.time-bar');

                    if (timeValue) {
                        timeValue.textContent = item.last_update;
                    }

                    if (timeStatus) {
                        timeStatus.className = `time-status ${item.status}`;
                        if (item.status === 'fresh') {
                            timeStatus.textContent = '实时';
                        } else if (item.status === 'normal') {
                            timeStatus.textContent = '正常';
                        } else {
                            timeStatus.textContent = '延迟';
                        }
                    }

                    if (timeBar) {
                        timeBar.className = `time-bar ${item.status}`;
                        // 根据状态设置进度条宽度
                        if (item.status === 'fresh') {
                            timeBar.style.width = '95%';
                        } else if (item.status === 'normal') {
                            timeBar.style.width = '75%';
                        } else {
                            timeBar.style.width = '40%';
                        }
                    }
                }
            });
        }
    } catch (error) {
        console.error('获取时效性数据失败:', error);
    }
}

// 处理改进建议按钮点击
function setupSuggestionButtons() {
    const actionButtons = document.querySelectorAll('.action-btn');

    actionButtons.forEach(button => {
        button.addEventListener('click', (e) => {
            const buttonText = e.target.textContent;

            if (buttonText === '查看详情') {
                showToast('详情功能开发中...', 'info');
            } else if (buttonText === '标记已读') {
                const suggestionItem = e.target.closest('.suggestion-item');
                suggestionItem.style.opacity = '0.5';
                showToast('已标记为已读', 'success');
            }
        });
    });
}

// 显示提示消息
function showToast(message, type = 'info') {
    const toast = document.getElementById('qualityToast');
    if (!toast) return;

    toast.textContent = message;
    toast.className = `toast ${type}`;
    toast.style.display = 'block';

    setTimeout(() => {
        toast.style.display = 'none';
    }, 3000);
}

// 动画效果：数据流动
function animateDataFlow() {
    const dataFlow = document.querySelector('.data-flow');
    if (!dataFlow) return;

    // 创建流动的数据点
    for (let i = 0; i < 5; i++) {
        const dot = document.createElement('div');
        dot.style.position = 'absolute';
        dot.style.width = '4px';
        dot.style.height = '4px';
        dot.style.background = 'rgba(60, 235, 220, 0.8)';
        dot.style.borderRadius = '50%';
        dot.style.boxShadow = '0 0 10px rgba(60, 235, 220, 0.8)';
        dot.style.top = `${Math.random() * 100}%`;
        dot.style.left = '-10px';
        dot.style.animation = `dataFlow ${8 + Math.random() * 4}s linear infinite`;
        dot.style.animationDelay = `${i * 2}s`;

        dataFlow.appendChild(dot);
    }
}

// 初始化
function init() {
    updateClock();
    setInterval(updateClock, 1000);

    updateQualityMetrics();
    setInterval(updateQualityMetrics, 10000);

    updateTimelinessMonitoring();
    setInterval(updateTimelinessMonitoring, 60000);

    setupSuggestionButtons();
    animateDataFlow();

    console.log('数据质量监控初始化完成');
}

// 页面加载完成后初始化
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    init();
}
