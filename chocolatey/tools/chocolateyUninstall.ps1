$ErrorActionPreference = 'Stop';

$packageName = $env:ChocolateyPackageName

# This will remove the Start Menu shortcut created during installation
Remove-ChocolateyShortcut -shortcutFilePath (Join-Path $env:ProgramData "Microsoft\Windows\Start Menu\Programs\$($packageName).lnk")