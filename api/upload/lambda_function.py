import base64
import json
import logging
import os
import uuid

import boto3
import nltk
from nltk.tokenize.punkt import PunktSentenceTokenizer

logger = logging.getLogger()

s3_client = boto3.client("s3")
dynamodb_client = boto3.client("dynamodb")


def segment_text(text):
    # Load the `punkt` tokenizer model
    pst = PunktSentenceTokenizer()

    # Split the text by new lines
    lines = text.splitlines()

    # Tokenize within each split
    sentences = []
    for line in lines:
        line = line.strip()
        if line:
            sentences.extend(pst.tokenize(line))

    return sentences


def lambda_handler(event, context):
    try:
        # Extracting data from the event
        body = event.get("body", None)

        if body is None:
            raise ValueError("The body is None, cannot process the file.")
        # Decode base64 if necessary
        is_base64_encoded = event.get("isBase64Encoded", False)
        if is_base64_encoded:
            file_content = base64.b64decode(body)
        else:
            file_content = body

        logger.info(f"Received file with {len(file_content)} characters.")

        # Generate a unique file ID
        file_id = str(uuid.uuid4())

        # Define S3 bucket and file name
        s3_bucket = os.environ["S3_BUCKET"]
        orig_key = f"uploads/{file_id}.txt"
        structured_key = f"processed/{file_id}.json"

        # Save the original text file to S3
        s3_client.put_object(Bucket=s3_bucket, Key=orig_key, Body=file_content)

        segmented_text = segment_text(file_content)
        segmented_json = json.dumps(segmented_text)

        logger.info(f"Segmented text into {len(segmented_text)} sentences.")
        logger.info(f"First three sentences: {segmented_text[:3]}")

        # Save the structured json file to S3
        s3_client.put_object(
            Bucket=s3_bucket, Key=structured_key, Body=segmented_json
        )

        # Add an entry to DynamoDB
        dynamodb_table = os.environ["DYNAMODB_FILE_TABLE"]
        dynamo_entry = {
            "file_id": {"S": file_id},
            "original_file": {"S": orig_key},
            "structured_file": {"S": structured_key},
        }
        dynamodb_client.put_item(
            TableName=dynamodb_table,
            Item=dynamo_entry,
        )
        logger.debug(f"Added entry to DynamoDB: {dynamo_entry}")

        return {
            "statusCode": 200,
            "body": json.dumps(
                {"structured_text": segmented_json, "file_id": file_id}
            ),
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps(f"Error processing file: {str(e)}"),
        }


if __name__ == "__main__":
    text = "This is a test. This is a test. This is a test."
    segmented = segment_text(text)
    print(json.dumps(segmented, indent=2))
