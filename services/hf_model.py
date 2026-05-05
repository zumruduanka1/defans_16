import os
from transformers import pipeline

classifier = pipeline("text-classification")

def hf_analyze(text):
    result = classifier(text)[0]
    return result