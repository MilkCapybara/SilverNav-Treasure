window.Dash = {
    token: localStorage.getItem("silvernav_token") || "",
    baseDate: "",
    range: "today",
    currency: localStorage.getItem("silvernav_currency") || "CNY",
    unit: parseInt(localStorage.getItem("silvernav_unit") || "10000"),
    refreshTimer: null,
};
