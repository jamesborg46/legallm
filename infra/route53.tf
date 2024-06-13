data "aws_acm_certificate" "cert" {
  domain      = "legallm.online"
  statuses    = ["ISSUED"] // Ensure the certificate is issued
  most_recent = true       // Get the most recent issued certificate
}

data "aws_route53_zone" "main" {
  name = "legallm.online"
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

