[Setup]
AppId={{8A7F4B21-9E12-4C11-B223-9A1009FF2A88}
AppName=Mercurio Gestionale ERP
AppVersion=0.1.0-alpha
AppPublisher=AB S.r.l.
DefaultDirName={autopf}\Mercurio Retail
DefaultGroupName=Mercurio Gestionale ERP
DisableProgramGroupPage=yes
OutputDir=Output
OutputBaseFilename=Mercurio_Retail_Setup_v0.1.0-alpha
Compression=lzma
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64compatible
SetupIconFile=icona.ico

[Languages]
Name: "italian"; MessagesFile: "compiler:Languages\Italian.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; Copia tutti i file e le cartelle dell'applicazione generati da PyInstaller
Source: "dist\Mercurio Gestionale ERP\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

; Copia il file dell'icona nella cartella di destinazione per i collegamenti
Source: "icona.ico"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\Mercurio Gestionale ERP"; Filename: "{app}\Mercurio Gestionale ERP.exe"; IconFilename: "{app}\icona.ico"
Name: "{group}\{cm:UninstallProgram,Mercurio Gestionale ERP}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\Mercurio Gestionale ERP"; Filename: "{app}\Mercurio Gestionale ERP.exe"; IconFilename: "{app}\icona.ico"; Tasks: desktopicon

[Run]
Filename: "{app}\Mercurio Gestionale ERP.exe"; Description: "{cm:LaunchProgram,Mercurio Gestionale ERP}"; Flags: nowait postinstall skipifsilent