; Script di configurazione Inno Setup per Mercurio Gestionale Retail v0.3.3 Alpha
;
; IMPORTANTE: questo script presuppone che il build_exe.bat usi:
;   --name "MercurioGestionale"
; Quindi l'exe generato è: dist\MercurioGestionale\MercurioGestionale.exe

#define MyAppVersion "0.3.3 Alpha"
#define MyAppName "Mercurio Gestionale Retail v0.3.3 Alpha"
#define MyAppShortName "Mercurio Gestionale Retail"
#define MyAppPublisher "Andrea Salerno"
#define MyAppURL "https://github.com/andreasalerno89/Mercurio-Gestionale-Retail"
#define MyAppExeName "MercurioGestionale.exe"

[Setup]
AppId={{A4B3C2D1-E5F6-7890-ABCD-EF1234567890}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}

DefaultDirName={autopf}\Mercurio Gestionale Retail
DefaultGroupName=Mercurio Gestionale Retail
AllowNoIcons=yes

; Rimuovi il commento se hai i file LICENSE e README.md
; LicenseFile=LICENSE
; InfoBeforeFile=README.md

OutputDir=Output
OutputBaseFilename=mercurio_gestionale_retail-v0.3.3-alpha-win64-setup
SetupIconFile=icona.ico

Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "italian"; MessagesFile: "compiler:Languages\Italian.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "dist\MercurioGestionale\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "icona.ico"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppShortName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\icona.ico"
Name: "{group}\{cm:ProgramOnTheWeb,{#MyAppShortName}}"; Filename: "{#MyAppURL}"
Name: "{group}\{cm:UninstallProgram,{#MyAppShortName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppShortName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\icona.ico"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#MyAppShortName}}"; Flags: nowait postinstall skipifsilent

[Code]
function InitializeSetup(): Boolean;
var
  ErrorCode: Integer;
begin
  Exec('taskkill', '/F /IM {#MyAppExeName}', '', SW_HIDE, ewWaitUntilTerminated, ErrorCode);
  Result := True;
end;