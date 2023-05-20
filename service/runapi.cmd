@echo off
cd /D %~dp0
SET AD_API_CONFIG=%CD%\config\prod
python api.py