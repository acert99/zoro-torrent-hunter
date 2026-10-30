; Inno Setup script: dist\Zoro-Setup.exe (Zoro - O caçador de Torrents)
; Build: python -I build.py, then ISCC installer.iss
#define AppName "Zoro"
#define AppVersion "2.4"

[Setup]
AppId={{6F1C2E7A-3B9D-4E52-9C1A-7D4B2E8F0A31}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher=acert99
DefaultDirName={autopf}\Zoro
UsePreviousAppDir=no
UsePreviousGroup=no
AppVerName=Zoro - O caçador de Torrents {#AppVersion}
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
OutputDir=dist
OutputBaseFilename=Zoro-Setup
SetupIconFile=assets\icon.ico
UninstallDisplayIcon={app}\Zoro.exe
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
Name: "pt"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"
Name: "en"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "dist\Zoro\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\Zoro.exe"
Name: "{group}\{cm:UninstallProgram,{#AppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\Zoro.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\Zoro.exe"; Description: "{cm:LaunchProgram,{#AppName}}"; Flags: nowait postinstall skipifsilent

[InstallDelete]
; v2.0 shipped as "Torrent Hunter": remove its folder and Start Menu entry (same AppId, so this upgrades it)
Type: filesandordirs; Name: "{localappdata}\Programs\TorrentHunter"
Type: filesandordirs; Name: "{userprograms}\Torrent Hunter"
Type: files; Name: "{userdesktop}\Torrent Hunter.lnk"

[UninstallDelete]
; plugins write cache/log files next to themselves at runtime
Type: filesandordirs; Name: "{app}\_internal\vendor"
