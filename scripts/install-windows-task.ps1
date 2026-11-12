$ErrorActionPreference = "Stop"
$argument = "-d Ubuntu-24.04 -u root -e /bin/bash /home/julio/projetos/ponto_away/scripts/wake-wsl.sh"
$action = New-ScheduledTaskAction -Execute "wsl.exe" -Argument $argument
$trigger = New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME
Register-ScheduledTask -TaskName "PontoAway" -Action $action -Trigger $trigger -Force | Out-Null
Write-Output "Tarefa PontoAway registrada para $env:USERNAME"
