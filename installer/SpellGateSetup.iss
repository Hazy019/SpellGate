; ─────────────────────────────────────────────────────────────────────────────
;  SpellGate Windows Installer
;  Built with Inno Setup 6.x — https://jrsoftware.org/isinfo.php
;
;  What this installer does:
;  1. Copies SpellGate to C:\Program Files\SpellGate\
;  2. Writes HKLM startup registry key (quoted path, no cmd wrapper)
;  3. Creates a Task Scheduler entry with auto-restart policy
;  4. Creates an uninstaller
;  5. Optionally launches SpellGate immediately after install
;
;  To compile:
;    iscc SpellGateSetup.iss
;  Output: installer\SpellGateSetup.exe
; ─────────────────────────────────────────────────────────────────────────────

#define AppName      "SpellGate"
#define AppVersion   "1.1.0"
#define AppPublisher "SpellGate Educational Software"
#define AppURL       "https://spellgate.web.app"
#define AppExeName   "SpellGate.exe"
#define SourceDir    "..\SpellGate\dist\SpellGate"

[Setup]
AppId                     = {{A3F6B912-1D4C-4E5A-8F2D-9C7B3E1A05F6}
AppName                   = {#AppName}
AppVersion                = {#AppVersion}
AppPublisherURL           = {#AppURL}
AppSupportURL             = {#AppURL}
AppUpdatesURL             = {#AppURL}
DefaultDirName            = {autopf}\SpellGate
DefaultGroupName          = SpellGate
AllowNoIcons              = yes
; Request admin so we can write HKLM and Task Scheduler
PrivilegesRequired        = admin
OutputDir                 = .
OutputBaseFilename        = SpellGateSetup
SetupIconFile             = ..\SpellGate\assets\icons\logo.ico
Compression               = lzma2/max
SolidCompression          = yes
WizardStyle               = modern
DisableWelcomePage        = no
; After install, DO NOT leave a file called serviceAccountKey.json anywhere
; The key is stored only in Credential Manager.

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "launchapp"; Description: "Launch SpellGate now (child will need to be present)"; Flags: unchecked

[Files]
; Copy the entire built output folder
Source: "{#SourceDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\SpellGate"; Filename: "{app}\{#AppExeName}"
Name: "{group}\Uninstall SpellGate"; Filename: "{uninstallexe}"
Name: "{commondesktop}\SpellGate"; Filename: "{app}\{#AppExeName}"

[Registry]
; HKLM startup — properly quoted, no cmd wrapper, requires admin
Root: HKLM; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; \
  ValueType: string; ValueName: "SpellGate"; \
  ValueData: """{app}\{#AppExeName}"""; \
  Flags: createvalueifdoesntexist uninsdeletevalue

[Run]
; Step 2: Launch SpellGate immediately if the task was checked
Filename: "{app}\{#AppExeName}"; \
  Description: "Launch SpellGate now"; \
  Flags: nowait postinstall skipifsilent; \
  Tasks: launchapp

[UninstallRun]
; Remove Task Scheduler entry on uninstall
Filename: "schtasks.exe"; \
  Parameters: "/Delete /TN ""SpellGate Security Monitor"" /F"; \
  Flags: runhidden

[UninstallDelete]
; Remove the data directory
Type: filesandordirs; Name: "{app}"


