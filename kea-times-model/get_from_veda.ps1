param (
    [string]$vedaWorkingDir,
    [string]$scenario
)

# Store the original directory to return to it later
$originalDir = Get-Location

if (-not $vedaWorkingDir) {
    # Prompt user for the VEDA working directory with a potential working directory as default
    $vedaWorkingDir = Read-Host "Enter the VEDA working directory [Default: C:\Users\$env:USERNAME\Veda2\Veda\GAMS_WrkTIMES]"
    if ($vedaWorkingDir -eq "") {
        $vedaWorkingDir = "C:\Users\$env:USERNAME\Veda2\Veda\GAMS_WrkTIMES"
    }
}

if (-not (Test-Path -Path $vedaWorkingDir)) {
    Write-Host "VEDA working directory not found: $vedaWorkingDir"
    return
}

if (-not $scenario) {
    # Get available scenario names
    $scenarios = Get-ChildItem -Path $vedaWorkingDir -Directory | Select-Object -ExpandProperty Name
    if ($scenarios.Count -eq 0) {
        Write-Host "No scenarios found in the VEDA working directory."
        return
    }
    $scenarioList = $scenarios -join ", "
    # Prompt user for the scenario name
    $scenario = Read-Host "Enter the scenario name [Available: $scenarioList]"
}

# Abort if no scenario is specified
if (-not $scenario) {
    Write-Host "No scenario specified. Aborting."
    return
}

if (-not (Test-Path -Path "$vedaWorkingDir\$scenario")) {
    Write-Host "Scenario directory not found in VEDA working directory: $scenario"
    return
}

$scenarioDir = Join-Path $PSScriptRoot $scenario

# Check if the scenario directory exists, if not, create it
if (Test-Path -Path $scenarioDir) {
    # Empty the scenario directory
    Write-Host "Clearing contents of the scenario directory: $scenarioDir"
    Remove-Item "$scenarioDir\*" -Recurse -Force
} else {
    New-Item -ItemType Directory -Path $scenarioDir
}

# Copy the necessary files from the VEDA working directory to the scenario directory
Copy-Item -Path "$vedaWorkingDir\$scenario\*.dd" -Destination $scenarioDir
Copy-Item -Path "$vedaWorkingDir\$scenario\$scenario.run" -Destination $scenarioDir
Copy-Item -Path "$vedaWorkingDir\$scenario\cplex.opt" -Destination $scenarioDir
Copy-Item -Path "$vedaWorkingDir\$scenario\times2veda.vdd" -Destination $scenarioDir

# Return to the original directory
Set-Location -Path $originalDir
