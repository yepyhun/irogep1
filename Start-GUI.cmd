@echo off
setlocal
pushd "%~dp0"
rem Indítás a repo gyökeréből – PowerShell nélkül, duplaklikkre
py -3 -m gui.app
popd
