from pathlib import Path

import cnn
import data_prep
import text_dataset
import torch
from torch.utils.data import DataLoader

MODEL_SAVE_PATH = "./artifacts/model.pt"
TOKENIZER_SAVE_PATH = "./artifacts/tokenizer.json"


def predict(model, dataloader):
    all_predictions = []
    all_labels = []

    for batch, labels in dataloader:

        # Forward pass
        predictions = model(batch)

        all_predictions.append(predictions)
        all_labels.append(labels)

    all_predictions = torch.cat(all_predictions)
    all_labels = torch.cat(all_labels)
    return all_predictions, all_labels


def calculate_metrics(preds, targets):
    # Ensure the predictions and targets are torch tensors
    if not isinstance(preds, torch.Tensor):
        preds = torch.tensor(preds)
    if not isinstance(targets, torch.Tensor):
        targets = torch.tensor(targets)

    # Threshold predictions to binary values (assuming binary classification
    # with threshold of 0.5)
    preds = (preds >= 0.5).float()

    # Calculate True Positives, False Positives, True Negatives, and False
    # Negatives
    TP = ((preds == 1) & (targets == 1)).sum().item()
    FP = ((preds == 1) & (targets == 0)).sum().item()
    TN = ((preds == 0) & (targets == 0)).sum().item()
    FN = ((preds == 0) & (targets == 1)).sum().item()

    # Calculate Accuracy
    accuracy = (TP + TN) / (TP + FP + TN + FN)

    # Calculate Precision, Recall, and F1 Score
    precision = TP / (TP + FP) if (TP + FP) > 0 else 0
    recall = TP / (TP + FN) if (TP + FN) > 0 else 0
    f1_score = (
        2 * (precision * recall) / (precision + recall)
        if (precision + recall) > 0
        else 0
    )

    # Confusion Matrix
    confusion_matrix = torch.tensor([[TN, FP], [FN, TP]])

    return {
        "True Positives": TP,
        "False Positives": FP,
        "True Negatives": TN,
        "False Negatives": FN,
        "Accuracy": accuracy,
        "Precision": precision,
        "Recall": recall,
        "F1 Score": f1_score,
        "Confusion Matrix": confusion_matrix,
    }


def train(
    model, train_dataloader, val_dataloader, optimizer, criterion, num_epochs
):
    for epoch in range(num_epochs):
        print(f"Epoch: {epoch+1}")
        model.train()
        for batch, labels in train_dataloader:

            # Forward pass
            predictions = model(batch)

            # Calculate loss
            loss = criterion(predictions, labels.view(-1, 1))

            # Backward pass and optimization
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

        model.eval()
        with torch.no_grad():
            train_predictions, train_labels = predict(model, train_dataloader)
            val_predictions, val_labels = predict(model, val_dataloader)
            val_metrics = calculate_metrics(
                val_predictions.flatten(), val_labels
            )
            train_metrics = calculate_metrics(
                train_predictions.flatten(), train_labels
            )
            print(f"val f1: {val_metrics["F1 Score"]}")
            print(f"train f1: {train_metrics["F1 Score"]}")


def main():
    train_files = [
        "../data/sbd_adjudicatory_dec/data_set/intellectual_property.json",
        "../data/sbd_adjudicatory_dec/data_set/bva.json",
        "../data/sbd_adjudicatory_dec/data_set/scotus.json",
    ]

    val_files = [
        "../data/sbd_adjudicatory_dec/data_set/cyber_crime.json",
    ]

    processed_train_data = data_prep.read_texts_from_json_files(train_files)
    processed_val_data = data_prep.read_texts_from_json_files(val_files)

    tokenizer = data_prep.prep_tokenizer(processed_train_data.texts)

    train_dataset = text_dataset.TextDataset(
        processed_train_data.texts, processed_train_data.ends, tokenizer
    )
    val_dataset = text_dataset.TextDataset(
        processed_val_data.texts, processed_val_data.ends, tokenizer
    )

    train_dataloader = DataLoader(train_dataset, batch_size=32, shuffle=True)
    val_dataloader = DataLoader(val_dataset, batch_size=1024, shuffle=False)

    model = cnn.CNNModel()
    optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
    criterion = torch.nn.BCELoss()

    train(
        model,
        train_dataloader,
        val_dataloader,
        optimizer,
        criterion,
        num_epochs=5,
    )

    Path("./artifacts").mkdir(exist_ok=True)

    torch.save(model.state_dict(), MODEL_SAVE_PATH)
    tokenizer.save(TOKENIZER_SAVE_PATH)


if __name__ == "__main__":
    main()
