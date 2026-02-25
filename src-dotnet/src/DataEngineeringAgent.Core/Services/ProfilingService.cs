using DataEngineeringAgent.Core.Models;

namespace DataEngineeringAgent.Core.Services;

public class ProfilingService : IProfilingService
{
    public DataProfile ProfileData(DataSample data)
    {
        if (data.SampleRows.Count == 0)
            return new DataProfile(new Dictionary<string, ColumnProfile>(), 0, 0, []);

        var profiles = new Dictionary<string, ColumnProfile>();
        var anomalies = new List<string>();
        var rowCount = data.SampleRows.Count;

        foreach (var col in data.Columns)
        {
            var values = data.SampleRows.Select(r => r.GetValueOrDefault(col)).ToList();
            var nullCount = values.Count(v => v is null);
            var nullRate = Math.Round((double)nullCount / rowCount, 3);
            var nonNull = values.Where(v => v is not null).ToList();
            var uniqueCount = nonNull.Distinct().Count();

            double? min = null, max = null, mean = null;
            Dictionary<string, int>? topValues = null;

            if (nonNull.Count > 0 && TryGetNumericValues(nonNull, out var numericValues))
            {
                min = numericValues.Min();
                max = numericValues.Max();
                mean = Math.Round(numericValues.Average(), 2);
            }
            else if (nonNull.Count > 0)
            {
                topValues = nonNull
                    .Select(v => v?.ToString() ?? "")
                    .GroupBy(v => v)
                    .OrderByDescending(g => g.Count())
                    .Take(5)
                    .ToDictionary(g => g.Key, g => g.Count());
            }

            var dtype = data.Dtypes.GetValueOrDefault(col, "object");

            if (nullRate > 0.5)
                anomalies.Add($"Column '{col}' has >50% nulls ({nullRate:P0})");

            if (uniqueCount == 1 && nonNull.Count > 1)
                anomalies.Add($"Column '{col}' has only 1 unique value (constant)");

            profiles[col] = new ColumnProfile(dtype, nullCount, nullRate, uniqueCount, min, max, mean, topValues);
        }

        return new DataProfile(profiles, rowCount, data.Columns.Count, anomalies);
    }

    private static bool TryGetNumericValues(List<object?> values, out List<double> numericValues)
    {
        numericValues = [];
        foreach (var v in values)
        {
            if (v is double d)
                numericValues.Add(d);
            else if (v is int i)
                numericValues.Add(i);
            else if (v is long l)
                numericValues.Add(l);
            else if (v is decimal dec)
                numericValues.Add((double)dec);
            else if (v is float f)
                numericValues.Add(f);
            else if (double.TryParse(v?.ToString(), out var parsed))
                numericValues.Add(parsed);
            else
                return false;
        }
        return numericValues.Count > 0;
    }
}
