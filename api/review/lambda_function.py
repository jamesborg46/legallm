import base64
import json
import logging
import os
import uuid

import boto3

logger = logging.getLogger()

bedrock_client = boto3.client("bedrock-runtime", region_name="us-west-2")
s3_client = boto3.client("s3")
dynamodb_client = boto3.client("dynamodb")

SYSTEM_PROMPT = """
You are an experienced lawyer, your task is to meticulously review contracts currently being drafted. Your intended audience is business people, who may not have extensive legal knowledge., and the contracts you are reviewing are standalone agreements between the parties. Your goal is to identify any legal issues that could potentially affect your client’s legal rights or obligations such as language in the contract which does not meet the standard or requirement of the party you represent. These issues could be points of contention, ambiguities, potential risks, or compliance matters that could lead to a dispute or liability. You will first be provided with the full contract for context. You will subsequently be presented with smaller sections of the contract, which you should provide feedback on. Your feedback should be strictly formatted as a JSON object as follows:
{
    “issue_found”: <bool>,
    “reworded”: <str>,
    “feedback”: <str>,
}
Where issue_found indicates if there is any issue with the language. When there is no issue, reworded and feedback can be left as empty or as null. When an issue is found, “reworded” should provide the suggested rewording, and “feedback” should provide the reasoning behind the suggestion.
"""


def lambda_handler(event, context):
    try:
        # Add logging for incoming event
        print("Received event:", json.dumps(event))

        body = json.loads(event["body"])
        # Get the file ID from the query parameters
        file_id = body["id"]
        review_query = body["review"]
        print(f"Processing file ID: {file_id}")
        print(f"Review query: {review_query}")

        # Fetch metadata from DynamoDB
        file_table = os.environ["DYNAMODB_FILE_TABLE"]
        response = dynamodb_client.get_item(
            TableName=file_table, Key={"file_id": {"S": file_id}}
        )

        if "Item" not in response:
            raise ValueError("File metadata not found")

        metadata = response["Item"]
        s3_bucket = os.environ["S3_BUCKET"]
        original_key = metadata["original_file"]["S"]

        # Fetch the original text file from S3
        s3_response = s3_client.get_object(Bucket=s3_bucket, Key=original_key)
        original_text = s3_response["Body"].read().decode("utf-8")
        print(original_text[:100])

        initial_prompt = f"""
        I will first provide you with the full contract for context. Please
        acknowledge only with a yes or no it you would like to proceed.
        The next message will contain a section from the contract for review.
        Please provide your feedback in json format.

        The full contract is as follows:
        --------------------------------
        {original_text}
        """

        review_prompt = f"""
        I will now provide you with a section from the contract for review.
        --------------------------------
        {review_query}
        """

        request = {
            "modelId": "anthropic.claude-3-opus-20240229-v1:0",
            "contentType": "application/json",
            "accept": "application/json",
            "body": json.dumps(
                {
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 1000,
                    "system": SYSTEM_PROMPT,
                    "messages": [
                        {"role": "user", "content": initial_prompt},
                        {"role": "assistant", "content": "yes"},
                        {"role": "user", "content": review_prompt},
                    ],
                }
            ),
        }

        s3_bucket = os.environ["S3_BUCKET"]
        dynamodb_table = os.environ["DYNAMODB_FILE_TABLE"]

        resp = bedrock_client.invoke_model(**request)
        resp_json = json.loads(resp["body"].read())

        print("Hello")
        return {
            "statusCode": 200,
            "body": json.dumps(resp_json),
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps(f"Error processing file: {str(e)}"),
        }
