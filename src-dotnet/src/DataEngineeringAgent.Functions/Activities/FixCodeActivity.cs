using System.Text.RegularExpressions;
using DataEngineeringAgent.Core.Prompts;
using DataEngineeringAgent.Core.Services;
using Microsoft.Azure.Functions.Worker;
using Microsoft.Extensions.Logging;

namespace DataEngineeringAgent.Functions.Activities;

public class FixCodeActivity
{
    private readonly IOpenAiService _openAi;
    private readonly ILogger<FixCodeActivity> _logger;

    private const string ConfigBeginMarker = "# --- BEGIN TRANSFORM_CONFIG ---";
    private const string ConfigEndMarker = "# --- END TRANSFORM_CONFIG ---";

    public FixCodeActivity(IOpenAiService openAi, ILogger<FixCodeActivity> logger)
    {
        _openAi = openAi;
        _logger = logger;
    }

    [Function(nameof(FixCode))]
    public async Task<string> FixCode([ActivityTrigger] FixCodeInput input)
    {
        // Extract config block from the assembled notebook
        var configBlock = ExtractConfigBlock(input.PySparkCode);

        var prompt = SystemPrompts.ConfigFix
            .Replace("{error_log}", input.ErrorLog)
            .Replace("{config_block}", configBlock);

        var fixedConfig = await _openAi.RunAgentCodeAsync(prompt, "Fix the TRANSFORM_CONFIG dict.");

        // Strip markdown code fences if present
        fixedConfig = StripCodeFences(fixedConfig);

        // Reassemble: replace the config block in the original notebook
        var fixedNotebook = ReplaceConfigBlock(input.PySparkCode, fixedConfig);

        _logger.LogInformation("Fixed TRANSFORM_CONFIG ({Chars} chars)", fixedConfig.Length);
        return fixedNotebook;
    }

    private static string ExtractConfigBlock(string notebook)
    {
        var startIdx = notebook.IndexOf(ConfigBeginMarker, StringComparison.Ordinal);
        var endIdx = notebook.IndexOf(ConfigEndMarker, StringComparison.Ordinal);

        if (startIdx < 0 || endIdx < 0 || endIdx <= startIdx)
            throw new InvalidOperationException("Could not find TRANSFORM_CONFIG markers in notebook");

        var blockStart = startIdx + ConfigBeginMarker.Length;
        return notebook[blockStart..endIdx].Trim();
    }

    private static string ReplaceConfigBlock(string notebook, string newConfig)
    {
        var startIdx = notebook.IndexOf(ConfigBeginMarker, StringComparison.Ordinal);
        var endIdx = notebook.IndexOf(ConfigEndMarker, StringComparison.Ordinal);

        if (startIdx < 0 || endIdx < 0 || endIdx <= startIdx)
            throw new InvalidOperationException("Could not find TRANSFORM_CONFIG markers in notebook");

        var before = notebook[..(startIdx + ConfigBeginMarker.Length)];
        var after = notebook[endIdx..];

        return before + "\n" + newConfig + "\n" + after;
    }

    private static string StripCodeFences(string text)
    {
        var match = Regex.Match(text, @"```(?:python)?\s*\n([\s\S]*?)\n\s*```", RegexOptions.Singleline);
        return match.Success ? match.Groups[1].Value.Trim() : text.Trim();
    }
}

public record FixCodeInput(string PySparkCode, string ErrorLog);
