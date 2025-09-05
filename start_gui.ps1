\
param()
$ErrorActionPreference = 'SilentlyContinue'
if (Get-Command pythonw -ErrorAction SilentlyContinue) { pythonw -m gui; exit $LASTEXITCODE }
if (Get-Command py -ErrorAction SilentlyContinue) { py -3 -m gui; exit $LASTEXITCODE }
python -m gui
