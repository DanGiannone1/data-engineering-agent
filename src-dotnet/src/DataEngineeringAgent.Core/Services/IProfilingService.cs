using DataEngineeringAgent.Core.Models;

namespace DataEngineeringAgent.Core.Services;

public interface IProfilingService
{
    DataProfile ProfileData(DataSample data);
}
