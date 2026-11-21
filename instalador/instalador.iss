; Instalador del aplicativo Registro de Sobretiempos (Inno Setup 6)
#define Nombre "Registro de Sobretiempos"
#define Version "1.1.0"
#define Ejecutable "RegistroSobretiempos.exe"

[Setup]
AppId={{6C3E2B8A-5E1F-4B7D-9C2A-3F4D5E6A7B80}
AppName={#Nombre}
AppVersion={#Version}
AppPublisher=Proyecto GDI - UCSM
DefaultDirName={autopf}\RegistroSobretiempos
DefaultGroupName={#Nombre}
OutputDir=salida
OutputBaseFilename=Instalador_RegistroSobretiempos_{#Version}
SetupIconFile=..\app\recursos\icono.ico
UninstallDisplayIcon={app}\{#Ejecutable}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
PrivilegesRequiredOverridesAllowed=dialog

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Tasks]
Name: "escritorio"; Description: "Crear un acceso directo en el escritorio"; GroupDescription: "Accesos directos:"

[Files]
Source: "..\dist\RegistroSobretiempos\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\config.ini.example"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\base_datos\sobretiempos.sql"; DestDir: "{app}\base_datos"; Flags: ignoreversion

[Icons]
Name: "{group}\{#Nombre}"; Filename: "{app}\{#Ejecutable}"
Name: "{group}\Script de la base de datos"; Filename: "{app}\base_datos"
Name: "{group}\Desinstalar {#Nombre}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#Nombre}"; Filename: "{app}\{#Ejecutable}"; Tasks: escritorio

[Run]
Filename: "{app}\{#Ejecutable}"; Description: "Abrir {#Nombre}"; Flags: nowait postinstall skipifsilent
