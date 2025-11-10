terraform {
  backend "s3" {
    bucket         = "pharma-tfstate-eu"
    key            = "pharma-test-gen/terraform.tfstate"
    region         = "eu-west-2"
    dynamodb_table = "terraform-locks"
    encrypt        = true
  }
}
