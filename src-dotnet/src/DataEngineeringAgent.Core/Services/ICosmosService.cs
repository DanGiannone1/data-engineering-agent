using DataEngineeringAgent.Core.Models;

namespace DataEngineeringAgent.Core.Services;

public interface ICosmosService
{
    Task SaveMessageAsync(ConversationMessage message);
    Task<List<Dictionary<string, object?>>> GetConversationHistoryAsync(string threadId);
}
