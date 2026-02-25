using System.Text.Json;
using DataEngineeringAgent.Core.Models;
using DataEngineeringAgent.Core.Prompts;
using DataEngineeringAgent.Core.Services;
using Microsoft.Azure.Functions.Worker;
using Microsoft.Extensions.Logging;

namespace DataEngineeringAgent.Functions.Activities;

public class ChangeDetectionActivity
{
    private readonly IAdlsService _adls;
    private readonly IApprovedCodeService _approvedCode;
    private readonly IOpenAiService _openAi;
    private readonly ILogger<ChangeDetectionActivity> _logger;

    public ChangeDetectionActivity(
        IAdlsService adls,
        IApprovedCodeService approvedCode,
        IOpenAiService openAi,
        ILogger<ChangeDetectionActivity> logger)
    {
        _adls = adls;
        _approvedCode = approvedCode;
        _openAi = openAi;
        _logger = logger;
    }

    [Function(nameof(ChangeDetection))]
    public async Task<ChangeDetectionResult> ChangeDetection(
        [ActivityTrigger] ChangeDetectionInput input)
    {
        var existing = _approvedCode.GetApprovedCode(input.ClientId);
        if (existing is null)
        {
            _logger.LogInformation("No existing code for {ClientId} — needs full generation", input.ClientId);
            return new ChangeDetectionResult(true, "No existing approved code", null);
        }

        var mapping = await _adls.ReadMappingSpreadsheetAsync(input.MappingPath);
        var sample = await _adls.SampleSourceDataAsync(input.DataPath);

        var userMessage = JsonSerializer.Serialize(new
        {
            current_mapping = mapping,
            current_data_sample = new
            {
                columns = sample.Columns,
                dtypes = sample.Dtypes,
                row_count = sample.RowCount,
                sample_rows = sample.SampleRows.Take(10),
            },
            stored_pseudocode = existing.Pseudocode,
        });

        var result = await _openAi.RunAgentJsonAsync<LlmChangeDetectionResult>(
            SystemPrompts.ChangeDetection, userMessage);

        return new ChangeDetectionResult(
            result.NeedsRegeneration,
            result.Reason,
            result.NeedsRegeneration ? null : existing);
    }
}

public record ChangeDetectionInput(string ClientId, string MappingPath, string DataPath);

internal record LlmChangeDetectionResult(bool NeedsRegeneration, string Reason);
