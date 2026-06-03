# Provisions an Atlas project, M10 cluster, database user, and a network access entry.

terraform {
  required_version = ">= 1.5"

  required_providers {
    mongodbatlas = {
      source = "mongodb/mongodbatlas"
      version = "~> 1.20"
    }
  }
}

# Authenticates with an Atlas Organization-level API key
provider "mongodbatlas" {
  public_key = var.atlas_public_key
  private_key = var.atlas_private_key
}

# The Atlas project, created by Terraform inside the organization
resource "mongodbatlas_project" "main" {
  name = var.project_name
  org_id = var.atlas_org_id
}

# The M10 dedicated cluster inside the Terraform-managed project
resource "mongodbatlas_advanced_cluster" "m10" {
  project_id = mongodbatlas_project.main.id
  name = var.cluster_name
  cluster_type = "REPLICASET"

  mongo_db_major_version = "8.1"

  replication_specs {
    region_configs {
      provider_name = "AWS"
      region_name = "AP_SOUTH_1"
      priority = 7

      electable_specs {
        instance_size = "M10"
        node_count = 3
      }
    }
  }
}

# Database user for connecting to the cluster.
resource "mongodbatlas_database_user" "user" {
  project_id = mongodbatlas_project.main.id
  username = var.db_username
  password = var.db_password
  auth_database_name = "admin"

  roles {
    role_name = "atlasAdmin"
    database_name = "admin"
  }
}

# Network access: allow the workstation's public IP to reach the cluster
resource "mongodbatlas_project_ip_access_list" "workstation" {
  project_id = mongodbatlas_project.main.id
  ip_address = var.allowed_ip
  comment = "workstation access"
}