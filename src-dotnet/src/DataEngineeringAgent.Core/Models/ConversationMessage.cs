namespace DataEngineeringAgent.Core.Models;

public record ConversationMessage
{
    public string Id { get; init; } = Guid.NewGuid().ToString();
    public required string ThreadId { get; init; }
    public required string ClientId { get; init; }
    public required string Role { get; init; }
    public required string Content { get; init; }
    public required string Phase { get; init; }
    public DateTime Timestamp { get; init; } = DateTime.UtcNow;
}
