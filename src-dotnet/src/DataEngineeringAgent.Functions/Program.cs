using Azure.Identity;
using Azure.Storage.Files.DataLake;
using Azure.AI.OpenAI;
using DataEngineeringAgent.Core.Configuration;
using DataEngineeringAgent.Core.Services;
using Microsoft.Azure.Cosmos;
using Microsoft.Azure.Functions.Worker;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using Microsoft.Extensions.Options;
using Polly;
using Polly.Extensions.Http;

var host = new HostBuilder()
    .ConfigureFunctionsWorkerDefaults()
    .ConfigureServices((context, services) =>
    {
        var config = context.Configuration;

        // Bind configuration sections
        services.AddOptions<AdlsOptions>()
            .Bind(config.GetSection(AdlsOptions.SectionName))
            .ValidateDataAnnotations()
            .ValidateOnStart();

        services.AddOptions<CosmosOptions>()
            .Bind(config.GetSection(CosmosOptions.SectionName))
            .ValidateDataAnnotations()
            .ValidateOnStart();

        services.AddOptions<DatabricksOptions>()
            .Bind(config.GetSection(DatabricksOptions.SectionName))
            .ValidateDataAnnotations()
            .ValidateOnStart();

        services.AddOptions<OpenAiOptions>()
            .Bind(config.GetSection(OpenAiOptions.SectionName))
            .ValidateDataAnnotations()
            .ValidateOnStart();

        // Azure credential (singleton)
        var credential = new DefaultAzureCredential();
        services.AddSingleton(credential);

        // Azure SDK clients
        services.AddSingleton(sp =>
        {
            var opts = sp.GetRequiredService<IOptions<AdlsOptions>>().Value;
            return new DataLakeServiceClient(
                new Uri($"https://{opts.AccountName}.dfs.core.windows.net"),
                credential);
        });

        services.AddSingleton(sp =>
        {
            var opts = sp.GetRequiredService<IOptions<CosmosOptions>>().Value;
            return new CosmosClient(opts.Endpoint, credential, new CosmosClientOptions
            {
                SerializerOptions = new CosmosSerializationOptions
                {
                    PropertyNamingPolicy = CosmosPropertyNamingPolicy.CamelCase,
                },
            });
        });

        services.AddSingleton(sp =>
        {
            var opts = sp.GetRequiredService<IOptions<OpenAiOptions>>().Value;
            return new AzureOpenAIClient(new Uri(opts.Endpoint), credential);
        });

        // HttpClient with Polly retry for Databricks
        services.AddHttpClient("Databricks")
            .AddPolicyHandler(HttpPolicyExtensions
                .HandleTransientHttpError()
                .WaitAndRetryAsync(3, attempt => TimeSpan.FromSeconds(Math.Pow(2, attempt))));

        // Application services
        services.AddSingleton<IAdlsService, AdlsService>();
        services.AddSingleton<IProfilingService, ProfilingService>();
        services.AddSingleton<IApprovedCodeService, ApprovedCodeService>();
        services.AddSingleton<IOpenAiService, OpenAiService>();
        services.AddSingleton<IDatabricksService, DatabricksService>();
        services.AddSingleton<IIntegrityService, IntegrityService>();

        services.AddSingleton<ICosmosService>(sp =>
        {
            var cosmosClient = sp.GetRequiredService<CosmosClient>();
            var opts = sp.GetRequiredService<IOptions<CosmosOptions>>().Value;
            var logger = sp.GetRequiredService<Microsoft.Extensions.Logging.ILogger<CosmosService>>();
            return new CosmosService(cosmosClient, opts.DatabaseName, logger);
        });

        // Application Insights (only when connection string is configured)
        var aiConnectionString = config["APPLICATIONINSIGHTS_CONNECTION_STRING"];
        if (!string.IsNullOrEmpty(aiConnectionString))
        {
            services.AddApplicationInsightsTelemetryWorkerService();
        }
    })
    .Build();

host.Run();
