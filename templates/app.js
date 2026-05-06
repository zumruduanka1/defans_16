const socket = io();

// --------------------
// BUTON CLICK FIX
// --------------------
window.addEventListener("DOMContentLoaded", () => {

    const btn = document.querySelector(".btn-main");
    const textarea = document.querySelector("textarea");
    const resultBox = document.getElementById("resultBox");

    if (!btn) {
        console.error("Buton bulunamadı");
        return;
    }

    btn.onclick = async () => {

        const text = textarea.value;

        if (!text) {
            alert("Metin gir");
            return;
        }

        try {
            const res = await fetch("/analyze", {
                method: "POST",
                headers: {"Content-Type":"application/json"},
                body: JSON.stringify({text})
            });

            const data = await res.json();

            if (resultBox) {
                resultBox.innerHTML =
                    `<b>Risk:</b> ${data.risk}% <br><br>${data.why || ""}`;
            }

        } catch (err) {
            console.error("API hata:", err);
        }
    };
});

// --------------------
// SOCKET FIX
// --------------------
socket.on("connect", () => {
    console.log("Socket bağlandı");
});

socket.on("live", (d) => {
    console.log("LIVE:", d);
});

socket.on("alert", (d) => {
    if (Notification.permission !== "granted") {
        Notification.requestPermission();
    }

    new Notification("⚠ Risk", {
        body: d.text?.slice(0, 80)
    });
});