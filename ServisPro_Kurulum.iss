; ServisPro - Inno Setup kurulum scripti
; Inno Setup 6 ile acip Compile yapin
#define MyAppName "ServisPro"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Fu-Lin"
#define MyAppExeName "ServisPro.exe"

[Setup]
AppId={{F1B2C3D4-1111-4222-8333-444455556666}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\FuLin\ServisPro
DefaultGroupName={#MyAppName}
OutputDir=.
OutputBaseFilename=ServisPro_Kurulum_1_0_0
SetupIconFile=servis\servis.ico
Compression=lzma
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
Name: "turkish"; MessagesFile: "compiler:Languages\Turkish.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "servis\servis.ico"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\servis.ico"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\servis.ico"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent
