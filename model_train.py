import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
import joblib

# -------------------------
# ÖRNEK DATASET (BAŞLANGIÇ)
# -------------------------
data = [
    ("Ünlü iş insanı öldü iddiası sosyal medyada yayıldı", 1),
    ("Seçim sonuçları manipüle edildi iddiası", 1),
    ("Gizli liste ifşa edildi iddiası", 1),
    ("Bilim insanları yeni keşif yaptı", 0),
    ("Yeni teknoloji haberi paylaşıldı", 0),
    ("Ekonomi büyüme verileri açıklandı", 0),
]

df = pd.DataFrame(data, columns=["text","label"])

# -------------------------
# TRAIN / TEST
# -------------------------
X_train, X_test, y_train, y_test = train_test_split(
    df["text"], df["label"], test_size=0.2
)

# -------------------------
# MODEL PIPELINE
# -------------------------
model = Pipeline([
    ("tfidf", TfidfVectorizer()),
    ("clf", LogisticRegression())
])

model.fit(X_train, y_train)

print("Model eğitildi ✔")

# -------------------------
# SAVE
# -------------------------
joblib.dump(model, "fake_news_model.pkl")