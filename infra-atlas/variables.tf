# Input variables for the Atlas infrastructure.

variable "atlas_public_key" {
  description = "Public key of the Atlas organization-level API key pair."
  type = string
}

variable "atlas_private_key" {
  description = "Private key of the Atlas organization-level API key pair."
  type = string
  sensitive = true
}

variable "atlas_org_id" {
  description = "ID of the Atlas organization where the project will be created."
  type = string
}

variable "project_name" {
  description = "Name for the new Atlas project, created by Terraform."
  type = string
}

variable "cluster_name" {
  description = "Name for the M10 cluster."
  type = string
}

variable "db_username" {
  description = "Username for the cluster database user."
  type = string
}

variable "db_password" {
  description = "Password for the cluster database user."
  type = string
  sensitive = true
}

variable "allowed_ip" {
  description = "Public IP allowed to reach the cluster."
  type = string
}