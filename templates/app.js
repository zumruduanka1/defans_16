let riskChart;

function initChart() {
    const ctx = document.getElementById("riskChart");

    riskChart = new Chart(ctx, {
        type: "line",
        data: {
            labels: [],
            datasets: [{
                label: "Risk Skoru",
                data: [],
                borderColor: "#7d5fff",
                backgroundColor: "rgba(125,95,255,0.1)",
                tension: 0.4,
                fill: true
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    labels: { color: "#fff" }
                }
            },
            scales: {
                x: {
                    ticks: { color: "#8b949e" }
                },
                y: {
                    min: 0,
                    max: 100,
                    ticks: { color: "#8b949e" }
                }
            }
        }
    });
}

function updateChart(risk) {
    const now = new Date().toLocaleTimeString();

    riskChart.data.labels.push(now);
    riskChart.data.datasets[0].data.push(risk);

    // fazla veri olmasın
    if (riskChart.data.labels.length > 10) {
        riskChart.data.labels.shift();
        riskChart.data.datasets[0].data.shift();
    }

    riskChart.update();
}

// init
window.addEventListener("load", initChart);