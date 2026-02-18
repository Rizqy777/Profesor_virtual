# 1️⃣ Importar librerías
import json
from datasets import Dataset
from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
    TrainingArguments,
    Trainer,
)
import numpy as np
from sklearn.metrics import accuracy_score, precision_recall_fscore_support

import transformers
print("Versión de transformers usada:", transformers.__version__)
print("Ruta del módulo transformers:", transformers.__file__)

# 2️⃣ Cargar dataset sintético
with open("Fine-tunning/dataset.json", "r", encoding="utf-8") as f:
    data = json.load(f)

dataset = Dataset.from_list(data)
dataset = dataset.train_test_split(test_size=0.2)
print(dataset)

# 3️⃣ Tokenizar textos
model_name = "dccuchile/bert-base-spanish-wwm-cased"
tokenizer = AutoTokenizer.from_pretrained(model_name)


def tokenize(batch):
    return tokenizer(batch["text"], padding=True, truncation=True, max_length=128)


dataset = dataset.map(tokenize, batched=True)

# Indicar que 'label' es la columna de etiquetas
dataset = dataset.rename_column("label", "labels")
dataset.set_format(type="torch", columns=["input_ids", "attention_mask", "labels"])

# 4️⃣ Crear modelo
num_labels = 3  # positivo, negativo, neutral
model = AutoModelForSequenceClassification.from_pretrained(
    model_name, num_labels=num_labels
)


# 5️⃣ Definir métricas
def compute_metrics(pred):
    labels = pred.label_ids
    preds = np.argmax(pred.predictions, axis=1)
    precision, recall, f1, _ = precision_recall_fscore_support(
        labels, preds, average="weighted"
    )
    acc = accuracy_score(labels, preds)
    return {"accuracy": acc, "precision": precision, "recall": recall, "f1": f1}


# 6️⃣ Definir argumentos de entrenamiento
training_args = TrainingArguments(
    output_dir="./results",
    num_train_epochs=3,
    per_device_train_batch_size=8,
    per_device_eval_batch_size=8,
    learning_rate=2e-5,
    save_strategy="epoch",
    logging_dir="./logs",
    logging_steps=10,
    load_best_model_at_end=True,
    metric_for_best_model="accuracy",
    save_total_limit=2,
)

# 7️⃣ Crear Trainer
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=dataset["train"],
    eval_dataset=dataset["test"],
    tokenizer=tokenizer,
    compute_metrics=compute_metrics,
)

# 8️⃣ Entrenar modelo
trainer.train()

# 9️⃣ Evaluar modelo
results = trainer.evaluate()
print("Resultados de evaluación:")
print(results)

# 10️⃣ Guardar modelo y tokenizer
model.save_pretrained("./fine_tuned_model")
tokenizer.save_pretrained("./fine_tuned_model")
