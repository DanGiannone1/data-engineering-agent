using System.Net.Http.Json;
using System.Text;
using System.Text.Json;
using Azure.Identity;
using DataEngineeringAgent.Core.Configuration;
using DataEngineeringAgent.Core.Models;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Options;

namespace DataEngineeringAgent.Core.Services;

public class DatabricksService : IDatabricksService
{
    private const string DatabricksResourceId = "2ff814a6-3304-4ab8-85cb-cd0e6f879c1d";
    private const int PollIntervalSeconds = 15;
    private const int TimeoutSeconds = 1800;

    private readonly IHttpClientFactory _httpClientFactory;
    private readonly DatabricksOptions _databricksOptions;
    private readonly AdlsOptions _adlsOptions;
    private readonly DefaultAzureCredential _credential;
    private readonly ILogger<DatabricksService> _logger;

    public DatabricksService(
        IHttpClientFactory httpClientFactory,
        IOptions<DatabricksOptions> databricksOptions,
        IOptions<AdlsOptions> adlsOptions,
        DefaultAzureCredential credential,
        ILogger<DatabricksService> logger)
    {
        _httpClientFactory = httpClientFactory;
        _databricksOptions = databricksOptions.Value;
        _adlsOptions = adlsOptions.Value;
        _credential = credential;
        _logger = logger;
    }

    public async Task<string> SubmitSparkJobAsync(string pysparkCode, string clientId = "")
    {
        var client = await CreateAuthenticatedClient();
        var host = _databricksOptions.Host.TrimEnd('/');

        // Upload notebook via Workspace API
        var jobId = Guid.NewGuid().ToString("N")[..12];
        var notebookPath = $"/Shared/dea_transform_{jobId}";

        var importPayload = new
        {
            path = notebookPath,
            format = "SOURCE",
            language = "PYTHON",
            content = Convert.ToBase64String(Encoding.UTF8.GetBytes(pysparkCode)),
            overwrite = true,
        };

        var importResp = await client.PostAsJsonAsync($"{host}/api/2.0/workspace/import", importPayload);
        importResp.EnsureSuccessStatusCode();

        var sparkConf = BuildSparkConf();

        var submitPayload = new
        {
            run_name = string.IsNullOrEmpty(clientId) ? "dea-transform" : $"dea-transform-{clientId}",
            new_cluster = new
            {
                spark_version = _databricksOptions.SparkVersion,
                node_type_id = _databricksOptions.NodeTypeId,
                num_workers = _databricksOptions.NumWorkers,
                spark_conf = sparkConf,
            },
            notebook_task = new { notebook_path = notebookPath },
            libraries = new[] { new { pypi = new { package = "openpyxl" } } },
        };

        var submitResp = await client.PostAsJsonAsync($"{host}/api/2.1/jobs/runs/submit", submitPayload);
        submitResp.EnsureSuccessStatusCode();

        var result = await submitResp.Content.ReadFromJsonAsync<JsonElement>();
        var runId = result.GetProperty("run_id").GetInt64().ToString();

        _logger.LogInformation("Submitted Spark job: run_id={RunId}, notebook={Notebook}", runId, notebookPath);
        return runId;
    }

    public async Task<SparkRunStatus> GetRunStatusAsync(string runId)
    {
        var client = await CreateAuthenticatedClient();
        var host = _databricksOptions.Host.TrimEnd('/');

        var resp = await client.GetAsync($"{host}/api/2.1/jobs/runs/get?run_id={runId}");
        resp.EnsureSuccessStatusCode();

        var data = await resp.Content.ReadFromJsonAsync<JsonElement>();
        var state = data.GetProperty("state");
        var lifeCycleState = state.GetProperty("life_cycle_state").GetString()!;
        var resultState = state.TryGetProperty("result_state", out var rs) ? rs.GetString() ?? "" : "";
        var errorLog = state.TryGetProperty("state_message", out var sm) ? sm.GetString() ?? "" : "";

        var done = lifeCycleState is "TERMINATED" or "SKIPPED" or "INTERNAL_ERROR";
        var success = resultState == "SUCCESS";

        // Fetch notebook output for better error details on failure
        if (done && !success)
        {
            try
            {
                var outResp = await client.GetAsync($"{host}/api/2.1/jobs/runs/get-output?run_id={runId}");
                outResp.EnsureSuccessStatusCode();
                var outData = await outResp.Content.ReadFromJsonAsync<JsonElement>();

                if (outData.TryGetProperty("error_trace", out var trace) && trace.GetString() is { } traceStr)
                {
                    errorLog = traceStr.Length > 3000 ? traceStr[^3000..] : traceStr;
                }
                else if (outData.TryGetProperty("error", out var err) && err.GetString() is { } errStr)
                {
                    errorLog = errStr;
                }
            }
            catch (Exception ex)
            {
                _logger.LogWarning(ex, "Failed to fetch notebook output for run {RunId}", runId);
            }
        }

        return new SparkRunStatus(lifeCycleState, resultState, errorLog, done, success);
    }

    public async Task<SparkExecutionResult> ExecuteSparkJobAsync(string pysparkCode, string clientId)
    {
        _logger.LogInformation("Submitting Spark job for {ClientId}", clientId);
        var runId = await SubmitSparkJobAsync(pysparkCode, clientId);

        var elapsed = 0;
        while (elapsed < TimeoutSeconds)
        {
            var status = await GetRunStatusAsync(runId);
            if (status.Done)
            {
                if (status.Success)
                    _logger.LogInformation("Spark job {RunId} succeeded", runId);
                else
                    _logger.LogWarning("Spark job {RunId} failed: {Error}", runId, status.ErrorLog);

                return new SparkExecutionResult(status.Success, runId, status.ErrorLog);
            }

            await Task.Delay(TimeSpan.FromSeconds(PollIntervalSeconds));
            elapsed += PollIntervalSeconds;
        }

        return new SparkExecutionResult(false, runId, $"Timed out after {TimeoutSeconds}s");
    }

    private async Task<HttpClient> CreateAuthenticatedClient()
    {
        var client = _httpClientFactory.CreateClient("Databricks");
        var token = await _credential.GetTokenAsync(
            new Azure.Core.TokenRequestContext([$"{DatabricksResourceId}/.default"]));
        client.DefaultRequestHeaders.Authorization =
            new System.Net.Http.Headers.AuthenticationHeaderValue("Bearer", token.Token);
        return client;
    }

    private Dictionary<string, string> BuildSparkConf()
    {
        var sa = _adlsOptions.AccountName;

        return new Dictionary<string, string>
        {
            [$"fs.azure.account.auth.type.{sa}.dfs.core.windows.net"] = "OAuth",
            [$"fs.azure.account.oauth.provider.type.{sa}.dfs.core.windows.net"] =
                "org.apache.hadoop.fs.azurebfs.oauth2.ClientCredsTokenProvider",
            [$"fs.azure.account.oauth2.client.id.{sa}.dfs.core.windows.net"] = _databricksOptions.SpClientId,
            [$"fs.azure.account.oauth2.client.secret.{sa}.dfs.core.windows.net"] = _databricksOptions.SpClientSecret,
            [$"fs.azure.account.oauth2.client.endpoint.{sa}.dfs.core.windows.net"] =
                $"https://login.microsoftonline.com/{_databricksOptions.TenantId}/oauth2/token",
        };
    }
}
