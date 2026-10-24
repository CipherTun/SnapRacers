; The Windows installer, built on Linux with NSIS (makensis) by tools/package-desktop.sh. It
; installs for the current user only, with no administrator prompt, into
; %LOCALAPPDATA%\Programs\SnapRacers, with a Start menu entry and an uninstall entry in
; Settings > Apps. Saves live in %APPDATA%\Godot\app_userdata\SnapRacers and are left alone.
;
;   makensis -DVERSION=0.9.0 -DEXE=<snapracers.exe> -DLICENSE=<LICENSE> -DOUT=<setup.exe> installer.nsi

Unicode true
SetCompressor /SOLID lzma

!ifndef VERSION | EXE | LICENSE | OUT
  !error "VERSION, EXE, LICENSE and OUT are given by the build"
!endif

!define KEY "Software\Microsoft\Windows\CurrentVersion\Uninstall\SnapRacers"

Name "SnapRacers"
OutFile "${OUT}"
InstallDir "$LOCALAPPDATA\Programs\SnapRacers"
InstallDirRegKey HKCU "${KEY}" "InstallLocation"
RequestExecutionLevel user

VIProductVersion "${VERSION}.0"
VIAddVersionKey "ProductName" "SnapRacers"
VIAddVersionKey "ProductVersion" "${VERSION}"
VIAddVersionKey "FileDescription" "SnapRacers setup"
VIAddVersionKey "FileVersion" "${VERSION}"
VIAddVersionKey "LegalCopyright" "Copyright (C) 2026 Dan Hunke. GPLv3 or later."

!include "MUI2.nsh"
!include "x64.nsh"
!define MUI_ICON "snapracers.ico"
!define MUI_UNICON "snapracers.ico"
!define MUI_FINISHPAGE_RUN "$INSTDIR\SnapRacers.exe"
!define MUI_FINISHPAGE_RUN_TEXT "Start SnapRacers"
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_LANGUAGE "English"

Function .onInit
  ${IfNot} ${RunningX64}
    MessageBox MB_OK|MB_ICONSTOP "SnapRacers needs 64-bit Windows."
    Abort
  ${EndIf}
FunctionEnd

Section
  SetOutPath "$INSTDIR"
  File "/oname=SnapRacers.exe" "${EXE}"
  File "/oname=LICENSE.txt" "${LICENSE}"
  WriteUninstaller "$INSTDIR\Uninstall.exe"
  CreateShortcut "$SMPROGRAMS\SnapRacers.lnk" "$INSTDIR\SnapRacers.exe"

  WriteRegStr HKCU "${KEY}" "DisplayName" "SnapRacers"
  WriteRegStr HKCU "${KEY}" "DisplayVersion" "${VERSION}"
  WriteRegStr HKCU "${KEY}" "Publisher" "Dan Hunke"
  WriteRegStr HKCU "${KEY}" "DisplayIcon" "$INSTDIR\SnapRacers.exe"
  WriteRegStr HKCU "${KEY}" "InstallLocation" "$INSTDIR"
  WriteRegStr HKCU "${KEY}" "UninstallString" '"$INSTDIR\Uninstall.exe"'
  WriteRegStr HKCU "${KEY}" "URLInfoAbout" "https://github.com/roge-rm/SnapRacers"
  SectionGetSize 0 $0
  WriteRegDWORD HKCU "${KEY}" "EstimatedSize" $0
  WriteRegDWORD HKCU "${KEY}" "NoModify" 1
  WriteRegDWORD HKCU "${KEY}" "NoRepair" 1
SectionEnd

Section "Uninstall"
  Delete "$SMPROGRAMS\SnapRacers.lnk"
  Delete "$INSTDIR\SnapRacers.exe"
  Delete "$INSTDIR\LICENSE.txt"
  Delete "$INSTDIR\Uninstall.exe"
  RMDir "$INSTDIR"
  DeleteRegKey HKCU "${KEY}"
SectionEnd
