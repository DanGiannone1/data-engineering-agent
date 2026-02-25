using System.ComponentModel.DataAnnotations;

namespace DataEngineeringAgent.Core.Configuration;

public class CosmosOptions
{
    public const string SectionName = "Cosmos";

    [Required]
    public string Endpoint { get; set; } = string.Empty;

    public string DatabaseName { get; set; } = "agent-db";
}
