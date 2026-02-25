using DataEngineeringAgent.Core.Services;
using FluentAssertions;
using Xunit;

namespace DataEngineeringAgent.Tests.Services;

public class OutputPathRewriterTests
{
    [Fact]
    public void Rewrite_ReplacesOutputPath()
    {
        var code = """
            df.write.parquet("abfss://output@deagentstorage.dfs.core.windows.net/CLIENT_001/20260207_120000")
            """;

        var result = OutputPathRewriter.Rewrite(code, "deagentstorage", "CLIENT_001/20260208_150000");

        result.Should().Contain("CLIENT_001/20260208_150000");
        result.Should().NotContain("20260207_120000");
    }

    [Fact]
    public void Rewrite_HandlesMultipleOccurrences()
    {
        var code = """
            output_path = "abfss://output@deagentstorage.dfs.core.windows.net/CLIENT_001/old"
            df.write.parquet("abfss://output@deagentstorage.dfs.core.windows.net/CLIENT_001/old")
            """;

        var result = OutputPathRewriter.Rewrite(code, "deagentstorage", "CLIENT_001/new");

        var count = result.Split("CLIENT_001/new").Length - 1;
        count.Should().Be(2);
    }

    [Fact]
    public void Rewrite_DoesNotAffectInputPaths()
    {
        var code = """
            input_path = "abfss://data@deagentstorage.dfs.core.windows.net/CLIENT_001/data.csv"
            output_path = "abfss://output@deagentstorage.dfs.core.windows.net/CLIENT_001/old"
            """;

        var result = OutputPathRewriter.Rewrite(code, "deagentstorage", "CLIENT_001/new");

        result.Should().Contain("abfss://data@deagentstorage.dfs.core.windows.net/CLIENT_001/data.csv");
    }
}
