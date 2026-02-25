namespace DataEngineeringAgent.Core.Exceptions;

public class AgentException : Exception
{
    public AgentException(string message) : base(message) { }
    public AgentException(string message, Exception inner) : base(message, inner) { }
}
