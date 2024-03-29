$ProjectName = "wagtail_feedback"

param (
    [Parameter(Mandatory=$false)]
    [string]$CommitMessage = "Update to package"
)


Function GITHUB_Upload {
    param (
        [string]$Version,
        [string]$CommitMessage = "Update to package"
    )

    git add .
    $gitVersion = "v${Version}"
    git tag $gitVersion
    git commit -m $CommitMessage
    git push -u origin main --tags
}

Function _NextVersionString {
    param (
        [string]$Version
    )

    $versionParts = $version -split "\."

    $major = [int]$versionParts[0]
    $minor = [int]$versionParts[1]
    $patch = [int]$versionParts[2] + 1

    if ($patch -gt 9) {
        $patch = 0
        $minor += 1
    }

    if ($minor -gt 9) {
        $minor = 0
        $major += 1
    }

    $newVersion = "$major.$minor.$patch"

    return $newVersion
}

function PYPI_NextVersion {
    param (
        [string]$ConfigFile = ".\setup.cfg"
    )
    # Read file content
    $fileContent = Get-Content -Path $ConfigFile

    # Extract the version, increment it, and prepare the updated version string
    $versionLine = $fileContent | Where-Object { $_ -match "version\s*=" }
    $version = $versionLine -split "=", 2 | ForEach-Object { $_.Trim() } | Select-Object -Last 1
    $newVersion = _NextVersionString -Version $version
    return $newVersion
}

function GITHUB_NextVersion {
    param (
        [string]$ConfigFile = ".\setup.cfg",
        [string]$PyVersionFile = ".\${ProjectName}\__init__.py"
    )


    # Extract the version, increment it, and prepare the updated version string
    try {
        $version = "$(git tag -l --format='VERSION=%(refname:short)' | Sort-Object -Descending | Select-Object -First 1)" -split "=v", 2 | ForEach-Object { $_.Trim() } | Select-Object -Last 1
        $newVersion = _NextVersionString -Version $version

        Write-Host "Next version (git): $newVersion"
    } catch {
        git init
        git add .
        git branch -M "main"
        git remote set-url origin "git@github.com:Nigel2392/$(ProjectName).git"
        $newVersion = PYPI_NextVersion -ConfigFile $ConfigFile
        Write-Host "Next version (pypi): $newVersion"
    }
    return $newVersion
}

Function GITHUB_UpdateVersion {
    param (
        [string]$ConfigFile = ".\setup.cfg",
        [string]$PyVersionFile = ".\${ProjectName}\__init__.py"
    )

    $newVersion = GITHUB_NextVersion -ConfigFile $ConfigFile

    # First update the init file so that in case something goes wrong 
    # the version doesn't persist in the config file
    if (Test-Path $PyVersionFile) {
        $initContent = Get-Content -Path $PyVersionFile
        $initContent = $initContent -replace "__version__\s*=\s*.+", "__version__ = '$newVersion'"
        Set-Content -Path $PyVersionFile -Value $initContent
    }

    # Read file content
    $fileContent = Get-Content -Path $ConfigFile

    # Update the version line in the file content
    Write-Host "Updating version in $ConfigFile to $newVersion"
    $updatedContent = $fileContent -replace "version\s*=\s*.+", "version = $newVersion"

    # Write the updated content back to the file
    Set-Content -Path $ConfigFile -Value $updatedContent

    return $newVersion
}

Function _PYPI_DistName {
    param (
        [string]$Version,
        [string]$Append = ".tar.gz"
    )

    return "$ProjectName-$Version$Append"
}

Function PYPI_Build {
    Write-Host "Building package"
    py .\setup.py sdist
}

Function PYPI_Check {
    param (
        [string]$Version
    )
    Write-Host "Testing package"

    $distFile = _PYPI_DistName -Version $Version
    py -m twine check "./dist/${distFile}"
}

Function PYPI_Upload {
    param (
        [string]$Version
    )
    Write-Host "Uploading package"

    $distFile = _PYPI_DistName -Version $Version
    py -m twine upload "./dist/${distFile}"
}



$version = GITHUB_UpdateVersion                               # Update the package version     (setup.cfg)
GITHUB_Upload -Version $version -CommitMessage $CommitMessage # Upload the package             (twine upload dist/<LATEST>)
PYPI_Build                                                    # Build the package              (python setup.py sdist)
PYPI_Check -Version $version                                  # Check the package              (twine check dist/<LATEST>)
PYPI_Upload -Version $version                                 # Upload the package             (twine upload dist/<LATEST>)




