<#
.SYNOPSIS
    Collects a one-page health snapshot of a Windows desktop for L1/L2 support.
.DESCRIPTION
    Read-only. Reports hardware, OS, disk, memory, uptime, pending reboot,
    network adapters, recent critical events and Defender status.
    Output: console summary + optional JSON/CSV for ticket attachment.
.EXAMPLE
    .\Get-DesktopHealth.ps1 -OutDir C:\Temp
#>
[CmdletBinding()]
param(
    [string]$ComputerName = $env:COMPUTERNAME,
    [string]$OutDir
)

$ErrorActionPreference = 'Stop'

function Get-PendingReboot {
    $keys = @(
        'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Component Based Servicing\RebootPending',
        'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\WindowsUpdate\Auto Update\RebootRequired'
    )
    foreach ($k in $keys) { if (Test-Path $k) { return $true } }
    return $false
}

$os   = Get-CimInstance Win32_OperatingSystem -ComputerName $ComputerName
$cs   = Get-CimInstance Win32_ComputerSystem  -ComputerName $ComputerName
$bios = Get-CimInstance Win32_BIOS            -ComputerName $ComputerName
$cpu  = Get-CimInstance Win32_Processor       -ComputerName $ComputerName | Select-Object -First 1

$disks = Get-CimInstance Win32_LogicalDisk -ComputerName $ComputerName -Filter 'DriveType=3' |
    ForEach-Object {
        [pscustomobject]@{
            Drive   = $_.DeviceID
            SizeGB  = [math]::Round($_.Size / 1GB, 1)
            FreeGB  = [math]::Round($_.FreeSpace / 1GB, 1)
            FreePct = [math]::Round(($_.FreeSpace / $_.Size) * 100, 1)
        }
    }

$nics = Get-NetIPConfiguration | Where-Object { $_.NetAdapter.Status -eq 'Up' } |
    ForEach-Object {
        [pscustomobject]@{
            Adapter = $_.InterfaceAlias
            IPv4    = ($_.IPv4Address.IPAddress -join ',')
            Gateway = ($_.IPv4DefaultGateway.NextHop -join ',')
            DNS     = ($_.DNSServer.ServerAddresses -join ',')
        }
    }

$events = Get-WinEvent -FilterHashtable @{LogName='System'; Level=1,2; StartTime=(Get-Date).AddDays(-3)} `
            -MaxEvents 10 -ErrorAction SilentlyContinue |
          Select-Object TimeCreated, ProviderName, Id, @{n='Msg';e={($_.Message -split "`n")[0]}}

$defender = try { Get-MpComputerStatus | Select-Object AMServiceEnabled, RealTimeProtectionEnabled, AntivirusSignatureLastUpdated } catch { $null }

$uptime = (Get-Date) - $os.LastBootUpTime
$memTotal = [math]::Round($cs.TotalPhysicalMemory / 1GB, 1)
$memFree  = [math]::Round($os.FreePhysicalMemory / 1MB, 1)

$report = [pscustomobject]@{
    Timestamp     = (Get-Date).ToString('s')
    Computer      = $cs.Name
    Model         = "$($cs.Manufacturer) $($cs.Model)"
    Serial        = $bios.SerialNumber
    OS            = "$($os.Caption) build $($os.BuildNumber)"
    CPU           = $cpu.Name
    MemoryGB      = $memTotal
    MemoryFreeGB  = $memFree
    UptimeDays    = [math]::Round($uptime.TotalDays, 1)
    PendingReboot = Get-PendingReboot
    Disks         = $disks
    Network       = $nics
    Defender      = $defender
    RecentErrors  = $events
}

# Simple findings engine -> what a support engineer would flag
$findings = New-Object System.Collections.Generic.List[string]
foreach ($d in $disks) { if ($d.FreePct -lt 15) { $findings.Add("Low disk space on $($d.Drive): $($d.FreePct)% free") } }
if ($report.UptimeDays -gt 14)   { $findings.Add("Uptime $($report.UptimeDays) days - schedule restart") }
if ($report.PendingReboot)       { $findings.Add('Pending reboot detected') }
if ($defender -and -not $defender.RealTimeProtectionEnabled) { $findings.Add('Defender real-time protection is OFF') }
if (-not $nics)                  { $findings.Add('No active network adapter') }
$report | Add-Member -NotePropertyName Findings -NotePropertyValue $findings

$report | Format-List Timestamp, Computer, Model, Serial, OS, CPU, MemoryGB, MemoryFreeGB, UptimeDays, PendingReboot
'--- Disks ---';   $disks | Format-Table -AutoSize
'--- Network ---'; $nics  | Format-Table -AutoSize
'--- Findings ---'
if ($findings.Count) { $findings | ForEach-Object { " [!] $_" } } else { ' [OK] No issues found' }

if ($OutDir) {
    New-Item -ItemType Directory -Path $OutDir -Force | Out-Null
    $file = Join-Path $OutDir ("health_{0}_{1:yyyyMMdd_HHmm}.json" -f $cs.Name, (Get-Date))
    $report | ConvertTo-Json -Depth 5 | Set-Content -Path $file -Encoding UTF8
    "Saved: $file"
}
