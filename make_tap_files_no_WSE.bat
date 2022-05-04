@echo off
cd %~dp0
call C:\ProgramData\Anaconda3\Scripts\activate.bat C:\ProgramData\Anaconda3\
call python make_tap_files_no_WSE.py
timeout 10