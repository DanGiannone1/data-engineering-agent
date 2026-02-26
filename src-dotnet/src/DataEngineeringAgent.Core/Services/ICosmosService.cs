using System.Text.Json;
using DataEngineeringAgent.Core.Models;

namespace DataEngineeringAgent.Core.Services;

public interface ICosmosService
{
    Task SaveMessageAsync(ConversationMessage message);
    Task<List<JsonElement>> GetConversationHistoryAsync(string threadId);
}
