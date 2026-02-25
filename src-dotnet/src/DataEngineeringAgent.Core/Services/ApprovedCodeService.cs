using System.Text.Json;
using DataEngineeringAgent.Core.Models;
using Microsoft.Extensions.Logging;

namespace DataEngineeringAgent.Core.Services;

public class ApprovedCodeService : IApprovedCodeService
{
    private static readonly JsonSerializerOptions SnakeCaseOptions = new()
    {
        WriteIndented = true,
        PropertyNamingPolicy = JsonNamingPolicy.SnakeCaseLower,
    };

    private readonly string _approvedCodeDir;
    private readonly ILogger<ApprovedCodeService> _logger;

    public ApprovedCodeService(ILogger<ApprovedCodeService> logger)
    {
        var repoRoot = Environment.GetEnvironmentVariable("REPO_ROOT")
            ?? throw new InvalidOperationException("REPO_ROOT environment variable must be set");
        _approvedCodeDir = Path.Combine(repoRoot, "approved-code");
        _logger = logger;
    }

    public ApprovedCode? GetApprovedCode(string clientId)
    {
        var clientDir = Path.Combine(_approvedCodeDir, clientId);
        if (!Directory.Exists(clientDir))
            return null;

        var pseudocodePath = Path.Combine(clientDir, "pseudocode.md");
        var transformPath = Path.Combine(clientDir, "transform.py");
        var metadataPath = Path.Combine(clientDir, "metadata.json");

        if (!File.Exists(pseudocodePath) || !File.Exists(transformPath) || !File.Exists(metadataPath))
            return null;

        var metadata = JsonSerializer.Deserialize<ApprovedCodeMetadata>(
            File.ReadAllText(metadataPath),
            new JsonSerializerOptions { PropertyNamingPolicy = JsonNamingPolicy.SnakeCaseLower, PropertyNameCaseInsensitive = true })!;

        return new ApprovedCode(
            Pseudocode: File.ReadAllText(pseudocodePath),
            PySparkCode: File.ReadAllText(transformPath),
            Metadata: metadata);
    }

    public void SaveApprovedCode(string clientId, string pseudocode, string pysparkCode, ApprovedCodeMetadata metadata)
    {
        var clientDir = Path.Combine(_approvedCodeDir, clientId);
        Directory.CreateDirectory(clientDir);

        File.WriteAllText(Path.Combine(clientDir, "pseudocode.md"), pseudocode);
        File.WriteAllText(Path.Combine(clientDir, "transform.py"), pysparkCode);
        File.WriteAllText(
            Path.Combine(clientDir, "metadata.json"),
            JsonSerializer.Serialize(metadata, SnakeCaseOptions));

        _logger.LogInformation("Saved approved code for {ClientId}", clientId);
    }
}
