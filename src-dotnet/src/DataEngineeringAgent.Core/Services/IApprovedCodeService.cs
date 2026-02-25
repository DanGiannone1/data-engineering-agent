using DataEngineeringAgent.Core.Models;

namespace DataEngineeringAgent.Core.Services;

public interface IApprovedCodeService
{
    ApprovedCode? GetApprovedCode(string clientId);
    void SaveApprovedCode(string clientId, string pseudocode, string pysparkCode, ApprovedCodeMetadata metadata);
}
