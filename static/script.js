// 🧠 analiz
async function analyze(){
  const text = document.getElementById("text").value;

  const res = await fetch("/api/analyze", {
    method:"POST",
    headers:{"Content-Type":"application/json"},
    body: JSON.stringify({text})
  });

  const data = await res.json();
  document.getElementById("risk").innerText = data.risk;
  document.getElementById("safe").innerText = data.safe;
}

// 🐦 sosyal veri
async function loadSocial(){
  const res = await fetch("/api/social");
  const data = await res.json();

  const div = document.getElementById("social");
  if(!div) return;

  div.innerHTML = "";
  data.forEach(t=>{
    const el = document.createElement("div");
    el.innerText = t.text;
    div.appendChild(el);
  });
}

// 📧 mail gönder
async function sendMail(){
  const text = document.getElementById("text").value;
  const email = document.getElementById("email").value;

  const res = await fetch("/api/notify", {
    method:"POST",
    headers:{"Content-Type":"application/json"},
    body: JSON.stringify({text, email})
  });

  const data = await res.json();
  alert(data.status);
}

loadSocial();