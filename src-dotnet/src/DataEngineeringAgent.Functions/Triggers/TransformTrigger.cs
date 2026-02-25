using System.Net;
using System.Text.Json;
using DataEngineeringAgent.Core.Configuration;
using DataEngineeringAgent.Core.Models;
using DataEngineeringAgent.Core.Services;
using Microsoft.Azure.Functions.Worker;
using Microsoft.Azure.Functions.Worker.Http;
using Microsoft.DurableTask.Client;
using Microsoft.Extensions.Options;

namespace DataEngineeringAgent.Functions.Triggers;

public class TransformTrigger
{
    private readonly ICosmosService _cosmos;
    private readonly AdlsOptions _adlsOptions;
    private static readonly JsonSerializerOptions JsonOptions = new()
    {
        PropertyNamingPolicy = JsonNamingPolicy.SnakeCaseLower,
        PropertyNameCaseInsensitive = true,
    };

    public TransformTrigger(ICosmosService cosmos, IOptions<AdlsOptions> adlsOptions)
    {
        _cosmos = cosmos;
        _adlsOptions = adlsOptions.Value;
    }

    [Function("StartTransform")]
    public async Task<HttpResponseData> StartTransform(
        [HttpTrigger(AuthorizationLevel.Anonymous, "post", Route = "transform")] HttpRequestData req,
        [DurableClient] DurableTaskClient client)
    {
        var body = await JsonSerializer.DeserializeAsync<JsonElement>(req.Body);

        // Validate required fields
        var requiredFields = new[] { "client_id", "mapping_path", "data_path" };
        var missing = requiredFields
            .Where(f => !body.TryGetProperty(f, out _) &&
                        !body.TryGetProperty(ToCamelCase(f), out _))
            .ToList();

        if (missing.Count > 0)
        {
            var errorResp = req.CreateResponse(HttpStatusCode.BadRequest);
            errorResp.Headers.Add("Content-Type", "application/json");
            await errorResp.WriteStringAsync(JsonSerializer.Serialize(new { error = $"Missing fields: {string.Join(", ", missing)}" }, JsonOptions));
            return errorResp;
        }

        var request = new TransformRequest(
            ClientId: GetStringProp(body, "client_id"),
            MappingPath: GetStringProp(body, "mapping_path"),
            DataPath: GetStringProp(body, "data_path"),
            AdlsAccountName: _adlsOptions.AccountName);

        var instanceId = await client.ScheduleNewOrchestrationInstanceAsync(
            "TransformOrchestration", request);

        var response = req.CreateResponse(HttpStatusCode.Accepted);
        response.Headers.Add("Content-Type", "application/json");
        await response.WriteStringAsync(JsonSerializer.Serialize(new
        {
            instance_id = instanceId,
            client_id = request.ClientId,
        }, JsonOptions));

        return response;
    }

    [Function("GetTransformStatus")]
    public async Task<HttpResponseData> GetTransformStatus(
        [HttpTrigger(AuthorizationLevel.Anonymous, "get", Route = "transform/{instanceId}/status")] HttpRequestData req,
        [DurableClient] DurableTaskClient client,
        string instanceId)
    {
        var metadata = await client.GetInstanceAsync(instanceId, getInputsAndOutputs: true);

        if (metadata is null)
        {
            var notFound = req.CreateResponse(HttpStatusCode.NotFound);
            notFound.Headers.Add("Content-Type", "application/json");
            await notFound.WriteStringAsync("""{"error":"Not found"}""");
            return notFound;
        }

        object? customStatus = null;
        object? output = null;
        try { customStatus = metadata.ReadCustomStatusAs<JsonElement>(); } catch { }
        try { if (metadata.IsCompleted) output = metadata.ReadOutputAs<JsonElement>(); } catch { }

        var result = new
        {
            instance_id = instanceId,
            runtime_status = metadata.RuntimeStatus.ToString(),
            custom_status = customStatus,
            output,
            created_time = metadata.CreatedAt.ToString("o"),
            last_updated_time = metadata.LastUpdatedAt.ToString("o"),
        };

        var response = req.CreateResponse(HttpStatusCode.OK);
        response.Headers.Add("Content-Type", "application/json");
        await response.WriteStringAsync(JsonSerializer.Serialize(result, JsonOptions));
        return response;
    }

    [Function("SubmitReview")]
    public async Task<HttpResponseData> SubmitReview(
        [HttpTrigger(AuthorizationLevel.Anonymous, "post", Route = "transform/{instanceId}/review")] HttpRequestData req,
        [DurableClient] DurableTaskClient client,
        string instanceId)
    {
        var body = await JsonSerializer.DeserializeAsync<JsonElement>(req.Body);

        if (!body.TryGetProperty("approved", out _))
        {
            var errorResp = req.CreateResponse(HttpStatusCode.BadRequest);
            errorResp.Headers.Add("Content-Type", "application/json");
            await errorResp.WriteStringAsync("""{"error":"Missing approved field"}""");
            return errorResp;
        }

        var review = new ReviewEvent(
            Approved: body.GetProperty("approved").GetBoolean(),
            Feedback: body.TryGetProperty("feedback", out var fb) ? fb.GetString() : null);

        await client.RaiseEventAsync(instanceId, "review", review);

        var response = req.CreateResponse(HttpStatusCode.OK);
        response.Headers.Add("Content-Type", "application/json");
        await response.WriteStringAsync(JsonSerializer.Serialize(new
        {
            status = "review submitted",
            approved = review.Approved,
        }, JsonOptions));
        return response;
    }

    [Function("GetMessages")]
    public async Task<HttpResponseData> GetMessages(
        [HttpTrigger(AuthorizationLevel.Anonymous, "get", Route = "transform/{instanceId}/messages")] HttpRequestData req,
        string instanceId)
    {
        var messages = await _cosmos.GetConversationHistoryAsync(instanceId);

        var response = req.CreateResponse(HttpStatusCode.OK);
        response.Headers.Add("Content-Type", "application/json");
        await response.WriteStringAsync(JsonSerializer.Serialize(messages, JsonOptions));
        return response;
    }

    private static string GetStringProp(JsonElement element, string snakeName)
    {
        if (element.TryGetProperty(snakeName, out var val))
            return val.GetString()!;
        if (element.TryGetProperty(ToCamelCase(snakeName), out val))
            return val.GetString()!;
        return "";
    }

    private static string ToCamelCase(string snakeCase)
    {
        var parts = snakeCase.Split('_');
        return parts[0] + string.Join("", parts.Skip(1).Select(p =>
            string.IsNullOrEmpty(p) ? p : char.ToUpper(p[0]) + p[1..]));
    }
}
