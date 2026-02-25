using DataEngineeringAgent.Core.Models;

namespace DataEngineeringAgent.Core.Exceptions;

public class IntegrityCheckException : AgentException
{
    public IntegrityReport? Report { get; }

    public IntegrityCheckException(string message, IntegrityReport? report = null)
        : base(message)
    {
        Report = report;
    }
}
