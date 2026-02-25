namespace DataEngineeringAgent.Core.Models;

public record ChangeDetectionResult(
    bool NeedsRegeneration,
    string Reason,
    ApprovedCode? ExistingCode);
