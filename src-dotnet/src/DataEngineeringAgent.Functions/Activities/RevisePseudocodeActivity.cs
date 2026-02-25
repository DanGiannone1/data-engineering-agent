using DataEngineeringAgent.Core.Prompts;
using DataEngineeringAgent.Core.Services;
using Microsoft.Azure.Functions.Worker;
using Microsoft.Extensions.Logging;

namespace DataEngineeringAgent.Functions.Activities;

public class RevisePseudocodeActivity
{
    private readonly IOpenAiService _openAi;
    private readonly ILogger<RevisePseudocodeActivity> _logger;

    public RevisePseudocodeActivity(IOpenAiService openAi, ILogger<RevisePseudocodeActivity> logger)
    {
        _openAi = openAi;
        _logger = logger;
    }

    [Function(nameof(RevisePseudocode))]
    public async Task<string> RevisePseudocode([ActivityTrigger] RevisePseudocodeInput input)
    {
        var prompt = SystemPrompts.PseudocodeRevision
            .Replace("{feedback}", input.Feedback)
            .Replace("{pseudocode}", input.Pseudocode);

        var revised = await _openAi.RunAgentAsync(prompt, "Please provide the revised pseudocode.");
        _logger.LogInformation("Revised pseudocode ({Chars} chars)", revised.Length);
        return revised;
    }
}

public record RevisePseudocodeInput(string Pseudocode, string Feedback);
