import os
import pandas as pd
import torch
from transformers import BertTokenizer, BertForSequenceClassification
from torch.utils.data import DataLoader, Dataset
from torch.optim import AdamW

data_train = "data/classifier/train.csv"
data_valid = "data/classifier/valid.csv"

df_train = pd.read_csv(data_train)
df_valid = pd.read_csv(data_valid)

label_map = {"STATIC": 0, "DYNAMIC": 1}


class HRDataset(Dataset):
    def __init__(self, df, tokenizer, max_len=128):
        self.df = df
        self.tok = tokenizer
        self.max_len = max_len

    def __len__(self):
        return len(self.df)

    def __getitem__(self, idx):
        text = self.df.iloc[idx]["text"]
        label = label_map[self.df.iloc[idx]["label"]]

        enc = self.tok(text, truncation=True, padding="max_length", max_length=128, return_tensors="pt")

        return {
            "input_ids": enc["input_ids"].squeeze(),
            "attention_mask": enc["attention_mask"].squeeze(),
            "labels": torch.tensor(label, dtype=torch.long)
        }


tokenizer = BertTokenizer.from_pretrained("bert-base-uncased")
model = BertForSequenceClassification.from_pretrained("bert-base-uncased", num_labels=2)

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model.to(device)

train_ds = HRDataset(df_train, tokenizer)
valid_ds = HRDataset(df_valid, tokenizer)

train_loader = DataLoader(train_ds, batch_size=8, shuffle=True)
valid_loader = DataLoader(valid_ds, batch_size=8)

optim = AdamW(model.parameters(), lr=2e-5)

EPOCHS = 3
for epoch in range(EPOCHS):
    print("\nEpoch", epoch + 1)
    model.train()

    for batch in train_loader:
        optim.zero_grad()
        out = model(
            input_ids=batch["input_ids"].to(device),
            attention_mask=batch["attention_mask"].to(device),
            labels=batch["labels"].to(device)
        )
        out.loss.backward()
        optim.step()
        print("loss:", out.loss.item())

# Save model
SAVE_DIR = "chatbot/ml/model_static_dynamic"
os.makedirs(SAVE_DIR, exist_ok=True)
model.save_pretrained(SAVE_DIR)
tokenizer.save_pretrained(SAVE_DIR)

print("Model saved to", SAVE_DIR)
