namespace DataEngineeringAgent.Core.Models;

public record ApprovedCode(
    string Pseudocode,
    string PySparkCode,
    ApprovedCodeMetadata Metadata);

public record ApprovedCodeMetadata(
    string ClientId,
    string ApprovedBy,
    DateTime ApprovedAt,
    DateTime? LastRunAt = null,
    int RunCount = 0);
