#define MyAppName "RoboParty Factory Firmware"
#ifndef BundleVersion
  #define BundleVersion "0.0.0"
#endif
#ifndef DistDir
  #define DistDir "..\dist"
#endif

[Setup]
AppId={{B7F7E6C2-2F72-4C45-9C1B-9B6C5C1E3A41}
AppName={#MyAppName}
AppVersion={#BundleVersion}
AppVerName={#MyAppName} {#BundleVersion}
AppPublisher=RoboParty
DefaultDirName={autopf}\RoboParty\Firmware
DefaultGroupName=RoboParty
DisableProgramGroupPage=yes
PrivilegesRequired=admin
OutputDir={#DistDir}
OutputBaseFilename=RoboParty-Firmware-{#BundleVersion}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64
UninstallDisplayName={#MyAppName}
UsePreviousAppDir=yes
AllowNoIcons=yes

[Files]
Source: "{#DistDir}\firmware\*"; DestDir: "{app}\firmware"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "{#DistDir}\manifest.json"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#DistDir}\SHA256SUMS"; DestDir: "{app}"; Flags: ignoreversion
