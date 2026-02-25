namespace DataEngineeringAgent.Core.Services;

public interface IOpenAiService
{
    Task<string> RunAgentAsync(string systemPrompt, string userMessage);
    Task<T> RunAgentJsonAsync<T>(string systemPrompt, string userMessage);
    Task<string> RunAgentCodeAsync(string systemPrompt, string userMessage);
}
