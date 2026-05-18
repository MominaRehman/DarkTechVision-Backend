"""
Training Service
"""

import torch
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader
import pandas as pd
import os

class TextDataset(Dataset):
    def __init__(self, texts, labels, label_map):
        self.texts = texts
        self.labels = [label_map.get(l, 0) for l in labels]
    
    def __len__(self):
        return len(self.texts)
    
    def __getitem__(self, idx):
        text = self.texts[idx]
        label = self.labels[idx]
        features = torch.zeros(128)
        for i, char in enumerate(text[:128]):
            features[i] = (ord(char) % 255) / 255.0
        return features, label


class TrainingService:
    def __init__(self):
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    
    def train_text_model(self, csv_path, epochs=50, batch_size=32, lr=0.001):
        try:
            from models.deep_learning import TextGNN
            
            df = pd.read_csv(csv_path)
            texts = df['text'].tolist()
            labels = df['label'].tolist()
            
            label_map = {'gun': 0, 'drug': 1, 'poison': 2}
            dataset = TextDataset(texts, labels, label_map)
            dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=True)
            
            model = TextGNN().to(self.device)
            optimizer = torch.optim.Adam(model.parameters(), lr=lr)
            
            logs = []
            for epoch in range(epochs):
                model.train()
                total_loss = 0
                correct = 0
                total = 0
                
                for features, batch_labels in dataloader:
                    features = features.to(self.device)
                    batch_labels = batch_labels.to(self.device)
                    
                    optimizer.zero_grad()
                    output = model(features)
                    loss = F.nll_loss(output, batch_labels)
                    loss.backward()
                    optimizer.step()
                    
                    total_loss += loss.item()
                    pred = output.argmax(dim=1)
                    correct += (pred == batch_labels).sum().item()
                    total += batch_labels.size(0)
                
                avg_loss = total_loss / len(dataloader)
                accuracy = correct / total
                logs.append({"epoch": epoch+1, "loss": avg_loss, "accuracy": accuracy})
                
                if (epoch+1) % 10 == 0:
                    print(f"Epoch {epoch+1}/{epochs} - Loss: {avg_loss:.4f}, Acc: {accuracy:.4f}")
            
            os.makedirs("models", exist_ok=True)
            torch.save(model.state_dict(), "models/text_gnn_model.pth")
            print(f"✅ Text GNN model saved")
            
            return {"status": "success", "logs": logs, "final_accuracy": accuracy}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def train_image_model(self, image_dir, epochs=10, batch_size=32, lr=0.0001):
        return {"status": "success", "message": "Image training not implemented in demo"}


training_service = TrainingService()