import os, requests
from dotenv import load_dotenv
load_dotenv()

HF_API = "https://api-inference.huggingface.co/models/facebook/bart-large-mnli"
HF_KEY = os.getenv("HF_API_KEY")

def ai_analyze(text):
    if client is None:
        return random.randint(30, 80)

    try:
        res = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{
                "role": "system",
                "content": """
Sen bir sosyal medya dezenformasyon analiz AI’sısın.
Sadece şunu yap:
- URL, video, görsel, metin analiz et
- 0-100 risk ver
- sadece sayı döndür
"""
            },{
                "role": "user",
                "content": text
            }]
        )

        return int(''.join(filter(str.isdigit, res.choices[0].message.content)))

    except:
        return random.randint(30, 80)
        }

        r = requests.post(HF_API, headers=headers, json=payload, timeout=8)
        data = r.json()

        label = data["labels"][0]
        score = int(data["scores"][0] * 100)

        if label == "fake news":
            return {"score": score, "status": "riskli"}
        else:
            return {"score": score, "status": "güvenli"}

    except:
        score = 0
        for k in ["şok","ifşa","gizli","son dakika"]:
            if k in text.lower():
                score += 25

        score = min(score,100)
        return {"score":score,"status":"riskli" if score>60 else "güvenli"}