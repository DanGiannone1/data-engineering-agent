using System.Text.Json;
using DataEngineeringAgent.Core.Models;
using DataEngineeringAgent.Core.Services;
using FluentAssertions;
using Microsoft.Extensions.Logging;
using Xunit;
using Moq;

namespace DataEngineeringAgent.Tests.Services;

public class ApprovedCodeServiceTests : IDisposable
{
    private readonly string _tempDir;
    private readonly ApprovedCodeService _sut;

    public ApprovedCodeServiceTests()
    {
        _tempDir = Path.Combine(Path.GetTempPath(), $"dea_test_{Guid.NewGuid():N}");
        Directory.CreateDirectory(_tempDir);
        Environment.SetEnvironmentVariable("REPO_ROOT", _tempDir);
        _sut = new ApprovedCodeService(Mock.Of<ILogger<ApprovedCodeService>>());
    }

    public void Dispose()
    {
        if (Directory.Exists(_tempDir))
            Directory.Delete(_tempDir, recursive: true);
        Environment.SetEnvironmentVariable("REPO_ROOT", null);
    }

    [Fact]
    public void GetApprovedCode_NoDirectory_ReturnsNull()
    {
        var result = _sut.GetApprovedCode("nonexistent");
        result.Should().BeNull();
    }

    [Fact]
    public void SaveAndGet_RoundTrips()
    {
        var metadata = new ApprovedCodeMetadata("CLIENT_001", "auditor", DateTime.UtcNow);

        _sut.SaveApprovedCode("CLIENT_001", "Step 1: Read data", "import pyspark", metadata);

        var result = _sut.GetApprovedCode("CLIENT_001");

        result.Should().NotBeNull();
        result!.Pseudocode.Should().Be("Step 1: Read data");
        result.PySparkCode.Should().Be("import pyspark");
        result.Metadata.ClientId.Should().Be("CLIENT_001");
    }

    [Fact]
    public void GetApprovedCode_MissingFile_ReturnsNull()
    {
        var clientDir = Path.Combine(_tempDir, "approved-code", "CLIENT_002");
        Directory.CreateDirectory(clientDir);
        File.WriteAllText(Path.Combine(clientDir, "pseudocode.md"), "test");
        // Missing transform.py and metadata.json

        var result = _sut.GetApprovedCode("CLIENT_002");
        result.Should().BeNull();
    }

    [Fact]
    public void SaveApprovedCode_OverwritesExisting()
    {
        var metadata = new ApprovedCodeMetadata("CLIENT_001", "auditor", DateTime.UtcNow);

        _sut.SaveApprovedCode("CLIENT_001", "V1", "code_v1", metadata);
        _sut.SaveApprovedCode("CLIENT_001", "V2", "code_v2", metadata);

        var result = _sut.GetApprovedCode("CLIENT_001");
        result!.Pseudocode.Should().Be("V2");
        result.PySparkCode.Should().Be("code_v2");
    }
}
