import json
from datasets import Dataset
from transformers import (
    DistilBertTokenizer,
    DistilBertForSequenceClassification,
    Trainer,
    TrainingArguments
)

# 📥 dataset yükle
with open("data/dataset.json", "r", encoding="utf-8") as f:
    data = json.load(f)

texts = [x["text"] for x in data]
labels = [x["label"] for x in data]

dataset = Dataset.from_dict({
    "text": texts,
    "label": labels
})

# 🔤 tokenizer
tokenizer = DistilBertTokenizer.from_pretrained("distilbert-base-uncased")

def tokenize(example):
    return tokenizer(example["text"], padding="max_length", truncation=True)

dataset = dataset.map(tokenize)

# 🔧 format
dataset = dataset.rename_column("label", "labels")
dataset.set_format(type="torch", columns=["input_ids", "attention_mask", "labels"])

# 🤖 model
model = DistilBertForSequenceClassification.from_pretrained(
    "distilbert-base-uncased",
    num_labels=2
)

# ⚙️ training ayarları
training_args = TrainingArguments(
    output_dir="./model",
    per_device_train_batch_size=2,
    num_train_epochs=3,
    logging_dir="./logs",
    save_strategy="epoch"
)

# 🧠 trainer
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=dataset
)

# 🚀 TRAIN
trainer.train()

# 💾 MODEL KAYDET
trainer.save_model("./model")
tokenizer.save_pretrained("./model")

print("MODEL BAŞARIYLA KAYDEDİLDİ 🚀")