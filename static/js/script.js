const state = {
    meteorCanvas: null,
    meteorCtx: null,
    gridCanvas: null,
    gridCtx: null,
    meteors: [],
    stars: [],
    constellations: [],
    fireworks: [],
    shippingLanes: [],
    seaBeacons: [],
    portContainers: [],
    portCranes: [],
    portShuttles: [],
    dockedVessels: [],
    waterScans: [],
    gridRotationDeg: 0,
    animId: 0,
    transitioning: false,
    stopSpawn: false,
    stopStartedAt: 0,
    cardShown: false,
    mobile: window.matchMedia("(max-width: 768px)").matches,
    nextConstellationAt: 0,
    nextFireworkAt: 0,
};

const CONFIG = {
    meteorCountDesktop: 45,
    meteorCountMobile: 20,
    speedMin: 2.5,
    speedMax: 6.0,
    lengthMin: 12,
    lengthMax: 20,
    angleMin: 15,
    angleMax: 45,
    stopFadeMs: 200,
    cardDelayMs: 350,
    gridStep: 62,
    starCountDesktop: 130,
    starCountMobile: 60,
    constellationFormMs: 3000,
    constellationFadeMs: 1000,
    fireworkIntervalMs: 2000,
    fireworkExplodeMs: 1500,
    lanePacketBaseSpeed: 0.000065,
    portShuttleBaseSpeed: 0.000085,
};

function now() {
    return performance.now();
}

function clamp(num, min, max) {
    return Math.max(min, Math.min(max, num));
}

function random(min, max) {
    return min + Math.random() * (max - min);
}

function pick(arr) {
    return arr[Math.floor(Math.random() * arr.length)];
}

function morseLampIntensity(pattern, currentMs, unitMs, phaseOffset = 0) {
    const timeline = [];
    for (let i = 0; i < pattern.length; i += 1) {
        const ch = pattern[i];
        if (ch === ".") {
            timeline.push({ on: true, dur: unitMs });
            timeline.push({ on: false, dur: unitMs });
        } else if (ch === "-") {
            timeline.push({ on: true, dur: 3 * unitMs });
            timeline.push({ on: false, dur: unitMs });
        } else {
            timeline.push({ on: false, dur: 3 * unitMs });
        }
    }

    let total = 0;
    for (let i = 0; i < timeline.length; i += 1) {
        total += timeline[i].dur;
    }
    if (!total) {
        return 0;
    }

    let t = (currentMs + phaseOffset) % total;
    for (let i = 0; i < timeline.length; i += 1) {
        const seg = timeline[i];
        if (t <= seg.dur) {
            return seg.on ? 1 : 0;
        }
        t -= seg.dur;
    }
    return 0;
}

function getMeteorTargetCount() {
    return state.mobile ? CONFIG.meteorCountMobile : CONFIG.meteorCountDesktop;
}

function getStarTargetCount() {
    return state.mobile ? CONFIG.starCountMobile : CONFIG.starCountDesktop;
}

function isCenterProtected(x, y, padding = 0) {
    const w = state.meteorCanvas.width;
    const h = state.meteorCanvas.height;
    const cx = w / 2;
    const cy = h / 2;
    const halfW = 260 + padding;
    const halfH = 200 + padding;
    return x > cx - halfW && x < cx + halfW && y > cy - halfH && y < cy + halfH;
}

function initCanvases() {
    state.meteorCanvas = document.getElementById("meteorCanvas");
    state.meteorCtx = state.meteorCanvas.getContext("2d");

    state.gridCanvas = document.getElementById("gridCanvas");
    state.gridCtx = state.gridCanvas.getContext("2d");

    resizeAll();
}

function resizeAll() {
    const width = window.innerWidth;
    const height = window.innerHeight;

    state.mobile = window.matchMedia("(max-width: 768px)").matches;

    state.meteorCanvas.width = width;
    state.meteorCanvas.height = height;
    state.gridCanvas.width = width;
    state.gridCanvas.height = height;

    seedMeteors();
    seedStars();
    seedMaritimeDecor();
    seedPortThroughput();
    seedDockedVessels();
    state.constellations = [];
    state.fireworks = [];
    state.nextConstellationAt = now() + random(260, 900);
    if (state.transitioning) {
        state.nextFireworkAt = now() + 300;
    }
}

function seedDockedVessels() {
    const w = state.meteorCanvas.width;
    const h = state.meteorCanvas.height;

    // 两侧靠泊货轮，避开中心登录区
    state.dockedVessels = [
        {
            side: "left",
            x: 0.07 * w,
            y: 0.73 * h,
            scale: state.mobile ? 0.78 : 1,
            hue: random(192, 218),
            phase: random(0, Math.PI * 2),
            morsePattern: "... --- ...",
            unitMs: 150,
            phaseOffset: random(0, 900),
        },
        {
            side: "right",
            x: 0.71 * w,
            y: 0.74 * h,
            scale: state.mobile ? 0.74 : 0.96,
            hue: random(188, 220),
            phase: random(0, Math.PI * 2),
            morsePattern: "-.-- .... -...",
            unitMs: 140,
            phaseOffset: random(0, 900),
        },
    ];

    state.waterScans = [
        { y: 0.81 * h, amp: 10, speed: 0.0018, phase: random(0, Math.PI * 2) },
        { y: 0.86 * h, amp: 12, speed: 0.0014, phase: random(0, Math.PI * 2) },
        { y: 0.9 * h, amp: 8, speed: 0.0019, phase: random(0, Math.PI * 2) },
    ];
}

function seedPortThroughput() {
    const w = state.meteorCanvas.width;
    const h = state.meteorCanvas.height;

    state.portContainers = [];
    state.portCranes = [];
    state.portShuttles = [];

    const zones = [
        { xMin: 0.03 * w, xMax: 0.31 * w, yBase: 0.9 * h, side: "left" },
        { xMin: 0.69 * w, xMax: 0.97 * w, yBase: 0.9 * h, side: "right" },
    ];

    for (let z = 0; z < zones.length; z += 1) {
        const zone = zones[z];
        const stackCount = state.mobile ? 7 : 11;

        for (let i = 0; i < stackCount; i += 1) {
            const x = random(zone.xMin, zone.xMax);
            const layers = Math.floor(random(2, 6));
            const boxW = random(18, 30);
            const boxH = random(7, 11);

            state.portContainers.push({
                x,
                y: zone.yBase,
                layers,
                boxW,
                boxH,
                phase: random(0, Math.PI * 2),
                hue: random(180, 235),
            });
        }

        state.portCranes.push({
            x: zone.side === "left" ? 0.2 * w : 0.8 * w,
            y: 0.72 * h,
            width: 0.16 * w,
            height: 0.17 * h,
            phase: random(0, Math.PI * 2),
            side: zone.side,
            craneId: zone.side === "left" ? "QC-L07" : "QC-R12",
            taskId: `JOB-${Math.floor(random(1200, 9800))}`,
            containerId: `MSCU${Math.floor(random(100000, 999999))}`,
        });
    }

    const shuttleCount = state.mobile ? 3 : 5;
    for (let i = 0; i < shuttleCount; i += 1) {
        const laneY = random(0.84 * h, 0.94 * h);
        state.portShuttles.push({
            phase: random(0, 1),
            laneY,
            width: random(12, 22),
            hue: random(188, 225),
            dir: i % 2 === 0 ? 1 : -1,
        });
    }
}

function seedMaritimeDecor() {
    const w = state.meteorCanvas.width;
    const h = state.meteorCanvas.height;

    // 4 条 AIS 风格航线：上/下/左/右环绕，避开中心登录区
    state.shippingLanes = [
        {
            p0: { x: -40, y: 0.24 * h },
            p1: { x: 0.28 * w, y: 0.14 * h },
            p2: { x: 0.72 * w, y: 0.34 * h },
            p3: { x: w + 40, y: 0.2 * h },
            width: 1.2,
            phase: random(0, 1),
            hue: random(185, 205),
            code: "CN-SHA → SGP",
        },
        {
            p0: { x: -30, y: 0.8 * h },
            p1: { x: 0.22 * w, y: 0.9 * h },
            p2: { x: 0.72 * w, y: 0.62 * h },
            p3: { x: w + 50, y: 0.78 * h },
            width: 1.35,
            phase: random(0, 1),
            hue: random(190, 218),
            code: "NGB → LAX",
        },
        {
            p0: { x: 0.12 * w, y: -40 },
            p1: { x: 0.23 * w, y: 0.25 * h },
            p2: { x: 0.09 * w, y: 0.7 * h },
            p3: { x: 0.2 * w, y: h + 40 },
            width: 1.05,
            phase: random(0, 1),
            hue: random(175, 198),
            code: "BOS HUB",
        },
        {
            p0: { x: 0.88 * w, y: -40 },
            p1: { x: 0.75 * w, y: 0.26 * h },
            p2: { x: 0.93 * w, y: 0.72 * h },
            p3: { x: 0.81 * w, y: h + 40 },
            width: 1.05,
            phase: random(0, 1),
            hue: random(195, 222),
            code: "DXB FEED",
        },
    ];

    // 海事信标：边缘布设，持续闪烁 + 扫描束
    state.seaBeacons = [
        { x: 0.08 * w, y: 0.18 * h, phase: random(0, Math.PI * 2), dir: 0.2 },
        { x: 0.9 * w, y: 0.16 * h, phase: random(0, Math.PI * 2), dir: 2.85 },
        { x: 0.06 * w, y: 0.82 * h, phase: random(0, Math.PI * 2), dir: -0.35 },
        { x: 0.92 * w, y: 0.82 * h, phase: random(0, Math.PI * 2), dir: 3.45 },
        { x: 0.48 * w, y: 0.06 * h, phase: random(0, Math.PI * 2), dir: 1.5 },
        { x: 0.5 * w, y: 0.92 * h, phase: random(0, Math.PI * 2), dir: -1.6 },
    ];
}

function bezierPoint(curve, t) {
    const mt = 1 - t;
    const mt2 = mt * mt;
    const t2 = t * t;
    return {
        x:
            curve.p0.x * mt2 * mt +
            3 * curve.p1.x * mt2 * t +
            3 * curve.p2.x * mt * t2 +
            curve.p3.x * t2 * t,
        y:
            curve.p0.y * mt2 * mt +
            3 * curve.p1.y * mt2 * t +
            3 * curve.p2.y * mt * t2 +
            curve.p3.y * t2 * t,
    };
}

function drawShippingLanes(current) {
    const ctx = state.meteorCtx;
    const tBase = current * CONFIG.lanePacketBaseSpeed;

    ctx.save();
    ctx.setLineDash([6, 12]);

    for (let i = 0; i < state.shippingLanes.length; i += 1) {
        const lane = state.shippingLanes[i];
        const alphaBoost = state.transitioning ? 1 : 0.86;

        ctx.strokeStyle = `hsla(${lane.hue}, 95%, 72%, ${0.3 * alphaBoost})`;
        ctx.lineWidth = lane.width;
        ctx.shadowBlur = 8;
        ctx.shadowColor = `hsla(${lane.hue}, 100%, 65%, ${0.5 * alphaBoost})`;
        ctx.lineDashOffset = -(current * 0.03 + lane.phase * 80);

        ctx.beginPath();
        ctx.moveTo(lane.p0.x, lane.p0.y);
        ctx.bezierCurveTo(lane.p1.x, lane.p1.y, lane.p2.x, lane.p2.y, lane.p3.x, lane.p3.y);
        ctx.stroke();

        for (let k = 0; k < 2; k += 1) {
            const t = (tBase * (1 + i * 0.08) + lane.phase + k * 0.48) % 1;
            const p = bezierPoint(lane, t);

            if (isCenterProtected(p.x, p.y, 85)) {
                continue;
            }

            ctx.beginPath();
            ctx.fillStyle = `hsla(${lane.hue + 12}, 100%, 78%, ${0.9 * alphaBoost})`;
            ctx.shadowBlur = 14;
            ctx.arc(p.x, p.y, 2.2, 0, Math.PI * 2);
            ctx.fill();

            if (k === 0) {
                ctx.font = "11px monospace";
                ctx.fillStyle = `rgba(186, 241, 255, ${0.46 * alphaBoost})`;
                ctx.shadowBlur = 0;
                ctx.fillText(lane.code, p.x + 8, p.y - 8);
            }
        }
    }

    ctx.restore();
}

function drawSeaBeacons(current) {
    const ctx = state.meteorCtx;
    ctx.save();

    for (let i = 0; i < state.seaBeacons.length; i += 1) {
        const b = state.seaBeacons[i];
        const pulse = 0.45 + 0.55 * Math.sin(current * 0.003 + b.phase);
        const sweep = b.dir + Math.sin(current * 0.0013 + b.phase) * 0.55;
        const len = state.mobile ? 54 : 74;
        const tipX = b.x + Math.cos(sweep) * len;
        const tipY = b.y + Math.sin(sweep) * len;

        if (!isCenterProtected(tipX, tipY, 120)) {
            const gradient = ctx.createLinearGradient(b.x, b.y, tipX, tipY);
            gradient.addColorStop(0, `rgba(111, 250, 255, ${0.28 + pulse * 0.3})`);
            gradient.addColorStop(1, "rgba(111, 250, 255, 0)");
            ctx.strokeStyle = gradient;
            ctx.lineWidth = 2;
            ctx.beginPath();
            ctx.moveTo(b.x, b.y);
            ctx.lineTo(tipX, tipY);
            ctx.stroke();
        }

        ctx.beginPath();
        ctx.fillStyle = `rgba(167, 255, 214, ${0.6 + pulse * 0.35})`;
        ctx.shadowBlur = 16;
        ctx.shadowColor = "rgba(102, 255, 229, 0.9)";
        ctx.arc(b.x, b.y, 2.1 + pulse * 1.3, 0, Math.PI * 2);
        ctx.fill();
    }

    ctx.restore();
}

function drawPortThroughput(current, frameScale) {
    const ctx = state.meteorCtx;
    const w = state.meteorCanvas.width;
    const h = state.meteorCanvas.height;

    // 1) 集装箱堆场：侧边底部密集堆叠，带动态流光
    ctx.save();
    for (let i = 0; i < state.portContainers.length; i += 1) {
        const c = state.portContainers[i];
        const glow = 0.24 + 0.2 * Math.sin(current * 0.003 + c.phase);

        for (let layer = 0; layer < c.layers; layer += 1) {
            const y = c.y - layer * (c.boxH + 1);
            const xJitter = Math.sin((current * 0.0017 + c.phase + layer) * 1.3) * 1.2;
            const x = c.x + xJitter;

            if (isCenterProtected(x, y, 60)) {
                continue;
            }

            ctx.fillStyle = `hsla(${c.hue}, 70%, 24%, ${0.35 + glow * 0.35})`;
            ctx.strokeStyle = `hsla(${c.hue + 10}, 95%, 68%, ${0.28 + glow * 0.5})`;
            ctx.lineWidth = 1;
            ctx.shadowBlur = 10;
            ctx.shadowColor = `hsla(${c.hue}, 100%, 65%, ${0.2 + glow * 0.5})`;
            ctx.beginPath();
            ctx.rect(x, y, c.boxW, c.boxH);
            ctx.fill();
            ctx.stroke();

            if (layer % 2 === 0) {
                ctx.beginPath();
                ctx.fillStyle = `rgba(146, 240, 255, ${0.14 + glow * 0.25})`;
                ctx.rect(x + 2, y + 2, c.boxW * 0.34, c.boxH * 0.28);
                ctx.fill();
            }
        }
    }
    ctx.restore();

    // 2) 龙门吊：立柱+横梁+小车往复+吊具扫描
    ctx.save();
    for (let i = 0; i < state.portCranes.length; i += 1) {
        const crane = state.portCranes[i];
        const p = 0.5 + 0.5 * Math.sin(current * 0.0015 + crane.phase);
        const trollyX = crane.x - crane.width / 2 + p * crane.width;
        const beamGlow = 0.4 + 0.6 * Math.sin(current * 0.0024 + crane.phase);

        const legOffset = crane.width * 0.38;
        const leftLegX = crane.x - legOffset;
        const rightLegX = crane.x + legOffset;
        const topY = crane.y;
        const bottomY = crane.y + crane.height;

        if (!isCenterProtected(crane.x, crane.y, 90)) {
            ctx.strokeStyle = `rgba(118, 220, 255, ${0.35 + 0.28 * beamGlow})`;
            ctx.lineWidth = 2;
            ctx.shadowBlur = 14;
            ctx.shadowColor = "rgba(94, 231, 255, 0.8)";

            ctx.beginPath();
            ctx.moveTo(leftLegX, topY);
            ctx.lineTo(leftLegX, bottomY);
            ctx.moveTo(rightLegX, topY);
            ctx.lineTo(rightLegX, bottomY);
            ctx.moveTo(leftLegX - 18, topY);
            ctx.lineTo(rightLegX + 18, topY);
            ctx.stroke();

            ctx.strokeStyle = `rgba(255, 204, 96, ${0.3 + 0.4 * beamGlow})`;
            ctx.lineWidth = 1.4;
            ctx.beginPath();
            ctx.moveTo(trollyX, topY + 1);
            ctx.lineTo(trollyX, bottomY - 10);
            ctx.stroke();

            ctx.beginPath();
            ctx.fillStyle = `rgba(255, 217, 132, ${0.45 + 0.4 * beamGlow})`;
            ctx.arc(trollyX, bottomY - 10, 3, 0, Math.PI * 2);
            ctx.fill();

            const sweepLen = state.mobile ? 42 : 62;
            const sweepDir = crane.side === "left" ? 1 : -1;
            const sx = trollyX + sweepDir * sweepLen;
            const sy = bottomY + 18;
            if (!isCenterProtected(sx, sy, 120)) {
                const g = ctx.createLinearGradient(trollyX, bottomY - 10, sx, sy);
                g.addColorStop(0, `rgba(255, 220, 132, ${0.36 + beamGlow * 0.35})`);
                g.addColorStop(1, "rgba(255, 220, 132, 0)");
                ctx.strokeStyle = g;
                ctx.lineWidth = 3;
                ctx.beginPath();
                ctx.moveTo(trollyX, bottomY - 10);
                ctx.lineTo(sx, sy);
                ctx.stroke();
            }

            // 岸桥作业编号 HUD 漂浮标签
            const hudX = crane.side === "left" ? rightLegX + 14 : leftLegX - 190;
            const hudY = topY - 24 + Math.sin(current * 0.002 + crane.phase) * 5;
            if (!isCenterProtected(hudX + 95, hudY + 16, 85)) {
                ctx.fillStyle = "rgba(10, 34, 58, 0.56)";
                ctx.strokeStyle = `rgba(120, 236, 255, ${0.45 + beamGlow * 0.25})`;
                ctx.lineWidth = 1;
                ctx.shadowBlur = 10;
                ctx.shadowColor = "rgba(99, 231, 255, 0.65)";
                ctx.beginPath();
                ctx.rect(hudX, hudY, 190, 34);
                ctx.fill();
                ctx.stroke();

                ctx.shadowBlur = 0;
                ctx.fillStyle = `rgba(178, 243, 255, ${0.72 + beamGlow * 0.2})`;
                ctx.font = "11px monospace";
                ctx.fillText(`${crane.craneId}  ${crane.taskId}`, hudX + 8, hudY + 13);
                ctx.fillStyle = "rgba(134, 223, 255, 0.72)";
                ctx.fillText(crane.containerId, hudX + 8, hudY + 27);
            }
        }
    }
    ctx.restore();

    // 3) 地面运输光轨：AGV/卡车吞吐流（底部，快速干练）
    ctx.save();
    const tBase = current * CONFIG.portShuttleBaseSpeed;
    for (let i = 0; i < state.portShuttles.length; i += 1) {
        const s = state.portShuttles[i];
        const laneStart = s.dir > 0 ? 0.04 * w : 0.96 * w;
        const laneEnd = s.dir > 0 ? 0.96 * w : 0.04 * w;
        const progress = (tBase * (1 + i * 0.17) + s.phase) % 1;
        const x = laneStart + (laneEnd - laneStart) * progress;
        const y = s.laneY + Math.sin(current * 0.002 + s.phase * Math.PI * 2) * 2.5;

        if (isCenterProtected(x, y, 130)) {
            continue;
        }

        const trail = s.width * 1.9;
        const gx = s.dir > 0 ? x - trail : x + trail;
        const grad = ctx.createLinearGradient(x, y, gx, y);
        grad.addColorStop(0, `hsla(${s.hue}, 100%, 73%, 0.9)`);
        grad.addColorStop(1, "rgba(90, 227, 255, 0)");

        ctx.strokeStyle = grad;
        ctx.lineWidth = 2.6;
        ctx.shadowBlur = 12;
        ctx.shadowColor = `hsla(${s.hue}, 100%, 68%, 0.8)`;
        ctx.beginPath();
        ctx.moveTo(x, y);
        ctx.lineTo(gx, y);
        ctx.stroke();

        ctx.fillStyle = `hsla(${s.hue + 8}, 100%, 82%, 0.95)`;
        ctx.beginPath();
        ctx.rect(x - 2, y - 2, 4, 4);
        ctx.fill();
    }

    // 4) 吞吐脉冲柱：模拟港口 KPI 动态柱状反馈
    const pulseZones = [
        { x0: 0.05 * w, x1: 0.17 * w, y: 0.77 * h },
        { x0: 0.83 * w, x1: 0.95 * w, y: 0.77 * h },
    ];
    for (let z = 0; z < pulseZones.length; z += 1) {
        const zone = pulseZones[z];
        const bars = state.mobile ? 6 : 10;
        for (let b = 0; b < bars; b += 1) {
            const x = zone.x0 + ((zone.x1 - zone.x0) / (bars - 1)) * b;
            const amp = 16 + 22 * (0.5 + 0.5 * Math.sin(current * 0.004 + b * 0.7 + z));
            const yTop = zone.y - amp;
            if (isCenterProtected(x, yTop, 95)) {
                continue;
            }
            ctx.strokeStyle = `rgba(120, 238, 255, ${0.24 + amp / 90})`;
            ctx.lineWidth = 2;
            ctx.beginPath();
            ctx.moveTo(x, zone.y);
            ctx.lineTo(x, yTop);
            ctx.stroke();
        }
    }
    ctx.restore();
}

function drawDockedVessels(current) {
    const ctx = state.meteorCtx;
    const w = state.meteorCanvas.width;
    const h = state.meteorCanvas.height;

    ctx.save();
    for (let i = 0; i < state.dockedVessels.length; i += 1) {
        const v = state.dockedVessels[i];
        const s = v.scale;
        const shimmer = 0.45 + 0.55 * Math.sin(current * 0.0022 + v.phase);
        const x = v.x;
        const y = v.y + Math.sin(current * 0.0013 + v.phase) * 1.4;
        const shipW = 300 * s;
        const shipH = 84 * s;

        if (isCenterProtected(x + shipW * 0.5, y + shipH * 0.3, 60)) {
            continue;
        }

        ctx.strokeStyle = `hsla(${v.hue}, 95%, 72%, ${0.34 + shimmer * 0.28})`;
        ctx.lineWidth = 1.7;
        ctx.shadowBlur = 14;
        ctx.shadowColor = `hsla(${v.hue}, 100%, 66%, ${0.52 + shimmer * 0.2})`;

        // 船体轮廓
        ctx.beginPath();
        ctx.moveTo(x + 10 * s, y + 56 * s);
        ctx.lineTo(x + shipW * 0.74, y + 56 * s);
        ctx.lineTo(x + shipW * 0.86, y + 44 * s);
        ctx.lineTo(x + shipW * 0.97, y + 46 * s);
        ctx.lineTo(x + shipW * 0.94, y + 67 * s);
        ctx.lineTo(x + 20 * s, y + 67 * s);
        ctx.closePath();
        ctx.stroke();

        // 上层甲板与集装箱线框
        ctx.beginPath();
        ctx.moveTo(x + shipW * 0.22, y + 44 * s);
        ctx.lineTo(x + shipW * 0.72, y + 44 * s);
        ctx.lineTo(x + shipW * 0.78, y + 36 * s);
        ctx.lineTo(x + shipW * 0.26, y + 36 * s);
        ctx.closePath();
        ctx.stroke();

        for (let c = 0; c < 6; c += 1) {
            const bx = x + shipW * (0.24 + c * 0.075);
            const by = y + 27 * s;
            ctx.beginPath();
            ctx.rect(bx, by, 18 * s, 8 * s);
            ctx.stroke();
        }

        // 驾驶楼
        ctx.beginPath();
        ctx.rect(x + shipW * 0.74, y + 23 * s, 28 * s, 20 * s);
        ctx.stroke();

        // 靠泊系泊线
        const bollardX = v.side === "left" ? x - 24 * s : x + shipW + 24 * s;
        const bollardY = y + 60 * s;
        ctx.beginPath();
        ctx.moveTo(v.side === "left" ? x + 12 * s : x + shipW - 10 * s, y + 60 * s);
        ctx.lineTo(bollardX, bollardY);
        ctx.stroke();
        ctx.beginPath();
        ctx.fillStyle = `rgba(170, 238, 255, ${0.45 + shimmer * 0.25})`;
        ctx.arc(bollardX, bollardY, 3.2, 0, Math.PI * 2);
        ctx.fill();

        // 靠泊时序灯语（摩斯节奏舷灯）
        const lampOn = morseLampIntensity(v.morsePattern, current, v.unitMs, v.phaseOffset);
        const lampAlpha = lampOn ? 0.9 : 0.18;
        const lampCount = 7;
        for (let l = 0; l < lampCount; l += 1) {
            const lx = x + shipW * (0.2 + l * 0.085);
            const ly = y + 60 * s;
            ctx.beginPath();
            ctx.fillStyle = `rgba(255, 226, 138, ${lampAlpha})`;
            ctx.shadowBlur = lampOn ? 16 : 4;
            ctx.shadowColor = lampOn ? "rgba(255, 226, 138, 0.95)" : "rgba(255, 226, 138, 0.2)";
            ctx.arc(lx, ly, 1.9, 0, Math.PI * 2);
            ctx.fill();
        }

        if (!isCenterProtected(x + shipW * 0.58, y + 20 * s, 85)) {
            ctx.shadowBlur = 0;
            ctx.fillStyle = `rgba(255, 230, 160, ${lampOn ? 0.58 : 0.22})`;
            ctx.font = "10px monospace";
            ctx.fillText(v.morsePattern, x + shipW * 0.5, y + 18 * s);
        }

        // 船体水线反光
        const reflY = y + 74 * s;
        const grad = ctx.createLinearGradient(x, reflY, x + shipW, reflY);
        grad.addColorStop(0, "rgba(125, 244, 255, 0)");
        grad.addColorStop(0.5, `rgba(125, 244, 255, ${0.32 + shimmer * 0.26})`);
        grad.addColorStop(1, "rgba(125, 244, 255, 0)");
        ctx.strokeStyle = grad;
        ctx.lineWidth = 3;
        ctx.beginPath();
        ctx.moveTo(x + 8 * s, reflY);
        ctx.lineTo(x + shipW - 8 * s, reflY);
        ctx.stroke();
    }
    ctx.restore();

    // 水面反射扫描层（底部横向扫描波）
    ctx.save();
    for (let i = 0; i < state.waterScans.length; i += 1) {
        const scan = state.waterScans[i];
        const baseY = scan.y + Math.sin(current * scan.speed + scan.phase) * scan.amp;
        const alpha = 0.16 + 0.14 * Math.sin(current * 0.002 + i);
        const sweepX = ((current * (0.11 + i * 0.025)) % (w + 260)) - 130;

        const lineGrad = ctx.createLinearGradient(0, baseY, w, baseY);
        lineGrad.addColorStop(0, "rgba(120, 240, 255, 0)");
        lineGrad.addColorStop(0.5, `rgba(120, 240, 255, ${alpha})`);
        lineGrad.addColorStop(1, "rgba(120, 240, 255, 0)");
        ctx.strokeStyle = lineGrad;
        ctx.lineWidth = 1.4;
        ctx.beginPath();
        ctx.moveTo(0, baseY);
        ctx.lineTo(w, baseY);
        ctx.stroke();

        const sweepGrad = ctx.createLinearGradient(sweepX - 70, baseY, sweepX + 70, baseY);
        sweepGrad.addColorStop(0, "rgba(255,255,255,0)");
        sweepGrad.addColorStop(0.5, "rgba(170,245,255,0.38)");
        sweepGrad.addColorStop(1, "rgba(255,255,255,0)");
        ctx.strokeStyle = sweepGrad;
        ctx.lineWidth = 3.2;
        ctx.beginPath();
        ctx.moveTo(sweepX - 70, baseY);
        ctx.lineTo(sweepX + 70, baseY);
        ctx.stroke();
    }

    // 码头水域轻雾层
    const mist = ctx.createLinearGradient(0, h * 0.75, 0, h);
    mist.addColorStop(0, "rgba(38, 114, 164, 0)");
    mist.addColorStop(1, "rgba(38, 114, 164, 0.22)");
    ctx.fillStyle = mist;
    ctx.fillRect(0, h * 0.75, w, h * 0.25);
    ctx.restore();
}

function seedMeteors() {
    const count = getMeteorTargetCount();
    state.meteors = Array.from({ length: count }, () => createMeteor(true));
}

function createMeteor(allowAnySpawn = false) {
    const w = state.meteorCanvas.width;
    const h = state.meteorCanvas.height;

    const spawnModes = [
        "top",
        "left",
        "right",
        "corner-tl",
        "corner-tr",
        "edge-top",
        "edge-left",
        "edge-right",
    ];

    const mode = spawnModes[Math.floor(Math.random() * spawnModes.length)];

    let x = 0;
    let y = 0;
    let direction = 0;

    const angleDeg = random(CONFIG.angleMin, CONFIG.angleMax);
    const angleRad = (angleDeg * Math.PI) / 180;

    if (mode === "top" || mode === "edge-top") {
        x = random(-0.1 * w, 1.1 * w);
        y = -random(10, 60);
        direction = Math.random() < 0.6 ? angleRad : Math.PI - angleRad;
    } else if (mode === "left" || mode === "edge-left") {
        x = -random(10, 80);
        y = random(-0.1 * h, 0.8 * h);
        direction = angleRad;
    } else if (mode === "right" || mode === "edge-right") {
        x = w + random(10, 80);
        y = random(-0.1 * h, 0.8 * h);
        direction = Math.PI - angleRad;
    } else if (mode === "corner-tl") {
        x = -random(0, 30);
        y = -random(0, 30);
        direction = angleRad;
    } else {
        x = w + random(0, 30);
        y = -random(0, 30);
        direction = Math.PI - angleRad;
    }

    if (!allowAnySpawn && state.stopSpawn) {
        return null;
    }

    const speed = random(CONFIG.speedMin, CONFIG.speedMax);
    const length = random(CONFIG.lengthMin, CONFIG.lengthMax);

    return {
        x,
        y,
        vx: Math.cos(direction) * speed,
        vy: Math.sin(direction) * speed,
        length,
        opacity: random(0.6, 1.0),
        width: random(1.2, 2.8),
        life: random(280, 520),
    };
}

function seedStars() {
    const count = getStarTargetCount();
    const w = state.gridCanvas.width;
    const h = state.gridCanvas.height;

    state.stars = Array.from({ length: count }, () => ({
        x: Math.random() * w,
        y: Math.random() * h,
        alpha: random(0.08, 0.46),
        pulse: random(0.002, 0.012),
        size: random(0.6, 1.8),
        dir: Math.random() > 0.5 ? 1 : -1,
    }));
}

function createConstellation() {
    const w = state.meteorCanvas.width;
    const h = state.meteorCanvas.height;

    let cx = random(0.14 * w, 0.86 * w);
    let cy = random(0.12 * h, 0.76 * h);

    for (let i = 0; i < 18 && isCenterProtected(cx, cy, 40); i += 1) {
        cx = random(0.14 * w, 0.86 * w);
        cy = random(0.12 * h, 0.76 * h);
    }

    if (isCenterProtected(cx, cy, 40)) {
        cy = random(0.08 * h, 0.26 * h);
    }

    const pointCount = Math.floor(random(5, 9));
    const points = [];
    const edges = [];

    for (let i = 0; i < pointCount; i += 1) {
        const angle = (Math.PI * 2 * i) / pointCount + random(-0.35, 0.35);
        const radius = random(24, 76);
        const px = cx + Math.cos(angle) * radius;
        const py = cy + Math.sin(angle) * radius;
        points.push({ x: px, y: py, size: random(1.2, 2.6) });
    }

    for (let i = 0; i < pointCount - 1; i += 1) {
        edges.push([i, i + 1]);
    }
    if (Math.random() > 0.45 && pointCount >= 6) {
        edges.push([0, Math.floor(pointCount / 2)]);
    }
    if (Math.random() > 0.65) {
        edges.push([pointCount - 1, 0]);
    }

    return {
        points,
        edges,
        startedAt: now(),
        hue: random(185, 230),
    };
}

function drawConstellations(current) {
    if (state.transitioning) {
        state.constellations = [];
        return;
    }

    if (current >= state.nextConstellationAt) {
        state.constellations.push(createConstellation());
        state.nextConstellationAt = current + random(2200, 3200);
    }

    const ctx = state.meteorCtx;
    const total = CONFIG.constellationFormMs + CONFIG.constellationFadeMs;

    state.constellations = state.constellations.filter((c) => {
        const elapsed = current - c.startedAt;
        if (elapsed >= total) {
            return false;
        }

        const formP = clamp(elapsed / CONFIG.constellationFormMs, 0, 1);
        const fadeP = elapsed > CONFIG.constellationFormMs
            ? 1 - clamp((elapsed - CONFIG.constellationFormMs) / CONFIG.constellationFadeMs, 0, 1)
            : 1;

        const drawRatio = elapsed <= CONFIG.constellationFormMs ? formP : 1;
        const glowAlpha = fadeP * 0.9;
        const lineCount = Math.floor(c.edges.length * drawRatio);
        const pointCount = Math.floor(c.points.length * drawRatio);

        ctx.save();
        ctx.strokeStyle = `hsla(${c.hue}, 90%, 76%, ${0.36 * glowAlpha})`;
        ctx.shadowBlur = 16;
        ctx.shadowColor = `hsla(${c.hue}, 100%, 72%, ${0.52 * glowAlpha})`;
        ctx.lineWidth = 1.2;

        for (let i = 0; i < lineCount; i += 1) {
            const [a, b] = c.edges[i];
            const p1 = c.points[a];
            const p2 = c.points[b];
            ctx.beginPath();
            ctx.moveTo(p1.x, p1.y);
            ctx.lineTo(p2.x, p2.y);
            ctx.stroke();
        }

        for (let i = 0; i < pointCount; i += 1) {
            const p = c.points[i];
            ctx.beginPath();
            ctx.fillStyle = `hsla(${c.hue}, 95%, 84%, ${0.7 * glowAlpha})`;
            ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
            ctx.fill();
        }

        ctx.restore();
        return true;
    });
}

function drawGridLayer() {
    const ctx = state.gridCtx;
    const w = state.gridCanvas.width;
    const h = state.gridCanvas.height;

    ctx.clearRect(0, 0, w, h);

    ctx.save();
    ctx.translate(w / 2, h / 2);

    state.gridRotationDeg += 0.01;
    ctx.rotate((state.gridRotationDeg * Math.PI) / 180);

    const halfW = w;
    const halfH = h;
    const step = CONFIG.gridStep;

    ctx.strokeStyle = getComputedStyle(document.body).getPropertyValue("--grid-color") || "rgba(0,255,198,0.15)";
    ctx.lineWidth = 0.8;

    for (let x = -halfW; x <= halfW; x += step) {
        ctx.beginPath();
        ctx.moveTo(x, -halfH);
        ctx.lineTo(x, halfH);
        ctx.stroke();
    }

    for (let y = -halfH; y <= halfH; y += step) {
        ctx.beginPath();
        ctx.moveTo(-halfW, y);
        ctx.lineTo(halfW, y);
        ctx.stroke();
    }

    for (let i = 0; i < state.stars.length; i += 1) {
        const star = state.stars[i];
        star.alpha += star.pulse * star.dir;
        if (star.alpha > 0.65 || star.alpha < 0.06) {
            star.dir *= -1;
        }
        ctx.fillStyle = `rgba(153, 248, 255, ${clamp(star.alpha, 0, 0.7)})`;
        ctx.beginPath();
        ctx.arc(star.x - w / 2, star.y - h / 2, star.size, 0, Math.PI * 2);
        ctx.fill();
    }

    ctx.restore();
}

function meteorOutOfBounds(m) {
    const w = state.meteorCanvas.width;
    const h = state.meteorCanvas.height;
    return m.x < -120 || m.x > w + 120 || m.y < -120 || m.y > h + 120;
}

function drawSingleMeteor(m) {
    const ctx = state.meteorCtx;
    const grad = ctx.createLinearGradient(m.x, m.y, m.x - m.vx * m.length, m.y - m.vy * m.length);
    grad.addColorStop(0, `rgba(255, 213, 79, ${m.opacity})`);
    grad.addColorStop(0.5, `rgba(255, 193, 7, ${m.opacity * 0.8})`);
    grad.addColorStop(1, "rgba(255, 193, 7, 0)");

    ctx.lineWidth = m.width;
    ctx.strokeStyle = grad;
    ctx.shadowColor = "rgba(255, 193, 7, 0.9)";
    ctx.shadowBlur = 14;

    ctx.beginPath();
    ctx.moveTo(m.x, m.y);
    ctx.lineTo(m.x - m.vx * m.length, m.y - m.vy * m.length);
    ctx.stroke();

    ctx.beginPath();
    ctx.fillStyle = `rgba(255, 213, 79, ${clamp(m.opacity, 0, 1)})`;
    ctx.arc(m.x, m.y, m.width * 0.65, 0, Math.PI * 2);
    ctx.fill();
}

function updateMeteors(frameScale) {
    const fadeProgress = state.stopStartedAt
        ? clamp((now() - state.stopStartedAt) / CONFIG.stopFadeMs, 0, 1)
        : 0;

    state.meteors = state.meteors.filter((meteor) => {
        if (!meteor) {
            return false;
        }

        if (state.stopSpawn) {
            meteor.vx *= 0.88;
            meteor.vy *= 0.88;
            meteor.opacity *= 1 - fadeProgress;
        }

        meteor.x += meteor.vx * frameScale;
        meteor.y += meteor.vy * frameScale;
        meteor.life -= frameScale;

        if (meteor.opacity <= 0.02 || meteor.life <= 0) {
            return false;
        }

        drawSingleMeteor(meteor);

        if (meteorOutOfBounds(meteor)) {
            return false;
        }

        return true;
    });

    if (!state.stopSpawn) {
        while (state.meteors.length < getMeteorTargetCount()) {
            const m = createMeteor(false);
            if (!m) {
                break;
            }
            state.meteors.push(m);
        }
    }
}

function createFireworkLaunch(current) {
    const w = state.meteorCanvas.width;
    const h = state.meteorCanvas.height;

    let startX = random(0.12 * w, 0.88 * w);
    for (let i = 0; i < 10 && isCenterProtected(startX, h - 20, 70); i += 1) {
        startX = random(0.08 * w, 0.92 * w);
    }

    let targetX = startX + random(-60, 60);
    let targetY = random(0.2 * h, 0.58 * h);
    for (let i = 0; i < 14 && isCenterProtected(targetX, targetY, 120); i += 1) {
        targetX = startX + random(-95, 95);
        targetY = random(0.18 * h, 0.52 * h);
    }

    return {
        phase: "launch",
        startAt: current,
        riseMs: random(760, 1180),
        fuseMs: random(0, 500),
        startX,
        startY: h + 18,
        targetX,
        targetY,
        x: startX,
        y: h + 18,
        holdStart: 0,
        explodeAt: 0,
        particles: [],
        palette: [
            "#39f6ff",
            "#6aff9b",
            "#ff6ff2",
            "#ffd75f",
            "#76a9ff",
            "#ff8c66",
        ],
    };
}

function explodeFirework(fw, current) {
    fw.phase = "explode";
    fw.explodeAt = current;

    const particleCount = Math.floor(random(22, 34));
    fw.particles = [];

    for (let i = 0; i < particleCount; i += 1) {
        const angle = random(0, Math.PI * 2);
        const speed = random(1.4, 3.2);
        const p = {
            x: fw.x,
            y: fw.y,
            vx: Math.cos(angle) * speed,
            vy: Math.sin(angle) * speed,
            size: random(1.4, 2.8),
            color: pick(fw.palette),
        };
        fw.particles.push(p);
    }
}

function drawAndUpdateFireworks(current, frameScale) {
    if (!state.transitioning) {
        state.fireworks = [];
        return;
    }

    if (current >= state.nextFireworkAt) {
        state.fireworks.push(createFireworkLaunch(current));
        state.nextFireworkAt = current + CONFIG.fireworkIntervalMs + random(-220, 280);
    }

    const ctx = state.meteorCtx;

    state.fireworks = state.fireworks.filter((fw) => {
        if (fw.phase === "launch") {
            const riseP = clamp((current - fw.startAt) / fw.riseMs, 0, 1);
            fw.x = fw.startX + (fw.targetX - fw.startX) * riseP;
            fw.y = fw.startY + (fw.targetY - fw.startY) * riseP;

            ctx.save();
            ctx.lineWidth = 1.8;
            ctx.strokeStyle = "rgba(150, 230, 255, 0.7)";
            ctx.shadowBlur = 10;
            ctx.shadowColor = "rgba(123, 219, 255, 0.9)";
            ctx.beginPath();
            ctx.moveTo(fw.x, fw.y + 12);
            ctx.lineTo(fw.x, fw.y - 4);
            ctx.stroke();
            ctx.beginPath();
            ctx.fillStyle = "rgba(255,255,255,0.95)";
            ctx.arc(fw.x, fw.y - 2, 2.2, 0, Math.PI * 2);
            ctx.fill();
            ctx.restore();

            if (riseP >= 1) {
                if (!fw.holdStart) {
                    fw.holdStart = current;
                }
                if (current - fw.holdStart >= fw.fuseMs) {
                    explodeFirework(fw, current);
                }
            }

            return true;
        }

        const elapsed = current - fw.explodeAt;
        if (elapsed >= CONFIG.fireworkExplodeMs) {
            return false;
        }

        const life = 1 - clamp(elapsed / CONFIG.fireworkExplodeMs, 0, 1);

        ctx.save();
        for (let i = 0; i < fw.particles.length; i += 1) {
            const p = fw.particles[i];
            p.vy += 0.012 * frameScale;
            p.x += p.vx * frameScale;
            p.y += p.vy * frameScale;

            const alpha = clamp(life * 0.95, 0, 1);

            ctx.fillStyle = `${p.color}${Math.round(alpha * 255).toString(16).padStart(2, "0")}`;
            ctx.shadowColor = p.color;
            ctx.shadowBlur = 10;
            ctx.beginPath();
            ctx.arc(p.x, p.y, p.size * life, 0, Math.PI * 2);
            ctx.fill();
        }

        const ringR = 18 + (1 - life) * 46;
        ctx.strokeStyle = `rgba(255,255,255,${0.22 * life})`;
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.arc(fw.x, fw.y, ringR, 0, Math.PI * 2);
        ctx.stroke();
        ctx.restore();

        return true;
    });
}

let prevTime = now();

function loop() {
    const current = now();
    const frameScale = clamp((current - prevTime) / (1000 / 60), 0.75, 2.2);
    prevTime = current;

    drawGridLayer();

    const ctx = state.meteorCtx;
    ctx.clearRect(0, 0, state.meteorCanvas.width, state.meteorCanvas.height);

    drawShippingLanes(current);
    drawSeaBeacons(current);
    drawDockedVessels(current);
    drawPortThroughput(current, frameScale);
    drawConstellations(current);
    updateMeteors(frameScale);
    drawAndUpdateFireworks(current, frameScale);

    state.animId = requestAnimationFrame(loop);
}

function collapseScene() {
    if (state.transitioning) {
        return;
    }
    state.transitioning = true;
    state.stopSpawn = true;
    state.stopStartedAt = now();
    state.nextFireworkAt = now() + 420;

    document.body.classList.add("scene-collapsing");

    window.setTimeout(() => {
        if (!state.cardShown) {
            state.cardShown = true;
            document.getElementById("authContainer").classList.add("show");
        }
    }, CONFIG.cardDelayMs);
}

function showToast(msg, isError = false) {
    const toast = document.getElementById("toast");
    toast.textContent = msg;
    toast.classList.toggle("error", isError);
    toast.classList.add("show");
    window.clearTimeout(showToast.timer);
    showToast.timer = window.setTimeout(() => {
        toast.classList.remove("show");
    }, 1800);
}

function bindSceneTrigger() {
    const trigger = () => collapseScene();
    document.body.addEventListener("pointerdown", trigger, { once: true });
}

function bindTidalSwitch() {
    const authContainer = document.getElementById("authContainer");
    const leftSwitchToRegister = document.getElementById("leftSwitchToRegister");
    const rightSwitchToLogin = document.getElementById("rightSwitchToLogin");

    function showRegister() {
        authContainer.classList.add("register-mode");
    }

    function showLogin() {
        authContainer.classList.remove("register-mode");
    }

    leftSwitchToRegister.addEventListener("click", showRegister);
    rightSwitchToLogin.addEventListener("click", showLogin);
}

async function submitForm(form, endpoint) {
    const payload = Object.fromEntries(new FormData(form).entries());

    try {
        const res = await fetch(endpoint, {
            method: "POST",
            body: JSON.stringify(payload),
            headers: {
                "Content-Type": "application/json",
                "X-Requested-With": "XMLHttpRequest",
            },
        });

        const data = await res.json();
        const ok = Boolean(data.success);
        showToast(data.msg || (ok ? "操作成功" : "操作失败"), !ok);
    } catch (err) {
        showToast("网络异常，请稍后重试", true);
    }
}

function bindForms() {
    const loginForm = document.getElementById("loginForm");
    const registerForm = document.getElementById("registerForm");

    loginForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        await submitForm(loginForm, "/api/login");
    });

    registerForm.addEventListener("submit", async (e) => {
        e.preventDefault();

        const pwd = registerForm.querySelector("input[name='password']").value;
        const confirm = registerForm.querySelector("input[name='confirm']").value;

        if (pwd !== confirm) {
            showToast("两次密码不一致", true);
            return;
        }

        await submitForm(registerForm, "/api/register");
    });
}

function boot() {
    initCanvases();
    bindSceneTrigger();
    bindTidalSwitch();
    bindForms();

    prevTime = now();
    loop();

    window.addEventListener("resize", resizeAll);
}

window.addEventListener("load", boot);
