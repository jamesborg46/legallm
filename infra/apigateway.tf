resource "aws_api_gateway_rest_api" "legallm_api" {
  name        = "legallm_api"
  description = "API for uploading and reviewing legal contract files"

  tags = var.tags
}

resource "aws_api_gateway_resource" "gateway_resources" {
  for_each    = var.endpoints
  rest_api_id = aws_api_gateway_rest_api.legallm_api.id
  parent_id   = aws_api_gateway_rest_api.legallm_api.root_resource_id
  path_part   = each.value.path
}

resource "aws_api_gateway_method" "gateway_methods" {
  for_each      = var.endpoints
  rest_api_id   = aws_api_gateway_rest_api.legallm_api.id
  resource_id   = aws_api_gateway_resource.gateway_resources[each.key].id
  http_method   = each.value.method
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "gateway_integrations" {
  for_each                = var.endpoints
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
  tags        = var.tags
}

resource "aws_api_gateway_domain_name" "custom_domain" {
  domain_name              = "legallm.online"
  regional_certificate_arn = data.aws_acm_certificate.cert.arn # Provide the ARN of your ACM certificate

  endpoint_configuration {
    types = ["REGIONAL"]
  }

  tags = var.tags
}

resource "aws_api_gateway_base_path_mapping" "path_mapping" {
  api_id      = aws_api_gateway_rest_api.legallm_api.id
  stage_name  = aws_api_gateway_stage.file_upload_stage.stage_name
  domain_name = aws_api_gateway_domain_name.custom_domain.domain_name
  base_path   = "" # Leave it empty for the root path
}
