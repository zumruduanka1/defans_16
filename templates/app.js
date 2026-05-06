const socket = io();

// ----------------
// CHART
// ----------------
const ctx = document.getElementById("chart");

const chart = new Chart(ctx, {
    type: "line",
    data: {
        labels: [],
        datasets: [{
            label: "Risk",
            data: [],
            borderColor: "#7d5fff",
            backgroundColor: "rgba(125,95,255,0.2)"
        }]
    },
    options: {
        scales: {
            y: { min:0, max:100 }
        }
    }
});

// ----------------
// ANALYZE
// ----------------
async function analyze(){
    const text = document.querySelector("textarea").value;

    const res = await fetch("/analyze",{
        method:"POST",
        headers:{"Content-Type":"application/json"},
        body:JSON.stringify({text})
    });

    const data = await res.json();

    document.getElementById("result").innerHTML =
        `Risk: ${data.risk}%<br>${data.why}`;
}

// ----------------
// LIVE STREAM
// ----------------
socket.on("live",(d)=>{
    const time = new Date().toLocaleTimeString();

    chart.data.labels.push(time);
    chart.data.datasets[0].data.push(d.risk);

    if(chart.data.labels.length>15){
        chart.data.labels.shift();
        chart.data.datasets[0].data.shift();
    }

    chart.update();

    addLog(d);
});

// ----------------
// LOG LIST
// ----------------
function addLog(d){
    const el = document.createElement("div");
    el.className="log";
    el.innerHTML = `Risk: ${d.risk}% - ${d.text.slice(0,50)}`;

    document.getElementById("logs").prepend(el);
}

// ----------------
// ALERT
// ----------------
socket.on("alert",(d)=>{
    if(Notification.permission!=="granted"){
        Notification.requestPermission();
    }

    new Notification("⚠ Risk!",{
        body:d.text.slice(0,80)
    });
});