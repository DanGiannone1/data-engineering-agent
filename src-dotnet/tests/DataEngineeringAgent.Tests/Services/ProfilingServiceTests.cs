using DataEngineeringAgent.Core.Models;
using DataEngineeringAgent.Core.Services;
using FluentAssertions;
using Xunit;

namespace DataEngineeringAgent.Tests.Services;

public class ProfilingServiceTests
{
    private readonly ProfilingService _sut = new();

    [Fact]
    public void ProfileData_EmptyData_ReturnsEmptyProfile()
    {
        var data = new DataSample([], new Dictionary<string, string>(), 0, []);

        var result = _sut.ProfileData(data);

        result.RowCount.Should().Be(0);
        result.Columns.Should().BeEmpty();
        result.Anomalies.Should().BeEmpty();
    }

    [Fact]
    public void ProfileData_NumericColumn_ComputesMinMaxMean()
    {
        var data = new DataSample(
            ["amount"],
            new Dictionary<string, string> { ["amount"] = "float64" },
            3,
            [
                new() { ["amount"] = 10.0 },
                new() { ["amount"] = 20.0 },
                new() { ["amount"] = 30.0 },
            ]);

        var result = _sut.ProfileData(data);

        result.Columns.Should().ContainKey("amount");
        var col = result.Columns["amount"];
        col.Min.Should().Be(10.0);
        col.Max.Should().Be(30.0);
        col.Mean.Should().Be(20.0);
        col.NullCount.Should().Be(0);
        col.UniqueCount.Should().Be(3);
    }

    [Fact]
    public void ProfileData_StringColumn_ComputesTopValues()
    {
        var data = new DataSample(
            ["status"],
            new Dictionary<string, string> { ["status"] = "object" },
            4,
            [
                new() { ["status"] = "active" },
                new() { ["status"] = "active" },
                new() { ["status"] = "closed" },
                new() { ["status"] = "active" },
            ]);

        var result = _sut.ProfileData(data);

        var col = result.Columns["status"];
        col.TopValues.Should().NotBeNull();
        col.TopValues!["active"].Should().Be(3);
        col.TopValues["closed"].Should().Be(1);
    }

    [Fact]
    public void ProfileData_HighNullRate_FlagsAnomaly()
    {
        var data = new DataSample(
            ["value"],
            new Dictionary<string, string> { ["value"] = "float64" },
            4,
            [
                new() { ["value"] = null },
                new() { ["value"] = null },
                new() { ["value"] = null },
                new() { ["value"] = 1.0 },
            ]);

        var result = _sut.ProfileData(data);

        result.Anomalies.Should().Contain(a => a.Contains("value") && a.Contains("50%"));
    }

    [Fact]
    public void ProfileData_ConstantColumn_FlagsAnomaly()
    {
        var data = new DataSample(
            ["type"],
            new Dictionary<string, string> { ["type"] = "object" },
            3,
            [
                new() { ["type"] = "A" },
                new() { ["type"] = "A" },
                new() { ["type"] = "A" },
            ]);

        var result = _sut.ProfileData(data);

        result.Anomalies.Should().Contain(a => a.Contains("type") && a.Contains("1 unique value"));
    }
}
