; Script Inno Setup per Mercurio Gestionale Retail v0.2.1-alpha
; Compilare con Inno Setup 6 (https://jrsoftware.org/isinfo.php)

#define MyAppName "Mercurio Gestionale Retail"
#define MyAppVersion "0.2.1-alpha"
#define MyAppPublisher "Andrea Salerno"
#define MyAppURL "https://github.com/andreasalerno/mercurio-retail"
#define MyAppExeName "app.exe"

[Setup]
; Identificatore unico dell'applicazione
AppId={{D3F9B2C4-8E1A-4D5F-9B3E-7C2A10F6829D}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
LicenseFile=LICENSE
; File dell'installer generato in output
OutputBaseFilename=Setup_Mercurio_Retail_v0.2.1-alpha
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
SetupIconFile=icona.ico

[Languages]
Name: "italian"; MessagesFile: "compiler:Languages\Italian.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; File eseguibile principale generato da PyInstaller (nella cartella dist\app)
Source: "dist\app\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
; Tutti i file e moduli di supporto presenti nella cartella di build
Source: "dist\app\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
; File di configurazione predefinito locale
Source: "config_mercurio.json"; DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\icona.ico"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\icona.ico"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent