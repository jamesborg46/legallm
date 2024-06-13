import torch
from torch.utils.data import DataLoader, Dataset


class TextDataset(Dataset):
    def __init__(self, texts, ends, tokenizer, padding=6, device="cpu"):
        """
        Initialize the TextDataset with texts, ends, tokenizer, padding, and
        device.

        Args:
            texts (list): List of texts to be encoded.
            ends (list): List of end positions for labels.
            tokenizer (object): Tokenizer to encode the texts.
            padding (int): Padding size for the encoded texts.
            device (str): Device to be used for torch tensors.
        """
        self.texts = texts
        self.ends = ends
        self.tokenizer = tokenizer
        self.device = device
        self.encoded_texts, self.labels = self._encode(
            texts, ends, tokenizer, padding
        )
        self.window_ids, self.windows_labels = self._extract_contexts(
            self.encoded_texts, self.labels
        )

    def _encode(self, train_texts, ends, tokenizer, padding):
        """
        Encode the texts and generate labels.

        Args:
            train_texts (list): List of texts to be encoded.
            ends (list): List of end positions for labels.
            tokenizer (object): Tokenizer to encode the texts.
            padding (int): Padding size for the encoded texts.

        Returns:
            tuple: A tuple containing encoded texts and labels.
        """
        encoded_texts = []
        labels = []
        pad_id = tokenizer.token_to_id("[PAD]")

        for i, text in enumerate(train_texts):
            encoded = tokenizer.encode(text)
            self._pad_encoded_text(encoded, padding, pad_id)
            encoded_texts.append(encoded)
            _, labeled_tokens = _label_tokens(encoded.offsets, ends[i])
            labels.append(labeled_tokens)

        return encoded_texts, labels

    def _pad_encoded_text(self, encoded, padding, pad_id):
        """
        Pad the encoded text on both sides.

        Args:
            encoded (object): Encoded text object.
            padding (int): Padding size for the encoded texts.
            pad_id (int): Pad token ID.
        """
        encoded.pad(len(encoded) + padding, direction="left", pad_id=pad_id)
        encoded.pad(len(encoded) + padding, direction="right", pad_id=pad_id)

    def _extract_contexts(
        self,
        encoded_texts,
        labels,
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
        window_labels = []

        for i, encoded_text in enumerate(encoded_texts):
            tokens = encoded_text.tokens
            num_tokens = len(tokens)
            for j in range(num_tokens):
                token = tokens[j]
                if (
                    (token in target_tokens)
                    or _is_end_of_line(tokens, j)
                    or labels[i][j]
                ):
                    start = max(0, j - context_size)
                    end = min(len(encoded_text), j + context_size + 1)
                    window_ids.append(encoded_text.ids[start:end])
                    window_labels.append(labels[i][j])

        return window_ids, window_labels

    def __len__(self):
        """Return the number of items in the dataset."""
        return len(self.window_ids)

    def __getitem__(self, idx):
        """
        Get the item at the specified index.

        Args:
            idx (int): Index of the item to be retrieved.

        Returns:
            tuple: A tuple containing window IDs and the corresponding label.
        """
        window_ids = torch.tensor(
            self.window_ids[idx], dtype=torch.int32, device=self.device
        )
        label = torch.tensor(
            self.windows_labels[idx], dtype=torch.float32, device=self.device
        )
        return window_ids, label


def _is_end_of_line(tokens, i):
    """
    Check if the current token is the end of a line.

    Args:
        tokens (list): List of tokens.
        i (int): Current index.

    Returns:
        bool: True if the current token is the end of a line, False
        otherwise.
    """
    num_tokens = len(tokens)
    if i >= num_tokens:
        raise ValueError("Index out of range")
    return (
        (i < (num_tokens - 1))
        and (tokens[i] != "\n")
        and (tokens[i + 1] == "\n")
    )


def _label_tokens(offsets, ends):
    ends_idx = 0
    labels = []
    encoded_end_idxes = []

    for offsets_idx, offset in enumerate(offsets):
        left, right = offset
        if (ends_idx < len(ends)) and (left <= (ends[ends_idx] - 1) < right):
            labels.append(True)
            encoded_end_idxes.append(offsets_idx)
            ends_idx += 1
        else:
            labels.append(False)

    return encoded_end_idxes, labels


if __name__ == "__main__":
    import data_prep

    file_paths = [
        "../data/sbd_adjudicatory_dec/data_set/intellectual_property.json",
        "../data/sbd_adjudicatory_dec/data_set/scotus.json",
    ]

    processed_data = data_prep.read_texts_from_json_files(file_paths)
    tokenizer = data_prep.prep_tokenizer(processed_data.texts)
    dataset = TextDataset(
        processed_data.texts[:3], processed_data.ends[:3], tokenizer
    )
    dataloader = DataLoader(dataset, batch_size=2, shuffle=True)
    batch, labels = next(iter(dataloader))
    print(batch)
    print(labels)
