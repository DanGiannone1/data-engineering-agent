using DataEngineeringAgent.Core.Models;
using DataEngineeringAgent.Core.Services;
using Microsoft.Azure.Functions.Worker;

namespace DataEngineeringAgent.Functions.Activities;

public class SparkExecutionActivity
{
    private readonly IDatabricksService _databricks;

    public SparkExecutionActivity(IDatabricksService databricks)
    {
        _databricks = databricks;
    }

    [Function(nameof(SparkExecution))]
    public async Task<SparkExecutionResult> SparkExecution([ActivityTrigger] SparkExecutionInput input)
    {
        return await _databricks.ExecuteSparkJobAsync(input.PySparkCode, input.ClientId);
    }
}

public record SparkExecutionInput(string PySparkCode, string ClientId);
