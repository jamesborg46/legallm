resource "aws_s3_bucket" "file_upload_bucket" {
  bucket = "legal-contract-review-files"

  tags = var.tags
}
