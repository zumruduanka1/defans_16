// =====================
// CONFIG
// =====================
const API = "";

// =====================
// ANALYZE BUTTON
// =====================
document.querySelector(".btn-main").onclick = async () => {
    const text = document.querySelector("textarea").value;
    const email = document.querySelector("input").value;

    if (!text || text.length < 5) {
        alert("Metin gir");
        return;
    }

    try {
        const res = await fetch("/api/analyze", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({ text, email })
        });

        const data = await res.json();

        alert("Risk: " + data.risk + "% | " + data.status);

        addToTable(text, data.risk, data.status);
        updateChart(data.risk);

    } catch (err) {
        alert("Sunucu hatası");
        console.error(err);
    }
};

// =====================
// TABLE ADD
// =====================
function addToTable(text, risk, status) {
    const tbody = document.querySelector("tbody");

    let color = "#444";
    let label = "Şüpheli";
    let pillClass = "pill-warning";

    if (risk > 70) {
        color = "red";
        label = "Tehlikeli";
    } else if (risk < 40) {
        color = "#2ed573";
        label = "Güvenli";
        pillClass = "pill-success";
    }

    const row = `
    <tr>
        <td style="color: var(--text-gray);">${text.substring(0,30)}</td>
        <td>
            <div class="progress-container">
                <div class="progress-bar" style="width:${risk}%; background:${color}"></div>
            </div>
        </td>
        <td>
            <span class="status-pill ${pillClass}">
                ${label}
            </span>
        </td>
    </tr>`;

    tbody.innerHTML = row + tbody.innerHTML;
}

// =====================
// SOCIAL LOAD
// =====================
async function loadSocial() {
    try {
        const res = await fetch("/api/social");
        const data = await res.json();

        const tbody = document.querySelector("tbody");
        tbody.innerHTML = "";

        data.forEach(p => {
            let icon = "📰";

            if (p.platform === "twitter") icon = "🐦";
            if (p.platform === "instagram") icon = "📸";
            if (p.platform === "tiktok") icon = "🎵";
            if (p.platform === "facebook") icon = "📘";

            const row = `
            <tr>
                <td>${icon} ${p.text.substring(0,40)}</td>
                <td>
                    <div class="progress-container">
                        <div class="progress-bar" style="width:${p.risk}%"></div>
                    </div>
                </td>
                <td>
                    <span class="status-pill ${p.risk > 70 ? "pill-warning" : "pill-success"}">
                        ${p.risk > 70 ? "⚠️ Şüpheli" : "✅ Güvenli"}
                    </span>
                </td>
            </tr>`;

            tbody.innerHTML += row;
        });

    } catch (err) {
        console.error("Social error:", err);
    }
}

// =====================
// VIDEO ANALYSIS
// =====================
async function analyzeVideo() {
    const url = document.getElementById("videoUrl").value;

    if (!url) {
        alert("Video URL gir");
        return;
    }

    try {
        const res = await fetch("/api/video", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({ url })
        });

        const data = await res.json();

        alert("Deepfake Risk: " + data.score + "%");

    } catch (err) {
        alert("Video analiz hatası");
    }
}

// =====================
// CHART
// =====================
let chart;

function updateChart(risk) {
    const ctx = document.getElementById("chart");

    if (!ctx) return;

    if (chart) chart.destroy();

    chart = new Chart(ctx, {
        type: "doughnut",
        data: {
            labels: ["Risk", "Güven"],
            datasets: [{
                data: [risk, 100 - risk]
            }]
        }
    });
}

// =====================
// INIT
// =====================
loadSocial();