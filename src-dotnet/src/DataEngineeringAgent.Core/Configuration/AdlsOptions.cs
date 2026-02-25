using System.ComponentModel.DataAnnotations;

namespace DataEngineeringAgent.Core.Configuration;

public class AdlsOptions
{
    public const string SectionName = "Adls";

    [Required]
    public string AccountName { get; set; } = string.Empty;
}
