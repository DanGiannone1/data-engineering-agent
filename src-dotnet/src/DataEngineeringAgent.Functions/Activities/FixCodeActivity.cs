using DataEngineeringAgent.Core.Prompts;
using DataEngineeringAgent.Core.Services;
using Microsoft.Azure.Functions.Worker;
using Microsoft.Extensions.Logging;

namespace DataEngineeringAgent.Functions.Activities;

public class FixCodeActivity
{
    private readonly IOpenAiService _openAi;
    private readonly ILogger<FixCodeActivity> _logger;

    public FixCodeActivity(IOpenAiService openAi, ILogger<FixCodeActivity> logger)
    {
        _openAi = openAi;
        _logger = logger;
    }

    [Function(nameof(FixCode))]
    public async Task<string> FixCode([ActivityTrigger] FixCodeInput input)
    {
        var prompt = SystemPrompts.CodeFix
            .Replace("{error_log}", input.ErrorLog)
            .Replace("{pyspark_code}", input.PySparkCode);

        var code = await _openAi.RunAgentCodeAsync(prompt, "Fix the code and return the complete corrected script.");
        _logger.LogInformation("Fixed PySpark code ({Chars} chars)", code.Length);
        return code;
    }
}

public record FixCodeInput(string PySparkCode, string ErrorLog);
