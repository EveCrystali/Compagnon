# Installe (ou met à jour) Pilou en une ligne, dans PowerShell :
# (fichier SANS BOM : avec « irm … | iex », un BOM devient du texte et casse la première ligne et param())
#   irm https://raw.githubusercontent.com/EveCrystali/Compagnon/main/installer.ps1 | iex
# Ce qu'il fait, et rien d'autre :
#   1. pose PilouBureau.zip (posé à côté du script, sinon téléchargé : gh si présent, sinon GitHub) dans
#      %USERPROFILE%\.claude\compagnon\bureau ;
#   2. si Claude Code est installé : ajoute le mod « compagnon » ;
#   3. si Codex est installé : pose les hooks de Pilou dans ~/.codex/hooks.json (les tiens restent) ;
#   4. le lance au démarrage de Windows et le démarre tout de suite.
# Désinstaller : clic droit sur Pilou → Intégrations → Codex : débrancher, puis supprimer le dossier bureau.
param(
    [string]$Zip = '',
    [switch]$SansDemarrage,
    [switch]$SansCodex,
    [switch]$SansClaude
)

$ErrorActionPreference = 'Stop'
$depot = 'EveCrystali/Compagnon'
$dossier = Join-Path $env:USERPROFILE '.claude\compagnon\bureau'
$exe = Join-Path $dossier 'PilouBureau.exe'

Write-Host '* Pilou arrive...' -ForegroundColor Cyan

# 1. L'overlay : zip donné, zip posé à côté du script (téléchargé depuis la release), gh, ou GitHub.
$voisin = if ($PSScriptRoot) { Join-Path $PSScriptRoot 'PilouBureau.zip' } else { '' }
$tmp = Join-Path $env:TEMP 'PilouBureau-installation.zip'
if ($Zip -and (Test-Path $Zip)) { Copy-Item $Zip $tmp -Force; $version = 'locale' }
elseif ($voisin -and (Test-Path $voisin)) { Copy-Item $voisin $tmp -Force; $version = 'locale' }
elseif (Get-Command gh -ErrorAction SilentlyContinue) {
    # dépôt privé : gh porte ta connexion GitHub ; la plus récente, préversion comprise
    $version = (gh release list --repo $depot --limit 1 --json tagName --jq '.[0].tagName')
    gh release download $version --repo $depot --pattern 'PilouBureau.zip' --output $tmp --clobber
}
else {
    $release = Invoke-RestMethod "https://api.github.com/repos/$depot/releases/latest" -Headers @{ 'User-Agent' = 'pilou-installer' }
    $asset = $release.assets | Where-Object name -eq 'PilouBureau.zip' | Select-Object -First 1
    if (-not $asset) { throw "La release $($release.tag_name) n'a pas de PilouBureau.zip." }
    Invoke-WebRequest $asset.browser_download_url -OutFile $tmp -UseBasicParsing
    $version = $release.tag_name
}
if (-not (Test-Path $tmp)) { throw "PilouBureau.zip introuvable : télécharge-le depuis la page des releases et pose-le à côté de ce script." }
Get-Process PilouBureau -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Milliseconds 400
New-Item -ItemType Directory -Force $dossier | Out-Null
Expand-Archive $tmp -DestinationPath $dossier -Force
Remove-Item $tmp
Write-Host "  overlay $version -> $dossier"

# 2. Le mod Claude Code
if (-not $SansClaude -and (Get-Command claude -ErrorAction SilentlyContinue)) {
    claude plugin marketplace add $depot 2>$null | Out-Null
    claude plugin marketplace update pilou 2>$null | Out-Null
    claude plugin install compagnon@pilou --scope user 2>$null | Out-Null
    Write-Host '  mod Claude Code installé (faire /reload-plugins dans les sessions ouvertes)'
}

# 3. Codex
if (-not $SansCodex -and ((Get-Command codex -ErrorAction SilentlyContinue) -or (Test-Path (Join-Path $env:USERPROFILE '.codex')))) {
    & $exe --brancher codex | Write-Host
}

# 4. Démarrage avec Windows, puis lancement
if (-not $SansDemarrage) {
    Set-ItemProperty 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Run' -Name PilouBureau -Value "`"$exe`""
}
Start-Process $exe
Write-Host '* Pilou est là, en bas de l''écran. Clic droit sur lui pour les réglages et les intégrations.' -ForegroundColor Cyan
