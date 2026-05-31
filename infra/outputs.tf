output "vm_public_ip" {
  description = "Public IP of the VM"
  value = azurerm_public_ip.main.ip_address
}

output "vm_dns_name" {
  description = "DNS name of the VM"
  value = azurerm_public_ip.main.fqdn
}

output "ssh_command" {
  description = "SSH command to connect to the VM"
  value = "ssh -i ~/.ssh/azure_vector_key ${var.vm_admin_username}@${azurerm_public_ip.main.fqdn}"
}