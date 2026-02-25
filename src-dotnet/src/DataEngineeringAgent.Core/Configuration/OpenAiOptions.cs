using System.ComponentModel.DataAnnotations;

namespace DataEngineeringAgent.Core.Configuration;

public class OpenAiOptions
{
    public const string SectionName = "OpenAi";

    [Required]
    public string Endpoint { get; set; } = string.Empty;

    public string DeploymentName { get; set; } = "gpt-4.1";

    public float Temperature { get; set; } = 0.2f;
}
