import json
from typing import Any, NamedTuple

from tokenizers import Regex, Tokenizer, models, pre_tokenizers, trainers
from tokenizers.models import BPE
from tokenizers.pre_tokenizers import Punctuation, Sequence, Split
from tokenizers.trainers import BpeTrainer

TEXT = "text"
ANNOTATIONS = "annotations"
END = "end"


class ProcessedData(NamedTuple):
    texts: tuple[str, ...]
    ends: tuple[tuple[int, ...], ...]


def process_data(
    data: [dict[str, Any]]
) -> tuple[list[str], list[tuple[int, ...]]]:
    """
    Process the data to extract texts and their corresponding sentence ends.

    Args:
        data: A list of dictionaries containing text and annotations.

    Returns:
        A tuple containing a list of texts and a list of tuples with sentence
        ends.
    """
    texts = []
    all_ends = []

    for key in data:
        text: str = data[key][TEXT]
        texts.append(text)
        sentence_ends = extract_ends(data[key][ANNOTATIONS])
        all_ends.append(sentence_ends)

    return texts, all_ends


def extract_ends(annotations: list[dict[str, int]]) -> tuple[int, ...]:
    """
    Extract sentence ends from a list of annotations.

    Args:
        annotations: A list of dictionaries containing annotation information.

    Returns:
        A tuple with sorted sentence ends.
    """
    sentence_ends = set()
    for annotation in annotations:
        sentence_ends.add(annotation[END])
    return tuple(sorted(sentence_ends))


def read_texts_from_json_files(file_paths: list[str]) -> ProcessedData:
    """
    Read texts from JSON files and process the data.

    Args:
        file_paths: A list of file paths to JSON files.

    Returns:
        ProcessedData object containing texts and sentence ends.
    """
    all_texts = []
    all_ends = []
    for file_path in file_paths:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            texts, ends = process_data(data)
            all_texts += texts
            all_ends += ends

    processed_data = ProcessedData(
        texts=tuple(all_texts), ends=tuple(all_ends)
    )
    return processed_data


def prep_tokenizer(texts: tuple[str, ...], vocab_size=300) -> Tokenizer:
    """
    Prepare a tokenizer for the given texts.

    Args:
        texts: A tuple of texts to train the tokenizer.
        vocab_size: The vocabulary size for the tokenizer.

    Returns:
        A Tokenizer object ready for tokenization.
    """
    tokenizer = Tokenizer(BPE(unk_token="[UNK]"))
    trainer = BpeTrainer(
        vocab_size=vocab_size, special_tokens=["[UNK]", "[PAD]"]
    )
    # Define the sequence of pre-tokenizers
    tokenizer.pre_tokenizer = Sequence(
        [
            Split(pattern="\n", behavior="isolated"),
            # Like the Whitespace() pre_tokenizer, but ignores newline "\n"
            # characters, as we want to tokenize these,
            Split(
                pattern=Regex(r"\w+|[^\w\t ]+"),
                behavior="removed",
                invert=True,
            ),
            Punctuation(),
        ]
    )

    tokenizer.train_from_iterator(texts, trainer=trainer)
    return tokenizer


if __name__ == "__main__":
    file_paths = [
        "../data/sbd_adjudicatory_dec/data_set/intellectual_property.json",
        "../data/sbd_adjudicatory_dec/data_set/scotus.json",
    ]

    processed_data = read_texts_from_json_files(file_paths)
    tokenizer = prep_tokenizer(processed_data.texts)

    print(processed_data.texts[0][:100])
    print(sorted(list(processed_data.ends[0]))[:10])
    print(tokenizer.encode(processed_data.texts[0]).tokens[:10])
