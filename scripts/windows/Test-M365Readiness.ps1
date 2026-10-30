<#
.SYNOPSIS
    Quick client-side checks for Microsoft 365 / Office / Teams / Outlook problems.
.DESCRIPTION
    Read-only. Checks Office install & channel, Outlook profile/OST size,
    DNS + HTTPS reachability of core M365 endpoints, time skew, and
    Teams / OneDrive processes. Prints PASS / WARN / FAIL per check.
#>
[CmdletBinding()]
param()

$results = New-Object System.Collections.Generic.List[object]
function Add-Result($Name, $Status, $Detail) {
    $results.Add([pscustomobject]@{ Check = $Name; Status = $Status; Detail = $Detail })
}

# 1. Office version / update channel
$c2r = 'HKLM:\SOFTWARE\Microsoft\Office\ClickToRun\Configuration'
if (Test-Path $c2r) {
    $cfg = Get-ItemProperty $c2r
    Add-Result 'Office Click-to-Run' 'PASS' "Version $($cfg.VersionToReport); Channel $($cfg.CDNBaseUrl)"
} else {
    Add-Result 'Office Click-to-Run' 'WARN' 'Not found (MSI install or Office not installed)'
}

# 2. Outlook OST size
$ostDir = Join-Path $env:LOCALAPPDATA 'Microsoft\Outlook'
if (Test-Path $ostDir) {
    Get-ChildItem $ostDir -Filter *.ost -ErrorAction SilentlyContinue | ForEach-Object {
        $gb = [math]::Round($_.Length / 1GB, 2)
        $st = if ($gb -gt 25) { 'WARN' } else { 'PASS' }
        Add-Result "OST $($_.Name)" $st "$gb GB"
    }
}

# 3. Endpoint reachability (DNS + TCP 443)
$endpoints = 'outlook.office365.com', 'login.microsoftonline.com', 'teams.microsoft.com', 'graph.microsoft.com'
foreach ($h in $endpoints) {
    try {
        $ip = (Resolve-DnsName $h -Type A -ErrorAction Stop | Where-Object Type -eq 'A' | Select-Object -First 1).IPAddress
        $tcp = Test-NetConnection -ComputerName $h -Port 443 -WarningAction SilentlyContinue
        $st = if ($tcp.TcpTestSucceeded) { 'PASS' } else { 'FAIL' }
        Add-Result "HTTPS $h" $st "DNS $ip; RTT $($tcp.PingReplyDetails.RoundtripTime) ms"
    } catch {
        Add-Result "HTTPS $h" 'FAIL' $_.Exception.Message
    }
}

# 4. Time skew (Kerberos / modern auth are sensitive to it)
try {
    $w32 = w32tm /stripchart /computer:time.windows.com /samples:1 /dataonly 2>$null | Select-Object -Last 1
    Add-Result 'Time skew vs time.windows.com' 'PASS' ($w32 -replace '\s+', ' ')
} catch { Add-Result 'Time skew' 'WARN' 'w32tm query failed' }

# 5. Client processes
foreach ($p in 'OUTLOOK', 'ms-teams', 'Teams', 'OneDrive') {
    $proc = Get-Process -Name $p -ErrorAction SilentlyContinue
    if ($proc) { Add-Result "Process $p" 'PASS' "Running ($($proc.Count))" }
}

$results | Format-Table -AutoSize -Wrap
$fail = ($results | Where-Object Status -eq 'FAIL').Count
if ($fail) { Write-Warning "$fail check(s) failed - see docs/sop/network-troubleshooting-flow.md"; exit 1 }
