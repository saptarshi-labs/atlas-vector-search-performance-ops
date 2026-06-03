# Outputs.

output "project_id" {
  description = "ID of the Atlas project created by Terraform."
  value = mongodbatlas_project.main.id
}

output "project_name" {
  description = "Name of the Atlas project created by Terraform."
  value = mongodbatlas_project.main.name
}

output "cluster_name" {
  description = "Name of the provisioned M10 cluster."
  value = mongodbatlas_advanced_cluster.m10.name
}

output "mongodb_version" {
  description = "MongoDB version running on the cluster."
  value = mongodbatlas_advanced_cluster.m10.mongo_db_major_version
}

output "connection_strings" {
  description = "Connection strings for the cluster."
  value = mongodbatlas_advanced_cluster.m10.connection_strings
  sensitive = true
}