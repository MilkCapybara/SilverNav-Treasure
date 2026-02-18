function showDashToast(msg, isError = false) {
    const toast = document.getElementById("dashToast");
    if (!toast) return;
    toast.textContent = msg;
    toast.classList.toggle("error", isError);
    toast.classList.add("show");
    window.clearTimeout(showDashToast.timer);
    showDashToast.timer = window.setTimeout(() => {
        toast.classList.remove("show");
    }, 1800);
}

function getUnitLabel(unit) {
    const labels = {
        10000: "万元",
        1000000: "百万元",
        10000000: "千万元",
        100000000: "亿元"
    };
    return labels[unit] || "万元";
}

function formatCurrency(value, currency = "CNY") {
    const num = Number(value || 0);
    const unit = window.Dash.unit || 10000;
    const scaled = num / unit;
    const unitLabel = getUnitLabel(unit);
    return `${scaled.toLocaleString("zh-CN", { maximumFractionDigits: 2 })} ${unitLabel} ${currency}`;
}

function formatPercent(value) {
    return `${(Number(value || 0) * 100).toFixed(2)}%`;
}

function setClock() {
    const clock = document.getElementById("cnClock");
    if (!clock) return;
    const now = new Date();
    const fmt = new Intl.DateTimeFormat("zh-CN", {
        timeZone: "Asia/Shanghai",
        year: "numeric",
        month: "2-digit",
        day: "2-digit",
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit",
    });
    clock.textContent = fmt.format(now).replaceAll("/", "-");
}

function initClock() {
    setClock();
    setInterval(setClock, 1000);
}

function donutGradient(element, segments) {
    if (!element) return;
    let current = 0;
    const colors = ["#3cebdc", "#ffd65c", "#ff5a7a", "#4fa8ff"];
    const stops = [];
    segments.forEach((seg, idx) => {
        const value = Math.max(0, Number(seg.value || 0));
        const color = colors[idx % colors.length];
        const start = current;
        const end = current + value;
        stops.push(`${color} ${start}deg ${end}deg`);
        current = end;
    });
    if (!stops.length || current <= 0) {
        element.style.background = "conic-gradient(#3cebdc 0deg, rgba(255,255,255,0.08) 0deg)";
        return;
    }
    element.style.background = `conic-gradient(${stops.join(",")})`;
}

function updateLegend(container, items) {
    if (!container) return;
    container.innerHTML = "";
    items.forEach((item) => {
        const row = document.createElement("div");
        row.className = "legend-item";
        const left = document.createElement("span");
        const dot = document.createElement("i");
        dot.className = "legend-dot";
        dot.style.background = item.color;
        left.appendChild(dot);
        left.appendChild(document.createTextNode(item.label));
        const right = document.createElement("strong");
        right.textContent = item.value;
        row.appendChild(left);
        row.appendChild(right);
        container.appendChild(row);
    });
}

function updateCurrencyBars(container, distributions, currency) {
    if (!container) return;
    const rows = distributions || [];
    if (!rows.length) {
        container.innerHTML = '<div style="text-align: center; color: var(--text-muted); padding: 20px;">暂无币种分布数据</div>';
        return;
    }
    const max = Math.max(...rows.map((r) => Number(r.amount || 0)), 1);
    container.innerHTML = "";
    rows.forEach((row) => {
        const item = document.createElement("div");
        item.className = "bar-row";
        const label = document.createElement("div");
        label.textContent = row.currency || "未知";
        const track = document.createElement("div");
        track.className = "bar-track";
        const fill = document.createElement("div");
        fill.className = "bar-fill";
        fill.style.width = `${(Number(row.amount || 0) / max) * 100}%`;
        track.appendChild(fill);
        const value = document.createElement("div");
        value.textContent = formatCurrency(row.amount, row.currency);
        item.appendChild(label);
        item.appendChild(track);
        item.appendChild(value);
        container.appendChild(item);
    });
}

function buildLinePath(values, width, height) {
    if (!values.length) return "";
    const max = Math.max(...values.map((v) => v.value));
    const min = Math.min(...values.map((v) => v.value));
    const range = max - min || 1;
    return values
        .map((v, idx) => {
            const x = (idx / (values.length - 1 || 1)) * width;
            const y = height - ((v.value - min) / range) * (height - 12) - 6;
            return `${idx === 0 ? "M" : "L"}${x.toFixed(2)} ${y.toFixed(2)}`;
        })
        .join(" ");
}

function updateTrendChart(containerId, exposure, score) {
    const container = document.getElementById(containerId);
    if (!container) return;
    const pathExposure = container.querySelector(".line.exposure");
    const pathScore = container.querySelector(".line.score");
    const empty = container.querySelector(".chart-empty");
    if (!exposure.length && !score.length) {
        empty.style.opacity = 1;
        pathExposure.setAttribute("d", "");
        pathScore.setAttribute("d", "");
        return;
    }
    empty.style.opacity = 0;
    const width = container.clientWidth;
    const height = container.clientHeight;
    const exposurePath = buildLinePath(exposure, width, height);
    const scorePath = buildLinePath(score, width, height);
    pathExposure.setAttribute("d", exposurePath);
    pathScore.setAttribute("d", scorePath);
}

function updateList(containerId, rows, formatter) {
    const container = document.getElementById(containerId);
    if (!container) return;
    container.innerHTML = "";
    if (!rows || !rows.length) {
        const empty = document.createElement("div");
        empty.className = "list-item";
        empty.textContent = "暂无数据";
        container.appendChild(empty);
        return;
    }
    rows.forEach((row, idx) => {
        const item = document.createElement("div");
        item.className = "list-item";
        item.innerHTML = formatter(row, idx);
        container.appendChild(item);
    });
}

function updateFactorList(rows) {
    const container = document.getElementById("riskFactorList");
    if (!container) return;
    container.innerHTML = "";
    if (!rows || !rows.length) {
        container.textContent = "暂无因子数据";
        return;
    }
    const max = Math.max(...rows.map((r) => Math.abs(Number(r.total_contribution || 0))), 1);
    rows.forEach((row) => {
        const item = document.createElement("div");
        item.className = "factor-item";
        const top = document.createElement("div");
        top.className = "factor-row";
        top.innerHTML = `<span>${row.factor_name}</span><strong>${Number(row.total_contribution).toFixed(2)}</strong>`;
        const bar = document.createElement("div");
        bar.className = "factor-bar";
        const fill = document.createElement("span");
        fill.style.width = `${(Math.abs(Number(row.total_contribution || 0)) / max) * 100}%`;
        bar.appendChild(fill);
        item.appendChild(top);
        item.appendChild(bar);
        container.appendChild(item);
    });
}

function updateCreditTop(rows, currency) {
    const container = document.getElementById("creditTopList");
    if (!container) return;
    container.innerHTML = "";
    if (!rows || !rows.length) {
        container.textContent = "暂无数据";
        return;
    }
    rows.forEach((row, idx) => {
        const line = document.createElement("div");
        line.textContent = `${idx + 1}. ${row.company_name || "未知企业"} - ${formatCurrency(row.used_amount, currency)}`;
        container.appendChild(line);
    });
}


function updateDashboard(data) {
    const summary = data.summary || {};
    const currency = data.currency || window.Dash.currency || "CNY";
    window.Dash.currency = currency;
    localStorage.setItem("silvernav_currency", currency);
    const currencyTag = document.getElementById("currencyTag");
    if (currencyTag) currencyTag.textContent = currency;
    const exposureCurrency = document.getElementById("exposureCurrency");
    if (exposureCurrency) exposureCurrency.textContent = currency;

    document.getElementById("totalExposure").textContent = formatCurrency(summary.total_exposure, currency);
    document.getElementById("highRiskExposure").textContent = formatCurrency(summary.high_risk_exposure, currency);
    document.getElementById("highRiskRatio").textContent = formatPercent(summary.high_risk_ratio);

    const riskDistribution = summary.risk_distribution || [];
    const totalRisk = riskDistribution.reduce((acc, cur) => acc + Number(cur.exposure_amount || 0), 0) || 1;
    const donutSegments = riskDistribution.map((row) => ({
        value: (Number(row.exposure_amount || 0) / totalRisk) * 360,
        label: row.risk_level,
    }));
    donutGradient(document.getElementById("riskDonut"), donutSegments);
    document.getElementById("riskDonutValue").textContent = formatCurrency(totalRisk, currency);
    updateLegend(
        document.getElementById("riskDistribution"),
        riskDistribution.map((row, idx) => ({
            label: row.risk_level || "-",
            value: formatCurrency(row.exposure_amount, currency),
            color: ["#3cebdc", "#ffd65c", "#ff5a7a", "#4fa8ff"][idx % 4],
        }))
    );

    const alerts = data.alerts || {};
    document.getElementById("highRiskCompanyCount").textContent = alerts.high_risk_company_count || 0;
    document.getElementById("highRiskVesselCount").textContent = alerts.high_risk_vessel_count || 0;
    document.getElementById("highRiskAssetCount").textContent = (alerts.high_risk_assets || []).length;
    document.getElementById("totalAssetCount").textContent = alerts.total_asset_count || 0;

    updateList("alertList", alerts.high_risk_assets || [], (row, idx) => {
        const name = row.company_name || row.vessel_name || "未知";
        return `<span>${idx + 1}. ${name}</span><strong>${formatCurrency(row.outstanding_amount, row.currency || currency)}</strong>`;
    });

    const npl = data.npl || {};
    const totalAmount = Number(npl.total_amount || 0);
    const nplAmount = Number(npl.npl_amount || 0);
    const nplRate = totalAmount ? nplAmount / totalAmount : 0;
    document.getElementById("nplRate").textContent = formatPercent(nplRate);
    document.getElementById("nplAmount").textContent = `不良金额 ${formatCurrency(nplAmount, currency)}`;

    const totalAssetAmountEl = document.getElementById("totalAssetAmount");
    if (totalAssetAmountEl) {
        totalAssetAmountEl.textContent = formatCurrency(totalAmount, currency);
    }

    updateCurrencyBars(document.getElementById("assetCurrencyBars"), npl.currency_distribution || [], currency);

    const company = data.risk_levels?.company || [];
    const vessel = data.risk_levels?.vessel || [];

    const companyTotal = company.reduce((acc, cur) => acc + Number(cur.count || 0), 0) || 1;
    donutGradient(
        document.getElementById("companyDonut"),
        company.map((row) => ({ value: (Number(row.count || 0) / companyTotal) * 360, label: row.risk_level }))
    );
    document.getElementById("companyDonutValue").textContent = companyTotal;
    updateLegend(
        document.getElementById("companyLegend"),
        company.map((row, idx) => ({
            label: row.risk_level || "-",
            value: row.count,
            color: ["#4fa8ff", "#ffd65c", "#ff5a7a"][idx % 3],
        }))
    );

    const vesselTotal = vessel.reduce((acc, cur) => acc + Number(cur.count || 0), 0) || 1;
    donutGradient(
        document.getElementById("vesselDonut"),
        vessel.map((row) => ({ value: (Number(row.count || 0) / vesselTotal) * 360, label: row.risk_level }))
    );
    document.getElementById("vesselDonutValue").textContent = vesselTotal;
    updateLegend(
        document.getElementById("vesselLegend"),
        vessel.map((row, idx) => ({
            label: row.risk_level || "-",
            value: row.count,
            color: ["#3cebdc", "#ffd65c", "#ff5a7a"][idx % 3],
        }))
    );

    updateTrendChart(
        "riskTrendChart",
        (data.trend?.high_risk_exposure || []).map((row) => ({ value: Number(row.high_risk_exposure || 0) })),
        (data.trend?.avg_risk_score || []).map((row) => ({ value: Number(row.avg_risk_score || 0) }))
    );

    updateList("vesselTopList", data.vessel_top || [], (row, idx) => {
        return `<span>${idx + 1}. ${row.vessel_name || "未知船舶"}</span><strong>${Number(row.risk_score || 0).toFixed(2)}</strong>`;
    });

    const credit = data.credit || {};
    const used = Number(credit.usage?.used_total || 0);
    const limit = Number(credit.usage?.limit_total || 0);
    const ratio = limit ? Math.min(used / limit, 1) : 0;
    document.getElementById("creditUsageValue").textContent = `${formatCurrency(used, currency)} / ${formatCurrency(limit, currency)}`;
    document.getElementById("creditUsageBar").style.width = `${ratio * 100}%`;
    updateCreditTop(credit.top || [], currency);

    updateFactorList(data.risk_factors || []);
}
