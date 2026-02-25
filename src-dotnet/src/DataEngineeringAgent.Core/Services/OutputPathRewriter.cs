using System.Text.RegularExpressions;

namespace DataEngineeringAgent.Core.Services;

public static class OutputPathRewriter
{
    /// <summary>
    /// Rewrites all ADLS paths in reused PySpark code to use the current storage account
    /// and updates the output path to this run's timestamped location.
    /// </summary>
    public static string Rewrite(string pysparkCode, string storageAccount, string newOutputPath)
    {
        // Replace any storage account name in abfss:// URIs with the current one
        var result = Regex.Replace(
            pysparkCode,
            @"abfss://(\w+)@[\w]+\.dfs\.core\.windows\.net/",
            $"abfss://$1@{storageAccount}.dfs.core.windows.net/");

        // Replace the output path specifically (now that the account is correct)
        var newOutput = $"abfss://output@{storageAccount}.dfs.core.windows.net/{newOutputPath}";
        var outputPattern = $@"abfss://output@{Regex.Escape(storageAccount)}\.dfs\.core\.windows\.net/[^""'\)\s]+";
        result = Regex.Replace(result, outputPattern, newOutput);

        return result;
    }
}
