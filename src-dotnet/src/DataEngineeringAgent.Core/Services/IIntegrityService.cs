using DataEngineeringAgent.Core.Models;

namespace DataEngineeringAgent.Core.Services;

public interface IIntegrityService
{
    Task<IntegrityReport> RunIntegrityChecksAsync(string outputPath, List<string>? expectedColumns = null);
}
