; Script di installazione per Mercurio Gestionale Retail v0.2.1-alpha
; Generato per Inno Setup 6

#define MyAppName "Mercurio Gestionale Retail"
#define MyAppVersion "0.2.1-alpha"
#define MyAppPublisher "Andrea Salerno"
#define MyAppExeName "MercurioGestionale.exe"

[Setup]
; Unique App ID per la gestione corretta di disinstallazioni e aggiornamenti
AppId={{B2D157B5-F832-412E-9C81-839F11E1D942}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\MercurioRetail
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
; Cartella di output dove Inno Setup salverà il file .exe finale dell'installer
OutputDir=Output
OutputBaseFilename=Setup_Mercurio_Retail_v0.2.1-alpha
Compression=lzma
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "italian"; MessagesFile: "compiler:Languages\Italian.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; Preleva l'intera cartella generata da PyInstaller (assicurati che il nome corrisponda a dist\MercurioGestionale)
Source: "dist\MercurioGestionale\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent