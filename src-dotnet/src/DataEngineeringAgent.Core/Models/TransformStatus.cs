namespace DataEngineeringAgent.Core.Models;

public record TransformStatus(
    string InstanceId,
    string ClientId,
    int Phase,
    string PhaseName,
    bool PendingReview = false,
    string? Pseudocode = null,
    Dictionary<string, object>? IntegrityReport = null,
    string? OutputPath = null,
    string? Error = null);
