function formatDateISO(date) {
    const yyyy = date.getFullYear();
    const mm = String(date.getMonth() + 1).padStart(2, "0");
    const dd = String(date.getDate()).padStart(2, "0");
    return `${yyyy}-${mm}-${dd}`;
}

function formatDateDisplay(date) {
    const yyyy = date.getFullYear();
    const mm = String(date.getMonth() + 1).padStart(2, "0");
    const dd = String(date.getDate()).padStart(2, "0");
    return `${yyyy}/${mm}/${dd}`;
}

function initDatePicker() {
    const group = document.getElementById("dateGroup");
    const toggle = document.getElementById("dateToggle");
    const panel = document.getElementById("datePanel");
    const grid = document.getElementById("dateGrid");
    const monthLabel = document.getElementById("monthLabel");
    const dateValue = document.getElementById("dateValue");
    const prevBtn = document.getElementById("prevMonth");
    const nextBtn = document.getElementById("nextMonth");

    if (!group || !toggle || !panel || !grid || !monthLabel || !dateValue || !prevBtn || !nextBtn) return;

    const today = new Date();
    let selected = window.Dash.baseDate ? new Date(window.Dash.baseDate) : today;
    if (Number.isNaN(selected.getTime())) {
        selected = today;
    }
    let view = new Date(selected.getFullYear(), selected.getMonth(), 1);

    const updateSelected = (date) => {
        selected = date;
        const iso = formatDateISO(selected);
        window.Dash.baseDate = iso;
        dateValue.textContent = formatDateDisplay(selected);
        // 保存到localStorage，以便其他页面同步
        localStorage.setItem("silvernav_base_date", iso);
    };

    const render = () => {
        monthLabel.textContent = `${view.getFullYear()}年${view.getMonth() + 1}月`;
        grid.innerHTML = "";

        const firstDay = new Date(view.getFullYear(), view.getMonth(), 1);
        const startWeekday = firstDay.getDay();
        const daysInMonth = new Date(view.getFullYear(), view.getMonth() + 1, 0).getDate();
        const daysInPrev = new Date(view.getFullYear(), view.getMonth(), 0).getDate();

        for (let i = 0; i < 42; i += 1) {
            const dayNumber = i - startWeekday + 1;
            const cellDate = new Date(view.getFullYear(), view.getMonth(), 1);
            let isMuted = false;

            if (dayNumber <= 0) {
                cellDate.setMonth(cellDate.getMonth() - 1);
                cellDate.setDate(daysInPrev + dayNumber);
                isMuted = true;
            } else if (dayNumber > daysInMonth) {
                cellDate.setMonth(cellDate.getMonth() + 1);
                cellDate.setDate(dayNumber - daysInMonth);
                isMuted = true;
            } else {
                cellDate.setDate(dayNumber);
            }

            const btn = document.createElement("button");
            btn.type = "button";
            btn.className = "date-cell";
            btn.textContent = cellDate.getDate();

            if (isMuted) btn.classList.add("muted");
            if (formatDateISO(cellDate) === formatDateISO(today)) btn.classList.add("today");
            if (formatDateISO(cellDate) === formatDateISO(selected)) btn.classList.add("selected");

            btn.addEventListener("click", () => {
                updateSelected(cellDate);
                render();
                panel.classList.remove("show");
                panel.setAttribute("aria-hidden", "true");
                fetchDashboard();
            });

            grid.appendChild(btn);
        }
    };

    updateSelected(selected);
    render();

    toggle.addEventListener("click", (e) => {
        e.stopPropagation();
        panel.classList.toggle("show");
        panel.setAttribute("aria-hidden", panel.classList.contains("show") ? "false" : "true");
    });

    prevBtn.addEventListener("click", (e) => {
        e.stopPropagation();
        view = new Date(view.getFullYear(), view.getMonth() - 1, 1);
        render();
    });

    nextBtn.addEventListener("click", (e) => {
        e.stopPropagation();
        view = new Date(view.getFullYear(), view.getMonth() + 1, 1);
        render();
    });

    document.addEventListener("click", (e) => {
        if (!group.contains(e.target)) {
            panel.classList.remove("show");
            panel.setAttribute("aria-hidden", "true");
        }
    });
}
