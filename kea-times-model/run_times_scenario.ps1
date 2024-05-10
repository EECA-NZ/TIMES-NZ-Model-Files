param (
    [string]$scenario
)

# Store the original directory to return to it later
$originalDir = Get-Location

# Function to get the list of scenarios
function Get-ScenarioNames {
    Get-ChildItem -Path $originalDir -Directory | Where-Object { $_.GetFiles("*.dd").Count -gt 0 } | Select-Object -ExpandProperty Name
}

# Function to find the highest version folder that starts with GAMS_SrcTIMES
function Get-HighestVersionGAMSDir {
    $baseDir = "C:\Users\$env:USERNAME\Veda2\Veda\"
    $searchPattern = "GAMS_SrcTIMES*"
    $dirs = Get-ChildItem -Path $baseDir -Directory -Filter $searchPattern
    if ($dirs.Count -eq 0) {
        return $null
    }

    # Extract numeric versions from folder names and sort them in descending order
    $sortedDirs = $dirs | Sort-Object -Property { 
        [version]($_.Name -replace "^GAMS_SrcTIMES.v", "")
    } -Descending
    return $sortedDirs[0].FullName
}

try {
    if (-not $scenario) {
        # Get available scenario names
        $scenarios = Get-ScenarioNames
        $scenarioList = $scenarios -join ", "
        # Prompt user for the scenario name
        $scenario = Read-Host "Enter the scenario name [Available: $scenarioList]"
    }

    $scenarioDir = Join-Path $originalDir $scenario
    if (-not (Test-Path -Path $scenarioDir)) {
        Write-Host "Scenario directory not found: $scenario"
        return
    }
    Set-Location -Path $scenarioDir

    if (-not $source_dir) {
        # Get the highest version GAMS directory
        $defaultGAMSDir = Get-HighestVersionGAMSDir
        if ($defaultGAMSDir) {
            $source_dir = Read-Host "Enter the TIMES source directory [Default: $defaultGAMSDir]"
            if ($source_dir -eq "") {
                $source_dir = $defaultGAMSDir
            }
        } else {
            $source_dir = Read-Host "Enter the TIMES source directory [Default: C:\Users\$env:USERNAME\Veda2\Veda\GAMS_SrcTIMES.v4.7.6]"
            if ($source_dir -eq "") {
                $source_dir = "C:\Users\$env:USERNAME\Veda2\Veda\GAMS_SrcTIMES.v4.7.6"
            }
        }
    }

    $gams_save_dir = Join-Path $originalDir "GAMSSAVE"

    # Check if necessary files exist before running GAMS and GDX2VEDA
    if ((Test-Path -Path "$scenario.run") -and (Test-Path -Path "times2veda.vdd")) {
        # Ensure the GAMSSAVE directory exists
        if (-not (Test-Path -Path $gams_save_dir)) {
            New-Item -ItemType Directory -Path $gams_save_dir
        }
        # Run GAMS to solve the scenario
        $gams_command = "GAMS " + $scenario + ".RUN IDIR=" + $source_dir + " GDX=" + $gams_save_dir + "\" + $scenario + " PS=99999 r=" + $source_dir + "\_times"
        Write-Host "Running GAMS with command: $gams_command"
        Invoke-Expression $gams_command
        # Run GDX2VEDA to convert the GDX file to VEDA format
        $gdx2veda_command = "GDX2VEDA " + $gams_save_dir + "\" + $scenario + " times2veda.vdd " + $scenario
        Write-Host "Running GDX2VEDA with command: $gdx2veda_command"
        Invoke-Expression $gdx2veda_command
    } else {
        Write-Host "Necessary files missing to run the scenario: $scenario"
    }
} catch {
    Write-Host "An error occurred: $_"
} finally {
    # Return to the original directory
    Set-Location -Path $originalDir
}
