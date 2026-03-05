window.Dash = {
    token: localStorage.getItem("silvernav_token") || "",
    baseDate: localStorage.getItem("silvernav_base_date") || new Date().toISOString().split('T')[0],
    range: "today",
    currency: localStorage.getItem("silvernav_currency") || "CNY",
    unit: parseInt(localStorage.getItem("silvernav_unit") || "10000"),
    refreshTimer: null,
};
