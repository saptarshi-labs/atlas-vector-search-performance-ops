terraform {
  required_version = ">= 1.5"
  required_providers {
    azurerm = {
      source = "hashicorp/azurerm"
      version = "~> 4.0"
    }
  }
}

provider "azurerm" {
  features {}
}

# 1. Resource group
resource "azurerm_resource_group" "main" {
  name = "rg-vector-search"
  location = var.location
}

# 2. VPC
resource "azurerm_virtual_network" "main" {
  name = "vpc-vector-search"
  address_space = ["10.0.0.0/16"]
  location = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
}

# 3. Subnet
resource "azurerm_subnet" "main" {
  name = "snet-vector-search"
  resource_group_name  = azurerm_resource_group.main.name
  virtual_network_name = azurerm_virtual_network.main.name
  address_prefixes = ["10.0.1.0/24"]
}

# 4. Public IP
resource "azurerm_public_ip" "main" {
  name = "pip-vector-search"
  location = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  allocation_method = "Static"
  sku = "Standard"
  domain_name_label = var.vm_name
}

# 5. Security Group
resource "azurerm_network_security_group" "main" {
  name = "nsg-vector-search"
  location = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name

  security_rule {
    name = "AllowSSHFromMyIP"
    priority = 100
    direction = "Inbound"
    access = "Allow"
    protocol = "Tcp"
    source_port_range = "*"
    destination_port_range = "22"
    source_address_prefix = var.my_ip
    destination_address_prefix = "*"
  }
}

# 6. Network Interface
resource "azurerm_network_interface" "main" {
  name = "nic-vector-search"
  location = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name

  ip_configuration {
    name = "ipconfig1"
    subnet_id = azurerm_subnet.main.id
    private_ip_address_allocation = "Dynamic"
    public_ip_address_id = azurerm_public_ip.main.id
  }
}

# 7. Attach the SG to the NI
resource "azurerm_network_interface_security_group_association" "main" {
  network_interface_id = azurerm_network_interface.main.id
  network_security_group_id = azurerm_network_security_group.main.id
}

# 8. VM
resource "azurerm_linux_virtual_machine" "main" {
  name = var.vm_name
  resource_group_name = azurerm_resource_group.main.name
  location = azurerm_resource_group.main.location
  size = var.vm_size
  admin_username = var.vm_admin_username
  network_interface_ids = [azurerm_network_interface.main.id]
  disable_password_authentication = true

  admin_ssh_key {
    username = var.vm_admin_username
    public_key = var.ssh_public_key
  }

  os_disk {
    caching = "ReadWrite"
    storage_account_type = "Standard_LRS"
  }

  source_image_reference {
    publisher = "Canonical"
    offer = "0001-com-ubuntu-server-jammy"
    sku = "22_04-lts-gen2"
    version = "latest"
  }

  tags = {
    project = "atlas-vector-search-ops"
  }
}