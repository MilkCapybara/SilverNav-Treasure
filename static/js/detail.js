// 详情页面逻辑
const Detail = {
    token: localStorage.getItem("silvernav_token") || "",
    type: "",
    currency: localStorage.getItem("silvernav_currency") || "CNY",
    unit: parseInt(localStorage.getItem("silvernav_unit") || "10000"),
};

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
    npl: {
        title: "不良资产明细",
        subtitle: "NPL资产分类与统计",
        icon: "📊"
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
    }, 1800);
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
        <div class="detail-filters">
            <div class="filter-group">
                <label>风险等级：</label>
                <select id="riskLevelFilter">
                    <option value="">全部</option>
                    <option value="high">高风险</option>
                    <option value="medium">中风险</option>
                    <option value="low">低风险</option>
                </select>
            </div>
            <div class="filter-group">
                <label>资产类型：</label>
                <select id="assetTypeFilter">
                    <option value="">全部</option>
                    <option value="company">企业</option>
                    <option value="vessel">船舶</option>
                </select>
            </div>
            <div class="filter-group">
                <input type="text" id="searchInput" placeholder="搜索公司名称、船舶名称或合同编号..." />
            </div>
            <button class="filter-btn" id="applyFilter">应用筛选</button>
        </div>
        <div class="detail-table-container">
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
                        <th>操作</th>
                    </tr>
                </thead>
                <tbody id="alertsTableBody">
                    <tr><td colspan="8" style="text-align: center; padding: 40px;">加载中...</td></tr>
                </tbody>
            </table>
        </div>
        <div class="detail-pagination" id="alertsPagination"></div>
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
        <div class="detail-table-container">
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
        <div class="detail-filters">
            <div class="filter-group">
                <label>选择客户：</label>
                <select id="customerSelect">
                    <option value="">全部客户（聚合）</option>
                </select>
            </div>
            <button class="filter-btn" id="applyFactorFilter">查看详情</button>
        </div>
        <div class="detail-content-grid">
            <div class="detail-chart-card full-width">
                <h3>风险因子贡献度排名</h3>
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
        case "npl":
            content = renderNplDetail();
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
        default:
            content = renderEmptyState("未知的详情类型");
    }

    container.innerHTML = `
        <section class="card detail-card">
            ${content}
        </section>
    `;
}

async function fetchDetailData() {
    if (!Detail.token) {
        showDetailToast("请先登录", true);
        window.location.href = "/";
        return;
    }

    // 暂时显示开发中提示
    showDetailToast("该详情页面正在开发中，数据接口尚未实现", false);

    // TODO: 后续实现具体的API调用
    // const response = await fetch(`/api/detail/${Detail.type}`, {
    //     method: "POST",
    //     headers: {
    //         "Content-Type": "application/json",
    //         "Authorization": `Bearer ${Detail.token}`
    //     },
    //     body: JSON.stringify({
    //         currency: Detail.currency,
    //         unit: Detail.unit
    //     })
    // });
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
}

window.addEventListener("load", () => {
    if (document.body.classList.contains("detail-page")) {
        bootDetail();
    }
});
