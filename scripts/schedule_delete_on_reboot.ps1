param(
  [string]$ProjectRoot = ".",
  [string[]]$Names = @("health_loop.stdout.log","health_loop.stderr.log")
)
$ErrorActionPreference = "Stop"
$root = (Resolve-Path -LiteralPath $ProjectRoot).Path
$healthRoot = Join-Path -Path $root -ChildPath "logs\health"

# P/Invoke MoveFileEx for delayed delete on reboot
$moveSig = @"
using System;
using System.Runtime.InteropServices;
public static class Win32Move {
  [DllImport("kernel32.dll", SetLastError=true, CharSet=CharSet.Unicode)]
  public static extern bool MoveFileEx(string lpExistingFileName, string lpNewFileName, int dwFlags);
}
"@
Add-Type -TypeDefinition $moveSig -ErrorAction SilentlyContinue | Out-Null
$MOVEFILE_DELAY_UNTIL_REBOOT = 0x00000004

foreach ($name in $Names) {
  $src = Join-Path -Path $healthRoot -ChildPath $name
  if (Test-Path -LiteralPath $src) {
    $ok = [Win32Move]::MoveFileEx($src, $null, $MOVEFILE_DELAY_UNTIL_REBOOT)
    if ($ok) { Write-Host ("Scheduled delete on reboot -> {0}" -f $src) }
    else {
      $err = [Runtime.InteropServices.Marshal]::GetLastWin32Error()
      Write-Warning ("Failed to schedule {0} (err={1})" -f $src, $err)
    }
  }
}
Write-Host "Reboot Windows to complete deletion if files reappear."
