using DataEngineeringAgent.Core.Models;
using DataEngineeringAgent.Core.Services;
using Microsoft.Azure.Functions.Worker;

namespace DataEngineeringAgent.Functions.Activities;

public class SaveCodeActivity
{
    private readonly IApprovedCodeService _approvedCode;

    public SaveCodeActivity(IApprovedCodeService approvedCode)
    {
        _approvedCode = approvedCode;
    }

    [Function(nameof(SaveCode))]
    public void SaveCode([ActivityTrigger] SaveCodeInput input)
    {
        var metadata = new ApprovedCodeMetadata(
            ClientId: input.ClientId,
            ApprovedBy: "auditor",
            ApprovedAt: DateTime.UtcNow);

        _approvedCode.SaveApprovedCode(input.ClientId, input.Pseudocode, input.PySparkCode, metadata);
    }
}

public record SaveCodeInput(string ClientId, string Pseudocode, string PySparkCode);
