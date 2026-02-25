namespace DataEngineeringAgent.Core.Models;

public record SparkExecutionResult(
    bool Success,
    string RunId,
    string ErrorLog);

public record SparkRunStatus(
    string LifeCycleState,
    string ResultState,
    string ErrorLog,
    bool Done,
    bool Success);
