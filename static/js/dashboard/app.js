function bindRangeButtons() {
    document.querySelectorAll(".range-btn").forEach((btn) => {
        btn.addEventListener("click", () => {
            document.querySelectorAll(".range-btn").forEach((node) => node.classList.remove("active"));
            btn.classList.add("active");
            window.Dash.range = btn.dataset.range || "today";
            fetchDashboard();
        });
    });
}

function bindRefresh() {
    const select = document.getElementById("refreshInterval");
    if (!select) return;

    const updateTimer = () => {
        const minutes = Number(select.value || 10);
        if (window.Dash.refreshTimer) {
            clearInterval(window.Dash.refreshTimer);
        }
        window.Dash.refreshTimer = setInterval(fetchDashboard, minutes * 60 * 1000);
    };

    select.addEventListener("change", updateTimer);
    updateTimer();
}

function bindCurrencySelect() {
    const btn = document.getElementById("currencyBtn");
    const options = document.getElementById("currencyOptions");
    if (!btn || !options) return;

    const close = () => options.classList.remove("show");
    const toggle = () => options.classList.toggle("show");

    options.querySelectorAll("button").forEach((node) => {
        if (node.dataset.currency === window.Dash.currency) {
            node.classList.add("active");
        }
    });
    const currencyTag = document.getElementById("currencyTag");
    const exposureCurrency = document.getElementById("exposureCurrency");
    if (currencyTag) currencyTag.textContent = window.Dash.currency;
    if (exposureCurrency) exposureCurrency.textContent = window.Dash.currency;

    btn.addEventListener("click", (e) => {
        e.stopPropagation();
        toggle();
    });

    options.querySelectorAll("button").forEach((opt) => {
        opt.addEventListener("click", () => {
            options.querySelectorAll("button").forEach((node) => node.classList.remove("active"));
            opt.classList.add("active");
            window.Dash.currency = opt.dataset.currency || "CNY";
            localStorage.setItem("silvernav_currency", window.Dash.currency);
            const currencyTag = document.getElementById("currencyTag");
            const exposureCurrency = document.getElementById("exposureCurrency");
            if (currencyTag) currencyTag.textContent = window.Dash.currency;
            if (exposureCurrency) exposureCurrency.textContent = window.Dash.currency;
            close();
            fetchDashboard();
        });
    });

    document.addEventListener("click", close);
}

function bindUnitSelect() {
    const btn = document.getElementById("unitBtn");
    const options = document.getElementById("unitOptions");
    if (!btn || !options) return;

    const close = () => options.classList.remove("show");
    const toggle = () => options.classList.toggle("show");

    options.querySelectorAll("button").forEach((node) => {
        if (parseInt(node.dataset.unit) === window.Dash.unit) {
            node.classList.add("active");
        }
    });
    const unitTag = document.getElementById("unitTag");
    if (unitTag) unitTag.textContent = getUnitLabel(window.Dash.unit);

    btn.addEventListener("click", (e) => {
        e.stopPropagation();
        toggle();
    });

    options.querySelectorAll("button").forEach((opt) => {
        opt.addEventListener("click", () => {
            options.querySelectorAll("button").forEach((node) => node.classList.remove("active"));
            opt.classList.add("active");
            window.Dash.unit = parseInt(opt.dataset.unit) || 10000;
            localStorage.setItem("silvernav_unit", window.Dash.unit.toString());
            const unitTag = document.getElementById("unitTag");
            if (unitTag) unitTag.textContent = getUnitLabel(window.Dash.unit);
            close();
            fetchDashboard();
        });
    });

    document.addEventListener("click", close);
}

function bindLogout() {
    const logoutBtn = document.getElementById("logoutBtn");
    if (!logoutBtn) return;

    logoutBtn.addEventListener("click", () => {
        localStorage.removeItem("silvernav_token");
        localStorage.removeItem("silvernav_currency");
        localStorage.removeItem("silvernav_unit");
        window.location.href = "/";
    });
}

async function fetchDashboard() {
    if (!window.Dash.token) {
        showDashToast("请先登录", true);
        window.location.href = "/";
        return;
    }
    const payload = {
        base_date: window.Dash.baseDate,
        range: window.Dash.range,
        currency: window.Dash.currency,
    };
    const controller = new AbortController();
    const timeoutId = window.setTimeout(() => controller.abort(), 35000);
    try {
        const res = await fetch("/api/dashboard", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                Authorization: `Bearer ${window.Dash.token}`,
            },
            body: JSON.stringify(payload),
            signal: controller.signal,
        });
        const data = await res.json();
        if (!data.success) {
            showDashToast(data.msg || data.detail || "数据加载失败", true);
            console.error("Dashboard API error:", data);
            if (res.status === 401) {
                window.location.href = "/";
            }
            return;
        }
        updateDashboard(data);
    } catch (err) {
        if (err.name === "AbortError") {
            showDashToast("数据请求超时，请稍后重试", true);
        } else {
            showDashToast("网络异常，稍后重试", true);
        }
        console.error("Dashboard fetch error:", err);
    } finally {
        window.clearTimeout(timeoutId);
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
    bindDrill();

    const hasDashboard = Boolean(document.getElementById("totalExposure"));
    if (!hasDashboard) return;

    initDatePicker();
    bindRangeButtons();
    bindRefresh();
    bindCurrencySelect();
    bindUnitSelect();
    bindLogout();
    fetchDashboard();
}

window.addEventListener("load", () => {
    if (document.body.classList.contains("dashboard-body")) {
        bootDashboard();
    }
});
