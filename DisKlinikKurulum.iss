; Dis Klinik Yonetim - Inno Setup kurulum scripti
; Kullanim: Inno Setup 6 ile acip Compile yapin -> Kurulum.exe olusur
#define MyAppName "Dis Klinik Yonetim"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Dis Sagligi Merkezi"
#define MyAppExeName "DisKlinikYonetim.exe"

[Setup]
AppId={{A1B2C3D4-1111-4222-8333-444455556666}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\DisKlinikYonetim
DefaultGroupName={#MyAppName}
OutputDir=.
OutputBaseFilename=DisKlinikKurulum_1_0_0
SetupIconFile=dis_ikon.ico
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
Source: "dis_ikon.ico"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\dis_ikon.ico"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\dis_ikon.ico"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent
