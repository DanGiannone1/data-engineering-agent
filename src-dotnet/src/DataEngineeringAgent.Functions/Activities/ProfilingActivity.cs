using System.Text.Json;
using DataEngineeringAgent.Core.Prompts;
using DataEngineeringAgent.Core.Services;
using Microsoft.Azure.Functions.Worker;
using Microsoft.Extensions.Logging;

namespace DataEngineeringAgent.Functions.Activities;

public class ProfilingActivity
{
    private readonly IAdlsService _adls;
    private readonly IProfilingService _profiling;
    private readonly IOpenAiService _openAi;
    private readonly ILogger<ProfilingActivity> _logger;

    public ProfilingActivity(
        IAdlsService adls,
        IProfilingService profiling,
        IOpenAiService openAi,
        ILogger<ProfilingActivity> logger)
    {
        _adls = adls;
        _profiling = profiling;
        _openAi = openAi;
        _logger = logger;
    }

    [Function(nameof(Profiling))]
    public async Task<string> Profiling([ActivityTrigger] ProfilingInput input)
    {
        var mapping = await _adls.ReadMappingSpreadsheetAsync(input.MappingPath);
        var sample = await _adls.SampleSourceDataAsync(input.DataPath);
        var profile = _profiling.ProfileData(sample);

        var userMessage = JsonSerializer.Serialize(new
        {
            client_id = input.ClientId,
            mapping,
            data_profile = profile,
            sample_rows = sample.SampleRows.Take(20),
        });

        var pseudocode = await _openAi.RunAgentAsync(SystemPrompts.ProfilingAndPseudocode, userMessage);
        _logger.LogInformation("Generated pseudocode for {ClientId} ({Chars} chars)", input.ClientId, pseudocode.Length);
        return pseudocode;
    }
}

public record ProfilingInput(string ClientId, string MappingPath, string DataPath);
