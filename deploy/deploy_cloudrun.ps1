<#
.SYNOPSIS
  Deploy CodeFix AI (web app + ADK/CrewAI agents + A2A + MCP) to Google Cloud Run.

.DESCRIPTION
  Builds the Dockerfile with Cloud Build (no local Docker needed), stores ZAI_API_KEY from
  .env in Secret Manager (never in the image or in plain env vars), deploys the service and then
  sets CODEFIX_PUBLIC_URL so the A2A agent card advertises the real URL.

  Prerequisites (once):  gcloud auth login ; a project with billing enabled.

.EXAMPLE
  ./deploy/deploy_cloudrun.ps1 -Project my-gcp-project            # private (needs a Google login to open)
  ./deploy/deploy_cloudrun.ps1 -Project my-gcp-project -Public    # anyone with the URL can use it
#>
param(
    [Parameter(Mandatory = $true)][string]$Project,
    [string]$Region = "asia-south1",
    [string]$Service = "codefix-ai",
    [switch]$Public
)
$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)

function Run([string[]]$cmdArgs) {
    & gcloud @cmdArgs
    if ($LASTEXITCODE -ne 0) { throw "gcloud $($cmdArgs -join ' ') failed" }
}

Run @("config", "set", "project", $Project)
Run @("services", "enable", "run.googleapis.com", "cloudbuild.googleapis.com", "artifactregistry.googleapis.com",
      "secretmanager.googleapis.com")

# --- ZAI_API_KEY -> Secret Manager (read from .env, never printed) ----------------------------
$line = Get-Content .env | Where-Object { $_ -match '^ZAI_API_KEY=(.+)$' } | Select-Object -First 1
if (-not $line) { throw "ZAI_API_KEY is not set in .env" }
$tmp = ([System.IO.Path]::GetTempFileName())
try {
    [IO.File]::WriteAllText($tmp, ($line -replace '^ZAI_API_KEY=', '').Trim())
    & gcloud secrets describe zai-api-key *> $null
    if ($LASTEXITCODE -ne 0) {
        Run @("secrets", "create", "zai-api-key", "--replication-policy=automatic", "--data-file=$tmp")
    } else {
        Run @("secrets", "versions", "add", "zai-api-key", "--data-file=$tmp")
    }
} finally { Remove-Item $tmp -Force }

# --- CODEFIX_A2A_TOKEN -> Secret Manager -----------------------------------------------------
# On a -Public service the A2A endpoint is reachable by anyone who finds the URL, so the shared
# bearer secret is what stops a stranger driving the CrewAI workers (and spending the API key).
# Reuse the value from .env if present, otherwise mint one; the agent card stays public either way.
& gcloud secrets describe codefix-a2a-token *> $null
if ($LASTEXITCODE -ne 0) {
    $envTok = Get-Content .env -ErrorAction SilentlyContinue |
              Where-Object { $_ -match '^CODEFIX_A2A_TOKEN=(.+)$' } | Select-Object -First 1
    $token = if ($envTok) { ($envTok -replace '^CODEFIX_A2A_TOKEN=', '').Trim() }
             else { [Convert]::ToBase64String([Security.Cryptography.RandomNumberGenerator]::GetBytes(32)) }
    $tmp2 = ([System.IO.Path]::GetTempFileName())
    try {
        [IO.File]::WriteAllText($tmp2, $token)
        Run @("secrets", "create", "codefix-a2a-token", "--replication-policy=automatic", "--data-file=$tmp2")
    } finally { Remove-Item $tmp2 -Force }
}

$number = (& gcloud projects describe $Project --format "value(projectNumber)").Trim()
$runtimeSa = "$number-compute@developer.gserviceaccount.com"
foreach ($secret in @("zai-api-key", "codefix-a2a-token")) {
    Run @("secrets", "add-iam-policy-binding", $secret, "--member=serviceAccount:$runtimeSa",
          "--role=roles/secretmanager.secretAccessor", "--quiet")
}

# --- build + deploy -------------------------------------------------------------------------------
$auth = if ($Public) { "--allow-unauthenticated" } else { "--no-allow-unauthenticated" }
# --no-cpu-throttling is REQUIRED, not a tuning knob. A run is started by POST /api/runs, which
# returns a task_id immediately and does the pipeline on a background thread. Cloud Run's default
# allocates CPU only while a request is in flight, so that thread is starved the moment the POST
# responds and the run sits at 0 attempts forever. Always-allocated CPU costs more per instance-
# hour, but the service still scales to zero when idle.
Run @("run", "deploy", $Service, "--source", ".", "--region", $Region, $auth, "--no-cpu-throttling",
      "--memory", "4Gi", "--cpu", "2", "--timeout", "3600", "--concurrency", "4", "--max-instances", "2",
      "--set-secrets", "ZAI_API_KEY=zai-api-key:latest,CODEFIX_A2A_TOKEN=codefix-a2a-token:latest", "--quiet")

$url = (& gcloud run services describe $Service --region $Region --format "value(status.url)").Trim()
Run @("run", "services", "update", $Service, "--region", $Region, "--update-env-vars", "CODEFIX_PUBLIC_URL=$url",
      "--quiet")

Write-Host ""
Write-Host "Deployed: $url"
Write-Host "  web app        $url/"
Write-Host "  A2A agent card $url/a2a/crew/.well-known/agent-card.json  (public by design)"
if ($Public) {
    Write-Host "  A2A message/send requires the bearer token in Secret Manager: codefix-a2a-token"
    Write-Host "  Read it with:  gcloud secrets versions access latest --secret codefix-a2a-token"
}
if (-not $Public) {
    Write-Host "  (private service: open it through  gcloud run services proxy $Service --region $Region  -> http://localhost:8080)"
}
