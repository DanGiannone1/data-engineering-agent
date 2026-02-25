using DataEngineeringAgent.Core.Models;

namespace DataEngineeringAgent.Core.Services;

public interface IDatabricksService
{
    Task<string> SubmitSparkJobAsync(string pysparkCode, string clientId = "");
    Task<SparkRunStatus> GetRunStatusAsync(string runId);
    Task<SparkExecutionResult> ExecuteSparkJobAsync(string pysparkCode, string clientId);
}
