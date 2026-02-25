namespace DataEngineeringAgent.Core.Exceptions;

public class SparkExecutionException : AgentException
{
    public string? RunId { get; }
    public string? ErrorLog { get; }

    public SparkExecutionException(string message, string? runId = null, string? errorLog = null)
        : base(message)
    {
        RunId = runId;
        ErrorLog = errorLog;
    }
}
