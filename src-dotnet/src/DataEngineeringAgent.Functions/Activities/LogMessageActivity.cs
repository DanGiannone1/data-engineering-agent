using DataEngineeringAgent.Core.Models;
using DataEngineeringAgent.Core.Services;
using Microsoft.Azure.Functions.Worker;

namespace DataEngineeringAgent.Functions.Activities;

public class LogMessageActivity
{
    private readonly ICosmosService _cosmos;

    public LogMessageActivity(ICosmosService cosmos)
    {
        _cosmos = cosmos;
    }

    [Function(nameof(LogMessage))]
    public async Task LogMessage([ActivityTrigger] LogMessageInput input)
    {
        var message = new ConversationMessage
        {
            ThreadId = input.ThreadId,
            ClientId = input.ClientId,
            Role = input.Role,
            Content = input.Content,
            Phase = input.Phase,
        };

        await _cosmos.SaveMessageAsync(message);
    }
}

public record LogMessageInput(string ThreadId, string ClientId, string Phase, string Role, string Content);
