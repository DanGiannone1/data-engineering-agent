namespace DataEngineeringAgent.Core.Models;

public record ReviewEvent(
    bool Approved,
    string? Feedback = null);
