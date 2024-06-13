# Legal Document Sentence Boundary Detection and Review

This project has two primary goals:
- Investigate and implement a sentence boundary detection model for legal documents.
- Host this model on a web application along with a review system such that a 
  client can upload a legal document, retrieve the sentences, and send them to
  a another endpoint for review.

Please note that this project is still in the early stages of development. As such,
the code and documentation may be incomplete or incorrect, and the quality is not
yet up to the standards of a production-ready application.

Once you have downloaded data for training and/or inference below, you can make
a POST request (requiring an a API token which can be provided on request) to
the endpoints currently hosted at https://legallm.online


# Downloading the Data
The SBD Adjudicatory decisions dataset, used for model training and evaluation,
as well as Contract Understanding Atticus Dataset (CUAD v1) which can be used
when running inference or testing the endpoints, can be downloaded with the 
following command:

`chmod +x ./scripts/install_data.sh && ./scripts/install_data.sh`

# Making an API request to hosted API endpoints

Upload and structuring the data can be performed with the following request.
Note that you will need to replace `<COPY YOUR API KEY HERE>` with the API key
and you should have downloaded the data as per the instructions above.

```
curl --location 'https://legallm.online/upload' \
--header 'Content-Type: application/octet-stream' \
--header 'x-api-key: <COPY YOUR API KEY HERE>' \
--data '@./data/CUAD_v1/full_contract_txt/ACCELERATEDTECHNOLOGIESHOLDINGCORP_04_24_2003-EX-10.13-JOINT VENTURE AGREEMENT.txt'
```

You should get a response like:
```
{
    "structured_text": [
        "EXHIBIT 10.13",
        "JOINT VENTURE AGREEMENT",
        "Collectible Concepts Group, Inc. (\"CCGI\") and Pivotal Self Service Tech, Inc. (\"PVSS\"), (the \"Parties\" or \"Joint Venturers\" if referred to collectively, or the \"Party\" or Joint Venturer\" if referred to singularly), by this Agreement associate themselves as business associates, and not as partners, in the formation of a joint venture (the \"Joint Venture\"), for the purpose of engaging generally in the business provided for by terms and provisions of this Agreement.",
        "1.",
        "Name of the Joint Venture.",
        "The name of the Joint Venture will be MightyCell      Batteries, and may sometimes be referred to as \"MightyCell\" or the \"Joint      Venture\" in this Agreement.",
        "The principal office and place of business      shall be located in 1600 Lower State Road, Doylestown, PA 18901.",
        "2.",
        "Scope of the Joint Venture Business.",
        "The Joint Venture is formed for the      purpose of engaging generally in the business of marketing batteries and      related products, (the \"Products\") that include the display of licensed      logos, images, brand names and other labels that differentiate them from      the branding (the \"PVSS Products\") under which PVSS and/or its affiliates,      sell to retailers and distributors in the normal course of their business.",
        "Without in any way limiting the generality of the foregoing, the business      of the Joint Venture shall include:",
        ...
        "GENERAL RESPONSIBILITIES OF THE PARTIES",
        "Collectible Concepts Group will:",
        "1)   Obtain any licenses deemed by the Joint Venturers to add value in the           marketing of the Products      2)   Prepare any artwork necessary for the reproduction of licensed or           branded images for the purpose of manufacturing the Products and / or           packaging      3)",
        "In concert with PVSS, appoint appropriate sales agents and / or           representatives and distributors to sell the Products into specific           retail channels      4)   Prepare marketing materials for sales agents', representatives' and           distributors' use in presentations to prospective clients      5)",
        "Engage in any support activities required to promote and sell the           Products      6)   Provide fulfillment services through affiliates for final distribution           of the Products",
        "Pivotal Self Service Tech, Inc. will:",
        "1)",
        "Provide the Products in accordance with the specifications and           quantities and time frames designated by CCGI      2)   Provision any additional Products deemed by the Joint Venturers to be           salable through the channels established by CCGI      3)",
        "Negotiate such favorable pricing and terms with the suppliers of the           Products so as to assure the viability of the Joint Venture offerings           and the continuity of Product availability to the customers of the           Joint Venture      4)   Provide alternate fulfillment and distribution services of the           Products as backup to those provided by CCGI"
    ],
    "file_id": "<FILE-ID>"
}
```

Make note of the file_id, as you will need it to make the next request.

You can then send a review request with the file_id, and the section of text
you would like reviewed. This text can be taken directly from one of the segments
of the structured text response above, or you can provide your own section of text
from the document.

Please note that you will need to replace `<COPY YOUR API KEY HERE>` with the API key
You will also need to replace the `<FILE-ID>` with the file_id you received in the
previous response.

```
curl --location 'https://legallm.online/review' \
--header 'x-api-key: <COPY YOUR API KEY HERE>' \
--header 'Content-Type: application/json' \
--data '{
    "id": "<FILE-ID>",
    "review": "Collectible Concepts Group, Inc. (\"CCGI\") and Pivotal Self Service Tech, Inc. (\"PVSS\"), (the \"Parties\" or \"Joint Venturers\" if referred to collectively, or the \"Party\" or Joint Venturer\" if referred to singularly), by this Agreement associate themselves as business associates, and not as partners, in the formation of a joint venture (the \"Joint Venture\"), for the purpose of engaging generally in the business provided for by terms and provisions of this Agreement."
}'
```

You should expect a response like:
```
{
    "issue_found": true,
    "reworded": "Collectible Concepts Group, Inc. (\"CCGI\") and Pivotal Self Service Tech, Inc. (\"PVSS\"), collectively referred to as the \"Parties\" or \"Joint Venturers\", or individually as a \"Party\" or \"Joint Venturer\", hereby enter into this Agreement to establish a joint venture (the \"Joint Venture\") for the purpose of engaging in the business activities as set forth in the terms and provisions of this Agreement. The Parties expressly agree that this Agreement does not create a partnership between them.",
    "feedback": "The original language could potentially be interpreted as creating a partnership between the parties, which may have unintended legal and tax consequences. The suggested rewording clarifies that the parties are entering into a joint venture agreement, not a partnership agreement, while retaining the key points. It's important to clearly state the nature of the business relationship to avoid ambiguity.",
    "severity": "medium"
}
```

Please note that both these requests can take a moment to process, typically on the order of 10s of seconds.

# R&D and Model Evaluation of Sentence Boundary Detection Methods

In `notebooks/` you will find a number of Jupyter notebooks that were used to
explore and evaluate different sentence boundary detection methods.

These investigations were inspired by the following paper:

Sheik, Reshma & Adethya T, Gokul & Nirmala, Jaya. (2022). Efficient Deep Learning-based Sentence Boundary Detection in Legal Text. 208-217. 10.18653/v1/2022.nllp-1.18. 
[Link to paper](https://aclanthology.org/2022.nllp-1.18.pdf)


These include:
- `pySBD baseline.ipynb`: A simple baseline using the `pySBD` library
- `LLM test (ChatGPT).ipynb`: Testing the `gpt-4o` model for sentence boundary detection
- `CNN Test.ipynb`: Testing a simple CNN model for sentence boundary detection

## Our Findings

We evaluate the models on the F1 score achieved when predicting if a token/character
is the end of the sentence. We preprocess the data to select a subset of tokens
to propose as potential sentence boundaries where those tokens/characters match
a particular set of delimiter characters such as ".", "!", "]" etc. or if they
are a ground truth sentence boundary.

| Model                |  F1 Score |
|----------------------|----------:|
| pySBD baseline       |     0.838 |
| LLM (ChatGPT gpt-4o) |    0.728* |
| CNN                  | **0.945** |

\*Note: The LLM model was evaluated only on a single text from the document due
to the runtime constraints of the model. 

Whilst our implementation of the CNN is based off the above paper, there are also
some differences. In particular we use byte pair encoding (BPE) tokenization.

Other findings:
- pySBD was the simplest to use as it was a prepackaged python library with inbuilt
  sentence boundary detection.
- The LLM model underperformed both in terms of F1 score, runtime/cost. Perhaps
  with better prompt engineering better performance could be achieved.
- As suggested in the above paper, we found the CNN model to be the most effective
  of the methods tested. It achieved the highest F1 score and was quick to train
  and perform inference with.

# Training the CNN model

Training and inference code for the CNN model has been prepared in the `model/`
directory and can be run from the `model/` directory with the following commands:

```
cd model
make setup
source env/bin/activate
python ./training/train.py
```

A trained version of this model has been uploaded to AWS SageMaker, and is powering
the sentence boundary detection occurring at the endpoint at https://legallm.online/upload
