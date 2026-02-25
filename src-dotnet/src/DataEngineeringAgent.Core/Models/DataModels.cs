namespace DataEngineeringAgent.Core.Models;

public record DataSample(
    List<string> Columns,
    Dictionary<string, string> Dtypes,
    int RowCount,
    List<Dictionary<string, object?>> SampleRows);

public record SheetData(
    List<string> Columns,
    int RowCount,
    List<Dictionary<string, object?>> SampleRows);

public record DataProfile(
    Dictionary<string, ColumnProfile> Columns,
    int RowCount,
    int TotalColumns,
    List<string> Anomalies);

public record ColumnProfile(
    string Dtype,
    int NullCount,
    double NullRate,
    int UniqueCount,
    double? Min = null,
    double? Max = null,
    double? Mean = null,
    Dictionary<string, int>? TopValues = null);
