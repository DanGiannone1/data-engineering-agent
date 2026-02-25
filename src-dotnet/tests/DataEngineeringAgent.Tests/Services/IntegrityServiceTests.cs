using DataEngineeringAgent.Core.Models;
using DataEngineeringAgent.Core.Services;
using FluentAssertions;
using Microsoft.Extensions.Logging;
using Moq;
using Xunit;

namespace DataEngineeringAgent.Tests.Services;

public class IntegrityServiceTests
{
    private readonly Mock<IAdlsService> _adlsMock = new();
    private readonly IntegrityService _sut;

    public IntegrityServiceTests()
    {
        _sut = new IntegrityService(_adlsMock.Object, Mock.Of<ILogger<IntegrityService>>());
    }

    [Fact]
    public async Task RunIntegrityChecks_ValidOutput_Passes()
    {
        var sample = new DataSample(
            ["id", "name", "amount"],
            new Dictionary<string, string> { ["id"] = "int64", ["name"] = "object", ["amount"] = "float64" },
            10,
            [
                new() { ["id"] = 1, ["name"] = "Alice", ["amount"] = 100.0 },
                new() { ["id"] = 2, ["name"] = "Bob", ["amount"] = 200.0 },
            ]);

        _adlsMock.Setup(a => a.ReadSparkOutputAsync(It.IsAny<string>(), 50))
            .ReturnsAsync(sample);

        var result = await _sut.RunIntegrityChecksAsync("test/output");

        result.OverallPass.Should().BeTrue();
        result.Errors.Should().BeEmpty();
    }

    [Fact]
    public async Task RunIntegrityChecks_EmptyOutput_Fails()
    {
        var sample = new DataSample(
            ["id"],
            new Dictionary<string, string> { ["id"] = "int64" },
            0,
            []);

        _adlsMock.Setup(a => a.ReadSparkOutputAsync(It.IsAny<string>(), 50))
            .ReturnsAsync(sample);

        var result = await _sut.RunIntegrityChecksAsync("test/output");

        result.OverallPass.Should().BeFalse();
        result.Errors.Should().Contain("Output has 0 rows");
    }

    [Fact]
    public async Task RunIntegrityChecks_NullColumn_Fails()
    {
        var sample = new DataSample(
            ["id", "bad_col"],
            new Dictionary<string, string> { ["id"] = "int64", ["bad_col"] = "object" },
            2,
            [
                new() { ["id"] = 1, ["bad_col"] = null },
                new() { ["id"] = 2, ["bad_col"] = null },
            ]);

        _adlsMock.Setup(a => a.ReadSparkOutputAsync(It.IsAny<string>(), 50))
            .ReturnsAsync(sample);

        var result = await _sut.RunIntegrityChecksAsync("test/output");

        result.OverallPass.Should().BeFalse();
        result.Errors.Should().Contain(e => e.Contains("bad_col") && e.Contains("null"));
    }

    [Fact]
    public async Task RunIntegrityChecks_Duplicates_Fails()
    {
        var sample = new DataSample(
            ["id", "name"],
            new Dictionary<string, string> { ["id"] = "int64", ["name"] = "object" },
            3,
            [
                new() { ["id"] = 1, ["name"] = "Alice" },
                new() { ["id"] = 1, ["name"] = "Alice" },
                new() { ["id"] = 2, ["name"] = "Bob" },
            ]);

        _adlsMock.Setup(a => a.ReadSparkOutputAsync(It.IsAny<string>(), 50))
            .ReturnsAsync(sample);

        var result = await _sut.RunIntegrityChecksAsync("test/output");

        result.OverallPass.Should().BeFalse();
        result.Errors.Should().Contain(e => e.Contains("duplicate"));
    }

    [Fact]
    public async Task RunIntegrityChecks_ReadFailure_ReturnsFailReport()
    {
        _adlsMock.Setup(a => a.ReadSparkOutputAsync(It.IsAny<string>(), 50))
            .ThrowsAsync(new Exception("Connection refused"));

        var result = await _sut.RunIntegrityChecksAsync("test/output");

        result.OverallPass.Should().BeFalse();
        result.Checks.Should().ContainSingle(c => c.Name == "read_output" && !c.Passed);
    }

    [Fact]
    public async Task RunIntegrityChecks_MissingColumns_Fails()
    {
        var sample = new DataSample(
            ["id", "name"],
            new Dictionary<string, string> { ["id"] = "int64", ["name"] = "object" },
            2,
            [
                new() { ["id"] = 1, ["name"] = "Alice" },
                new() { ["id"] = 2, ["name"] = "Bob" },
            ]);

        _adlsMock.Setup(a => a.ReadSparkOutputAsync(It.IsAny<string>(), 50))
            .ReturnsAsync(sample);

        var result = await _sut.RunIntegrityChecksAsync("test/output", ["id", "name", "amount"]);

        result.OverallPass.Should().BeFalse();
        result.Errors.Should().Contain(e => e.Contains("amount"));
    }
}
