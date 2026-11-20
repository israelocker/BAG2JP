; Installer for BAG2JP release build (Bust A Groove 2 Dance Tengoku Mix recompiled).
; Build (Windows): makensis -DPAYLOAD="<folder>" -DOUTDIR="<folder>" bag2jp_release.nsi
; Creates a single .exe installer that unpacks the full game folder.
Unicode true
SetCompressor zlib
RequestExecutionLevel user

!define APPNAME   "Bust A Groove 2"
!define APPKEY    "BAG2JP"
!define VERSION   "1.0"
!ifndef PAYLOAD
  !error "pass -DPAYLOAD=<folder with the release files>"
!endif
!ifndef OUTDIR
  !define OUTDIR "."
!endif

Name "${APPNAME}"
OutFile "${OUTDIR}/BAG2JP-Installer.exe"
InstallDir "$LOCALAPPDATA\Programs\${APPNAME}"
BrandingText "BAG2JP"
ShowInstDetails show

!include "MUI2.nsh"
!include "nsDialogs.nsh"
!include "LogicLib.nsh"

!define MUI_ABORTWARNING
!define MUI_ICON "${NSISDIR}\Contrib\Graphics\Icons\modern-install.ico"
!define MUI_UNICON "${NSISDIR}\Contrib\Graphics\Icons\modern-uninstall.ico"

!define MUI_WELCOMEPAGE_TITLE "Bust A Groove 2"
!define MUI_WELCOMEPAGE_TEXT "Este asistente instala Bust A Groove 2 Dance Tengoku Mix recompilado para PC.$\r$\n$\r$\nTodo est� incluido: el juego, el disco, assets, BIOS y configuraci�n.$\r$\n$\r$\nPulsa Siguiente para continuar."
!insertmacro MUI_PAGE_WELCOME
Page custom FolderPage FolderLeave
!insertmacro MUI_PAGE_INSTFILES
!define MUI_FINISHPAGE_TITLE "Listo para jugar"
!define MUI_FINISHPAGE_TEXT "Bust A Groove 2 qued� instalado.$\r$\n$\r$\nPara jugar, haz doble clic en el acceso directo «Bust A Groove 2»."
!define MUI_FINISHPAGE_RUN "$INSTDIR\BAG2JP.exe"
!define MUI_FINISHPAGE_RUN_PARAMETERS "--no-launcher"
!define MUI_FINISHPAGE_RUN_TEXT "Abrir el juego ahora"
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

!insertmacro MUI_LANGUAGE "Spanish"

Var Dlg
Var DirText
Var ChkDesktop
Var WantDesktop

Function .onInit
  StrCpy $WantDesktop ${BST_CHECKED}
FunctionEnd

; ------------------------------------------------------------------ page 2: folder + shortcut
Function FolderPage
  !insertmacro MUI_HEADER_TEXT "Carpeta de instalaci�n" "Elige d�nde se instala el juego."
  nsDialogs::Create 1018
  Pop $Dlg
  ${If} $Dlg == error
    Abort
  ${EndIf}
  ${NSD_CreateLabel} 0 0 100% 24u "El juego se instalar� en esta carpeta. Para usar otra, pulsa Examinar."
  Pop $0
  ${NSD_CreateDirRequest} 0 30u 75% 13u "$INSTDIR"
  Pop $DirText
  ${NSD_CreateBrowseButton} 77% 29u 23% 15u "Examinar..."
  Pop $0
  ${NSD_OnClick} $0 FolderBrowse
  ${NSD_CreateLabel} 0 52u 100% 12u "Espacio necesario: unos 1.2 GB."
  Pop $0
  ${NSD_CreateCheckbox} 0 76u 100% 12u "Crear un acceso directo en el escritorio"
  Pop $ChkDesktop
  ${NSD_SetState} $ChkDesktop $WantDesktop
  nsDialogs::Show
FunctionEnd

Function FolderBrowse
  ${NSD_GetText} $DirText $0
  nsDialogs::SelectFolderDialog "Elige la carpeta del juego" "$0"
  Pop $0
  ${If} $0 != error
    ${NSD_SetText} $DirText "$0\${APPNAME}"
  ${EndIf}
FunctionEnd

Function FolderLeave
  ${NSD_GetText} $DirText $0
  ${If} $0 == ""
    MessageBox MB_ICONEXCLAMATION "Elige una carpeta."
    Abort
  ${EndIf}
  StrCpy $INSTDIR $0
  ${NSD_GetState} $ChkDesktop $WantDesktop
FunctionEnd

; ------------------------------------------------------------------ install
Section "Juego" SecGame
  SectionIn RO
  SetOutPath "$INSTDIR"
  DetailPrint "Copiando el juego..."
  SetCompress auto
  File /r "${PAYLOAD}\*.*"

  DetailPrint "Creando accesos directos..."
  CreateDirectory "$SMPROGRAMS\${APPNAME}"
  CreateShortcut "$SMPROGRAMS\${APPNAME}\${APPNAME}.lnk" "$INSTDIR\BAG2JP.exe" "--no-launcher" "$INSTDIR\BAG2JP.exe" 0
  CreateShortcut "$SMPROGRAMS\${APPNAME}\BAG2JP - Configuraci�n.lnk" "$INSTDIR\BAG2JP.exe" "" "$INSTDIR\BAG2JP.exe" 0

  ${If} $WantDesktop == ${BST_CHECKED}
    CreateShortcut "$DESKTOP\${APPNAME}.lnk" "$INSTDIR\BAG2JP.exe" "--no-launcher" "$INSTDIR\BAG2JP.exe" 0
  ${EndIf}

  WriteUninstaller "$INSTDIR\Desinstalar.exe"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPKEY}" "DisplayName" "${APPNAME}"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPKEY}" "DisplayVersion" "${VERSION}"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPKEY}" "Publisher" "BAG2JP"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPKEY}" "DisplayIcon" "$INSTDIR\BAG2JP.exe"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPKEY}" "InstallLocation" "$INSTDIR"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPKEY}" "UninstallString" '"$INSTDIR\Desinstalar.exe"'
  WriteRegDWORD HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPKEY}" "NoModify" 1
  WriteRegDWORD HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPKEY}" "NoRepair" 1
SectionEnd

; ------------------------------------------------------------------ uninstall
Section "Uninstall"
  Delete "$DESKTOP\${APPNAME}.lnk"
  RMDir /r "$SMPROGRAMS\${APPNAME}"
  DeleteRegKey HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPKEY}"
  MessageBox MB_YESNO|MB_ICONQUESTION "�Borrar tambi�n tus partidas guardadas (memory cards)?$\r$\nSi eliges No, quedan en:$\r$\n$INSTDIR\saves" IDYES all
    ; keep saves: delete everything else
    FindFirst $0 $1 "$INSTDIR\*.*"
    next:
      StrCmp $1 "" done
      StrCmp $1 "." skip
      StrCmp $1 ".." skip
      StrCmp $1 "saves" skip
      ${If} ${FileExists} "$INSTDIR\$1\*.*"
        RMDir /r "$INSTDIR\$1"
      ${Else}
        Delete "$INSTDIR\$1"
      ${EndIf}
      skip:
      FindNext $0 $1
      Goto next
    done:
    FindClose $0
    Goto end
  all:
    RMDir /r "$INSTDIR"
  end:
SectionEnd
