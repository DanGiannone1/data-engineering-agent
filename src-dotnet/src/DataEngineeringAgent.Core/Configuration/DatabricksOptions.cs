using System.ComponentModel.DataAnnotations;

namespace DataEngineeringAgent.Core.Configuration;

public class DatabricksOptions
{
    public const string SectionName = "Databricks";

    [Required]
    public string Host { get; set; } = string.Empty;

    [Required]
    public string SpClientId { get; set; } = string.Empty;

    [Required]
    public string SpClientSecret { get; set; } = string.Empty;

    [Required]
    public string TenantId { get; set; } = string.Empty;

    public string SparkVersion { get; set; } = "14.3.x-scala2.12";

    public string NodeTypeId { get; set; } = "Standard_D4s_v3";

    public int NumWorkers { get; set; } = 1;
}
