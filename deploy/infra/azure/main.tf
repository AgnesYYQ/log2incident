# Azure Infrastructure (Terraform example)
provider "azurerm" {
  features {}
}

# Virtual Network
resource "azurerm_virtual_network" "main" {
  name                = "log2incident-vnet"
  address_space       = ["10.1.0.0/16"]
  location            = var.location
  resource_group_name = var.resource_group
}

# Subnet
resource "azurerm_subnet" "main" {
  name                 = "log2incident-subnet"
  resource_group_name  = var.resource_group
  virtual_network_name = azurerm_virtual_network.main.name
  address_prefixes     = ["10.1.1.0/24"]
}

# Managed Identity
resource "azurerm_user_assigned_identity" "main" {
  name                = "log2incident-identity"
  resource_group_name = var.resource_group
  location            = var.location
}

# AKS Cluster
resource "azurerm_kubernetes_cluster" "main" {
  name                = "log2incident-aks"
  location            = var.location
  resource_group_name = var.resource_group
  dns_prefix          = "log2incident"
  default_node_pool {
    name       = "default"
    node_count = 1
    vm_size    = "Standard_DS2_v2"
    vnet_subnet_id = azurerm_subnet.main.id
  }
  identity {
    type = "UserAssigned"
    user_assigned_identity_id = azurerm_user_assigned_identity.main.id
  }
  network_profile {
    network_plugin = "azure"
    network_policy = "azure"
  }
}

# Event Hub Namespace
resource "azurerm_eventhub_namespace" "log_stream" {
  name                = "log2incident-eh"
  location            = var.location
  resource_group_name = var.resource_group
  sku                 = "Standard"
}

# Application Insights
resource "azurerm_application_insights" "main" {
  name                = "log2incident-ai"
  location            = var.location
  resource_group_name = var.resource_group
  application_type    = "web"
}

# CosmosDB Account
resource "azurerm_cosmosdb_account" "main" {
  name                = "log2incident-cosmos"
  location            = var.location
  resource_group_name = var.resource_group
  offer_type          = "Standard"
  kind                = "GlobalDocumentDB"
  consistency_policy {
    consistency_level = "Session"
  }
  geo_location {
    location          = var.location
    failover_priority = 0
  }
}

# CosmosDB Database and Containers
resource "azurerm_cosmosdb_sql_database" "events" {
  name                = "events-db"
  resource_group_name = var.resource_group
  account_name        = azurerm_cosmosdb_account.main.name
}
resource "azurerm_cosmosdb_sql_container" "events" {
  name                = "events"
  resource_group_name = var.resource_group
  account_name        = azurerm_cosmosdb_account.main.name
  database_name       = azurerm_cosmosdb_sql_database.events.name
  partition_key_path  = "/event_id"
}
resource "azurerm_cosmosdb_sql_database" "incidents" {
  name                = "incidents-db"
  resource_group_name = var.resource_group
  account_name        = azurerm_cosmosdb_account.main.name
}
resource "azurerm_cosmosdb_sql_container" "incidents" {
  name                = "incidents"
  resource_group_name = var.resource_group
  account_name        = azurerm_cosmosdb_account.main.name
  database_name       = azurerm_cosmosdb_sql_database.incidents.name
  partition_key_path  = "/incident_id"
}

# Event Hub Topic
resource "azurerm_eventhub" "logs" {
  name                = "log2incident-logs"
  namespace_name      = azurerm_eventhub_namespace.log_stream.name
  resource_group_name = var.resource_group
  partition_count     = 2
  message_retention   = 7
}

# Outputs
output "vnet_id" {
  value = azurerm_virtual_network.main.id
}
output "aks_cluster_name" {
  value = azurerm_kubernetes_cluster.main.name
}
output "managed_identity_id" {
  value = azurerm_user_assigned_identity.main.id
}
output "eventhub_namespace_name" {
  value = azurerm_eventhub_namespace.log_stream.name
}
output "application_insights_name" {
  value = azurerm_application_insights.main.name
}
output "cosmosdb_account_name" {
  value = azurerm_cosmosdb_account.main.name
}
output "eventhub_topic_name" {
  value = azurerm_eventhub.logs.name
}
