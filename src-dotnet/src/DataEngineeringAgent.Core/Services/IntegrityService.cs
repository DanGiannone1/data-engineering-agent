using DataEngineeringAgent.Core.Models;
using Microsoft.Extensions.Logging;

namespace DataEngineeringAgent.Core.Services;

public class IntegrityService : IIntegrityService
{
    private readonly IAdlsService _adlsService;
    private readonly ILogger<IntegrityService> _logger;

    public IntegrityService(IAdlsService adlsService, ILogger<IntegrityService> logger)
    {
        _adlsService = adlsService;
        _logger = logger;
    }

    public async Task<IntegrityReport> RunIntegrityChecksAsync(string outputPath, List<string>? expectedColumns = null)
    {
        var checks = new List<CheckResult>();
        var errors = new List<string>();

        // 1. Read output
        DataSample output;
        try
        {
            output = await _adlsService.ReadSparkOutputAsync(outputPath);
        }
        catch (Exception e)
        {
            return new IntegrityReport(
                [new CheckResult("read_output", false, $"Failed to read output: {e.Message}")],
                false,
                [e.Message]);
        }

        // 2. Row count check
        var rowCountPass = output.RowCount > 0;
        checks.Add(new CheckResult(
            "row_count", rowCountPass, $"Output has {output.RowCount} rows",
            new Dictionary<string, object> { ["row_count"] = output.RowCount }));
        if (!rowCountPass)
            errors.Add("Output has 0 rows");

        // 3. Schema conformance
        if (expectedColumns is { Count: > 0 })
        {
            var actualCols = output.Columns.ToHashSet();
            var missing = expectedColumns.Where(c => !actualCols.Contains(c)).ToList();
            var pass = missing.Count == 0;
            checks.Add(new CheckResult(
                "schema_conformance",
                pass,
                pass ? "All expected columns present" : $"Missing columns: {string.Join(", ", missing)}",
                new Dictionary<string, object>
                {
                    ["missing"] = missing,
                    ["actual"] = output.Columns,
                }));
            if (!pass)
                errors.Add($"Missing columns: {string.Join(", ", missing)}");
        }

        // 4. Null column check (warning only — entirely null columns may be legitimate
        //    when source data has null fields, especially with small sample sizes)
        if (output.SampleRows.Count > 0)
        {
            foreach (var col in output.Columns)
            {
                var nullCount = output.SampleRows.Count(r => r.GetValueOrDefault(col) is null);
                if (nullCount == output.SampleRows.Count)
                {
                    _logger.LogWarning("Column '{Column}' is entirely null in sample ({Count} rows)", col, output.SampleRows.Count);
                    checks.Add(new CheckResult($"null_check_{col}", true, $"Column '{col}' is entirely null in sample (warning)"));
                }
            }
        }

        // 5. Duplicate check (on sample)
        if (output.SampleRows.Count > 0)
        {
            var sampleStrs = output.SampleRows
                .Select(r => string.Join("|", r.OrderBy(kv => kv.Key).Select(kv => $"{kv.Key}={kv.Value}")))
                .ToList();
            var uniqueCount = sampleStrs.Distinct().Count();
            var dupCount = sampleStrs.Count - uniqueCount;
            checks.Add(new CheckResult(
                "duplicate_check",
                dupCount == 0,
                dupCount > 0 ? $"{dupCount} duplicate rows found in sample" : "No duplicates in sample",
                new Dictionary<string, object>
                {
                    ["duplicates"] = dupCount,
                    ["sample_size"] = sampleStrs.Count,
                }));
            if (dupCount > 0)
                errors.Add($"{dupCount} duplicate rows in sample");
        }

        var overallPass = checks.All(c => c.Passed);
        _logger.LogInformation("Integrity checks for {OutputPath}: {Result}", outputPath, overallPass ? "PASS" : "FAIL");

        return new IntegrityReport(checks, overallPass, errors);
    }
}
