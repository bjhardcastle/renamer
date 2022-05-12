@echo off
cd %~dp0
call C:\ProgramData\Anaconda3\Scripts\activate.bat C:\ProgramData\Anaconda3\
call python rename.py
timeout 10