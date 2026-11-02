; Installer for the BAG2JP online build (Bust A Move 2 Dance Tengoku Mix recompiled).
; Build (Linux VM):  NSISDIR=~/tools/nsis/usr/share/nsis ~/tools/nsis/usr/bin/makensis \
;                    -DPAYLOAD=<folder with the release files> -DOUTDIR=<output folder> bag2jp_online.nsi
; Pages: welcome -> folder + desktop shortcut -> game disc (.cue + .bin, copied into the game) ->
; install -> finish (run). Per-user install, no admin rights needed.
Unicode true
SetCompressor zlib
RequestExecutionLevel user

!define APPNAME   "Bust A Move 2 Online"
!define APPKEY    "BAG2JP-Online"
!define VERSION   "2.0"
!ifndef PAYLOAD
  !error "pass -DPAYLOAD=<folder>"
!endif
!ifndef OUTDIR
  !define OUTDIR "."
!endif

Name "${APPNAME}"
OutFile "${OUTDIR}/BAG2JP-Online-Setup.exe"
InstallDir "$LOCALAPPDATA\Programs\${APPNAME}"
BrandingText "BAG2JP"
ShowInstDetails show

!include "MUI2.nsh"
!include "nsDialogs.nsh"
!include "LogicLib.nsh"
!include "FileFunc.nsh"

!define MUI_ABORTWARNING
!define MUI_ICON "${NSISDIR}\Contrib\Graphics\Icons\modern-install.ico"
!define MUI_UNICON "${NSISDIR}\Contrib\Graphics\Icons\modern-uninstall.ico"

!define MUI_WELCOMEPAGE_TITLE "Bust A Move 2 Online"
!define MUI_WELCOMEPAGE_TEXT "Este asistente instala Bust A Move 2 Dance Tengoku Mix recompilado para PC, con juego online contra otra persona.$\r$\n$\r$\nQué necesitas:$\r$\n  • Tu propia copia del juego: la imagen del disco japonés (SLPM-86219) en archivos .cue y .bin.$\r$\n  • Unos 1.2 GB libres (el juego y una copia del disco).$\r$\n$\r$\nAl terminar, abre el juego con el acceso directo y elige 2PLAYER GAME para jugar online.$\r$\n$\r$\nPulsa Siguiente para continuar."
!insertmacro MUI_PAGE_WELCOME
Page custom FolderPage FolderLeave
Page custom DiscPage DiscLeave
!insertmacro MUI_PAGE_INSTFILES
!define MUI_FINISHPAGE_TITLE "Listo para jugar"
!define MUI_FINISHPAGE_TEXT "Bust A Move 2 Online quedó instalado.$\r$\n$\r$\nPara jugar, haz doble clic en el acceso directo «Bust A Move 2 Online». La primera vez Windows puede preguntar por el firewall: elige «Permitir» para poder jugar online."
!define MUI_FINISHPAGE_RUN "$INSTDIR\BAG2JP.exe"
!define MUI_FINISHPAGE_RUN_PARAMETERS "--no-launcher"
!define MUI_FINISHPAGE_RUN_TEXT "Abrir el juego ahora"
!define MUI_FINISHPAGE_SHOWREADME "$INSTDIR\LEEME.txt"
!define MUI_FINISHPAGE_SHOWREADME_TEXT "Ver instrucciones (controles y online)"
!define MUI_FINISHPAGE_SHOWREADME_NOTCHECKED
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

!insertmacro MUI_LANGUAGE "Spanish"

Var Dlg
Var DirText
Var ChkDesktop
Var WantDesktop
Var CueText
Var BinText
Var CuePath
Var BinPath

Function .onInit
  StrCpy $WantDesktop ${BST_CHECKED}
FunctionEnd

; ------------------------------------------------------------------ page 2: folder + shortcut
Function FolderPage
  !insertmacro MUI_HEADER_TEXT "Carpeta de instalación" "Elige dónde se instala el juego."
  nsDialogs::Create 1018
  Pop $Dlg
  ${If} $Dlg == error
    Abort
  ${EndIf}
  ${NSD_CreateLabel} 0 0 100% 24u "El juego se instalará en esta carpeta. Para usar otra, pulsa Examinar."
  Pop $0
  ${NSD_CreateDirRequest} 0 30u 75% 13u "$INSTDIR"
  Pop $DirText
  ${NSD_CreateBrowseButton} 77% 29u 23% 15u "Examinar..."
  Pop $0
  ${NSD_OnClick} $0 FolderBrowse
  ${NSD_CreateLabel} 0 52u 100% 12u "Espacio necesario: unos 1.2 GB (juego y copia del disco)."
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

; ------------------------------------------------------------------ page 3: game disc
Function DiscPage
  !insertmacro MUI_HEADER_TEXT "Disco del juego" "Elige tu imagen del disco japonés (SLPM-86219)."
  nsDialogs::Create 1018
  Pop $Dlg
  ${If} $Dlg == error
    Abort
  ${EndIf}
  ${NSD_CreateLabel} 0 0 100% 30u "Elige el archivo .cue y el archivo .bin de tu copia del juego. Se copian a la carpeta del juego, así funciona aunque después muevas los originales. Al elegir el .cue, el .bin se completa solo si está al lado."
  Pop $0
  ${NSD_CreateLabel} 0 36u 100% 10u "Archivo .cue:"
  Pop $0
  ${NSD_CreateText} 0 47u 75% 13u "$CuePath"
  Pop $CueText
  ${NSD_CreateBrowseButton} 77% 46u 23% 15u "Examinar..."
  Pop $0
  ${NSD_OnClick} $0 CueBrowse
  ${NSD_CreateLabel} 0 68u 100% 10u "Archivo .bin:"
  Pop $0
  ${NSD_CreateText} 0 79u 75% 13u "$BinPath"
  Pop $BinText
  ${NSD_CreateBrowseButton} 77% 78u 23% 15u "Examinar..."
  Pop $0
  ${NSD_OnClick} $0 BinBrowse
  nsDialogs::Show
FunctionEnd

; $R0 = path of a .cue -> $R1 = file named in its first FILE line ("" if none), $R2 = number of FILE lines
Function CueFileName
  StrCpy $R1 ""
  StrCpy $R2 0
  ClearErrors
  FileOpen $R3 $R0 r
  IfErrors done
  loop:
    ClearErrors
    FileRead $R3 $R4
    IfErrors close
    ; skip leading spaces/tabs
    StrCpy $R5 0
    trim:
      StrCpy $R6 $R4 1 $R5
      ${If} $R6 == " "
      ${OrIf} $R6 == "$\t"
        IntOp $R5 $R5 + 1
        Goto trim
      ${EndIf}
    StrCpy $R6 $R4 5 $R5
    ${If} $R6 != "FILE "
      Goto loop
    ${EndIf}
    IntOp $R2 $R2 + 1
    ${If} $R2 > 1
      Goto loop
    ${EndIf}
    ; text between the first two quotes
    IntOp $R5 $R5 + 5
    StrCpy $R6 $R4 1 $R5
    ${If} $R6 != '"'
      Goto loop
    ${EndIf}
    IntOp $R5 $R5 + 1
    StrCpy $R7 $R5
    scan:
      StrCpy $R6 $R4 1 $R7
      ${If} $R6 == ""
        Goto loop
      ${EndIf}
      ${If} $R6 != '"'
        IntOp $R7 $R7 + 1
        Goto scan
      ${EndIf}
    IntOp $R7 $R7 - $R5
    StrCpy $R1 $R4 $R7 $R5
    Goto loop
  close:
    FileClose $R3
  done:
FunctionEnd

Function CueBrowse
  ${NSD_GetText} $CueText $0
  nsDialogs::SelectFileDialog open "$0" "Imagen de disco (*.cue)|*.cue|Todos los archivos (*.*)|*.*"
  Pop $0
  ${If} $0 == error
  ${OrIf} $0 == ""
    Return
  ${EndIf}
  ${NSD_SetText} $CueText $0
  StrCpy $R0 $0
  Call CueFileName
  ${If} $R1 != ""
    ${GetParent} $0 $R8
    ${If} ${FileExists} "$R8\$R1"
      ${NSD_SetText} $BinText "$R8\$R1"
    ${EndIf}
  ${EndIf}
FunctionEnd

Function BinBrowse
  ${NSD_GetText} $BinText $0
  nsDialogs::SelectFileDialog open "$0" "Imagen de disco (*.bin)|*.bin|Todos los archivos (*.*)|*.*"
  Pop $0
  ${If} $0 != error
  ${AndIf} $0 != ""
    ${NSD_SetText} $BinText $0
  ${EndIf}
FunctionEnd

Function DiscLeave
  ${NSD_GetText} $CueText $CuePath
  ${NSD_GetText} $BinText $BinPath
  ${IfNot} ${FileExists} "$CuePath"
    MessageBox MB_ICONEXCLAMATION "Elige el archivo .cue del juego."
    Abort
  ${EndIf}
  ${IfNot} ${FileExists} "$BinPath"
    MessageBox MB_ICONEXCLAMATION "Elige el archivo .bin del juego."
    Abort
  ${EndIf}
  ${GetFileExt} "$CuePath" $0
  ${If} $0 != "cue"
    MessageBox MB_ICONEXCLAMATION "El primer archivo debe ser un .cue."
    Abort
  ${EndIf}
  StrCpy $R0 $CuePath
  Call CueFileName
  ${If} $R2 > 1
    MessageBox MB_ICONEXCLAMATION "Este .cue usa varios archivos .bin. Usa una imagen de un solo archivo .bin (la habitual de este juego)."
    Abort
  ${EndIf}
  FileOpen $1 "$BinPath" r
  FileSeek $1 0 END $0
  FileClose $1
  IntOp $0 $0 / 1048576
  ${If} $0 < 100
    MessageBox MB_ICONEXCLAMATION "El archivo .bin parece demasiado pequeño ($0 MB). Elige la imagen completa del disco."
    Abort
  ${EndIf}
FunctionEnd

; game.cue = the user's .cue with its FILE line pointing at the copied .bin
Function WriteCue
  ${GetFileName} "$BinPath" $R9
  FileOpen $R3 "$CuePath" r
  FileOpen $R8 "$INSTDIR\disc_image\game.cue" w
  loop:
    ClearErrors
    FileRead $R3 $R4
    IfErrors done
    StrCpy $R5 0
    trim:
      StrCpy $R6 $R4 1 $R5
      ${If} $R6 == " "
      ${OrIf} $R6 == "$\t"
        IntOp $R5 $R5 + 1
        Goto trim
      ${EndIf}
    StrCpy $R6 $R4 5 $R5
    ${If} $R6 == "FILE "
      FileWrite $R8 'FILE "$R9" BINARY$\r$\n'
    ${Else}
      FileWrite $R8 $R4
    ${EndIf}
    Goto loop
  done:
  FileClose $R3
  FileClose $R8
FunctionEnd

; ------------------------------------------------------------------ install
Section "Juego" SecGame
  SectionIn RO
  SetOutPath "$INSTDIR"
  DetailPrint "Copiando el juego..."
  SetCompress auto
  File /r /x "*.flac" /x "*.mpg" /x "LEEME.txt" /x "settings.toml" /x "card1.mcd" "${PAYLOAD}/*.*"
  SetCompress off
  File /r "${PAYLOAD}/*.flac"
  File /r "${PAYLOAD}/*.mpg"
  SetCompress auto
  File "/oname=$INSTDIR\settings.toml" "settings.toml"
  File "/oname=$INSTDIR\LEEME.txt" "LEEME.txt"
  ; memory card with saved progress: never replace one the player already has (reinstall/update)
  CreateDirectory "$INSTDIR\saves"
  SetOverwrite off
  File "/oname=$INSTDIR\saves\card1.mcd" "${PAYLOAD}/saves/card1.mcd"
  SetOverwrite on

  DetailPrint "Copiando el disco del juego (puede tardar un poco)..."
  CreateDirectory "$INSTDIR\disc_image"
  ${GetFileName} "$BinPath" $0
  CopyFiles /SILENT "$BinPath" "$INSTDIR\disc_image\$0"
  Call WriteCue
  FileOpen $0 "$INSTDIR\disc.cfg" w
  FileWrite $0 "disc_image/game.cue"
  FileClose $0

  ; shortcuts: the game opens straight away; the launcher stays for settings
  CreateDirectory "$SMPROGRAMS\${APPNAME}"
  CreateShortcut "$SMPROGRAMS\${APPNAME}\${APPNAME}.lnk" "$INSTDIR\BAG2JP.exe" "--no-launcher" "$INSTDIR\BAG2JP.exe" 0
  CreateShortcut "$SMPROGRAMS\${APPNAME}\BAG2JP - Configuración.lnk" "$INSTDIR\BAG2JP.exe" "" "$INSTDIR\BAG2JP.exe" 0
  CreateShortcut "$SMPROGRAMS\${APPNAME}\Instrucciones.lnk" "$INSTDIR\LEEME.txt"
  CreateShortcut "$SMPROGRAMS\${APPNAME}\Desinstalar.lnk" "$INSTDIR\Desinstalar.exe"
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
  MessageBox MB_YESNO|MB_ICONQUESTION "¿Borrar también tus partidas guardadas (memory cards)?$\r$\nSi eliges No, quedan en:$\r$\n$INSTDIR\saves" IDYES all
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
