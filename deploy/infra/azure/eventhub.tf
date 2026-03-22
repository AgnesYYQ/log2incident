# Azure Event Hubs Terraform example
resource "azurerm_eventhub_namespace" "main" {
  name                = "log2incident-eh"
  location            = var.location
  resource_group_name = var.resource_group
  sku                 = "Standard"
}

resource "azurerm_eventhub" "logs" {
  name                = "log2incident-logs"
  namespace_name      = azurerm_eventhub_namespace.main.name
  resource_group_name = var.resource_group
  partition_count     = 2
  message_retention   = 7
}
