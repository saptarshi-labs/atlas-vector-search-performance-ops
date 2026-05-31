variable "location" {
  description = "Azure region to deploy"
  type = string
}

variable "vm_size" {
  description = "Azure VM Size"
  type = string
}

variable "my_ip" {
  description = "Source IP allowed to SSH to the VM"
  type = string
}

variable "ssh_public_key" {
  description = "Key file for SSH"
  type = string
}

variable "vm_name" {
  description = "Name of the Azure VM."
  type = string
}

variable "vm_admin_username" {
  description = "Admin username for the Azure VM."
  type = string
}