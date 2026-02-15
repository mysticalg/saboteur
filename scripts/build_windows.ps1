Param(
  [string]$Python = "python",
  [string]$Version = "0.1.0"
)

$ErrorActionPreference = "Stop"

& $Python -m pip install --upgrade pip
& $Python -m pip install -r requirements.txt pyinstaller

if (Test-Path dist) { Remove-Item -Recurse -Force dist }
if (Test-Path build) { Remove-Item -Recurse -Force build }

& $Python -m PyInstaller --noconfirm --clean --windowed --name Saboteur game.py

$exePath = Join-Path $PWD "dist/Saboteur/Saboteur.exe"
if (!(Test-Path $exePath)) {
  throw "Build failed: $exePath not found"
}

$inno = "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe"
if (!(Test-Path $inno)) {
  Write-Warning "Inno Setup not found. EXE build completed at $exePath"
  exit 0
}

@"
#define AppName "Saboteur"
#define AppVersion "$Version"
#define AppExeName "Saboteur.exe"

[Setup]
AppId={{9EA4DDC0-A572-4E88-89C6-1535C7B4BE8E}
AppName={#AppName}
AppVersion={#AppVersion}
DefaultDirName={autopf}\\{#AppName}
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
OutputDir=dist
OutputBaseFilename=Saboteur-Installer
Compression=lzma
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Files]
Source: "dist\\Saboteur\\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\\{#AppName}"; Filename: "{app}\\{#AppExeName}"
Name: "{autodesktop}\\{#AppName}"; Filename: "{app}\\{#AppExeName}"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop icon"; GroupDescription: "Additional icons:"

[Run]
Filename: "{app}\\{#AppExeName}"; Description: "Launch {#AppName}"; Flags: nowait postinstall skipifsilent
"@ | Set-Content -Path .\installer.iss -NoNewline

& $inno .\installer.iss
Write-Host "Built installer at dist/Saboteur-Installer.exe"
