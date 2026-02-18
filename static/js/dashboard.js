const Dash = {
    token: localStorage.getItem("silvernav_token") || "",
    baseDate: "",
    range: "today",
    refreshTimer: null,
};

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

function formatCurrency(value) {
    const num = Number(value || 0);
    return num.toLocaleString("zh-CN", { maximumFractionDigits: 2 });
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

function initBaseDate() {
    const input = document.getElementById("baseDate");
    if (!input) return;
    const today = new Date();
    const yyyy = today.getFullYear();
    const mm = String(today.getMonth() + 1).padStart(2, "0");
    const dd = String(today.getDate()).padStart(2, "0");
    const value = `${yyyy}-${mm}-${dd}`;
    input.value = value;
    Dash.baseDate = value;
    input.addEventListener("change", () => {
        Dash.baseDate = input.value || value;
        fetchDashboard();
    });
}

function bindRangeButtons() {
    document.querySelectorAll(".range-btn").forEach((btn) => {
        btn.addEventListener("click", () => {
            document.querySelectorAll(".range-btn").forEach((node) => node.classList.remove("active"));
            btn.classList.add("active");
            Dash.range = btn.dataset.range || "today";
            fetchDashboard();
        });
    });
}

function bindRefresh() {
    const select = document.getElementById("refreshInterval");
    if (!select) return;

    const updateTimer = () => {
        const minutes = Number(select.value || 10);
        if (Dash.refreshTimer) {
            clearInterval(Dash.refreshTimer);
        }
        Dash.refreshTimer = setInterval(fetchDashboard, minutes * 60 * 1000);
    };

    select.addEventListener("change", updateTimer);
    updateTimer();
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

function updateOverdueBars(container, buckets) {
    if (!container) return;
    const rows = [
        { label: "1-30天", value: Number(buckets.overdue_1_30 || 0) },
        { label: "31-90天", value: Number(buckets.overdue_31_90 || 0) },
        { label: ">90天", value: Number(buckets.overdue_90_plus || 0) },
    ];
    const max = Math.max(...rows.map((r) => r.value), 1);
    container.innerHTML = "";
    rows.forEach((row) => {
        const item = document.createElement("div");
        item.className = "bar-row";
        const label = document.createElement("div");
        label.textContent = row.label;
        const track = document.createElement("div");
        track.className = "bar-track";
        const fill = document.createElement("div");
        fill.className = "bar-fill";
        fill.style.width = `${(row.value / max) * 100}%`;
        track.appendChild(fill);
        const value = document.createElement("div");
        value.textContent = formatCurrency(row.value);
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

function updateCreditTop(rows) {
    const container = document.getElementById("creditTopList");
    if (!container) return;
    container.innerHTML = "";
    if (!rows || !rows.length) {
        container.textContent = "暂无数据";
        return;
    }
    rows.forEach((row, idx) => {
        const line = document.createElement("div");
        line.textContent = `${idx + 1}. ${row.company_name || "未知企业"} - ${formatCurrency(row.used_amount)}`;
        container.appendChild(line);
    });
}

function updateFxExposure(rows) {
    const container = document.getElementById("fxExposureList");
    if (!container) return;
    container.innerHTML = "";
    if (!rows || !rows.length) {
        container.textContent = "暂无外币敞口";
        return;
    }
    rows.forEach((row) => {
        const line = document.createElement("div");
        line.textContent = `${row.currency}: ${formatCurrency(row.exposure_amount)}`;
        container.appendChild(line);
    });
}

function updateDashboard(data) {
    const summary = data.summary || {};
    document.getElementById("totalExposure").textContent = formatCurrency(summary.total_exposure);
    document.getElementById("highRiskExposure").textContent = formatCurrency(summary.high_risk_exposure);
    document.getElementById("highRiskRatio").textContent = formatPercent(summary.high_risk_ratio);

    const riskDistribution = summary.risk_distribution || [];
    const totalRisk = riskDistribution.reduce((acc, cur) => acc + Number(cur.exposure_amount || 0), 0) || 1;
    const donutSegments = riskDistribution.map((row) => ({
        value: (Number(row.exposure_amount || 0) / totalRisk) * 360,
        label: row.risk_level,
    }));
    donutGradient(document.getElementById("riskDonut"), donutSegments);
    document.getElementById("riskDonutValue").textContent = formatCurrency(totalRisk);
    updateLegend(
        document.getElementById("riskDistribution"),
        riskDistribution.map((row, idx) => ({
            label: row.risk_level || "-",
            value: formatCurrency(row.exposure_amount),
            color: ["#3cebdc", "#ffd65c", "#ff5a7a", "#4fa8ff"][idx % 4],
        }))
    );

    const alerts = data.alerts || {};
    document.getElementById("highRiskCompanyCount").textContent = alerts.high_risk_company_count || 0;
    document.getElementById("highRiskVesselCount").textContent = alerts.high_risk_vessel_count || 0;
    document.getElementById("highRiskAssetCount").textContent = (alerts.high_risk_assets || []).length;
    document.getElementById("dueSoonAmount").textContent = formatCurrency(alerts.overdue?.due_soon_amount || 0);

    updateList("alertList", alerts.high_risk_assets || [], (row, idx) => {
        const name = row.company_name || row.vessel_name || "未知";
        return `<span>${idx + 1}. ${name}</span><strong>${formatCurrency(row.outstanding_amount)} ${row.currency || ""}</strong>`;
    });

    const npl = data.npl || {};
    const totalAmount = Number(npl.total_amount || 0);
    const nplAmount = Number(npl.npl_amount || 0);
    const nplRate = totalAmount ? nplAmount / totalAmount : 0;
    document.getElementById("nplRate").textContent = formatPercent(nplRate);
    document.getElementById("nplAmount").textContent = `不良金额 ${formatCurrency(nplAmount)}`;

    const overdue = alerts.overdue || {};
    const overdueAmount = Number(overdue.overdue_amount || 0);
    const overdueRate = totalAmount ? overdueAmount / totalAmount : 0;
    document.getElementById("overdueRate").textContent = formatPercent(overdueRate);
    document.getElementById("overdueAmount").textContent = `逾期金额 ${formatCurrency(overdueAmount)}`;

    updateOverdueBars(document.getElementById("overdueBars"), npl.overdue_buckets || {});

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
    document.getElementById("creditUsageValue").textContent = `${formatCurrency(used)} / ${formatCurrency(limit)}`;
    document.getElementById("creditUsageBar").style.width = `${ratio * 100}%`;
    updateCreditTop(credit.top || []);

    updateFactorList(data.risk_factors || []);

    updateTrendChart(
        "fxChart",
        (data.fx?.rates || []).filter((r) => r.base_currency === "USD").map((row) => ({ value: Number(row.rate || 0) })),
        (data.fx?.rates || []).filter((r) => r.base_currency === "EUR").map((row) => ({ value: Number(row.rate || 0) }))
    );

    const fxRates = data.fx?.rates || [];
    const latestUsd = [...fxRates].reverse().find((r) => r.base_currency === "USD");
    const latestEur = [...fxRates].reverse().find((r) => r.base_currency === "EUR");
    const fxCurrent = document.getElementById("fxCurrent");
    if (fxCurrent) {
        fxCurrent.textContent = `USD/CNY ${latestUsd?.rate || "--"} | EUR/CNY ${latestEur?.rate || "--"}`;
    }

    updateFxExposure(data.fx?.exposure || []);
}

async function fetchDashboard() {
    if (!Dash.token) {
        showDashToast("请先登录", true);
        window.location.href = "/";
        return;
    }
    const payload = { base_date: Dash.baseDate, range: Dash.range };
    try {
        const res = await fetch("/api/dashboard", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                Authorization: `Bearer ${Dash.token}`,
            },
            body: JSON.stringify(payload),
        });
        const data = await res.json();
        if (!data.success) {
            showDashToast(data.msg || "数据加载失败", true);
            if (res.status === 401) {
                window.location.href = "/";
            }
            return;
        }
        updateDashboard(data);
    } catch (err) {
        showDashToast("网络异常，稍后重试", true);
    }
}

function bindDrill() {
    document.querySelectorAll("[data-drill]").forEach((card) => {
        card.addEventListener("click", () => {
            const type = card.dataset.drill;
            if (!type) return;
            window.location.href = `/detail?type=${type}`;
        });
    });

    const backBtn = document.getElementById("backBtn");
    if (backBtn) {
        backBtn.addEventListener("click", () => {
            window.location.href = "/dashboard";
        });
    }
}

function bootDashboard() {
    initClock();
    initBaseDate();
    bindRangeButtons();
    bindRefresh();
    bindDrill();
    fetchDashboard();
}

window.addEventListener("load", () => {
    if (document.body.classList.contains("dashboard-body")) {
        bootDashboard();
    }
});
