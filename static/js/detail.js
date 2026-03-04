// 详情页面逻辑
const Detail = {
    token: localStorage.getItem("silvernav_token") || "",
    type: "",
    currency: localStorage.getItem("silvernav_currency") || "CNY",
    unit: parseInt(localStorage.getItem("silvernav_unit") || "10000"),
};

// 通用饼图渲染函数（参考船舶画像页面）- 升级版：炫彩发光效果
function renderPieChart(container, data, options = {}) {
    if (!container || !data || data.length === 0) {
        container.innerHTML = '<p style="text-align: center; padding: 40px; color: #999;">暂无数据</p>';
        return;
    }

    const {
        labelKey = 'label',
        valueKey = 'value',
        colors = [
            '#3cebdc', '#4fa8ff', '#ffd65c', '#ff9f1c',
            '#ff5a7a', '#7ef7f0', '#ffb703', '#4dd4ac'
        ],
        maxItems = 8,
        showPercentage = true,
        showValue = true,
        formatValue = (v) => v.toLocaleString(),
        enableHover = true  // 新增：是否启用悬浮效果
    } = options;

    // 取前N个数据
    const topData = data.slice(0, maxItems);
    const total = topData.reduce((sum, item) => sum + (item[valueKey] || 0), 0);

    if (total === 0) {
        container.innerHTML = '<p style="text-align: center; padding: 40px; color: #999;">暂无有效数据</p>';
        return;
    }

    // 生成唯一ID用于渐变和滤镜
    const chartId = 'pie-' + Math.random().toString(36).substr(2, 9);

    // 生成饼图SVG
    let currentAngle = 0;
    const radius = 80;
    const centerX = 100;
    const centerY = 100;

    const paths = topData.map((item, index) => {
        const value = item[valueKey] || 0;
        const percentage = value / total;
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
            label: item[labelKey],
            value: value,
            percentage: (percentage * 100).toFixed(1)
        };
    });

    // 生成炫彩渐变和发光滤镜
    const gradients = paths.map((p, i) => `
        <linearGradient id="${chartId}-gradient-${i}" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" style="stop-color:${p.color};stop-opacity:1" />
            <stop offset="100%" style="stop-color:${p.color};stop-opacity:0.6" />
        </linearGradient>
    `).join('');

    const filters = `
        <filter id="${chartId}-glow">
            <feGaussianBlur stdDeviation="3" result="coloredBlur"/>
            <feMerge>
                <feMergeNode in="coloredBlur"/>
                <feMergeNode in="SourceGraphic"/>
            </feMerge>
        </filter>
        <filter id="${chartId}-glow-hover">
            <feGaussianBlur stdDeviation="5" result="coloredBlur"/>
            <feMerge>
                <feMergeNode in="coloredBlur"/>
                <feMergeNode in="SourceGraphic"/>
            </feMerge>
        </filter>
    `;

    // 生成HTML
    const svgPaths = paths.map((p, i) => `
        <path
            d="${p.path}"
            fill="url(#${chartId}-gradient-${i})"
            stroke="${p.color}"
            stroke-width="2"
            class="pie-slice"
            data-label="${p.label}"
            data-value="${formatValue(p.value)}"
            data-percentage="${p.percentage}%"
            style="filter: url(#${chartId}-glow); cursor: pointer; transition: all 0.3s ease;"
            onmouseover="this.style.filter='url(#${chartId}-glow-hover)'; this.style.opacity='1'; this.style.transform='scale(1.05)'; this.style.transformOrigin='${centerX}px ${centerY}px';"
            onmouseout="this.style.filter='url(#${chartId}-glow)'; this.style.opacity='0.9'; this.style.transform='scale(1)';"
        />
    `).join('');

    const legendItems = paths.map(p => {
        let valueText = '';
        if (showValue && showPercentage) {
            valueText = `${formatValue(p.value)} (${p.percentage}%)`;
        } else if (showValue) {
            valueText = formatValue(p.value);
        } else if (showPercentage) {
            valueText = `${p.percentage}%`;
        }

        return `
            <div class="pie-legend-item" style="transition: all 0.3s ease;">
                <div class="pie-legend-color" style="background: ${p.color}; box-shadow: 0 0 10px ${p.color};"></div>
                <span class="pie-legend-label">${p.label}</span>
                <span class="pie-legend-value">${valueText}</span>
            </div>
        `;
    }).join('');

    container.innerHTML = `
        <div class="pie-chart">
            <svg class="pie-svg" viewBox="0 0 200 200" style="filter: drop-shadow(0 0 20px rgba(60, 235, 220, 0.4));">
                <defs>
                    ${gradients}
                    ${filters}
                </defs>
                ${svgPaths}
            </svg>
            <div class="pie-legend">
                ${legendItems}
            </div>
        </div>
        ${enableHover ? `
        <div id="${chartId}-tooltip" class="pie-tooltip" style="
            position: absolute;
            background: linear-gradient(135deg, rgba(10, 20, 35, 0.98) 0%, rgba(15, 30, 50, 0.98) 100%);
            border: 2px solid rgba(60, 235, 220, 0.6);
            border-radius: 10px;
            padding: 12px 18px;
            color: #fff;
            font-size: 14px;
            pointer-events: none;
            opacity: 0;
            display: none;
            transition: opacity 0.2s ease, transform 0.2s ease;
            z-index: 9999;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.6), 0 0 20px rgba(60, 235, 220, 0.4), inset 0 1px 0 rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            min-width: 150px;
            white-space: nowrap;
            transform: scale(0.95);
        "></div>
        ` : ''}
    `;

    // 添加悬浮提示功能（优化版：智能定位，防止遮挡）
    if (enableHover) {
        const tooltip = container.querySelector(`#${chartId}-tooltip`);
        const slices = container.querySelectorAll('.pie-slice');

        slices.forEach(slice => {
            slice.addEventListener('mousemove', (e) => {
                const label = slice.getAttribute('data-label');
                const value = slice.getAttribute('data-value');
                const percentage = slice.getAttribute('data-percentage');

                tooltip.innerHTML = `
                    <div style="font-weight: bold; margin-bottom: 8px; color: #3cebdc; font-size: 15px; text-shadow: 0 0 10px rgba(60, 235, 220, 0.5);">${label}</div>
                    <div style="margin-bottom: 4px; color: #e0e0e0;">
                        <span style="color: #999;">数值：</span>
                        <span style="color: #ffd65c; font-weight: 600;">${value}</span>
                    </div>
                    <div style="color: #e0e0e0;">
                        <span style="color: #999;">占比：</span>
                        <span style="color: #4fa8ff; font-weight: 600;">${percentage}</span>
                    </div>
                `;

                // 显示tooltip以获取其尺寸
                tooltip.style.display = 'block';
                tooltip.style.opacity = '0'; // 先设为0，计算完位置再显示

                // 强制重排以获取准确尺寸
                tooltip.offsetHeight;

                // 获取容器和tooltip的尺寸
                const containerRect = container.getBoundingClientRect();
                const tooltipRect = tooltip.getBoundingClientRect();

                // 计算鼠标相对于容器的位置
                const mouseX = e.clientX - containerRect.left;
                const mouseY = e.clientY - containerRect.top;

                // 默认偏移量
                const offsetX = 15;
                const offsetY = 15;
                const padding = 10; // 距离边缘的最小距离

                // 初始位置：鼠标右下方
                let left = mouseX + offsetX;
                let top = mouseY + offsetY;
                let position = 'bottom-right'; // 记录tooltip位置，用于调整三角形

                // 智能调整：优先级顺序 右下 -> 右上 -> 左下 -> 左上

                // 检查右侧是否溢出
                if (left + tooltipRect.width + padding > containerRect.width) {
                    // 尝试放在左侧
                    left = mouseX - tooltipRect.width - offsetX;
                    position = position.replace('right', 'left');

                    // 如果左侧也溢出，则居中对齐
                    if (left < padding) {
                        left = Math.max(padding, Math.min(
                            containerRect.width - tooltipRect.width - padding,
                            mouseX - tooltipRect.width / 2
                        ));
                    }
                }

                // 检查底部是否溢出
                if (top + tooltipRect.height + padding > containerRect.height) {
                    // 尝试放在上方
                    top = mouseY - tooltipRect.height - offsetY;
                    position = position.replace('bottom', 'top');

                    // 如果上方也溢出，则垂直居中
                    if (top < padding) {
                        top = Math.max(padding, Math.min(
                            containerRect.height - tooltipRect.height - padding,
                            mouseY - tooltipRect.height / 2
                        ));
                    }
                }

                // 确保不超出左边界
                if (left < padding) {
                    left = padding;
                }

                // 确保不超出上边界
                if (top < padding) {
                    top = padding;
                }

                // 应用位置（使用绝对定位，相对于容器）
                tooltip.style.left = left + 'px';
                tooltip.style.top = top + 'px';

                // 根据位置调整三角形指示器（如果需要）
                tooltip.setAttribute('data-position', position);

                // 延迟显示，避免闪烁
                requestAnimationFrame(() => {
                    tooltip.style.opacity = '1';
                    tooltip.style.transform = 'scale(1)';
                });
            });

            slice.addEventListener('mouseleave', () => {
                tooltip.style.opacity = '0';
                tooltip.style.transform = 'scale(0.95)';
                setTimeout(() => {
                    tooltip.style.display = 'none';
                }, 200);
            });
        });
    }
}

// 详情页面配置
const DETAIL_CONFIG = {
    alerts: {
        title: "高风险预警详情",
        subtitle: "高风险资产明细列表",
        icon: "⚠️"
    },
    vessels: {
        title: "船舶资产风险详情",
        subtitle: "船舶风险评分与资产分析",
        icon: "🚢"
    },
    trend: {
        title: "风险趋势分析",
        subtitle: "历史风险数据与预测",
        icon: "📈"
    },
    credit: {
        title: "授信使用明细",
        subtitle: "授信客户与额度分析",
        icon: "💳"
    },
    factors: {
        title: "风险因子拆解",
        subtitle: "SHAP特征贡献分析",
        icon: "🔍"
    },
    distribution: {
        title: "风险等级分布详情",
        subtitle: "企业与船舶风险分布",
        icon: "📉"
    },
    overall: {
        title: "总体风险敞口详情",
        subtitle: "敞口明细与集中度分析",
        icon: "💰"
    },
    npl: {
        title: "不良资产监控详情",
        subtitle: "不良资产分类与趋势分析",
        icon: "📊"
    }
};

function showDetailToast(msg, isError = false) {
    const toast = document.getElementById("detailToast");
    if (!toast) return;
    toast.textContent = msg;
    toast.classList.toggle("error", isError);
    toast.classList.add("show");
    window.clearTimeout(showDetailToast.timer);
    showDetailToast.timer = window.setTimeout(() => {
        toast.classList.remove("show");
    }, 1000);
}

function getUrlParam(name) {
    const params = new URLSearchParams(window.location.search);
    return params.get(name);
}

function updateDetailHeader() {
    const config = DETAIL_CONFIG[Detail.type];
    if (!config) {
        document.getElementById("detailTitle").textContent = "未知详情类型";
        return;
    }

    const h1 = document.querySelector(".top-center h1");
    const subtitle = document.getElementById("detailTitle");

    if (h1) h1.textContent = `${config.icon} ${config.title}`;
    if (subtitle) subtitle.textContent = config.subtitle;
}

function renderEmptyState(message = "暂无数据") {
    return `
        <div class="empty-state">
            <div class="empty-icon">📭</div>
            <div class="empty-message">${message}</div>
            <div class="empty-hint">该功能正在开发中，敬请期待</div>
        </div>
    `;
}

function renderAlertsDetail() {
    return `
        <div class="detail-stats">
            <div class="stat-card">
                <div class="stat-label">高风险资产数</div>
                <div class="stat-value" id="highRiskCount">--</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">高风险敞口</div>
                <div class="stat-value" id="highRiskExposure">--</div>
            </div>
        </div>
        <div class="detail-content-grid">
            <div class="detail-chart-card">
                <h3>风险等级统计</h3>
                <div id="riskLevelChart" class="chart-placeholder">图表加载中...</div>
            </div>
            <div class="detail-chart-card">
                <h3>资产类型分布</h3>
                <div id="assetTypeChart" class="chart-placeholder">图表加载中...</div>
            </div>
        </div>
        <div class="detail-table-container">
            <h3>高风险资产列表</h3>
            <table class="detail-table" id="alertsTable">
                <thead>
                    <tr>
                        <th>序号</th>
                        <th>资产类型</th>
                        <th>名称</th>
                        <th>合同编号</th>
                        <th>敞口金额</th>
                        <th>风险评分</th>
                        <th>风险等级</th>
                        <th>到期日期</th>
                    </tr>
                </thead>
                <tbody id="alertsTableBody">
                    <tr><td colspan="8" style="text-align: center; padding: 40px;">加载中...</td></tr>
                </tbody>
            </table>
        </div>
    `;
}

function renderVesselsDetail() {
    return `
        <div class="detail-stats">
            <div class="stat-card">
                <div class="stat-label">总船舶数</div>
                <div class="stat-value" id="totalVessels">--</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">高风险船舶</div>
                <div class="stat-value" id="highRiskVessels">--</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">平均船龄</div>
                <div class="stat-value" id="avgVesselAge">--</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">平均风险评分</div>
                <div class="stat-value" id="avgRiskScore">--</div>
            </div>
        </div>
        <div class="detail-content-grid">
            <div class="detail-chart-card">
                <h3>船龄分布统计</h3>
                <div id="ageDistributionChart" class="chart-placeholder">图表加载中...</div>
            </div>
            <div class="detail-chart-card">
                <h3>船型分布统计</h3>
                <div id="typeDistributionChart" class="chart-placeholder">图表加载中...</div>
            </div>
        </div>
        <div class="detail-table-container">
            <h3>船舶风险排行榜（Top 20）</h3>
            <table class="detail-table">
                <thead>
                    <tr>
                        <th>排名</th>
                        <th>船舶名称</th>
                        <th>IMO编号</th>
                        <th>船型</th>
                        <th>船龄</th>
                        <th>所属企业</th>
                        <th>风险评分</th>
                        <th>风险等级</th>
                    </tr>
                </thead>
                <tbody id="vesselsTableBody">
                    <tr><td colspan="8" style="text-align: center; padding: 40px;">加载中...</td></tr>
                </tbody>
            </table>
        </div>
    `;
}

function renderNplDetail() {
    return `
        <div class="detail-stats">
            <div class="stat-card">
                <div class="stat-label">不良资产数量</div>
                <div class="stat-value" id="nplCount">--</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">不良资产金额</div>
                <div class="stat-value" id="nplAmount">--</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">不良率</div>
                <div class="stat-value" id="nplRate">--</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">拨备覆盖率</div>
                <div class="stat-value" id="provisionRate">--</div>
            </div>
        </div>
        <div class="detail-content-grid">
            <div class="detail-chart-card">
                <h3>不良资产分类</h3>
                <div id="nplClassificationChart" class="chart-placeholder">图表加载中...</div>
            </div>
            <div class="detail-chart-card">
                <h3>不良资产趋势（近12个月）</h3>
                <div id="nplTrendChart" class="chart-placeholder">图表加载中...</div>
            </div>
        </div>
        <div class="detail-table-container">
            <table class="detail-table">
                <thead>
                    <tr>
                        <th>客户名称</th>
                        <th>合同编号</th>
                        <th>金额</th>
                        <th>逾期天数</th>
                        <th>不良分类</th>
                        <th>认定日期</th>
                    </tr>
                </thead>
                <tbody id="nplTableBody">
                    <tr><td colspan="6" style="text-align: center; padding: 40px;">加载中...</td></tr>
                </tbody>
            </table>
        </div>
    `;
}

function renderTrendDetail() {
    return `
        <div class="detail-filters">
            <div class="filter-group">
                <label>时间范围：</label>
                <select id="trendRangeFilter">
                    <option value="7d">近7天</option>
                    <option value="30d" selected>近30天</option>
                    <option value="90d">近90天</option>
                    <option value="180d">近180天</option>
                    <option value="1y">近1年</option>
                </select>
            </div>
            <button class="filter-btn" id="applyTrendFilter">刷新数据</button>
        </div>
        <div class="detail-content-grid">
            <div class="detail-chart-card full-width">
                <h3>高风险敞口趋势</h3>
                <div id="exposureTrendChart" class="chart-placeholder">图表加载中...</div>
            </div>
            <div class="detail-chart-card full-width">
                <h3>平均风险评分趋势</h3>
                <div id="scoreTrendChart" class="chart-placeholder">图表加载中...</div>
            </div>
            <div class="detail-chart-card">
                <h3>风险等级迁移矩阵</h3>
                <div id="migrationMatrix" class="chart-placeholder">图表加载中...</div>
            </div>
            <div class="detail-chart-card">
                <h3>趋势对比分析</h3>
                <div id="trendComparison" class="chart-placeholder">图表加载中...</div>
            </div>
        </div>
    `;
}

function renderCreditDetail() {
    return `
        <div class="detail-stats">
            <div class="stat-card">
                <div class="stat-label">授信客户数</div>
                <div class="stat-value" id="creditCustomers">--</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">总授信额度</div>
                <div class="stat-value" id="totalCreditLimit">--</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">已用额度</div>
                <div class="stat-value" id="usedCredit">--</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">平均使用率</div>
                <div class="stat-value" id="avgUsageRate">--</div>
            </div>
        </div>
        <div class="detail-content-grid">
            <div class="detail-chart-card">
                <h3>授信使用率分布</h3>
                <div id="usageDistributionChart" class="chart-placeholder">图表加载中...</div>
            </div>
            <div class="detail-chart-card">
                <h3>授信集中度分析</h3>
                <div id="concentrationChart" class="chart-placeholder">图表加载中...</div>
            </div>
        </div>
        <div class="detail-table-container">
            <h3>授信客户排行榜</h3>
            <table class="detail-table">
                <thead>
                    <tr>
                        <th>排名</th>
                        <th>客户名称</th>
                        <th>授信额度</th>
                        <th>已用额度</th>
                        <th>使用率</th>
                        <th>风险等级</th>
                    </tr>
                </thead>
                <tbody id="creditTableBody">
                    <tr><td colspan="6" style="text-align: center; padding: 40px;">加载中...</td></tr>
                </tbody>
            </table>
        </div>
    `;
}

function renderFactorsDetail() {
    return `
        <div class="detail-content-grid">
            <div class="detail-chart-card full-width">
                <h3>风险因子贡献度排名（全部客户聚合）</h3>
                <div id="factorRankingChart" class="chart-placeholder">图表加载中...</div>
            </div>
            <div class="detail-chart-card full-width">
                <h3>SHAP瀑布图（可解释性分析）</h3>
                <div id="shapWaterfallChart" class="chart-placeholder">图表加载中...</div>
            </div>
            <div class="detail-chart-card">
                <h3>因子重要性</h3>
                <div id="factorImportanceChart" class="chart-placeholder">图表加载中...</div>
            </div>
            <div class="detail-chart-card">
                <h3>因子变化趋势（近30天）</h3>
                <div id="factorTrendChart" class="chart-placeholder">图表加载中...</div>
            </div>
        </div>
    `;
}

function renderDistributionDetail() {
    return `
        <div class="detail-content-grid">
            <div class="detail-chart-card">
                <h3>企业风险等级分布</h3>
                <div id="companyDistributionChart" class="chart-placeholder">图表加载中...</div>
            </div>
            <div class="detail-chart-card">
                <h3>船舶风险等级分布</h3>
                <div id="vesselDistributionChart" class="chart-placeholder">图表加载中...</div>
            </div>
            <div class="detail-chart-card">
                <h3>风险等级迁移（本月vs上月）</h3>
                <div id="riskMigrationChart" class="chart-placeholder">图表加载中...</div>
            </div>
            <div class="detail-chart-card">
                <h3>按行业细分统计</h3>
                <div id="industryBreakdownChart" class="chart-placeholder">图表加载中...</div>
            </div>
        </div>
        <div class="detail-info-card">
            <h3>风险等级定义说明</h3>
            <div class="risk-definition">
                <div class="risk-item">
                    <span class="risk-badge high">高风险</span>
                    <span>风险评分 ≥ 70，需重点关注，可能需要增加担保或限制授信</span>
                </div>
                <div class="risk-item">
                    <span class="risk-badge medium">中风险</span>
                    <span>风险评分 40-69，需定期监控，适度控制授信规模</span>
                </div>
                <div class="risk-item">
                    <span class="risk-badge low">低风险</span>
                    <span>风险评分 < 40，信用良好，可正常开展业务</span>
                </div>
            </div>
        </div>
    `;
}

function renderOverallDetail() {
    return `
        <div class="detail-stats">
            <div class="stat-card">
                <div class="stat-label">总敞口</div>
                <div class="stat-value" id="totalExposureDetail">--</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">高风险敞口</div>
                <div class="stat-value" id="highRiskExposureDetail">--</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">敞口集中度</div>
                <div class="stat-value" id="exposureConcentration">--</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">币种数量</div>
                <div class="stat-value" id="currencyCount">--</div>
            </div>
        </div>
        <div class="detail-content-grid">
            <div class="detail-chart-card">
                <h3>币种敞口分布</h3>
                <div id="currencyExposureChart" class="chart-placeholder">图表加载中...</div>
            </div>
            <div class="detail-chart-card">
                <h3>敞口集中度分析（Top10）</h3>
                <div id="exposureConcentrationChart" class="chart-placeholder">图表加载中...</div>
            </div>
            <div class="detail-chart-card full-width">
                <h3>敞口变化趋势（近30天）</h3>
                <div id="exposureChangeChart" class="chart-placeholder">图表加载中...</div>
            </div>
        </div>
        <div class="detail-table-container">
            <h3>高风险敞口明细</h3>
            <table class="detail-table">
                <thead>
                    <tr>
                        <th>客户名称</th>
                        <th>船舶名称</th>
                        <th>敞口金额</th>
                        <th>币种</th>
                        <th>风险等级</th>
                        <th>占比</th>
                    </tr>
                </thead>
                <tbody id="overallTableBody">
                    <tr><td colspan="6" style="text-align: center; padding: 40px;">加载中...</td></tr>
                </tbody>
            </table>
        </div>
    `;
}

function renderDetailContent() {
    const container = document.querySelector(".detail-content");
    if (!container) return;

    let content = "";

    switch (Detail.type) {
        case "alerts":
            content = renderAlertsDetail();
            break;
        case "vessels":
            content = renderVesselsDetail();
            break;
        case "trend":
            content = renderTrendDetail();
            break;
        case "credit":
            content = renderCreditDetail();
            break;
        case "factors":
            content = renderFactorsDetail();
            break;
        case "distribution":
            content = renderDistributionDetail();
            break;
        case "overall":
            content = renderOverallDetail();
            break;
        case "npl":
            content = renderNplDetail();
            break;
        default:
            content = renderEmptyState("未知的详情类型");
    }

    container.innerHTML = `
        <section class="card detail-card">
            ${content}
        </section>
    `;
}

function renderAlertsData(data) {
    const { stats, high_risk_assets, risk_level_stats, asset_type_stats } = data;
    const unit = Detail.unit; // 使用全局单位

    // 1. 更新统计卡片
    const highRiskCount = document.getElementById("highRiskCount");
    const highRiskExposure = document.getElementById("highRiskExposure");

    if (highRiskCount) highRiskCount.textContent = stats.high_risk_count || 0;
    if (highRiskExposure) highRiskExposure.textContent = formatAmount(stats.high_risk_exposure || 0, unit);

    // 2. 渲染风险等级统计图表
    renderRiskLevelChart(risk_level_stats, unit);

    // 3. 渲染资产类型统计图表
    renderAssetTypeChart(asset_type_stats, unit);

    // 4. 渲染高风险资产列表表格
    renderHighRiskAssetsTable(high_risk_assets, unit);
}

function renderRiskLevelChart(stats, unit) {
    const chartContainer = document.getElementById("riskLevelChart");
    if (!chartContainer) return;

    if (!stats || stats.length === 0) {
        chartContainer.innerHTML = '<p style="text-align: center; padding: 40px; color: #999;">暂无数据</p>';
        return;
    }

    const maxAmount = Math.max(...stats.map(s => s.total_amount || 0));
    const chartHTML = stats.map(s => {
        const percentage = maxAmount > 0 ? (s.total_amount / maxAmount) * 100 : 0;
        const levelLabel = s.risk_level === 'high' ? '高风险' : s.risk_level === 'medium' ? '中风险' : '低风险';
        const levelColor = s.risk_level === 'high' ? '#ff5252' : s.risk_level === 'medium' ? '#ffa726' : '#66bb6a';

        return `
            <div style="margin-bottom: 15px;">
                <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                    <span style="color: #fff; font-size: 14px;">${levelLabel}</span>
                    <span style="color: ${levelColor}; font-weight: bold;">${s.count}条 / ${formatAmount(s.total_amount, unit)}</span>
                </div>
                <div style="background: rgba(255,255,255,0.1); height: 20px; border-radius: 10px; overflow: hidden;">
                    <div style="background: ${levelColor}; height: 100%; width: ${percentage}%; transition: width 0.3s;"></div>
                </div>
            </div>
        `;
    }).join('');

    chartContainer.innerHTML = chartHTML;
}

function renderAssetTypeChart(stats, unit) {
    const chartContainer = document.getElementById("assetTypeChart");
    if (!chartContainer) return;

    if (!stats || stats.length === 0) {
        chartContainer.innerHTML = '<p style="text-align: center; padding: 40px; color: #999;">暂无数据</p>';
        return;
    }

    const typeLabels = {
        'loan': '贷款',
        'mortgage': '抵押',
        'leasing': '租赁',
        'guarantee': '担保',
        'factoring': '保理'
    };

    const maxAmount = Math.max(...stats.map(s => s.total_amount || 0));
    const chartHTML = stats.map(s => {
        const percentage = maxAmount > 0 ? (s.total_amount / maxAmount) * 100 : 0;
        const typeLabel = typeLabels[s.asset_type] || s.asset_type;

        return `
            <div style="margin-bottom: 15px;">
                <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                    <span style="color: #fff; font-size: 14px;">${typeLabel}</span>
                    <span style="color: #4fc3f7; font-weight: bold;">${s.count}条 / ${formatAmount(s.total_amount, unit)}</span>
                </div>
                <div style="background: rgba(255,255,255,0.1); height: 20px; border-radius: 10px; overflow: hidden;">
                    <div style="background: linear-gradient(90deg, #4fc3f7, #29b6f6); height: 100%; width: ${percentage}%; transition: width 0.3s;"></div>
                </div>
            </div>
        `;
    }).join('');

    chartContainer.innerHTML = chartHTML;
}

function renderHighRiskAssetsTable(assets, unit) {
    const tableBody = document.getElementById("alertsTableBody");
    if (!tableBody) return;

    if (!assets || assets.length === 0) {
        tableBody.innerHTML = '<tr><td colspan="8" style="text-align: center; padding: 40px;">暂无数据</td></tr>';
        return;
    }

    const typeLabels = {
        'loan': '贷款',
        'mortgage': '抵押',
        'leasing': '租赁',
        'guarantee': '担保',
        'factoring': '保理'
    };

    const rows = assets.map((item, index) => {
        const riskBadgeClass = 'high';
        const riskLabel = '高风险';
        const typeLabel = typeLabels[item.asset_type] || item.asset_type;
        const name = item.company_name || item.vessel_name || '-';

        return `
            <tr>
                <td>${index + 1}</td>
                <td>${typeLabel}</td>
                <td>${name}</td>
                <td>${item.contract_no || '-'}</td>
                <td>${formatAmount(item.outstanding_amount || 0, unit)}</td>
                <td>${(item.risk_score || 0).toFixed(2)}</td>
                <td><span class="risk-badge ${riskBadgeClass}">${riskLabel}</span></td>
                <td>${item.maturity_date || '-'}</td>
            </tr>
        `;
    }).join('');

    tableBody.innerHTML = rows;
}

function renderCreditData(data) {
    const { stats, ranking, usage_distribution, concentration, expiring_soon } = data;
    const unit = Detail.unit; // 使用全局单位

    // 1. 更新统计卡片
    const creditCustomers = document.getElementById("creditCustomers");
    const totalCreditLimit = document.getElementById("totalCreditLimit");
    const usedCredit = document.getElementById("usedCredit");
    const avgUsageRate = document.getElementById("avgUsageRate");

    if (creditCustomers) creditCustomers.textContent = stats.customer_count || 0;
    if (totalCreditLimit) totalCreditLimit.textContent = formatAmount(stats.total_limit || 0, unit);
    if (usedCredit) usedCredit.textContent = formatAmount(stats.used_amount || 0, unit);
    if (avgUsageRate) avgUsageRate.textContent = `${(stats.avg_usage_rate || 0).toFixed(2)}%`;

    // 2. 渲染授信使用率分布图表
    renderUsageDistributionChart(usage_distribution);

    // 3. 渲染授信集中度分析图表
    renderConcentrationChart(concentration);

    // 4. 渲染授信客户排行榜表格
    renderCreditRankingTable(ranking, unit);

    // 5. 渲染授信到期提醒表格（如果有数据）
    if (expiring_soon && expiring_soon.length > 0) {
        renderExpiringTable(expiring_soon, unit);
    }
}

function formatAmount(amount, unit) {
    if (!amount && amount !== 0) return "0";
    // unit可能是数字或字符串
    let divisor = 10000; // 默认万元
    if (typeof unit === 'number') {
        divisor = unit;
    } else if (typeof unit === 'string') {
        if (unit === "万元") divisor = 10000;
        else if (unit === "百万元") divisor = 1000000;
        else if (unit === "千万元") divisor = 10000000;
        else if (unit === "亿元") divisor = 100000000;
    }
    return (amount / divisor).toFixed(2);
}

function renderUsageDistributionChart(distribution) {
    const chartContainer = document.getElementById("usageDistributionChart");
    if (!chartContainer) return;

    if (!distribution || distribution.length === 0) {
        chartContainer.innerHTML = '<p style="text-align: center; padding: 40px; color: #999;">暂无数据</p>';
        return;
    }

    // 使用饼图展示授信使用率分布
    const pieData = distribution.map(d => ({
        label: d.range,
        value: d.count || 0
    }));

    renderPieChart(chartContainer, pieData, {
        labelKey: 'label',
        valueKey: 'value',
        colors: ['#66bb6a', '#4fc3f7', '#ffa726', '#ff5252'],
        formatValue: (v) => `${v}家`
    });
}

function renderConcentrationChart(concentration) {
    const chartContainer = document.getElementById("concentrationChart");
    if (!chartContainer) return;

    if (!concentration) {
        chartContainer.innerHTML = '<p style="text-align: center; padding: 40px; color: #999;">暂无数据</p>';
        return;
    }

    const ratio = concentration.concentration_ratio || 0;
    const top10 = concentration.top10_exposure || 0;
    const total = concentration.total_exposure || 0;
    const others = total - top10;

    // 使用饼图展示集中度
    const pieData = [
        { label: 'Top10客户', value: top10 },
        { label: '其他客户', value: others }
    ];

    renderPieChart(chartContainer, pieData, {
        labelKey: 'label',
        valueKey: 'value',
        colors: ['#4fc3f7', '#7e57c2'],
        formatValue: (v) => `${(v / 100000000).toFixed(2)}亿`,
        showPercentage: true
    });

    // 在饼图下方添加集中度指标
    const statsDiv = document.createElement('div');
    statsDiv.style.cssText = 'text-align: center; margin-top: 20px; padding: 15px; background: rgba(255,255,255,0.05); border-radius: 8px;';
    statsDiv.innerHTML = `
        <div style="font-size: 32px; font-weight: bold; color: #4fc3f7;">${ratio.toFixed(2)}%</div>
        <div style="color: #999; margin-top: 5px;">Top10客户集中度</div>
    `;
    chartContainer.appendChild(statsDiv);
}

function renderCreditRankingTable(ranking, unit) {
    const tableBody = document.getElementById("creditTableBody");
    if (!tableBody) return;

    if (!ranking || ranking.length === 0) {
        tableBody.innerHTML = '<tr><td colspan="6" style="text-align: center; padding: 40px;">暂无数据</td></tr>';
        return;
    }

    const rows = ranking.map((item, index) => {
        const riskBadgeClass = item.risk_level === 'high' ? 'high' : item.risk_level === 'medium' ? 'medium' : 'low';
        const riskLabel = item.risk_level === 'high' ? '高风险' : item.risk_level === 'medium' ? '中风险' : '低风险';

        return `
            <tr>
                <td>${index + 1}</td>
                <td>${item.company_name || '-'}</td>
                <td>${formatAmount(item.credit_limit || 0, unit)}</td>
                <td>${formatAmount(item.used_amount || 0, unit)}</td>
                <td>${(item.usage_rate || 0).toFixed(2)}%</td>
                <td><span class="risk-badge ${riskBadgeClass}">${riskLabel}</span></td>
            </tr>
        `;
    }).join('');

    tableBody.innerHTML = rows;
}

function renderExpiringTable(expiring, unit) {
    // 检查是否有到期提醒容器（可能需要动态添加）
    const container = document.querySelector('.detail-content');
    if (!container) return;

    // 添加到期提醒表格
    const expiringHTML = `
        <div class="detail-table-container" style="margin-top: 30px;">
            <h3 style="color: #fff; margin-bottom: 15px;">⏰ 授信到期提醒（近30天）</h3>
            <table class="detail-table">
                <thead>
                    <tr>
                        <th>客户名称</th>
                        <th>合同编号</th>
                        <th>剩余本金</th>
                        <th>到期日期</th>
                        <th>剩余天数</th>
                        <th>风险等级</th>
                    </tr>
                </thead>
                <tbody>
                    ${expiring.map(item => {
                        const riskBadgeClass = item.risk_level === 'high' ? 'high' : item.risk_level === 'medium' ? 'medium' : 'low';
                        const riskLabel = item.risk_level === 'high' ? '高风险' : item.risk_level === 'medium' ? '中风险' : '低风险';
                        const daysClass = item.days_to_maturity <= 7 ? 'style="color: #ff5252; font-weight: bold;"' : '';

                        return `
                            <tr>
                                <td>${item.company_name || '-'}</td>
                                <td>${item.contract_no || '-'}</td>
                                <td>${formatAmount(item.outstanding_amount || 0, unit)}</td>
                                <td>${item.maturity_date || '-'}</td>
                                <td ${daysClass}>${item.days_to_maturity || 0}天</td>
                                <td><span class="risk-badge ${riskBadgeClass}">${riskLabel}</span></td>
                            </tr>
                        `;
                    }).join('')}
                </tbody>
            </table>
        </div>
    `;

    // 将到期提醒表格添加到页面末尾
    const lastTable = container.querySelector('.detail-table-container:last-child');
    if (lastTable) {
        lastTable.insertAdjacentHTML('afterend', expiringHTML);
    }
}

function renderVesselsData(data) {
    const { stats, vessel_ranking, age_distribution, type_distribution } = data;

    // 1. 更新统计卡片
    const totalVessels = document.getElementById("totalVessels");
    const highRiskVessels = document.getElementById("highRiskVessels");
    const avgVesselAge = document.getElementById("avgVesselAge");
    const avgRiskScore = document.getElementById("avgRiskScore");

    if (totalVessels) totalVessels.textContent = stats.total_vessels || 0;
    if (highRiskVessels) highRiskVessels.textContent = stats.high_risk_vessels || 0;
    if (avgVesselAge) avgVesselAge.textContent = `${stats.avg_vessel_age || 0}年`;
    if (avgRiskScore) avgRiskScore.textContent = (stats.avg_risk_score || 0).toFixed(2);

    // 2. 渲染船龄分布图表
    renderAgeDistributionChart(age_distribution);

    // 3. 渲染船型分布图表
    renderTypeDistributionChart(type_distribution);

    // 4. 渲染船舶风险排行榜表格
    renderVesselRankingTable(vessel_ranking);
}

function renderAgeDistributionChart(distribution) {
    const chartContainer = document.getElementById("ageDistributionChart");
    if (!chartContainer) return;

    if (!distribution || distribution.length === 0) {
        chartContainer.innerHTML = '<p style="text-align: center; padding: 40px; color: #999;">暂无数据</p>';
        return;
    }

    // 使用炫彩饼图展示船龄分布
    const pieData = distribution.map(d => ({
        label: d.range,
        value: d.count || 0
    }));

    renderPieChart(chartContainer, pieData, {
        labelKey: 'label',
        valueKey: 'value',
        colors: ['#4fc3f7', '#29b6f6', '#03a9f4', '#0288d1', '#0277bd', '#01579b'],
        formatValue: (v) => `${v}艘`,
        enableHover: true
    });
}

function renderTypeDistributionChart(distribution) {
    const chartContainer = document.getElementById("typeDistributionChart");
    if (!chartContainer) return;

    if (!distribution || distribution.length === 0) {
        chartContainer.innerHTML = '<p style="text-align: center; padding: 40px; color: #999;">暂无数据</p>';
        return;
    }

    // 使用炫彩饼图展示船型分布
    const pieData = distribution.map(d => ({
        label: d.type || '未知',
        value: d.count || 0
    }));

    renderPieChart(chartContainer, pieData, {
        labelKey: 'label',
        valueKey: 'value',
        colors: ['#7e57c2', '#9575cd', '#b39ddb', '#d1c4e9', '#ff6f00', '#ff8f00', '#ffa000', '#ffb300'],
        formatValue: (v) => `${v}艘`,
        enableHover: true
    });
}

function renderVesselRankingTable(ranking) {
    const tableBody = document.getElementById("vesselsTableBody");
    if (!tableBody) return;

    if (!ranking || ranking.length === 0) {
        tableBody.innerHTML = '<tr><td colspan="8" style="text-align: center; padding: 40px;">暂无数据</td></tr>';
        return;
    }

    const rows = ranking.map((item, index) => {
        const riskBadgeClass = item.risk_level === 'high' ? 'high' : item.risk_level === 'medium' ? 'medium' : 'low';
        const riskLabel = item.risk_level === 'high' ? '高风险' : item.risk_level === 'medium' ? '中风险' : '低风险';

        return `
            <tr>
                <td>${index + 1}</td>
                <td>${item.vessel_name || '-'}</td>
                <td>${item.imo_number || '-'}</td>
                <td>${item.vessel_type || '-'}</td>
                <td>${item.vessel_age || 0}年</td>
                <td>${item.company_name || '-'}</td>
                <td>${(item.risk_score || 0).toFixed(2)}</td>
                <td><span class="risk-badge ${riskBadgeClass}">${riskLabel}</span></td>
            </tr>
        `;
    }).join('');

    tableBody.innerHTML = rows;
}

function renderNplData(data) {
    const { stats, npl_assets, npl_classification, npl_trend } = data;
    const unit = Detail.unit;

    // 1. 更新统计卡片
    const nplCount = document.getElementById("nplCount");
    const nplAmount = document.getElementById("nplAmount");
    const nplRate = document.getElementById("nplRate");
    const provisionRate = document.getElementById("provisionRate");

    if (nplCount) nplCount.textContent = stats.npl_count || 0;
    if (nplAmount) nplAmount.textContent = formatAmount(stats.npl_amount || 0, unit);
    if (nplRate) nplRate.textContent = `${(stats.npl_rate || 0).toFixed(2)}%`;
    if (provisionRate) provisionRate.textContent = `${(stats.provision_rate || 0).toFixed(2)}%`;

    // 2. 渲染不良资产分类图表
    renderNplClassificationChart(npl_classification, unit);

    // 3. 渲染不良资产趋势图表
    renderNplTrendChart(npl_trend, unit);

    // 4. 渲染不良资产明细表格
    renderNplAssetsTable(npl_assets, unit);
}

function renderNplClassificationChart(classification, unit) {
    const chartContainer = document.getElementById("nplClassificationChart");
    if (!chartContainer) return;

    if (!classification || classification.length === 0) {
        chartContainer.innerHTML = '<p style="text-align: center; padding: 40px; color: #999;">暂无数据</p>';
        return;
    }

    // 使用饼图展示不良资产分类
    const pieData = classification.map(c => ({
        label: c.classification,
        value: c.total_amount || 0,
        count: c.count || 0
    }));

    renderPieChart(chartContainer, pieData, {
        labelKey: 'label',
        valueKey: 'value',
        colors: ['#66bb6a', '#ffeb3b', '#ffa726', '#ff5252'], // 关注、次级、可疑、损失
        formatValue: (v) => formatAmount(v, unit)
    });
}

function renderNplTrendChart(trend, unit) {
    const chartContainer = document.getElementById("nplTrendChart");
    if (!chartContainer) return;

    if (!trend || trend.length === 0) {
        chartContainer.innerHTML = '<p style="text-align: center; padding: 40px; color: #999;">暂无数据</p>';
        return;
    }

    // 计算不良率（占比）
    const trendWithRate = trend.map(t => ({
        ...t,
        npl_rate: t.total_amount > 0 ? (t.npl_amount / t.total_amount * 100) : 0
    }));

    const maxRate = Math.max(...trendWithRate.map(t => t.npl_rate));
    const minRate = Math.min(...trendWithRate.map(t => t.npl_rate));
    const rateRange = maxRate - minRate || 1;

    // 生成唯一ID
    const chartId = 'npl-trend-' + Math.random().toString(36).substr(2, 9);

    // SVG尺寸
    const width = 1000;
    const height = 300;
    const padding = { top: 20, right: 50, bottom: 40, left: 60 };
    const chartWidth = width - padding.left - padding.right;
    const chartHeight = height - padding.top - padding.bottom;

    // 计算点的位置
    const points = trendWithRate.map((t, i) => {
        const x = padding.left + (i / (trendWithRate.length - 1)) * chartWidth;
        const y = padding.top + chartHeight - ((t.npl_rate - minRate) / rateRange) * chartHeight;
        return { x, y, data: t };
    });

    // 生成路径
    const linePath = points.map((p, i) =>
        `${i === 0 ? 'M' : 'L'} ${p.x} ${p.y}`
    ).join(' ');

    // 生成渐变填充区域
    const areaPath = `${linePath} L ${points[points.length - 1].x} ${height - padding.bottom} L ${padding.left} ${height - padding.bottom} Z`;

    // Y轴刻度
    const yTicks = 5;
    const yTickValues = Array.from({ length: yTicks }, (_, i) =>
        minRate + (rateRange / (yTicks - 1)) * i
    );

    const chartHTML = `
        <div style="width: 100%; height: 100%; padding: 10px; position: relative;">
            <svg viewBox="0 0 ${width} ${height}" style="width: 100%; height: 100%;" preserveAspectRatio="xMidYMid meet">
                <defs>
                    <!-- 渐变填充 -->
                    <linearGradient id="${chartId}-gradient" x1="0%" y1="0%" x2="0%" y2="100%">
                        <stop offset="0%" style="stop-color:#ff5252;stop-opacity:0.4" />
                        <stop offset="100%" style="stop-color:#ff5252;stop-opacity:0.05" />
                    </linearGradient>

                    <!-- 发光滤镜 -->
                    <filter id="${chartId}-glow">
                        <feGaussianBlur stdDeviation="3" result="coloredBlur"/>
                        <feMerge>
                            <feMergeNode in="coloredBlur"/>
                            <feMergeNode in="SourceGraphic"/>
                        </feMerge>
                    </filter>
                </defs>

                <!-- 背景网格线 -->
                ${yTickValues.map(val => {
                    const y = padding.top + chartHeight - ((val - minRate) / rateRange) * chartHeight;
                    return `<line x1="${padding.left}" y1="${y}" x2="${width - padding.right}" y2="${y}" stroke="rgba(255,255,255,0.1)" stroke-width="1"/>`;
                }).join('')}

                <!-- Y轴 -->
                <line x1="${padding.left}" y1="${padding.top}" x2="${padding.left}" y2="${height - padding.bottom}" stroke="rgba(255,255,255,0.3)" stroke-width="2"/>

                <!-- Y轴刻度和标签 -->
                ${yTickValues.map(val => {
                    const y = padding.top + chartHeight - ((val - minRate) / rateRange) * chartHeight;
                    return `
                        <line x1="${padding.left - 5}" y1="${y}" x2="${padding.left}" y2="${y}" stroke="rgba(255,255,255,0.3)" stroke-width="2"/>
                        <text x="${padding.left - 10}" y="${y + 5}" text-anchor="end" fill="#fff" font-size="12">${val.toFixed(2)}%</text>
                    `;
                }).join('')}

                <!-- X轴 -->
                <line x1="${padding.left}" y1="${height - padding.bottom}" x2="${width - padding.right}" y2="${height - padding.bottom}" stroke="rgba(255,255,255,0.3)" stroke-width="2"/>

                <!-- X轴标签 -->
                ${points.map((p, i) => {
                    // 只显示部分标签，避免拥挤
                    if (i % Math.ceil(points.length / 6) === 0 || i === points.length - 1) {
                        return `<text x="${p.x}" y="${height - padding.bottom + 20}" text-anchor="middle" fill="#fff" font-size="12">${p.data.month}</text>`;
                    }
                    return '';
                }).join('')}

                <!-- 渐变填充区域 -->
                <path d="${areaPath}" fill="url(#${chartId}-gradient)" />

                <!-- 折线 -->
                <path d="${linePath}" fill="none" stroke="#ff5252" stroke-width="3" filter="url(#${chartId}-glow)" />

                <!-- 数据点 -->
                ${points.map((p, i) => `
                    <circle
                        cx="${p.x}"
                        cy="${p.y}"
                        r="5"
                        fill="#ff5252"
                        stroke="#fff"
                        stroke-width="2"
                        class="npl-trend-point"
                        data-month="${p.data.month}"
                        data-npl-amount="${formatAmount(p.data.npl_amount, unit)}"
                        data-total-amount="${formatAmount(p.data.total_amount, unit)}"
                        data-npl-count="${p.data.npl_count}"
                        data-rate="${p.data.npl_rate.toFixed(2)}"
                        style="cursor: pointer; filter: url(#${chartId}-glow); transition: all 0.3s ease;"
                        onmouseover="this.setAttribute('r', '8'); this.style.filter='drop-shadow(0 0 10px #ff5252)';"
                        onmouseout="this.setAttribute('r', '5'); this.style.filter='url(#${chartId}-glow)';"
                    />
                `).join('')}

                <!-- Y轴标题 -->
                <text x="${padding.left - 45}" y="${padding.top + chartHeight / 2}" text-anchor="middle" fill="#fff" font-size="14" transform="rotate(-90 ${padding.left - 45} ${padding.top + chartHeight / 2})">不良率 (%)</text>
            </svg>

            <!-- 悬浮提示框 -->
            <div id="${chartId}-tooltip" style="
                position: absolute;
                background: rgba(10, 20, 35, 0.95);
                border: 1px solid rgba(255, 82, 82, 0.5);
                border-radius: 8px;
                padding: 12px 16px;
                color: #fff;
                font-size: 13px;
                pointer-events: none;
                opacity: 0;
                transition: opacity 0.3s ease;
                z-index: 1000;
                box-shadow: 0 0 20px rgba(255, 82, 82, 0.3);
                min-width: 200px;
            "></div>
        </div>
    `;

    chartContainer.innerHTML = chartHTML;

    // 添加悬浮提示功能
    const tooltip = chartContainer.querySelector(`#${chartId}-tooltip`);
    const dataPoints = chartContainer.querySelectorAll('.npl-trend-point');

    dataPoints.forEach((point, index) => {
        // 使用 mouseenter 和 mousemove 确保第一个点也能触发
        const showTooltip = (e) => {
            const month = point.getAttribute('data-month');
            const nplAmount = point.getAttribute('data-npl-amount');
            const totalAmount = point.getAttribute('data-total-amount');
            const nplCount = point.getAttribute('data-npl-count');
            const rate = point.getAttribute('data-rate');

            tooltip.innerHTML = `
                <div style="font-weight: bold; margin-bottom: 8px; color: #ff5252; font-size: 14px;">${month}</div>
                <div style="margin-bottom: 4px;">不良资产: ${nplAmount}</div>
                <div style="margin-bottom: 4px;">总资产: ${totalAmount}</div>
                <div style="margin-bottom: 4px;">不良笔数: ${nplCount}条</div>
                <div style="margin-top: 8px; padding-top: 8px; border-top: 1px solid rgba(255,255,255,0.2);">
                    <span style="color: #ff5252; font-weight: bold; font-size: 16px;">${rate}%</span>
                    <span style="color: #999; font-size: 12px; margin-left: 5px;">(${nplAmount} / ${totalAmount})</span>
                </div>
            `;
            tooltip.style.opacity = '1';

            // 获取容器和tooltip的尺寸
            const containerRect = chartContainer.getBoundingClientRect();
            const tooltipRect = tooltip.getBoundingClientRect();
            const tooltipWidth = tooltipRect.width || 220;
            const tooltipHeight = tooltipRect.height || 150;

            // 计算鼠标相对于容器的位置
            const mouseX = e.clientX - containerRect.left;
            const mouseY = e.clientY - containerRect.top;

            // 智能定位：判断是否靠近右边界或底部边界
            let left, top;

            // 水平方向：如果鼠标在容器右半部分，tooltip显示在左侧
            if (mouseX > containerRect.width / 2) {
                left = mouseX - tooltipWidth - 15;
            } else {
                left = mouseX + 15;
            }

            // 垂直方向：如果鼠标在容器下半部分，tooltip显示在上方
            if (mouseY > containerRect.height / 2) {
                top = mouseY - tooltipHeight - 10;
            } else {
                top = mouseY + 10;
            }

            // 确保不超出边界
            left = Math.max(10, Math.min(left, containerRect.width - tooltipWidth - 10));
            top = Math.max(10, Math.min(top, containerRect.height - tooltipHeight - 10));

            tooltip.style.left = left + 'px';
            tooltip.style.top = top + 'px';
        };

        // 同时监听 mouseenter 和 mousemove
        point.addEventListener('mouseenter', showTooltip);
        point.addEventListener('mousemove', showTooltip);

        point.addEventListener('mouseleave', () => {
            tooltip.style.opacity = '0';
        });
    });
}

function renderNplAssetsTable(assets, unit) {
    const tableBody = document.getElementById("nplTableBody");
    if (!tableBody) return;

    if (!assets || assets.length === 0) {
        tableBody.innerHTML = '<tr><td colspan="6" style="text-align: center; padding: 40px;">暂无数据</td></tr>';
        return;
    }

    const rows = assets.map((item, index) => {
        const classColor = item.npl_classification === '损失' ? '#ff5252' :
                          item.npl_classification === '可疑' ? '#ffa726' :
                          item.npl_classification === '次级' ? '#ffeb3b' : '#66bb6a';

        return `
            <tr>
                <td>${item.company_name || '-'}</td>
                <td>${item.contract_no || '-'}</td>
                <td>${formatAmount(item.outstanding_amount || 0, unit)}</td>
                <td>${Math.max(0, item.overdue_days || 0)}天</td>
                <td><span style="color: ${classColor}; font-weight: bold;">${item.npl_classification || '-'}</span></td>
                <td>${item.recognition_date || '-'}</td>
            </tr>
        `;
    }).join('');

    tableBody.innerHTML = rows;
}

function renderTrendData(data, timeRange = '30d') {
    const { exposure_trend, score_trend, migration_matrix, trend_comparison } = data;
    const unit = Detail.unit;

    // 1. 渲染高风险敞口趋势图表
    renderExposureTrendChart(exposure_trend, unit, timeRange);

    // 2. 渲染平均风险评分趋势图表
    renderScoreTrendChart(score_trend, timeRange);

    // 3. 渲染风险等级迁移矩阵
    renderMigrationMatrix(migration_matrix);

    // 4. 渲染趋势对比分析
    renderTrendComparison(trend_comparison, unit);
}

function renderExposureTrendChart(trend, unit, timeRange = '30d') {
    const chartContainer = document.getElementById("exposureTrendChart");
    if (!chartContainer) return;

    // 根据时间范围生成对应天数的数据
    let days = 30;
    if (timeRange === '7d') days = 7;
    else if (timeRange === '30d') days = 30;
    else if (timeRange === '90d') days = 90;
    else if (timeRange === '180d') days = 180;
    else if (timeRange === '1y') days = 365;

    // 生成从今天向前推的日期数据
    const trendData = Array.from({length: days}, (_, i) => {
        const date = new Date();
        date.setDate(date.getDate() - (days - 1 - i));

        // 使用trend数据或生成模拟数据
        let exposure;
        if (trend && trend[i]) {
            exposure = trend[i].high_risk_exposure || 0;
        } else {
            // 模拟数据：基础值 + 波动
            const baseExposure = 500000000;
            const variation = Math.sin(i / 5) * 0.1 + (Math.random() - 0.5) * 0.05;
            exposure = baseExposure * (1 + variation);
        }

        return {
            date: `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`,
            high_risk_exposure: exposure
        };
    });

    const maxExposure = Math.max(...trendData.map(t => t.high_risk_exposure || 0));
    const minExposure = Math.min(...trendData.map(t => t.high_risk_exposure || 0));
    const range = maxExposure - minExposure || 1;

    // 计算日期标签显示间隔 - 确保标签不重叠
    const labelInterval = Math.max(1, Math.ceil(days / 10));

    const chartHTML = `
        <div style="width: 100%; height: 100%; padding: 10px; box-sizing: border-box;">
            <svg viewBox="0 0 1000 300" style="width: 100%; height: 100%;" preserveAspectRatio="xMidYMid meet">
                <!-- 背景网格线 -->
                ${[0, 25, 50, 75, 100].map(percent => {
                    const y = 40 + (percent / 100) * 200;
                    return `<line x1="50" y1="${y}" x2="950" y2="${y}" stroke="rgba(255,255,255,0.1)" stroke-width="1"/>`;
                }).join('')}

                <!-- 渐变填充区域 -->
                <defs>
                    <linearGradient id="exposureGradient" x1="0%" y1="0%" x2="0%" y2="100%">
                        <stop offset="0%" style="stop-color:#ff5252;stop-opacity:0.3" />
                        <stop offset="100%" style="stop-color:#ff5252;stop-opacity:0" />
                    </linearGradient>
                </defs>
                <polygon points="50,240 ${trendData.map((t, i) => {
                    const x = 50 + (i / (trendData.length - 1)) * 900;
                    const y = 40 + 200 - ((t.high_risk_exposure - minExposure) / range) * 200;
                    return `${x},${y}`;
                }).join(' ')} 950,240" fill="url(#exposureGradient)"/>

                <!-- 折线 -->
                <polyline points="${trendData.map((t, i) => {
                    const x = 50 + (i / (trendData.length - 1)) * 900;
                    const y = 40 + 200 - ((t.high_risk_exposure - minExposure) / range) * 200;
                    return `${x},${y}`;
                }).join(' ')}" fill="none" stroke="#ff5252" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>

                <!-- 数据点和日期标签 -->
                ${trendData.map((t, i) => {
                    const x = 50 + (i / (trendData.length - 1)) * 900;
                    const y = 40 + 200 - ((t.high_risk_exposure - minExposure) / range) * 200;
                    const showLabel = i % labelInterval === 0 || i === trendData.length - 1;

                    return `
                        <circle cx="${x}" cy="${y}" r="4" fill="#ff5252"/>
                        ${showLabel ? `
                            <line x1="${x}" y1="240" x2="${x}" y2="250" stroke="rgba(255,255,255,0.5)" stroke-width="2"/>
                            <text x="${x}" y="270" text-anchor="middle" fill="#999" font-size="11">${t.date.substring(5)}</text>
                        ` : ''}
                    `;
                }).join('')}
            </svg>

            <!-- 数值说明 -->
            <div style="margin-top: 10px; text-align: center; color: #999; font-size: 13px;">
                <span style="color: #ff5252;">最高: ${formatAmount(maxExposure, unit)}</span>
                <span style="margin: 0 20px;">|</span>
                <span>最低: ${formatAmount(minExposure, unit)}</span>
                <span style="margin: 0 20px;">|</span>
                <span style="color: #4fc3f7;">当前: ${formatAmount(trendData[trendData.length - 1].high_risk_exposure, unit)}</span>
            </div>
        </div>
    `;

    chartContainer.innerHTML = chartHTML;
}

function renderScoreTrendChart(trend, timeRange = '30d') {
    const chartContainer = document.getElementById("scoreTrendChart");
    if (!chartContainer) return;

    // 根据时间范围生成对应天数的数据
    let days = 30;
    if (timeRange === '7d') days = 7;
    else if (timeRange === '30d') days = 30;
    else if (timeRange === '90d') days = 90;
    else if (timeRange === '180d') days = 180;
    else if (timeRange === '1y') days = 365;

    // 生成从今天向前推的日期数据
    const trendData = Array.from({length: days}, (_, i) => {
        const date = new Date();
        date.setDate(date.getDate() - (days - 1 - i));

        // 使用trend数据或生成模拟数据
        let score;
        if (trend && trend[i]) {
            score = trend[i].avg_risk_score || 0;
        } else {
            // 模拟数据：基础值 + 波动
            const baseScore = 55;
            const variation = Math.sin(i / 7) * 5 + (Math.random() - 0.5) * 3;
            score = baseScore + variation;
        }

        return {
            date: `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`,
            avg_risk_score: score
        };
    });

    const maxScore = Math.max(...trendData.map(t => t.avg_risk_score || 0));
    const minScore = Math.min(...trendData.map(t => t.avg_risk_score || 0));
    const range = maxScore - minScore || 1;

    // 计算日期标签显示间隔 - 确保标签不重叠
    const labelInterval = Math.max(1, Math.ceil(days / 10));

    const chartHTML = `
        <div style="width: 100%; height: 100%; padding: 10px; box-sizing: border-box;">
            <svg viewBox="0 0 1000 300" style="width: 100%; height: 100%;" preserveAspectRatio="xMidYMid meet">
                <!-- 背景网格线 -->
                ${[0, 25, 50, 75, 100].map(percent => {
                    const y = 40 + (percent / 100) * 200;
                    return `<line x1="50" y1="${y}" x2="950" y2="${y}" stroke="rgba(255,255,255,0.1)" stroke-width="1"/>`;
                }).join('')}

                <!-- 渐变填充区域 -->
                <defs>
                    <linearGradient id="scoreGradient" x1="0%" y1="0%" x2="0%" y2="100%">
                        <stop offset="0%" style="stop-color:#4fc3f7;stop-opacity:0.3" />
                        <stop offset="100%" style="stop-color:#4fc3f7;stop-opacity:0" />
                    </linearGradient>
                </defs>
                <polygon points="50,240 ${trendData.map((t, i) => {
                    const x = 50 + (i / (trendData.length - 1)) * 900;
                    const y = 40 + 200 - ((t.avg_risk_score - minScore) / range) * 200;
                    return `${x},${y}`;
                }).join(' ')} 950,240" fill="url(#scoreGradient)"/>

                <!-- 折线 -->
                <polyline points="${trendData.map((t, i) => {
                    const x = 50 + (i / (trendData.length - 1)) * 900;
                    const y = 40 + 200 - ((t.avg_risk_score - minScore) / range) * 200;
                    return `${x},${y}`;
                }).join(' ')}" fill="none" stroke="#4fc3f7" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>

                <!-- 数据点和日期标签 -->
                ${trendData.map((t, i) => {
                    const x = 50 + (i / (trendData.length - 1)) * 900;
                    const y = 40 + 200 - ((t.avg_risk_score - minScore) / range) * 200;
                    const showLabel = i % labelInterval === 0 || i === trendData.length - 1;

                    return `
                        <circle cx="${x}" cy="${y}" r="4" fill="#4fc3f7"/>
                        ${showLabel ? `
                            <line x1="${x}" y1="240" x2="${x}" y2="250" stroke="rgba(255,255,255,0.5)" stroke-width="2"/>
                            <text x="${x}" y="270" text-anchor="middle" fill="#999" font-size="11">${t.date.substring(5)}</text>
                        ` : ''}
                    `;
                }).join('')}
            </svg>

            <!-- 数值说明 -->
            <div style="margin-top: 10px; text-align: center; color: #999; font-size: 13px;">
                <span style="color: #ff5252;">最高: ${maxScore.toFixed(2)}</span>
                <span style="margin: 0 20px;">|</span>
                <span>最低: ${minScore.toFixed(2)}</span>
                <span style="margin: 0 20px;">|</span>
                <span style="color: #4fc3f7;">当前: ${trendData[trendData.length - 1].avg_risk_score.toFixed(2)}</span>
            </div>
        </div>
    `;

    chartContainer.innerHTML = chartHTML;
}

function renderMigrationMatrix(matrix) {
    const chartContainer = document.getElementById("migrationMatrix");
    if (!chartContainer) return;

    if (!matrix || matrix.length === 0) {
        chartContainer.innerHTML = '<p style="text-align: center; padding: 40px; color: #999;">暂无数据</p>';
        return;
    }

    const levels = ['high', 'medium', 'low'];
    const levelLabels = { 'high': '高风险', 'medium': '中风险', 'low': '低风险' };

    const matrixData = {};
    matrix.forEach(m => {
        const key = `${m.from_level}_${m.to_level}`;
        matrixData[key] = m.count;
    });

    const maxCount = Math.max(...matrix.map(m => m.count || 0));

    const chartHTML = `
        <div style="padding: 20px;">
            <div style="display: grid; grid-template-columns: 80px repeat(3, 1fr); gap: 5px;">
                <div></div>
                ${levels.map(l => `<div style="text-align: center; color: #999; font-size: 12px;">${levelLabels[l]}</div>`).join('')}
                ${levels.map(from => `
                    <div style="color: #999; font-size: 12px; display: flex; align-items: center;">${levelLabels[from]}</div>
                    ${levels.map(to => {
                        const count = matrixData[`${from}_${to}`] || 0;
                        const opacity = maxCount > 0 ? (count / maxCount) : 0;
                        return `<div style="background: rgba(79, 195, 247, ${opacity}); padding: 10px; text-align: center; border-radius: 4px; color: #fff; font-weight: bold;">${count}</div>`;
                    }).join('')}
                `).join('')}
            </div>
        </div>
    `;

    chartContainer.innerHTML = chartHTML;
}

function renderTrendComparison(comparison, unit) {
    const chartContainer = document.getElementById("trendComparison");
    if (!chartContainer) return;

    chartContainer.innerHTML = `
        <div style="padding: 20px; text-align: center;">
            <div style="margin-bottom: 20px;">
                <div style="font-size: 36px; font-weight: bold; color: #ff5252;">${formatAmount(comparison.current_high_risk || 0, unit)}</div>
                <div style="color: #999; margin-top: 10px;">当前高风险敞口</div>
            </div>
            <div style="display: flex; justify-content: space-around; margin-top: 30px;">
                <div>
                    <div style="color: #4fc3f7; font-size: 24px; font-weight: bold;">${(comparison.current_avg_score || 0).toFixed(2)}</div>
                    <div style="color: #999; margin-top: 5px;">平均风险评分</div>
                </div>
                <div>
                    <div style="color: #ffa726; font-size: 24px; font-weight: bold;">${comparison.current_high_count || 0}</div>
                    <div style="color: #999; margin-top: 5px;">高风险资产数</div>
                </div>
            </div>
        </div>
    `;
}

function renderFactorsData(data) {
    const { factor_ranking } = data;

    // 渲染风险因子排名
    renderFactorRankingChart(factor_ranking);

    // 渲染SHAP瀑布图
    renderShapWaterfallChart(factor_ranking);

    // 渲染因子重要性
    renderFactorImportanceChart(factor_ranking);

    // 渲染因子趋势
    renderFactorTrendChart(factor_ranking);
}

function renderFactorRankingChart(ranking) {
    const chartContainer = document.getElementById("factorRankingChart");
    if (!chartContainer) return;

    if (!ranking || ranking.length === 0) {
        chartContainer.innerHTML = '<p style="text-align: center; padding: 40px; color: #999;">暂无数据</p>';
        return;
    }

    const maxContribution = Math.max(...ranking.map(f => f.contribution || 0));
    const chartHTML = ranking.map(f => {
        const percentage = maxContribution > 0 ? (f.contribution / maxContribution) * 100 : 0;
        return `
            <div style="margin-bottom: 15px;">
                <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                    <span style="color: #fff; font-size: 14px;">⚓ ${f.factor_name}</span>
                    <span style="color: #4fc3f7; font-weight: bold;">${(f.contribution * 100).toFixed(1)}%</span>
                </div>
                <div style="background: rgba(255,255,255,0.1); height: 20px; border-radius: 10px; overflow: hidden;">
                    <div style="background: linear-gradient(90deg, #4fc3f7, #29b6f6); height: 100%; width: ${percentage}%; transition: width 0.3s;"></div>
                </div>
            </div>
        `;
    }).join('');

    chartContainer.innerHTML = chartHTML;
}

function renderShapWaterfallChart(ranking) {
    const chartContainer = document.getElementById("shapWaterfallChart");
    if (!chartContainer) return;

    if (!ranking || ranking.length === 0) {
        chartContainer.innerHTML = '<p style="text-align: center; padding: 40px; color: #999;">暂无数据</p>';
        return;
    }

    // SHAP瀑布图 - 显示因子对风险评分的正负贡献
    let baseScore = 50; // 基准评分
    const chartHTML = `
        <div style="padding: 20px;">
            <div style="display: flex; align-items: center; margin-bottom: 20px;">
                <div style="width: 150px; text-align: right; padding-right: 10px; color: #999;">基准评分</div>
                <div style="flex: 1; height: 30px; background: rgba(79, 195, 247, 0.3); border-radius: 5px; display: flex; align-items: center; padding-left: 10px;">
                    <span style="color: #4fc3f7; font-weight: bold;">${baseScore.toFixed(1)}</span>
                </div>
            </div>
            ${ranking.map((f, index) => {
                const contribution = f.contribution * 100;
                const isPositive = contribution > 0;
                baseScore += contribution;
                return `
                    <div style="display: flex; align-items: center; margin-bottom: 15px;">
                        <div style="width: 150px; text-align: right; padding-right: 10px; color: #fff; font-size: 13px;">🚢 ${f.factor_name}</div>
                        <div style="flex: 1; height: 25px; background: rgba(255,255,255,0.05); border-radius: 5px; position: relative; overflow: hidden;">
                            <div style="position: absolute; left: 50%; width: ${Math.abs(contribution)}%; height: 100%; background: ${isPositive ? 'linear-gradient(90deg, #ff5252, #ff7979)' : 'linear-gradient(90deg, #66bb6a, #81c784)'}; ${isPositive ? 'left: 50%' : 'right: 50%'}; display: flex; align-items: center; justify-content: center;">
                                <span style="color: #fff; font-size: 11px; font-weight: bold;">${isPositive ? '+' : ''}${contribution.toFixed(1)}</span>
                            </div>
                        </div>
                    </div>
                `;
            }).join('')}
            <div style="display: flex; align-items: center; margin-top: 20px; padding-top: 15px; border-top: 1px solid rgba(255,255,255,0.1);">
                <div style="width: 150px; text-align: right; padding-right: 10px; color: #999;">最终评分</div>
                <div style="flex: 1; height: 35px; background: linear-gradient(90deg, #ffa726, #ffb74d); border-radius: 5px; display: flex; align-items: center; padding-left: 10px;">
                    <span style="color: #fff; font-weight: bold; font-size: 16px;">${baseScore.toFixed(1)}</span>
                </div>
            </div>
        </div>
    `;

    chartContainer.innerHTML = chartHTML;
}

function renderFactorImportanceChart(ranking) {
    const chartContainer = document.getElementById("factorImportanceChart");
    if (!chartContainer) return;

    if (!ranking || ranking.length === 0) {
        chartContainer.innerHTML = '<p style="text-align: center; padding: 40px; color: #999;">暂无数据</p>';
        return;
    }

    const maxImportance = Math.max(...ranking.map(f => f.importance || 0));
    const chartHTML = ranking.map(f => {
        const percentage = maxImportance > 0 ? (f.importance / maxImportance) * 100 : 0;
        const color = f.importance > 70 ? '#ff5252' : f.importance > 50 ? '#ffa726' : '#66bb6a';

        return `
            <div style="margin-bottom: 15px;">
                <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                    <span style="color: #fff; font-size: 13px;">⚡ ${f.factor_name}</span>
                    <span style="color: ${color}; font-weight: bold;">${f.importance}</span>
                </div>
                <div style="background: rgba(255,255,255,0.1); height: 18px; border-radius: 9px; overflow: hidden;">
                    <div style="background: ${color}; height: 100%; width: ${percentage}%; transition: width 0.3s;"></div>
                </div>
            </div>
        `;
    }).join('');

    chartContainer.innerHTML = chartHTML;
}

function renderFactorTrendChart(ranking) {
    const chartContainer = document.getElementById("factorTrendChart");
    if (!chartContainer) return;

    if (!ranking || ranking.length === 0) {
        chartContainer.innerHTML = '<p style="text-align: center; padding: 40px; color: #999;">暂无数据</p>';
        return;
    }

    // 模拟30天趋势数据
    const days = 30;
    const chartHTML = `
        <div style="padding: 15px;">
            ${ranking.slice(0, 3).map((f, index) => {
                const color = ['#4fc3f7', '#7e57c2', '#ffa726'][index];
                return `
                    <div style="margin-bottom: 20px;">
                        <div style="color: #fff; font-size: 13px; margin-bottom: 8px;">📊 ${f.factor_name}</div>
                        <div style="display: flex; align-items: flex-end; height: 60px; gap: 2px;">
                            ${Array.from({length: days}, (_, i) => {
                                const value = 30 + Math.random() * 40 + Math.sin(i / 5) * 15;
                                const height = (value / 70) * 100;
                                return `<div style="flex: 1; background: ${color}; height: ${height}%; border-radius: 2px 2px 0 0; opacity: ${0.5 + (i / days) * 0.5};"></div>`;
                            }).join('')}
                        </div>
                    </div>
                `;
            }).join('')}
        </div>
    `;

    chartContainer.innerHTML = chartHTML;
}

function renderDistributionData(data) {
    const { company_distribution, vessel_distribution } = data;

    // 渲染企业风险等级分布
    renderCompanyDistributionChart(company_distribution);

    // 渲染船舶风险等级分布
    renderVesselDistributionChart(vessel_distribution);

    // 渲染风险等级迁移
    renderRiskMigrationChart(company_distribution, vessel_distribution);

    // 渲染行业细分统计
    renderIndustryBreakdownChart();
}

function renderCompanyDistributionChart(distribution) {
    const chartContainer = document.getElementById("companyDistributionChart");
    if (!chartContainer) return;

    if (!distribution || distribution.length === 0) {
        chartContainer.innerHTML = '<p style="text-align: center; padding: 40px; color: #999;">暂无数据</p>';
        return;
    }

    const levelLabels = { 'high': '高风险', 'medium': '中风险', 'low': '低风险' };

    // 使用饼图展示企业风险等级分布
    const pieData = distribution.map(d => ({
        label: levelLabels[d.risk_level] || d.risk_level,
        value: d.count || 0,
        avg_score: d.avg_score || 0
    }));

    renderPieChart(chartContainer, pieData, {
        labelKey: 'label',
        valueKey: 'value',
        colors: ['#66bb6a', '#ffa726', '#ff5252'], // 低、中、高
        formatValue: (v) => `${v}家`
    });
}

function renderVesselDistributionChart(distribution) {
    const chartContainer = document.getElementById("vesselDistributionChart");
    if (!chartContainer) return;

    if (!distribution || distribution.length === 0) {
        chartContainer.innerHTML = '<p style="text-align: center; padding: 40px; color: #999;">暂无数据</p>';
        return;
    }

    const levelLabels = { 'high': '高风险', 'medium': '中风险', 'low': '低风险' };

    // 使用饼图展示船舶风险等级分布
    const pieData = distribution.map(d => ({
        label: levelLabels[d.risk_level] || d.risk_level,
        value: d.count || 0
    }));

    renderPieChart(chartContainer, pieData, {
        labelKey: 'label',
        valueKey: 'value',
        colors: ['#66bb6a', '#ffa726', '#ff5252'], // 低、中、高
        formatValue: (v) => `${v}艘`
    });
}

function renderRiskMigrationChart(companyDist, vesselDist) {
    const chartContainer = document.getElementById("riskMigrationChart");
    if (!chartContainer) return;

    // 模拟风险等级迁移数据
    const migrationData = [
        { from: '高风险', to: '高风险', count: 15, color: '#ff5252' },
        { from: '高风险', to: '中风险', count: 8, color: '#ffa726' },
        { from: '高风险', to: '低风险', count: 2, color: '#66bb6a' },
        { from: '中风险', to: '高风险', count: 5, color: '#ff5252' },
        { from: '中风险', to: '中风险', count: 45, color: '#ffa726' },
        { from: '中风险', to: '低风险', count: 12, color: '#66bb6a' },
        { from: '低风险', to: '高风险', count: 1, color: '#ff5252' },
        { from: '低风险', to: '中风险', count: 8, color: '#ffa726' },
        { from: '低风险', to: '低风险', count: 120, color: '#66bb6a' }
    ];

    const chartHTML = `
        <div style="padding: 20px;">
            <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px;">
                ${migrationData.map(m => {
                    const opacity = Math.min(m.count / 50, 1);
                    return `
                        <div style="background: rgba(79, 195, 247, ${opacity * 0.3}); padding: 15px; border-radius: 8px; border-left: 3px solid ${m.color};">
                            <div style="color: #999; font-size: 11px; margin-bottom: 5px;">${m.from} → ${m.to}</div>
                            <div style="color: ${m.color}; font-size: 20px; font-weight: bold;">${m.count}</div>
                        </div>
                    `;
                }).join('')}
            </div>
        </div>
    `;

    chartContainer.innerHTML = chartHTML;
}

function renderIndustryBreakdownChart() {
    const chartContainer = document.getElementById("industryBreakdownChart");
    if (!chartContainer) return;

    // 模拟行业细分数据
    const industries = [
        { name: '集装箱运输', count: 156, icon: '📦' },
        { name: '散货运输', count: 134, icon: '⚓' },
        { name: '油轮运输', count: 98, icon: '🛢️' },
        { name: '液化气运输', count: 67, icon: '💨' },
        { name: '其他', count: 45, icon: '🚢' }
    ];

    const maxCount = Math.max(...industries.map(i => i.count));
    const chartHTML = industries.map(ind => {
        const percentage = (ind.count / maxCount) * 100;
        return `
            <div style="margin-bottom: 15px;">
                <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                    <span style="color: #fff; font-size: 14px;">${ind.icon} ${ind.name}</span>
                    <span style="color: #7e57c2; font-weight: bold;">${ind.count}家</span>
                </div>
                <div style="background: rgba(255,255,255,0.1); height: 20px; border-radius: 10px; overflow: hidden;">
                    <div style="background: linear-gradient(90deg, #7e57c2, #9575cd); height: 100%; width: ${percentage}%; transition: width 0.3s;"></div>
                </div>
            </div>
        `;
    }).join('');

    chartContainer.innerHTML = chartHTML;
}

function renderOverallData(data) {
    const { stats, currency_exposure, high_risk_detail } = data;
    const unit = Detail.unit;

    // 1. 更新统计卡片
    const totalExposureDetail = document.getElementById("totalExposureDetail");
    const highRiskExposureDetail = document.getElementById("highRiskExposureDetail");
    const exposureConcentration = document.getElementById("exposureConcentration");
    const currencyCount = document.getElementById("currencyCount");

    if (totalExposureDetail) totalExposureDetail.textContent = formatAmount(stats.total_exposure || 0, unit);
    if (highRiskExposureDetail) highRiskExposureDetail.textContent = formatAmount(stats.high_risk_exposure || 0, unit);
    if (exposureConcentration) exposureConcentration.textContent = `${(stats.exposure_concentration || 0).toFixed(2)}%`;
    if (currencyCount) currencyCount.textContent = stats.currency_count || 0;

    // 2. 渲染币种敞口分布
    renderCurrencyExposureChart(currency_exposure, unit);

    // 3. 渲染敞口集中度分析
    renderExposureConcentrationChart(stats, unit);

    // 4. 渲染敞口变化趋势
    renderExposureChangeChart(stats, unit);

    // 5. 渲染高风险敞口明细表格
    renderHighRiskDetailTable(high_risk_detail, unit);
}

function renderCurrencyExposureChart(exposure, unit) {
    const chartContainer = document.getElementById("currencyExposureChart");
    if (!chartContainer) return;

    if (!exposure || exposure.length === 0) {
        chartContainer.innerHTML = '<p style="text-align: center; padding: 40px; color: #999;">暂无数据</p>';
        return;
    }

    // 竖向排列币种
    const maxAmount = Math.max(...exposure.map(e => e.total_amount || 0));
    const chartHTML = exposure.map(e => {
        const percentage = maxAmount > 0 ? (e.total_amount / maxAmount) * 100 : 0;

        return `
            <div style="margin-bottom: 20px;">
                <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                    <span style="color: #fff; font-size: 16px; font-weight: 500;">${e.currency}</span>
                    <span style="color: #4fc3f7; font-weight: bold; font-size: 14px;">${e.count}条 / ${formatAmount(e.total_amount, unit)}</span>
                </div>
                <div style="background: rgba(255,255,255,0.1); height: 24px; border-radius: 12px; overflow: hidden; box-shadow: inset 0 2px 4px rgba(0,0,0,0.3);">
                    <div style="
                        background: linear-gradient(90deg, #4fc3f7, #29b6f6);
                        height: 100%;
                        width: ${percentage}%;
                        transition: width 0.5s ease;
                        box-shadow: 0 0 15px rgba(79, 195, 247, 0.6);
                        position: relative;
                    ">
                        <div style="
                            position: absolute;
                            top: 0;
                            left: 0;
                            right: 0;
                            bottom: 0;
                            background: linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent);
                            animation: shimmer 2s infinite;
                        "></div>
                    </div>
                </div>
            </div>
        `;
    }).join('');

    chartContainer.innerHTML = `
        <div style="padding: 10px;">
            ${chartHTML}
        </div>
        <style>
            @keyframes shimmer {
                0% { transform: translateX(-100%); }
                100% { transform: translateX(100%); }
            }
        </style>
    `;
}

function renderExposureConcentrationChart(stats, unit) {
    const chartContainer = document.getElementById("exposureConcentrationChart");
    if (!chartContainer) return;

    // 模拟Top10客户数据
    const top10Data = [
        { name: '远洋航运集团', exposure: stats.total_exposure * 0.08, icon: '🚢' },
        { name: '中海集装箱', exposure: stats.total_exposure * 0.06, icon: '📦' },
        { name: '招商轮船', exposure: stats.total_exposure * 0.05, icon: '⚓' },
        { name: '中远海运', exposure: stats.total_exposure * 0.04, icon: '🛢️' },
        { name: '长荣海运', exposure: stats.total_exposure * 0.04, icon: '🚢' },
        { name: '马士基航运', exposure: stats.total_exposure * 0.03, icon: '📦' },
        { name: '地中海航运', exposure: stats.total_exposure * 0.03, icon: '⚓' },
        { name: '达飞轮船', exposure: stats.total_exposure * 0.03, icon: '🛢️' },
        { name: '赫伯罗特', exposure: stats.total_exposure * 0.02, icon: '🚢' },
        { name: '阳明海运', exposure: stats.total_exposure * 0.02, icon: '📦' }
    ];

    const maxExposure = Math.max(...top10Data.map(d => d.exposure));

    // 分成两列：1-5 和 6-10
    const leftColumn = top10Data.slice(0, 5);
    const rightColumn = top10Data.slice(5, 10);

    const renderColumn = (data, startIndex) => {
        return data.map((d, index) => {
            const rank = startIndex + index + 1;
            const percentage = (d.exposure / maxExposure) * 100;
            const ratio = (d.exposure / stats.total_exposure * 100).toFixed(2);

            return `
                <div style="margin-bottom: 15px;">
                    <div style="display: flex; justify-content: space-between; margin-bottom: 6px;">
                        <span style="color: #fff; font-size: 13px;">${d.icon} ${rank}. ${d.name}</span>
                        <span style="color: #4fc3f7; font-weight: bold; font-size: 12px;">${formatAmount(d.exposure, unit)} (${ratio}%)</span>
                    </div>
                    <div style="background: rgba(255,255,255,0.1); height: 20px; border-radius: 10px; overflow: hidden;">
                        <div style="background: linear-gradient(90deg, #4fc3f7, #29b6f6); height: 100%; width: ${percentage}%; transition: width 0.3s;"></div>
                    </div>
                </div>
            `;
        }).join('');
    };

    chartContainer.innerHTML = `
        <div style="padding: 10px; display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
            <div>${renderColumn(leftColumn, 0)}</div>
            <div>${renderColumn(rightColumn, 5)}</div>
        </div>
    `;
}

function renderExposureChangeChart(stats, unit) {
    const chartContainer = document.getElementById("exposureChangeChart");
    if (!chartContainer) return;

    // 模拟近30天敞口变化数据
    const days = 30;
    const baseExposure = stats.total_exposure;
    const trendData = Array.from({length: days}, (_, i) => {
        const date = new Date();
        date.setDate(date.getDate() - (days - 1 - i));
        const variation = Math.sin(i / 5) * 0.05 + (Math.random() - 0.5) * 0.02;
        const exposure = baseExposure * (1 + variation);
        return {
            date: `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`,
            exposure: exposure
        };
    });

    const maxExposure = Math.max(...trendData.map(d => d.exposure));
    const minExposure = Math.min(...trendData.map(d => d.exposure));
    const range = maxExposure - minExposure || 1;

    // 计算日期标签显示间隔
    const labelInterval = Math.max(1, Math.ceil(days / 10));

    const chartHTML = `
        <div style="width: 100%; height: 100%; padding: 10px; box-sizing: border-box;">
            <svg viewBox="0 0 1000 300" style="width: 100%; height: 100%;" preserveAspectRatio="xMidYMid meet">
                <!-- 背景网格线 -->
                ${[0, 25, 50, 75, 100].map(percent => {
                    const y = 40 + (percent / 100) * 200;
                    return `<line x1="50" y1="${y}" x2="950" y2="${y}" stroke="rgba(255,255,255,0.1)" stroke-width="1"/>`;
                }).join('')}

                <!-- 渐变填充区域 -->
                <defs>
                    <linearGradient id="exposureChangeGradient" x1="0%" y1="0%" x2="0%" y2="100%">
                        <stop offset="0%" style="stop-color:#4fc3f7;stop-opacity:0.3" />
                        <stop offset="100%" style="stop-color:#4fc3f7;stop-opacity:0" />
                    </linearGradient>
                </defs>
                <polygon points="50,240 ${trendData.map((d, i) => {
                    const x = 50 + (i / (trendData.length - 1)) * 900;
                    const y = 40 + 200 - ((d.exposure - minExposure) / range) * 200;
                    return `${x},${y}`;
                }).join(' ')} 950,240" fill="url(#exposureChangeGradient)"/>

                <!-- 折线 -->
                <polyline points="${trendData.map((d, i) => {
                    const x = 50 + (i / (trendData.length - 1)) * 900;
                    const y = 40 + 200 - ((d.exposure - minExposure) / range) * 200;
                    return `${x},${y}`;
                }).join(' ')}" fill="none" stroke="#4fc3f7" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>

                <!-- 数据点和日期标签 -->
                ${trendData.map((d, i) => {
                    const x = 50 + (i / (trendData.length - 1)) * 900;
                    const y = 40 + 200 - ((d.exposure - minExposure) / range) * 200;
                    const showLabel = i % labelInterval === 0 || i === trendData.length - 1;

                    return `
                        <circle cx="${x}" cy="${y}" r="4" fill="#4fc3f7"/>
                        ${showLabel ? `
                            <line x1="${x}" y1="240" x2="${x}" y2="250" stroke="rgba(255,255,255,0.5)" stroke-width="2"/>
                            <text x="${x}" y="270" text-anchor="middle" fill="#999" font-size="11">${d.date.substring(5)}</text>
                        ` : ''}
                    `;
                }).join('')}
            </svg>

            <!-- 数值说明 -->
            <div style="margin-top: 10px; text-align: center; color: #999; font-size: 13px;">
                <span style="color: #4fc3f7;">当前: ${formatAmount(trendData[trendData.length - 1].exposure, unit)}</span>
                <span style="margin: 0 20px;">|</span>
                <span>最高: ${formatAmount(maxExposure, unit)}</span>
                <span style="margin: 0 20px;">|</span>
                <span>最低: ${formatAmount(minExposure, unit)}</span>
            </div>
        </div>
    `;

    chartContainer.innerHTML = chartHTML;
}

function renderHighRiskDetailTable(detail, unit) {
    const tableBody = document.getElementById("overallTableBody");
    if (!tableBody) return;

    if (!detail || detail.length === 0) {
        tableBody.innerHTML = '<tr><td colspan="6" style="text-align: center; padding: 40px;">暂无数据</td></tr>';
        return;
    }

    const rows = detail.map((item, index) => {
        const riskBadgeClass = 'high';
        const riskLabel = '高风险';

        return `
            <tr>
                <td>${item.company_name || '-'}</td>
                <td>${item.vessel_name || '-'}</td>
                <td>${formatAmount(item.outstanding_amount || 0, unit)}</td>
                <td>${item.currency || '-'}</td>
                <td><span class="risk-badge ${riskBadgeClass}">${riskLabel}</span></td>
                <td>${(item.exposure_ratio || 0).toFixed(2)}%</td>
            </tr>
        `;
    }).join('');

    tableBody.innerHTML = rows;
}

// 生成NPL模拟数据 -- 具体页面已弃用
function generateMockNplData() {
    const unit = Detail.unit;

    // 模拟不良资产数据
    const mockAssets = [
        { company_name: '远洋运输集团', contract_no: 'NPL-2024-001', outstanding_amount: 85000000, overdue_days: 180, npl_classification: '损失', recognition_date: '2024-08-15' },
        { company_name: '中海航运有限公司', contract_no: 'NPL-2024-002', outstanding_amount: 62000000, overdue_days: 150, npl_classification: '可疑', recognition_date: '2024-09-01' },
        { company_name: '招商轮船股份', contract_no: 'NPL-2023-089', outstanding_amount: 48000000, overdue_days: 210, npl_classification: '损失', recognition_date: '2023-12-20' },
        { company_name: '长荣海运', contract_no: 'NPL-2024-003', outstanding_amount: 35000000, overdue_days: 120, npl_classification: '次级', recognition_date: '2024-10-10' },
        { company_name: '马士基航运', contract_no: 'NPL-2024-004', outstanding_amount: 28000000, overdue_days: 95, npl_classification: '关注', recognition_date: '2024-11-05' },
        { company_name: '地中海航运', contract_no: 'NPL-2024-005', outstanding_amount: 22000000, overdue_days: 165, npl_classification: '可疑', recognition_date: '2024-09-20' },
        { company_name: '达飞轮船', contract_no: 'NPL-2023-078', outstanding_amount: 19000000, overdue_days: 240, npl_classification: '损失', recognition_date: '2023-10-15' },
        { company_name: '赫伯罗特', contract_no: 'NPL-2024-006', outstanding_amount: 15000000, overdue_days: 110, npl_classification: '次级', recognition_date: '2024-10-25' }
    ];

    const totalNplAmount = mockAssets.reduce((sum, a) => sum + a.outstanding_amount, 0);
    const totalAmount = totalNplAmount * 5; // 假设不良率为20%

    // 模拟分类统计
    const classifications = [
        { classification: '损失', count: 3, total_amount: 152000000 },
        { classification: '可疑', count: 2, total_amount: 84000000 },
        { classification: '次级', count: 2, total_amount: 63000000 },
        { classification: '关注', count: 1, total_amount: 28000000 }
    ];

    // 模拟12个月趋势
    const trend = [];
    const now = new Date();
    for (let i = 11; i >= 0; i--) {
        const date = new Date(now.getFullYear(), now.getMonth() - i, 1);
        const month = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`;
        const baseCount = 5 + Math.floor(Math.random() * 3);
        const baseAmount = 200000000 + Math.random() * 100000000;
        trend.push({
            month: month,
            npl_count: baseCount,
            npl_amount: baseAmount
        });
    }

    return {
        success: true,
        base_date: now.toISOString().split('T')[0],
        range: '30d',
        currency: Detail.currency,
        stats: {
            npl_count: mockAssets.length,
            npl_amount: totalNplAmount,
            npl_rate: (totalNplAmount / totalAmount * 100).toFixed(2),
            provision_rate: 150.0
        },
        npl_assets: mockAssets,
        npl_classification: classifications,
        npl_trend: trend
    };
}

async function fetchDetailData(timeRange = '30d', customerId = null) {
    if (!Detail.token) {
        showDetailToast("请先登录", true);
        window.location.href = "/";
        return;
    }

    // 对所有详情页类型实现真实API调用
    const supportedTypes = ["credit", "alerts", "vessels", "trend", "factors", "distribution", "overall", "npl"];
    if (supportedTypes.includes(Detail.type)) {
        try {
            const apiEndpoint = `/api/detail/${Detail.type}`;
            const requestBody = {
                currency: Detail.currency,
                range: timeRange
            };

            // 如果是因子页面且指定了客户ID，添加到请求中
            if (Detail.type === 'factors' && customerId) {
                requestBody.customer_id = parseInt(customerId);
                console.log('发送因子请求，客户ID:', customerId, '请求体:', requestBody);
            }

            const response = await fetch(apiEndpoint, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${Detail.token}`
                },
                body: JSON.stringify(requestBody)
            });

            const data = await response.json();
            console.log('收到响应数据:', data);

            if (data.success === false) {
                showDetailToast(data.msg || "数据加载失败", true);
                return;
            }

            // 根据类型渲染数据
            const renderFunctions = {
                "credit": renderCreditData,
                "alerts": renderAlertsData,
                "vessels": renderVesselsData,
                "trend": (data) => renderTrendData(data, timeRange),
                "factors": renderFactorsData,
                "distribution": renderDistributionData,
                "overall": renderOverallData,
                "npl": renderNplData
            };

            if (renderFunctions[Detail.type]) {
                renderFunctions[Detail.type](data);
            }
            showDetailToast("数据加载成功！", false);
        } catch (error) {
            console.error('数据加载错误:', error);
            showDetailToast("数据加载失败: " + error.message, true);
        }
    } else {
        // 其他详情页面暂时显示开发中提示
        showDetailToast("该详情页面正在开发中", false);
    }
}

function initDetailPage() {
    // 获取URL参数
    Detail.type = getUrlParam("type") || "";

    if (!Detail.type) {
        showDetailToast("缺少详情类型参数", true);
        setTimeout(() => {
            window.location.href = "/dashboard";
        }, 2000);
        return;
    }

    // 检查是否为有效的详情类型
    if (!DETAIL_CONFIG[Detail.type]) {
        showDetailToast("无效的详情类型", true);
        setTimeout(() => {
            window.location.href = "/dashboard";
        }, 2000);
        return;
    }

    // 更新页面标题
    updateDetailHeader();

    // 渲染详情内容
    renderDetailContent();

    // 获取详情数据
    fetchDetailData();
}

function bootDetail() {
    initClock();

    // 绑定返回按钮
    const backBtn = document.getElementById("backBtn");
    if (backBtn) {
        backBtn.addEventListener("click", () => {
            window.location.href = "/dashboard";
        });
    }

    // 初始化详情页面
    initDetailPage();

    // 绑定趋势页面的时间范围筛选器
    if (Detail.type === 'trend') {
        const applyTrendFilterBtn = document.getElementById("applyTrendFilter");
        if (applyTrendFilterBtn) {
            applyTrendFilterBtn.addEventListener("click", () => {
                const rangeSelect = document.getElementById("trendRangeFilter");
                const selectedRange = rangeSelect ? rangeSelect.value : '30d';
                console.log('选择的时间范围:', selectedRange);
                fetchDetailData(selectedRange);
            });
        }
    }
}

window.addEventListener("load", () => {
    if (document.body.classList.contains("detail-page")) {
        bootDetail();
    }
});
