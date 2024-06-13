resource "aws_dynamodb_table" "file_metadata" {
  name         = "file_metadata"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "file_id"

  attribute {
    name = "file_id"
    type = "S"
  }

  tags = var.tags
}
