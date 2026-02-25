namespace DataEngineeringAgent.Core.Models;

public record IntegrityReport(
    List<CheckResult> Checks,
    bool OverallPass,
    List<string> Errors);

public record CheckResult(
    string Name,
    bool Passed,
    string Message,
    Dictionary<string, object>? Details = null);
