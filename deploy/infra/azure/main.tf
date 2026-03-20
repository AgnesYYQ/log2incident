# Azure Infrastructure (Terraform example)
provider "azurerm" {
  features {}
}

resource "azurerm_kubernetes_cluster" "main" {
  name                = "log2incident-aks"
  location            = var.location
  resource_group_name = var.resource_group
  dns_prefix          = "log2incident"
  default_node_pool {
    name       = "default"
    node_count = 1
    vm_size    = "Standard_DS2_v2"
  }
  identity {
    type = "SystemAssigned"
  }
}

resource "azurerm_eventhub_namespace" "log_stream" {
  name                = "log2incident-eh"
  location            = var.location
  resource_group_name = var.resource_group
  sku                 = "Standard"
}

# Add Blob Storage, Managed Identity, etc. as needed
