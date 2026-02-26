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

    public async Task<List<JsonElement>> GetConversationHistoryAsync(string threadId)
    {
        var query = new QueryDefinition(
            "SELECT * FROM c WHERE c.thread_id = @threadId ORDER BY c.timestamp ASC")
            .WithParameter("@threadId", threadId);

        var results = new List<JsonElement>();
        using var iterator = _container.GetItemQueryStreamIterator(
            query, requestOptions: new QueryRequestOptions { PartitionKey = new PartitionKey(threadId) });

        while (iterator.HasMoreResults)
        {
            using var response = await iterator.ReadNextAsync();
            if (!response.IsSuccessStatusCode) continue;

            using var doc = await JsonDocument.ParseAsync(response.Content);
            foreach (var item in doc.RootElement.GetProperty("Documents").EnumerateArray())
            {
                results.Add(item.Clone());
            }
        }

        return results;
    }
}
