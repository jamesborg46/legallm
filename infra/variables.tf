variable "region" {
  default = "ap-northeast-1"
}

variable "service_name" {
  default = "legallm"
}

variable "environment" {
  default = "dev"
}

variable "tags" {
  default = {
    Service     = "legallm"
    Environment = "dev" // Adjust as necessary
  }
}

variable "endpoints" {
  type = map(object({
    path          = string
    method        = string
    function_name = string
    package_file  = string
  }))
  default = {
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

variable "domain_name" {
  default = "legallm.online"
}

variable "model_endpoint_name" {
  default = "legallm-model-endpoint"
}
