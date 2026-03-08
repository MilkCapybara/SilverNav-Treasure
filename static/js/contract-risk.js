// 合同风险分析页面JavaScript

// 全局变量
let currentPage = 1;
let pageSize = 10;  // 每页10条
let totalPages = 1;
let currentFilters = {
    keyword: '',
    risk_level: '',
    min_score: null,
    max_score: null
};

// 初始化
document.addEventListener('DOMContentLoaded', function() {
    initClock();
    initEventListeners();
    loadStatistics();
    loadContracts();
});

// 初始化时钟
function initClock() {
    function updateClock() {
        const now = new Date();
        const timeStr = now.toLocaleString('zh-CN', {
            timeZone: 'Asia/Shanghai',
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit',
            hour12: false
        });
        document.getElementById('cnClock').textContent = timeStr;
    }
    updateClock();
    setInterval(updateClock, 1000);
}

// 初始化事件监听
function initEventListeners() {
    // 返回按钮
    document.getElementById('backBtn').addEventListener('click', function() {
        window.location.href = '/dashboard';
    });

    // 搜索按钮
    document.getElementById('searchBtn').addEventListener('click', function() {
        currentPage = 1;
        applyFilters();
    });

    // 重置按钮
    document.getElementById('resetBtn').addEventListener('click', function() {
        document.getElementById('searchKeyword').value = '';
        document.getElementById('riskLevelFilter').value = '';
        document.getElementById('minScoreFilter').value = '';
        document.getElementById('maxScoreFilter').value = '';
        currentPage = 1;
        currentFilters = {
            keyword: '',
            risk_level: '',
            min_score: null,
            max_score: null
        };
        loadContracts();
    });

    // 回车搜索
    document.getElementById('searchKeyword').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            currentPage = 1;
            applyFilters();
        }
    });

    // 分页按钮
    document.getElementById('prevPage').addEventListener('click', function() {
        if (currentPage > 1) {
            currentPage--;
            loadContracts();
        }
    });

    document.getElementById('nextPage').addEventListener('click', function() {
        if (currentPage < totalPages) {
            currentPage++;
            loadContracts();
        }
    });

    // 关闭弹窗
    document.getElementById('modalClose').addEventListener('click', function() {
        closeModal();
    });

    // 点击弹窗外部关闭
    document.getElementById('contractModal').addEventListener('click', function(e) {
        if (e.target === this) {
            closeModal();
        }
    });
}

// 应用筛选条件
function applyFilters() {
    currentFilters.keyword = document.getElementById('searchKeyword').value.trim();
    currentFilters.risk_level = document.getElementById('riskLevelFilter').value;

    const minScore = document.getElementById('minScoreFilter').value;
    const maxScore = document.getElementById('maxScoreFilter').value;

    currentFilters.min_score = minScore ? parseFloat(minScore) : null;
    currentFilters.max_score = maxScore ? parseFloat(maxScore) : null;

    loadContracts();
}

// 加载统计数据
async function loadStatistics() {
    try {
        const response = await fetch('/api/contracts/stats/overview');
        const data = await response.json();

        if (data.success) {
            const stats = data.stats;

            // 更新统计卡片
            document.getElementById('totalContracts').textContent = stats.total.toLocaleString();
            document.getElementById('highRiskContracts').textContent = stats.high_risk.toLocaleString();
            document.getElementById('highRiskPercent').textContent = `${stats.high_risk_percent}%`;
            document.getElementById('mediumRiskContracts').textContent = stats.medium_risk.toLocaleString();
            document.getElementById('mediumRiskPercent').textContent = `${stats.medium_risk_percent}%`;
            document.getElementById('lowRiskContracts').textContent = stats.low_risk.toLocaleString();
            document.getElementById('lowRiskPercent').textContent = `${stats.low_risk_percent}%`;
            document.getElementById('avgRiskScore').textContent = stats.avg_score.toFixed(1);

            // 渲染风险等级分布环形图
            renderRiskRingChart(stats);

            // 渲染合同金额分布
            renderAmountDistribution();
        }
    } catch (error) {
        console.error('加载统计数据失败:', error);
    }
}

// 渲染风险等级分布环形图
function renderRiskRingChart(stats) {
    const canvas = document.getElementById('riskRingChart');
    const ctx = canvas.getContext('2d');

    // 设置canvas尺寸
    canvas.width = 300;
    canvas.height = 300;

    const centerX = canvas.width / 2;
    const centerY = canvas.height / 2;
    const outerRadius = 120;
    const innerRadius = 80;

    // 数据
    const data = [
        { label: '低风险', value: stats.low_risk, color: 'rgba(60, 235, 220, 0.8)' },
        { label: '中风险', value: stats.medium_risk, color: 'rgba(255, 181, 3, 0.8)' },
        { label: '高风险', value: stats.high_risk, color: 'rgba(255, 90, 122, 0.8)' }
    ];

    const total = data.reduce((sum, item) => sum + item.value, 0);

    // 绘制环形图
    let startAngle = -Math.PI / 2;

    data.forEach((item, index) => {
        const sliceAngle = (item.value / total) * 2 * Math.PI;
        const endAngle = startAngle + sliceAngle;

        // 绘制扇形
        ctx.beginPath();
        ctx.arc(centerX, centerY, outerRadius, startAngle, endAngle);
        ctx.arc(centerX, centerY, innerRadius, endAngle, startAngle, true);
        ctx.closePath();

        // 填充颜色
        ctx.fillStyle = item.color;
        ctx.fill();

        // 绘制边框
        ctx.strokeStyle = 'rgba(60, 235, 220, 0.3)';
        ctx.lineWidth = 2;
        ctx.stroke();

        // 添加发光效果
        ctx.shadowColor = item.color;
        ctx.shadowBlur = 10;

        startAngle = endAngle;
    });

    // 清除阴影
    ctx.shadowBlur = 0;

    // 更新中心文本
    document.getElementById('centerTotal').textContent = total.toLocaleString();

    // 更新图例
    document.getElementById('legendLow').textContent = stats.low_risk.toLocaleString();
    document.getElementById('legendMedium').textContent = stats.medium_risk.toLocaleString();
    document.getElementById('legendHigh').textContent = stats.high_risk.toLocaleString();
}

// 渲染合同金额分布
let cachedAmounts = null; // 缓存金额数据用于窗口resize

async function renderAmountDistribution() {
    try {
        // 获取合同数据样本
        const response = await fetch('/api/contracts/search', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                page: 1,
                page_size: 1000  // 获取更多样本用于统计
            })
        });

        const data = await response.json();

        if (data.success && data.contracts.length > 0) {
            const contracts = data.contracts;

            // 统计金额
            const amounts = contracts
                .filter(c => c.principal_amount)
                .map(c => c.principal_amount);

            if (amounts.length === 0) {
                return;
            }

            cachedAmounts = amounts; // 缓存数据

            const totalAmount = amounts.reduce((sum, amt) => sum + amt, 0);
            const avgAmount = totalAmount / amounts.length;
            const maxAmount = Math.max(...amounts);

            // 更新统计数据
            document.getElementById('totalAmount').textContent = '$' + (totalAmount / 1000000).toFixed(1) + 'M';
            document.getElementById('avgAmount').textContent = '$' + (avgAmount / 1000).toFixed(1) + 'K';
            document.getElementById('maxAmount').textContent = '$' + (maxAmount / 1000).toFixed(1) + 'K';

            // 绘制金额分布柱状图
            drawAmountChart(amounts);
        }
    } catch (error) {
        console.error('加载金额分布失败:', error);
    }
}

// 窗口大小改变时重新绘制图表
let resizeTimer;
window.addEventListener('resize', function() {
    clearTimeout(resizeTimer);
    resizeTimer = setTimeout(function() {
        if (cachedAmounts && cachedAmounts.length > 0) {
            drawAmountChart(cachedAmounts);
        }
    }, 250); // 防抖，250ms后执行
});

// 绘制金额分布图表
let chartData = null; // 存储图表数据用于悬浮交互

function drawAmountChart(amounts) {
    const canvas = document.getElementById('amountDistributionChart');
    const ctx = canvas.getContext('2d');
    const container = canvas.parentElement;

    // 获取容器的实际显示尺寸
    const containerWidth = container.clientWidth;
    const containerHeight = container.clientHeight;

    // 设置canvas的实际像素尺寸（不要超过容器）
    canvas.width = Math.min(containerWidth, 1200);
    canvas.height = Math.min(containerHeight, 350);

    // 设置canvas的CSS显示尺寸
    canvas.style.width = containerWidth + 'px';
    canvas.style.height = containerHeight + 'px';

    // 分组统计
    const ranges = [
        { min: 0, max: 2000000, label: '0-2M' },
        { min: 2000000, max: 4000000, label: '2-4M' },
        { min: 4000000, max: 6000000, label: '4-6M' },
        { min: 6000000, max: 8000000, label: '6-8M' },
        { min: 8000000, max: 10000000, label: '8-10M' },
        { min: 10000000, max: Infinity, label: '10M+' }
    ];

    const distribution = ranges.map((range, index) => ({
        label: range.label,
        count: amounts.filter(amt => amt >= range.min && amt < range.max).length,
        range: range
    }));

    const maxCount = Math.max(...distribution.map(d => d.count), 1);

    // 计算绘图区域 - 留出更多空间给图表
    const padding = { top: 30, right: 20, bottom: 50, left: 40 };
    const chartWidth = canvas.width - padding.left - padding.right;
    const chartHeight = canvas.height - padding.top - padding.bottom;

    // 绘制Y轴标签
    ctx.fillStyle = 'rgba(233, 246, 255, 0.68)';
    ctx.font = '12px "Saira Condensed"';
    ctx.textAlign = 'right';
    ctx.textBaseline = 'middle';

    // Y轴刻度
    const ySteps = 5;
    for (let i = 0; i <= ySteps; i++) {
        const value = Math.round((maxCount / ySteps) * i);
        const y = padding.top + chartHeight - (chartHeight / ySteps) * i;
        ctx.fillText(value.toString(), padding.left - 10, y);

        // 绘制网格线
        ctx.strokeStyle = 'rgba(60, 235, 220, 0.1)';
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.moveTo(padding.left, y);
        ctx.lineTo(padding.left + chartWidth, y);
        ctx.stroke();
    }

    // 绘制柱状图
    const barWidth = chartWidth / distribution.length * 0.75;
    const barGap = chartWidth / distribution.length * 0.25;

    chartData = {
        bars: [],
        canvas: canvas,
        padding: padding
    };

    distribution.forEach((item, index) => {
        const barHeight = (item.count / maxCount) * chartHeight;
        const x = padding.left + index * (barWidth + barGap) + barGap / 2;
        const y = padding.top + chartHeight - barHeight;

        // 存储柱子信息用于悬浮检测
        chartData.bars.push({
            x: x,
            y: y,
            width: barWidth,
            height: barHeight,
            label: item.label,
            count: item.count,
            range: item.range
        });

        // 绘制柱子 - 渐变效果
        const gradient = ctx.createLinearGradient(x, y, x, y + barHeight);
        gradient.addColorStop(0, 'rgba(60, 235, 220, 0.9)');
        gradient.addColorStop(0.5, 'rgba(79, 168, 255, 0.8)');
        gradient.addColorStop(1, 'rgba(60, 235, 220, 0.6)');

        ctx.fillStyle = gradient;
        ctx.fillRect(x, y, barWidth, barHeight);

        // 绘制发光边框
        ctx.strokeStyle = 'rgba(60, 235, 220, 0.8)';
        ctx.lineWidth = 2;
        ctx.strokeRect(x, y, barWidth, barHeight);

        // 添加发光效果
        ctx.shadowColor = 'rgba(60, 235, 220, 0.5)';
        ctx.shadowBlur = 10;
        ctx.strokeRect(x, y, barWidth, barHeight);
        ctx.shadowBlur = 0;

        // 绘制数值（在柱子上方）
        if (barHeight > 20) {
            ctx.fillStyle = '#e9f6ff';
            ctx.font = 'bold 14px "Saira Condensed"';
            ctx.textAlign = 'center';
            ctx.textBaseline = 'bottom';
            ctx.fillText(item.count, x + barWidth / 2, y - 5);
        }

        // 绘制X轴标签
        ctx.fillStyle = 'rgba(233, 246, 255, 0.68)';
        ctx.font = '12px "Saira Condensed"';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'top';
        ctx.fillText(item.label, x + barWidth / 2, padding.top + chartHeight + 10);
    });

    // 绘制坐标轴标题
    ctx.fillStyle = 'rgba(233, 246, 255, 0.8)';
    ctx.font = 'bold 13px "Saira Condensed"';

    // Y轴标题
    ctx.save();
    ctx.translate(15, canvas.height / 2);
    ctx.rotate(-Math.PI / 2);
    ctx.textAlign = 'center';
    ctx.fillText('合同个数', 0, 0);
    ctx.restore();

    // X轴标题
    ctx.textAlign = 'center';
    ctx.fillText('金额区间', canvas.width / 2, canvas.height - 10);

    // 添加鼠标悬浮事件
    setupChartHover();
}

// 设置图表悬浮效果
function setupChartHover() {
    if (!chartData) return;

    const canvas = chartData.canvas;
    const container = canvas.parentElement;

    // 创建悬浮提示框
    let tooltip = document.getElementById('chartTooltip');
    if (!tooltip) {
        tooltip = document.createElement('div');
        tooltip.id = 'chartTooltip';
        tooltip.style.cssText = `
            position: absolute;
            display: none;
            background: rgba(9, 28, 52, 0.95);
            border: 2px solid rgba(60, 235, 220, 0.6);
            border-radius: 8px;
            padding: 12px 16px;
            color: #e9f6ff;
            font-size: 13px;
            pointer-events: none;
            z-index: 1000;
            box-shadow: 0 4px 20px rgba(60, 235, 220, 0.3);
            backdrop-filter: blur(10px);
            min-width: 180px;
        `;
        container.appendChild(tooltip);
    }

    // 鼠标移动事件
    canvas.addEventListener('mousemove', function(e) {
        const rect = canvas.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;

        // 检测鼠标是否在某个柱子上
        let hoveredBar = null;
        for (const bar of chartData.bars) {
            if (x >= bar.x && x <= bar.x + bar.width &&
                y >= bar.y && y <= bar.y + bar.height) {
                hoveredBar = bar;
                break;
            }
        }

        if (hoveredBar) {
            // 显示提示框
            const rangeText = hoveredBar.range.max === Infinity
                ? `$${(hoveredBar.range.min / 1000000).toFixed(0)}M+`
                : `$${(hoveredBar.range.min / 1000000).toFixed(0)}M - $${(hoveredBar.range.max / 1000000).toFixed(0)}M`;

            tooltip.innerHTML = `
                <div style="font-weight: bold; color: #3cebdc; margin-bottom: 6px;">
                    ${hoveredBar.label}
                </div>
                <div style="color: rgba(233, 246, 255, 0.8); margin-bottom: 4px;">
                    金额区间: ${rangeText}
                </div>
                <div style="color: #e9f6ff; font-weight: 600;">
                    合同数量: ${hoveredBar.count}
                </div>
            `;
            tooltip.style.display = 'block';

            // 计算提示框位置，确保在容器内
            const containerRect = container.getBoundingClientRect();
            const tooltipWidth = tooltip.offsetWidth;
            const tooltipHeight = tooltip.offsetHeight;

            let tooltipX = e.clientX - containerRect.left + 15;
            let tooltipY = e.clientY - containerRect.top - tooltipHeight - 10;

            // 确保不超出右边界
            if (tooltipX + tooltipWidth > containerRect.width) {
                tooltipX = e.clientX - containerRect.left - tooltipWidth - 15;
            }

            // 确保不超出上边界
            if (tooltipY < 0) {
                tooltipY = e.clientY - containerRect.top + 15;
            }

            // 确保不超出下边界
            if (tooltipY + tooltipHeight > containerRect.height) {
                tooltipY = containerRect.height - tooltipHeight - 10;
            }

            tooltip.style.left = tooltipX + 'px';
            tooltip.style.top = tooltipY + 'px';

            // 改变鼠标样式
            canvas.style.cursor = 'pointer';
        } else {
            // 隐藏提示框
            tooltip.style.display = 'none';
            canvas.style.cursor = 'default';
        }
    });

    // 鼠标离开画布
    canvas.addEventListener('mouseleave', function() {
        tooltip.style.display = 'none';
        canvas.style.cursor = 'default';
    });
}

// 加载合同列表
async function loadContracts() {
    const tbody = document.getElementById('contractsTableBody');
    tbody.innerHTML = '<tr><td colspan="8" class="loading-row">加载中...</td></tr>';

    try {
        const payload = {
            page: currentPage,
            page_size: pageSize,
            ...currentFilters
        };

        const response = await fetch('/api/contracts/search', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        });

        const data = await response.json();

        if (data.success) {
            totalPages = data.total_pages;
            renderContractsTable(data.contracts);
            updatePagination(data.page, data.total_pages, data.total);
        } else {
            tbody.innerHTML = `<tr><td colspan="8" class="loading-row">加载失败: ${data.msg}</td></tr>`;
        }
    } catch (error) {
        console.error('加载合同列表失败:', error);
        tbody.innerHTML = '<tr><td colspan="8" class="loading-row">加载失败</td></tr>';
    }
}

// 渲染合同列表
function renderContractsTable(contracts) {
    const tbody = document.getElementById('contractsTableBody');

    if (!contracts || contracts.length === 0) {
        tbody.innerHTML = '<tr><td colspan="9" class="loading-row">暂无数据</td></tr>';
        return;
    }

    tbody.innerHTML = contracts.map(contract => {
        const riskClass = contract.risk_level ? contract.risk_level.toLowerCase() : 'low';
        const riskLabel = {
            'high': '高风险',
            'medium': '中风险',
            'low': '低风险'
        }[riskClass] || '未知';

        // 格式化金额
        const amount = contract.principal_amount
            ? '$' + (contract.principal_amount / 1000).toFixed(0) + 'K'
            : '-';

        // 格式化利率
        const rate = contract.interest_rate
            ? contract.interest_rate.toFixed(2) + '%'
            : '-';

        return `
            <tr>
                <td>${contract.contract_id || '-'}</td>
                <td>${contract.contract_type || '-'}</td>
                <td>${contract.vessel_name || '-'}</td>
                <td>${contract.vessel_imo || '-'}</td>
                <td>${contract.company_name || '-'}</td>
                <td>${amount}</td>
                <td>${rate}</td>
                <td><span class="risk-badge ${riskClass}">${riskLabel}</span></td>
                <td>
                    <button class="view-btn" onclick="viewContractDetail('${contract.contract_id}')">查看</button>
                </td>
            </tr>
        `;
    }).join('');
}

// 更新分页
function updatePagination(page, total, count) {
    document.getElementById('pageInfo').textContent = `第 ${page} 页 / 共 ${total} 页 (共 ${count} 条)`;
    document.getElementById('prevPage').disabled = page <= 1;
    document.getElementById('nextPage').disabled = page >= total;
}

// 查看合同详情
async function viewContractDetail(contractId) {
    const modal = document.getElementById('contractModal');
    const modalBody = document.getElementById('modalBody');

    modal.classList.add('active');
    modalBody.innerHTML = '<div class="loading">加载中...</div>';

    try {
        const response = await fetch(`/api/contracts/${contractId}`);
        const data = await response.json();

        if (data.success) {
            renderContractDetail(data.contract);
        } else {
            modalBody.innerHTML = `<div class="loading">加载失败: ${data.msg}</div>`;
        }
    } catch (error) {
        console.error('加载合同详情失败:', error);
        modalBody.innerHTML = '<div class="loading">加载失败</div>';
    }
}

// 渲染合同详情
function renderContractDetail(contract) {
    const modalBody = document.getElementById('modalBody');

    const riskClass = contract.risk_level ? contract.risk_level.toLowerCase() : 'low';
    const riskLabel = {
        'high': '高风险',
        'medium': '中风险',
        'low': '低风险'
    }[riskClass] || '未知';

    modalBody.innerHTML = `
        <div class="detail-section">
            <h4>合同信息</h4>
            <div class="detail-grid">
                <div class="detail-item">
                    <div class="detail-label">合同编号</div>
                    <div class="detail-value">${contract.contract_id || '-'}</div>
                </div>
                <div class="detail-item">
                    <div class="detail-label">合同类型</div>
                    <div class="detail-value">${contract.contract_type || '-'}</div>
                </div>
                <div class="detail-item">
                    <div class="detail-label">合同日期</div>
                    <div class="detail-value">${contract.contract_date || '-'}</div>
                </div>
                <div class="detail-item">
                    <div class="detail-label">到期日期</div>
                    <div class="detail-value">${contract.maturity_date || '-'}</div>
                </div>
                <div class="detail-item">
                    <div class="detail-label">风险等级</div>
                    <div class="detail-value"><span class="risk-badge ${riskClass}">${riskLabel}</span></div>
                </div>
            </div>
        </div>

        <div class="detail-section">
            <h4>融资信息</h4>
            <div class="detail-grid">
                <div class="detail-item">
                    <div class="detail-label">本金金额</div>
                    <div class="detail-value">${contract.principal_amount ? '$' + contract.principal_amount.toLocaleString() : '-'}</div>
                </div>
                <div class="detail-item">
                    <div class="detail-label">年利率</div>
                    <div class="detail-value">${contract.interest_rate ? contract.interest_rate + '%' : '-'}</div>
                </div>
            </div>
        </div>

        <div class="detail-section">
            <h4>借款方信息 (Party A - Borrower)</h4>
            <div class="detail-grid">
                <div class="detail-item">
                    <div class="detail-label">企业名称</div>
                    <div class="detail-value">${contract.company_name || '-'}</div>
                </div>
                <div class="detail-item">
                    <div class="detail-label">企业类型</div>
                    <div class="detail-value">${contract.company_type || '-'}</div>
                </div>
                <div class="detail-item">
                    <div class="detail-label">注册国家</div>
                    <div class="detail-value">${contract.registration_country || '-'}</div>
                </div>
                <div class="detail-item">
                    <div class="detail-label">信用评分</div>
                    <div class="detail-value">${contract.credit_score ? contract.credit_score.toFixed(2) : '-'}</div>
                </div>
            </div>
        </div>

        <div class="detail-section">
            <h4>贷款方信息 (Party B - Lender)</h4>
            <div class="detail-grid">
                <div class="detail-item">
                    <div class="detail-label">机构名称</div>
                    <div class="detail-value">${contract.institution_name || '-'}</div>
                </div>
            </div>
        </div>

        <div class="detail-section">
            <h4>抵押物信息 (Collateral - Vessel)</h4>
            <div class="detail-grid">
                <div class="detail-item">
                    <div class="detail-label">IMO编号</div>
                    <div class="detail-value">${contract.vessel_imo || '-'}</div>
                </div>
                <div class="detail-item">
                    <div class="detail-label">船舶名称</div>
                    <div class="detail-value">${contract.vessel_name || '-'}</div>
                </div>
                <div class="detail-item">
                    <div class="detail-label">船舶类型</div>
                    <div class="detail-value">${contract.vessel_type || '-'}</div>
                </div>
                <div class="detail-item">
                    <div class="detail-label">建造年份</div>
                    <div class="detail-value">${contract.build_year || '-'}</div>
                </div>
                <div class="detail-item">
                    <div class="detail-label">船旗国</div>
                    <div class="detail-value">${contract.flag_country || '-'}</div>
                </div>
                <div class="detail-item">
                    <div class="detail-label">资产风险评分</div>
                    <div class="detail-value">${contract.asset_risk_score ? contract.asset_risk_score.toFixed(2) : '-'}</div>
                </div>
            </div>
        </div>

        <div class="detail-section">
            <h4>风险评估</h4>
            <div class="detail-grid">
                <div class="detail-item">
                    <div class="detail-label">风险评分</div>
                    <div class="detail-value">${contract.risk_score !== undefined ? contract.risk_score.toFixed(1) : '-'}</div>
                </div>
                <div class="detail-item">
                    <div class="detail-label">高风险关键词数</div>
                    <div class="detail-value">${contract.high_risk_count || 0}</div>
                </div>
                <div class="detail-item">
                    <div class="detail-label">中风险关键词数</div>
                    <div class="detail-value">${contract.medium_risk_count || 0}</div>
                </div>
                <div class="detail-item">
                    <div class="detail-label">低风险关键词数</div>
                    <div class="detail-value">${contract.low_risk_count || 0}</div>
                </div>
            </div>
        </div>

        ${contract.high_risk_keywords && contract.high_risk_keywords.length > 0 ? `
        <div class="detail-section">
            <h4>高风险关键词</h4>
            <div class="keywords-container">
                ${contract.high_risk_keywords.map(kw => `
                    <div class="keyword-tag">
                        <span>${kw.keyword}</span>
                        <span class="keyword-count">${kw.count}</span>
                    </div>
                `).join('')}
            </div>
        </div>
        ` : ''}

        ${contract.text_preview ? `
        <div class="detail-section">
            <h4>合同预览</h4>
            <div class="detail-item" style="grid-column: 1 / -1;">
                <div class="detail-value" style="white-space: pre-wrap; font-size: 0.9rem; line-height: 1.6;">
                    ${contract.text_preview}
                </div>
            </div>
        </div>
        ` : ''}
    `;
}

// 关闭弹窗
function closeModal() {
    document.getElementById('contractModal').classList.remove('active');
}

// 创建粒子效果
function createParticles() {
    const container = document.getElementById('particles');
    if (!container) return;

    for (let i = 0; i < 30; i++) {
        const particle = document.createElement('div');
        particle.style.cssText = `
            position: absolute;
            width: 2px;
            height: 2px;
            background: rgba(60, 235, 220, 0.6);
            border-radius: 50%;
            left: ${Math.random() * 100}%;
            top: ${Math.random() * 100}%;
            animation: float ${5 + Math.random() * 10}s linear infinite;
            animation-delay: ${Math.random() * 5}s;
        `;
        container.appendChild(particle);
    }
}

// 添加粒子动画样式
const style = document.createElement('style');
style.textContent = `
    @keyframes float {
        0% {
            transform: translateY(0) translateX(0);
            opacity: 0;
        }
        10% {
            opacity: 1;
        }
        90% {
            opacity: 1;
        }
        100% {
            transform: translateY(-100vh) translateX(${Math.random() * 100 - 50}px);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);

// 创建粒子
createParticles();
