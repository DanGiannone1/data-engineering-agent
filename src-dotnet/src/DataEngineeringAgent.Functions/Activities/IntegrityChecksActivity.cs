using DataEngineeringAgent.Core.Models;
using DataEngineeringAgent.Core.Services;
using Microsoft.Azure.Functions.Worker;

namespace DataEngineeringAgent.Functions.Activities;

public class IntegrityChecksActivity
{
    private readonly IIntegrityService _integrity;

    public IntegrityChecksActivity(IIntegrityService integrity)
    {
        _integrity = integrity;
    }

    [Function(nameof(IntegrityChecks))]
    public async Task<IntegrityReport> IntegrityChecks([ActivityTrigger] IntegrityChecksInput input)
    {
        return await _integrity.RunIntegrityChecksAsync(input.OutputPath);
    }
}

public record IntegrityChecksInput(string OutputPath);
