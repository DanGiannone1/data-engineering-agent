using DataEngineeringAgent.Core.Prompts;
using DataEngineeringAgent.Core.Services;
using Microsoft.Azure.Functions.Worker;
using Microsoft.Extensions.Logging;

namespace DataEngineeringAgent.Functions.Activities;

public class CodeGenerationActivity
{
    private readonly IAdlsService _adls;
    private readonly IOpenAiService _openAi;
    private readonly ILogger<CodeGenerationActivity> _logger;

    public CodeGenerationActivity(IAdlsService adls, IOpenAiService openAi, ILogger<CodeGenerationActivity> logger)
    {
        _adls = adls;
        _openAi = openAi;
        _logger = logger;
    }

    [Function(nameof(CodeGeneration))]
    public async Task<string> CodeGeneration([ActivityTrigger] CodeGenerationInput input)
    {
        var sourceColumns = "";
        if (!string.IsNullOrEmpty(input.DataPath))
        {
            try
            {
                var sample = await _adls.SampleSourceDataAsync(input.DataPath, nRows: 5);
                sourceColumns = string.Join(", ", sample.Columns);
            }
            catch (Exception e)
            {
                _logger.LogWarning(e, "Could not sample source data for column names");
            }
        }

        var prompt = SystemPrompts.CodeGeneration
            .Replace("{input_path}", input.InputPath)
            .Replace("{output_path}", input.OutputPath)
            .Replace("{client_id}", input.ClientId)
            .Replace("{pseudocode}", input.Pseudocode)
            .Replace("{source_columns}", sourceColumns);

        var code = await _openAi.RunAgentCodeAsync(prompt, "Generate the PySpark transformation code.");
        _logger.LogInformation("Generated PySpark code for {ClientId} ({Chars} chars)", input.ClientId, code.Length);
        return code;
    }
}

public record CodeGenerationInput(
    string ClientId,
    string Pseudocode,
    string InputPath,
    string OutputPath,
    string DataPath = "");
