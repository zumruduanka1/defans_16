document.querySelector(".btn-main").onclick = async () => {
    const text = document.querySelector("textarea").value;
    const email = document.querySelector("input").value;

    const res = await fetch("/api/analyze", {
        method: "POST",
        headers: {"Content-Type":"application/json"},
        body: JSON.stringify({ text, email })
    });

    const data = await res.json();

    alert("Risk: " + data.risk + "% | " + data.status);
    addToTable(text, data.risk);
};

function addToTable(text, risk) {
    const tbody = document.querySelector("tbody");

    let color = risk > 70 ? "red" : (risk < 40 ? "#2ed573" : "#f39c12");

    const row = `
    <tr>
        <td>${text.substring(0,30)}</td>
        <td>
            <div class="progress-container">
                <div class="progress-bar" style="width:${risk}%; background:${color}"></div>
            </div>
        </td>
        <td>${risk > 70 ? "⚠️ Şüpheli" : "✅ Güvenli"}</td>
    </tr>`;

    tbody.innerHTML = row + tbody.innerHTML;
}

// 🔥 SOSYAL VERİ
async function loadSocial(){
    const res = await fetch("/api/social");
    const data = await res.json();

    const tbody = document.querySelector("tbody");

    data.forEach(p=>{
        let icon = "📰";

        if(p.platform==="twitter") icon="🐦";
        if(p.platform==="instagram") icon="📸";
        if(p.platform==="tiktok") icon="🎵";
        if(p.platform==="facebook") icon="📘";

        const row = `
        <tr>
            <td>${icon} ${p.text.substring(0,40)}</td>
            <td>
                <div class="progress-container">
                    <div class="progress-bar" style="width:${p.risk}%"></div>
                </div>
            </td>
            <td>${p.risk > 70 ? "⚠️ Şüpheli" : "✅ Güvenli"}</td>
        </tr>`;

        tbody.innerHTML += row;
    });
}

loadSocial();