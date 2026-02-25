using System.Text.Json;
using DataEngineeringAgent.Core.Models;
using Microsoft.Azure.Cosmos;
using Microsoft.Extensions.Logging;

namespace DataEngineeringAgent.Core.Services;

public class CosmosService : ICosmosService
{
    private readonly Container _container;
    private readonly ILogger<CosmosService> _logger;

    public CosmosService(CosmosClient cosmosClient, string databaseName, ILogger<CosmosService> logger)
    {
        _container = cosmosClient.GetContainer(databaseName, "conversations");
        _logger = logger;
    }

    public async Task SaveMessageAsync(ConversationMessage message)
    {
        var doc = new Dictionary<string, object?>
        {
            ["id"] = message.Id,
            ["thread_id"] = message.ThreadId,
            ["client_id"] = message.ClientId,
            ["role"] = message.Role,
            ["content"] = message.Content,
            ["phase"] = message.Phase,
            ["timestamp"] = message.Timestamp.ToString("o"),
        };

        await _container.UpsertItemAsync(doc, new PartitionKey(message.ThreadId));
        _logger.LogDebug("Saved message {Id} to thread {ThreadId}", message.Id, message.ThreadId);
    }

    public async Task<List<Dictionary<string, object?>>> GetConversationHistoryAsync(string threadId)
    {
        var query = new QueryDefinition(
            "SELECT * FROM c WHERE c.thread_id = @threadId ORDER BY c.timestamp ASC")
            .WithParameter("@threadId", threadId);

        var results = new List<Dictionary<string, object?>>();
        using var iterator = _container.GetItemQueryIterator<JsonElement>(
            query, requestOptions: new QueryRequestOptions { PartitionKey = new PartitionKey(threadId) });

        while (iterator.HasMoreResults)
        {
            var response = await iterator.ReadNextAsync();
            foreach (var item in response)
            {
                results.Add(JsonElementToDict(item));
            }
        }

        return results;
    }

    private static Dictionary<string, object?> JsonElementToDict(JsonElement element)
    {
        if (element.ValueKind != JsonValueKind.Object)
            return new Dictionary<string, object?> { ["raw"] = element.ToString() };

        var dict = new Dictionary<string, object?>();
        foreach (var prop in element.EnumerateObject())
        {
            dict[prop.Name] = prop.Value.ValueKind switch
            {
                JsonValueKind.String => prop.Value.GetString(),
                JsonValueKind.Number => prop.Value.GetDouble(),
                JsonValueKind.True => true,
                JsonValueKind.False => false,
                JsonValueKind.Null => null,
                _ => prop.Value.ToString()
            };
        }
        return dict;
    }
}
