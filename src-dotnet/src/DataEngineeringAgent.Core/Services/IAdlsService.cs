using DataEngineeringAgent.Core.Models;

namespace DataEngineeringAgent.Core.Services;

public interface IAdlsService
{
    Task<byte[]> DownloadFileAsync(string container, string path);
    Task<List<string>> ListFilesAsync(string container, string prefix = "");
    Task<Dictionary<string, SheetData>> ReadMappingSpreadsheetAsync(string path);
    Task<DataSample> SampleSourceDataAsync(string path, int nRows = 100);
    Task<DataSample> ReadSparkOutputAsync(string path, int nRows = 50);
}
