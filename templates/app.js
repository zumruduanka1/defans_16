let chart;

window.onload = async () => {

const ctx = document.getElementById("trendChart");

chart = new Chart(ctx,{
    type:"line",
    data:{
        labels:[],
        datasets:[{
            label:"Risk",
            data:[],
            borderColor:"#7d5fff",
            fill:true
        }]
    }
});

setInterval(async ()=>{
    const r = await fetch("/trend");
    const d = await r.json();

    chart.data.labels = d.map(x=>"");
    chart.data.datasets[0].data = d.map(x=>x.risk);

    chart.update();
},3000);

};