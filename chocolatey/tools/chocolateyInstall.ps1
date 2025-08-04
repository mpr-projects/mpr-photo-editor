$ErrorActionPreference = 'Stop';

$packageName = $env:ChocolateyPackageName
$packageVersion = $env:ChocolateyPackageVersion
$toolsDir = "$(Split-Path -parent $MyInvocation.MyCommand.Definition)"
$installDir = Join-Path $toolsDir "app"

# Construct the download URL from the GitHub release
$url = "https://github.com/mpr-projects/mpr-photo-editor/releases/download/v$($packageVersion)/PhotoEditor-Windows.zip"

$installArgs = @{
  packageName   = $packageName
  unzipLocation = $installDir
  url           = $url
  # You can add checksums here in the future for added security
  # checksum      = ''
  # checksumType  = 'sha256'
}

Install-ChocolateyZipPackage @installArgs

# Create a Start Menu shortcut for the application
$shortcutPath = Join-Path $env:ProgramData "Microsoft\Windows\Start Menu\Programs\$($packageName).lnk"
$targetPath = Join-Path $installDir "PhotoEditor.exe"
Install-ChocolateyShortcut -shortcutFilePath $shortcutPath -targetPath $targetPath