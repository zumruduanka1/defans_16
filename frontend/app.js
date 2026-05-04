document.getElementById("btn").addEventListener("click", analyze);

async function analyze() {
  const text = document.getElementById("input").value;

  try {
    const res = await fetch("/api/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text })
    });

    if (!res.ok) {
      const t = await res.text();
      console.error("API ERROR:", t);
      alert("API hata verdi. Console'a bak.");
      return;
    }

    const data = await res.json();

    document.getElementById("risk").innerText = data.risk ?? 0;
    document.getElementById("safe").innerText = data.safe ?? 0;

  } catch (e) {
    console.error(e);
    alert("İstek atılamadı. Network hatası.");
  }
}