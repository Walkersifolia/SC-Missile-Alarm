@echo off
chcp 65001 >nul
title 星际公民玩家自己的闹钟生成器
cd /d "%~dp0"
start "" "dist\MissileAlert\MissileAlert.exe"
