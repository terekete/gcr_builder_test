
resource "google_storage_bucket" "diff_bucket" {
  project                     = var.project_id
  name                        = format("rc-diffs-%s", var.project_id)
  uniform_bucket_level_access = true
  location                    = var.region
}