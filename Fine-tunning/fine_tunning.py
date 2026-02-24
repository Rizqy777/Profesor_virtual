
# 1️⃣ Importar librerías
import json
from datasets import Dataset
from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
    TrainingArguments,
    Trainer,
)
import torch
import numpy as np
from sklearn.metrics import accuracy_score, precision_recall_fscore_support

import transformers
print("Versión de transformers usada:", transformers.__version__)
print("Ruta del módulo transformers:", transformers.__file__)

## Seccion para entrenamiento del modelo, descomentar para usar

# ---
# 2️⃣ Cargar dataset sintético y preparar datos (solo para entrenamiento)
# with open("Fine-tunning/dataset.json", "r", encoding="utf-8") as f:
#     data = json.load(f)
# dataset = Dataset.from_list(data)
# dataset = dataset.train_test_split(test_size=0.2)
# print(dataset)

# # 3️⃣ Tokenizar textos (solo para entrenamiento)
# model_name = "dccuchile/bert-base-spanish-wwm-cased"
# tokenizer = AutoTokenizer.from_pretrained(model_name)
# def tokenize(batch):
#     return tokenizer(batch["text"], padding=True, truncation=True, max_length=128)
# dataset = dataset.map(tokenize, batched=True)
# dataset = dataset.rename_column("label", "labels")
# dataset.set_format(type="torch", columns=["input_ids", "attention_mask", "labels"])
# num_labels = 3  # positivo, negativo, neutral
# model = AutoModelForSequenceClassification.from_pretrained(model_name, num_labels=num_labels)

# ---
# 4️⃣ Definir métricas y argumentos de entrenamiento (solo para entrenamiento)
# def compute_metrics(pred):
#     labels = pred.label_ids
#     preds = np.argmax(pred.predictions, axis=1)
#     precision, recall, f1, _ = precision_recall_fscore_support(
#         labels, preds, average="weighted"
#     )
#     acc = accuracy_score(labels, preds)
#     return {"accuracy": acc, "precision": precision, "recall": recall, "f1": f1}
# training_args = TrainingArguments(
#     output_dir="./results",
#     num_train_epochs=3,
#     per_device_train_batch_size=8,
#     per_device_eval_batch_size=8,
#     evaluation_strategy="epoch",
#     learning_rate=2e-5,
#     save_strategy="epoch",
#     logging_dir="./logs",
#     logging_steps=10,
#     load_best_model_at_end=True,
#     metric_for_best_model="accuracy",
#     save_total_limit=2,
# )
# trainer = Trainer(
#     model=model,
#     args=training_args,
#     train_dataset=dataset["train"],
#     eval_dataset=dataset["test"],
#     tokenizer=tokenizer,
#     compute_metrics=compute_metrics,
# )
# trainer.train()
# results = trainer.evaluate()
# print("Resultados de evaluación:")
# print(results)
# model.save_pretrained("./fine_tuned_model")
# tokenizer.save_pretrained("./fine_tuned_model")

# ---
# 5️⃣ Inferencia: predicción sobre un texto nuevo

# Seccion para test del modelo
model_dir = "./fine_tuned_model"
tokenizer = AutoTokenizer.from_pretrained(model_dir)
model = AutoModelForSequenceClassification.from_pretrained(model_dir)

text = "El estudiante se esfuerza al maximo pero tiene que mejorar"  # Cambia aquí el texto para probar
inputs = tokenizer(text, return_tensors="pt", padding=True, truncation=True, max_length=128)
with torch.no_grad():
    outputs = model(**inputs)
    logits = outputs.logits
    predicted_class_id = int(np.argmax(logits.numpy()))

etiquetas = {0: "negativo", 1: "positivo", 2: "neutral"}
print(f"Texto: {text}")
print(f"Predicción: {etiquetas[predicted_class_id]}")
