@echo off
REM Launch Chrome with remote debugging for LinkedIn + Upwork MCP
REM Run this script on Windows before using the LinkedIn/Upwork MCP tools

SET CHROME="C:\Program Files\Google\Chrome\Application\chrome.exe"
SET PROFILE=%LOCALAPPDATA%\Google\Chrome\UserData_MCP

%CHROME% ^
  --remote-debugging-port=9222 ^
  --user-data-dir="%PROFILE%" ^
  --no-first-run ^
  --no-default-browser-check ^
  about:blank

REM After Chrome opens:
REM 1. Log into LinkedIn (linkedin.com)
REM 2. Log into Upwork (upwork.com)
REM 3. Keep Chrome running
REM 4. Return to WSL and use linkedin_search_jobs / upwork_search_jobs
