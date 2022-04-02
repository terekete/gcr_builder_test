variable "region" {
  type    = string
  default = "northamerica-northeast1"
}
variable "project_id" {
  type    = string
  default = "bi-stg-pineapple-345822"
}
variable "project_name" {
  type    = string
  default = "bi-stg-pineapple"
}
variable "project_number" {
  type    = string
  default = "193169332843"
}
variable "env" {
  type    = string
  default = "np"
}
variable "build_diff_file_bucket" {
  type    = string
  default = "bi-stg-pineapple-345822-cb-diff"
}
variable "container_image_registry" {
  type    = string
  default = "gcr.io/bi-stg-pineapple-345822/bilayer"
}
variable "base_branch" {
  type    = string
  default = "main"
}