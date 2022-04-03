terraform {
  required_providers {
    random = {
      source  = "hashicorp/random"
      version = ">=3.0.0"

    }
    google = {
      source  = "hashicorp/google"
      version = ">=3.61.0"

    }
    google-beta = {
      source  = "hashicorp/google-beta"
      version = ">=3.61.0"

    }
  }
}