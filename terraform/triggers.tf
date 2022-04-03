resource "google_cloudbuild_trigger" "image_pull_request" {
  provider = google-beta
  project  = var.project_id
  name     = "build-image-rc"
  filename = "cloudbuild/build.yaml"

  substitutions = {
    _DIFF_BUCKET              = google_storage_bucket.diff_bucket.name
    _CONTAINER_IMAGE_REGISTRY = var.container_image_registry
    _BASE_BRANCH              = var.base_branch
  }

  github {
    owner = "terekete"
    name  = "gcr_builder_test"
    pull_request {
      branch = "^${var.base_branch}$"
    }
  }
}

resource "google_cloudbuild_trigger" "image_push" {
  provider = google-beta
  project  = var.project_id
  name     = "release-image"
  filename = "cloudbuild/release.yaml"

  substitutions = {
    _DIFF_BUCKET              = google_storage_bucket.diff_bucket.name
    _CONTAINER_IMAGE_REGISTRY = var.container_image_registry
  }

  github {
    owner = "terekete"
    name  = "gcr_builder_test"
    push {
      branch = "^${var.base_branch}$"
    }
  }
}
