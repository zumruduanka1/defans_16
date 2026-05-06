@app.route("/analyze", methods=["POST"])
def analyze():
    ip = request.remote_addr

    if not rate(ip):
        return jsonify({"error":"rate limit"}),429

    data = request.get_json(silent=True) or {}
    text = data.get("text","")

    if not text:
        return jsonify({"error":"no text"}),400

    # filtre
    if not is_social(text):
        return jsonify({
            "risk": 0,
            "why": "Sosyal medya / haber içeriği tespit edilmedi"
        })

    # AI skor
    risk = ai_score(text)
    why = explain(text)

    result = {
        "text": text,
        "risk": risk,
        "why": why
    }

    logs.append(result)
    if len(logs) > 50:
        logs.pop(0)

    socketio.emit("live", result)

    if risk >= 70:
        socketio.emit("alert", result)

    return jsonify(result)