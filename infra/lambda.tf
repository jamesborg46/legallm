resource "aws_lambda_function" "lambda_functions" {
  for_each      = var.endpoints
  filename      = each.value.package_file
  function_name = each.value.function_name
  role          = aws_iam_role.lambda_role.arn
  handler       = "lambda_function.lambda_handler"
  runtime       = "python3.12"
  timeout       = 120
  memory_size   = 128

  source_code_hash = filebase64sha256(each.value.package_file)

  environment {
    variables = {
      S3_BUCKET      = aws_s3_bucket.file_upload_bucket.bucket
      DYNAMODB_FILE_TABLE = aws_dynamodb_table.file_metadata.name
      MODEL_ENDPOINT_NAME = "legallm-model-endpoint"
    }
  }

  tags = var.tags
}

resource "aws_lambda_permission" "apigw_lambda" {
  for_each      = var.endpoints
  statement_id  = "AllowAPIGatewayInvoke-${each.key}"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.lambda_functions[each.key].function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.legallm_api.execution_arn}/*/*"
}
