locals {
  function_name = "${var.resource_prefix}-webcrawler"
}

# Archive a source code to be used with Lambda using consistent file mode
data "archive_file" "lambda_sourcecode" {
  type             = "zip"
  source_file      = "${path.module}/src/function/index.py"
  output_file_mode = "0666"
  output_path      = "${path.module}/files/lambda_sourcecode.zip"
}

# Archive a source code to be used as a Lambda Layer using consistent file mode
data "archive_file" "lambda_layer" {
  type             = "zip"
  source_dir       = "${path.module}/src/layer/"
  output_file_mode = "0666"
  output_path      = "${path.module}/files/lambda_layer.zip"
}

module "lambda_function_externally_managed_package" {
  source  = "terraform-aws-modules/lambda/aws"
  version = "7.2.1"

  function_name = local.function_name
  description   = "My lambda function code is deployed separately"
  handler       = "index.lambda_handler"
  runtime       = "python3.11"

  create_package         = false
  local_existing_package = "${path.module}/files/lambda_sourcecode.zip"

  ignore_source_code_hash = true

  layers = [
    module.lambda_layer_local.lambda_layer_arn
  ]

  # environment_variables = {
  #   Hello      = "World"
  #   Serverless = "Terraform"
  # }

  attach_policy_json     = true
  policy_json            = <<-EOT
    {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "dynamodb:*",
                    "sns:*"
                ],
                "Resource": ["*"]
            }
        ]
    }
  EOT
  number_of_policy_jsons = 1

  tags = {
    Foo = "Bar"
  }
}

module "lambda_layer_local" {
  source  = "terraform-aws-modules/lambda/aws"
  version = "7.2.1"

  create_layer = true

  layer_name               = "${var.resource_prefix}-layer-local"
  description              = "My amazing lambda layer (deployed from local)"
  compatible_runtimes      = ["python3.11"]
  compatible_architectures = ["x86_64"]

  source_path = "${path.module}/files/lambda_layer.zip"
}