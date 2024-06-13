import json

import numpy as np
import torch
from flask import Flask, jsonify, request
from tokenizers import Tokenizer

import text_dataset
from cnn import CNNModel

app = Flask(__name__)

model = CNNModel()
model.load_state_dict(torch.load("/opt/ml/model/model.pt"))
tokenizer = Tokenizer.from_file("/opt/ml/model/tokenizer.json")


def _extract_contexts(
    encoded_text,
    target_tokens=None,
    context_size=6,
):
    """
    Extract context windows and labels.

    Args:
        encoded_texts (list): List of encoded texts.
        labels (list): List of labels.
        target_tokens (list): List of target tokens to consider for
            context extraction.
        context_size (int): Size of the context window.

    Returns:
        tuple: A tuple containing window IDs and window labels.
    """
    if target_tokens is None:
        target_tokens = [".", '"', "]", ")", ":", '"', "'", "*", ">", ";"]

    window_ids = []
    token_idxes = []

    tokens = encoded_text.tokens
    num_tokens = len(tokens)
    for i in range(num_tokens):
        token = tokens[i]
        if (token in target_tokens) or text_dataset._is_end_of_line(tokens, i):
            start = max(0, i - context_size)
            end = min(len(encoded_text), i + context_size + 1)
            window_ids.append(encoded_text.ids[start:end])
            token_idxes.append(i)

    return window_ids, token_idxes


@app.route("/ping", methods=["GET"])
def ping():
    health = isinstance(model, CNNModel) & isinstance(tokenizer, Tokenizer)
    status = 200 if health else 404
    return "", status


@app.route("/invocations", methods=["POST"])
def predict():
    text_data = request.get_data()
    if type(text_data) is bytes:
        text_data = text_data.decode("utf-8")

    pad_id = tokenizer.token_to_id("[PAD]")
    encoded = tokenizer.encode(text_data)
    encoded.pad(len(encoded) + 6, direction="left", pad_id=pad_id)
    encoded.pad(len(encoded) + 6, direction="right", pad_id=pad_id)

    contexts, token_idxes = _extract_contexts(encoded)
    contexts = torch.tensor(contexts, dtype=torch.int32, device="cpu")

    with torch.no_grad():
        prediction = (model(contexts) > 0.5).flatten()

    end_token_idxes = np.array(token_idxes)[prediction]

    ends = np.array(encoded.offsets)[:, 1][end_token_idxes].tolist()

    segments = [text_data[:ends[0]]] + [
        text_data[ends[i] : ends[i + 1]].strip() for i in range(len(ends) - 1)
    ]

    return jsonify({"segments": segments, "ends": ends})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
