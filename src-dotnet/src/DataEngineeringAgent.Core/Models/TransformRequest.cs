namespace DataEngineeringAgent.Core.Models;

public record TransformRequest(
    string ClientId,
    string MappingPath,
    string DataPath,
    string AdlsAccountName);
