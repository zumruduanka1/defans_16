risk = real_ai_analyze(text)

if risk is None:
    risk = analyze_ai(text)

    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        return None

    try:
        r = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": "gpt-4o-mini",
                "messages": [
                    {"role": "system", "content": "0 ile 100 arasında sadece risk puanı ver."},
                    {"role": "user", "content": text}
                ]
            },
            timeout=10
        )

        data = r.json()
        result = data["choices"][0]["message"]["content"]

        # sadece sayı çek
        risk = int(''.join(filter(str.isdigit, result))[:3])

        return min(risk, 100)

    except:
        return None