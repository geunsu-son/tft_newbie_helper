@echo off
setlocal
set "PROJECT_ROOT=%~dp0"
if "%PROJECT_ROOT:~-1%"=="\" set "PROJECT_ROOT=%PROJECT_ROOT:~0,-1%"

powershell -NoProfile -ExecutionPolicy Bypass -Command "$ErrorActionPreference='Stop'; $root='%PROJECT_ROOT%'; $apiPidFile=Join-Path $root 'data\api.pid'; $webPidFile=Join-Path $root 'data\web.pid'; $apiListeners=@(Get-NetTCPConnection -State Listen -LocalPort 8000 -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique); $webListeners=@(Get-NetTCPConnection -State Listen -LocalPort 5173 -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique); $targets=Get-CimInstance Win32_Process | Where-Object { ($_.ProcessId -in $apiListeners -and $_.Name -eq 'python.exe' -and $_.CommandLine -match 'backend\.app:app') -or ($_.ProcessId -in $webListeners -and $_.Name -eq 'node.exe' -and $_.CommandLine -match 'vite') }; foreach($process in $targets){Stop-Process -Id $process.ProcessId -Force -ErrorAction SilentlyContinue}; Remove-Item $apiPidFile,$webPidFile -Force -ErrorAction SilentlyContinue; Start-Sleep -Seconds 1; $python=Join-Path $root '.venv\Scripts\python.exe'; if(!(Test-Path $python)){$python=(Get-Command py.exe).Source}; $apiArgs='-m uvicorn --app-dir "'+$root+'" backend.app:app --host 0.0.0.0 --port 8000'; $api=Start-Process -PassThru -WindowStyle Hidden -FilePath $python -ArgumentList $apiArgs -WorkingDirectory $root; $api.Id | Set-Content $apiPidFile -NoNewline; $node=(Get-Command node.exe).Source; $vite=Join-Path $root 'frontend\node_modules\vite\bin\vite.js'; $web=Start-Process -PassThru -WindowStyle Hidden -FilePath $node -ArgumentList ('"'+$vite+'" --host 0.0.0.0') -WorkingDirectory (Join-Path $root 'frontend'); $web.Id | Set-Content $webPidFile -NoNewline; Start-Sleep -Seconds 2; if(!(Get-Process -Id $api.Id -ErrorAction SilentlyContinue)){throw 'API process failed to stay running'}; if(!(Get-Process -Id $web.Id -ErrorAction SilentlyContinue)){throw 'Frontend process failed to stay running'}"
if errorlevel 1 (
  echo Failed to start the local API or frontend.
  pause
  exit /b 1
)
endlocal
