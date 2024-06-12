provider "aws" {
  region = "ap-northeast-1"
}

locals {
  service_name = "upload"
  tags = {
    Service     = local.service_name
    Environment = "dev" // Adjust as necessary
  }
  endpoints = {
    upload = {
      path = "upload"
      method = "POST"
      function_name = "file_upload_function"
      package_file = "../api/upload/my_deployment_package.zip"
    },
    review = {
      path = "review"
      method = "POST"
      function_name = "review_function"
      package_file = "../api/review/my_deployment_package.zip"
    }
  }
}

resource "aws_s3_bucket" "file_upload_bucket" {
  bucket = "legal-contract-review-files"

  tags = local.tags
}

resource "aws_dynamodb_table" "file_metadata" {
  name         = "file_metadata"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "file_id"

  attribute {
    name = "file_id"
    type = "S"
  }

  tags = local.tags
}

resource "aws_iam_role" "lambda_role" {
  name = "lambda_role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      },
    ]
  })

  managed_policy_arns = [
    "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole",
    "arn:aws:iam::aws:policy/AmazonS3FullAccess",
    "arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess",
    "arn:aws:iam::aws:policy/AmazonBedrockFullAccess",
  ]

  tags = local.tags
}

resource "aws_lambda_function" "lambda_functions" {
  for_each      = local.endpoints
  filename      = each.value.package_file
  function_name = each.value.function_name
  role          = aws_iam_role.lambda_role.arn
  handler       = "lambda_function.lambda_handler"
  runtime       = "python3.12"
  timeout       = 60
  memory_size   = 128

  source_code_hash = filebase64sha256(each.value.package_file)

  environment {
    variables = {
      S3_BUCKET      = aws_s3_bucket.file_upload_bucket.bucket
      DYNAMODB_FILE_TABLE = aws_dynamodb_table.file_metadata.name
    }
  }

  tags = local.tags
}

resource "aws_lambda_permission" "apigw_lambda" {
  for_each      = local.endpoints
  statement_id  = "AllowAPIGatewayInvoke-${each.key}"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.lambda_functions[each.key].function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.legallm_api.execution_arn}/*/*"
}

resource "aws_api_gateway_rest_api" "legallm_api" {
  name        = "legallm_api"
  description = "API for uploading and reviewing legal contract files"

  tags = local.tags
}

resource "aws_api_gateway_resource" "gateway_resources" {
  for_each    = local.endpoints
  rest_api_id = aws_api_gateway_rest_api.legallm_api.id
  parent_id   = aws_api_gateway_rest_api.legallm_api.root_resource_id
  path_part   = each.value.path
}

resource "aws_api_gateway_method" "gateway_methods" {
  for_each      = local.endpoints
  rest_api_id   = aws_api_gateway_rest_api.legallm_api.id
  resource_id   = aws_api_gateway_resource.gateway_resources[each.key].id
  http_method   = each.value.method
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "gateway_integrations" {
  for_each                = local.endpoints
  rest_api_id             = aws_api_gateway_rest_api.legallm_api.id
  resource_id             = aws_api_gateway_resource.gateway_resources[each.key].id
  http_method             = aws_api_gateway_method.gateway_methods[each.key].http_method
  type                    = "AWS_PROXY"
  integration_http_method = each.value.method
  uri                     = aws_lambda_function.lambda_functions[each.key].invoke_arn
}

resource "aws_api_gateway_deployment" "legallm_deployment" {
  rest_api_id = aws_api_gateway_rest_api.legallm_api.id

  lifecycle {
    create_before_destroy = true
  }

  depends_on = [
    aws_api_gateway_integration.gateway_integrations,
    aws_api_gateway_method.gateway_methods
  ]

  description = "Deployment for upload service"
}

resource "aws_api_gateway_stage" "file_upload_stage" {
  stage_name    = "dev"
  rest_api_id   = aws_api_gateway_rest_api.legallm_api.id
  deployment_id = aws_api_gateway_deployment.legallm_deployment.id

  description = "Development stage for upload API"
  tags        = local.tags
}

data "aws_acm_certificate" "cert" {
  domain      = "legallm.online"
  statuses    = ["ISSUED"] // Ensure the certificate is issued
  most_recent = true       // Get the most recent issued certificate
}

data "aws_route53_zone" "main" {
  name = "legallm.online"
}

resource "aws_api_gateway_domain_name" "custom_domain" {
  domain_name              = "legallm.online"
  regional_certificate_arn = data.aws_acm_certificate.cert.arn # Provide the ARN of your ACM certificate

  endpoint_configuration {
    types = ["REGIONAL"]
  }

  tags = local.tags
}

resource "aws_api_gateway_base_path_mapping" "path_mapping" {
  api_id      = aws_api_gateway_rest_api.legallm_api.id
  stage_name  = aws_api_gateway_stage.file_upload_stage.stage_name
  domain_name = aws_api_gateway_domain_name.custom_domain.domain_name
  base_path   = "" # Leave it empty for the root path
}

resource "aws_route53_record" "apigw_alias" {
  zone_id = data.aws_route53_zone.main.zone_id
  name    = aws_api_gateway_domain_name.custom_domain.domain_name
  type    = "A"

  alias {
    name                   = aws_api_gateway_domain_name.custom_domain.regional_domain_name
    zone_id                = aws_api_gateway_domain_name.custom_domain.regional_zone_id
    evaluate_target_health = false
  }
}

