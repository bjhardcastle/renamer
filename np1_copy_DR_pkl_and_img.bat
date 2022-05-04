@echo off
cd %~dp0
call C:\ProgramData\Anaconda3\Scripts\activate.bat C:\ProgramData\Anaconda3\
call python np1_copy_DR_pkl_and_img.py
timeout 10