# Tourne la vidéo de présentation de Pilou sur ton VRAI écran de GAUCHE, tout seul, et prépare un zip à envoyer.
#   powershell -ExecutionPolicy Bypass -File .\tourner-ecran-gauche.ps1
#   (options : -Ffmpeg C:\chemin\ffmpeg.exe · -Exe C:\chemin\PilouBureau.exe · -Ips 30 · -Oui pour ne pas demander)
#
# Ce que fait le script, dans l'ordre :
#   1. trouve l'écran le plus à gauche (pixels physiques, mise à l'échelle comprise), te le montre (cadre
#      « ÉCRAN FILMÉ » quelques secondes) et te demande de confirmer : c'est lui, et lui seul, qui est filmé ;
#   2. vérifie ffmpeg (sinon l'installe avec winget : Gyan.FFmpeg) et filme cet écran (gdigrab, 30 i/s, souris
#      visible, H.264, sans son) en arrière-plan ;
#   3. remplace pour un moment ton Pilou par un Pilou de démonstration posé en bas de cet écran, qui joue une
#      visite guidée de 1 min 30 à 2 min : promenade, une IA qui attend, le vrai menu clic droit et ses sous-menus,
#      la boutique, la fenêtre Amis, le clavier, la photo, une visite chez Léo, la pluie, deux petits jeux,
#      l'évolution, puis (si ta version les a) la Défense du bureau, les Expéditions et le rayon Ensembles,
#      et enfin le menu de l'icône près de l'horloge. La souris bouge toute seule : n'y touche pas ;
#   4. arrête le film, relance ton Pilou habituel et crée pilou-ecran-gauche.zip sur le Bureau
#      (la vidéo + chronologie.json : l'instant de chaque étape, pour le montage).
# Rien de personnel : le Pilou de démo lit trois sessions FICTIVES (« api », « site », « docs ») dans un dossier
# temporaire, avec un profil, des amis (Léo, Maya, Sam, Noé) et un code ami fictifs, en mémoire. Ton profil
# (XP, po, objets), tes amis, tes connecteurs et tes réglages ne sont ni lus ni modifiés. Aucun réseau.
# Mais l'écran, lui, est filmé tel quel : ferme d'abord tout ce qui est personnel dessus (et mets « Ne pas
# déranger » pour que les notifications ne s'y affichent pas). Arrêter en cours de route : Échap ou Ctrl+C ici.
# Il faut une version de Pilou qui connaît --visite-guidee (menu de Pilou → Version → Chercher une mise à jour).
# Les scènes plus récentes (Défense du bureau, Expéditions, rayon Ensembles de la boutique) sont jouées si la
# version installée les a, sautées sinon : chronologie.json dit pour chaque étape « jouee » vrai ou faux,
# et donne la version de Pilou (version_pilou) et la liste de ce qui manque (a_venir).
param(
    [string]$Ffmpeg = '',
    [string]$Exe = '',
    [int]$Ips = 30,
    [switch]$Oui
)
$ErrorActionPreference = 'Stop'

# ---- 0. Pixels physiques : le script se déclare « conscient de la mise à l'échelle » avant de lire les écrans.
Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
public static class PilouTournage
{
    [DllImport("shcore.dll")] public static extern int SetProcessDpiAwareness(int valeur);
    [DllImport("user32.dll")] public static extern bool SetProcessDPIAware();

    [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Unicode)]
    public struct DEVMODE
    {
        [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 32)] public string dmDeviceName;
        public short dmSpecVersion, dmDriverVersion, dmSize, dmDriverExtra;
        public int dmFields, dmPositionX, dmPositionY, dmDisplayOrientation, dmDisplayFixedOutput;
        public short dmColor, dmDuplex, dmYResolution, dmTTOption, dmCollate;
        [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 32)] public string dmFormName;
        public short dmLogPixels;
        public int dmBitsPerPel, dmPelsWidth, dmPelsHeight, dmDisplayFlags, dmDisplayFrequency;
        public int dmICMMethod, dmICMIntent, dmMediaType, dmDitherType, dmReserved1, dmReserved2, dmPanningWidth, dmPanningHeight;
    }
    [DllImport("user32.dll", CharSet = CharSet.Unicode)] private static extern bool EnumDisplaySettingsW(string ecran, int mode, ref DEVMODE dm);

    // Position et taille réelles d'un écran (pixels physiques, quelle que soit la mise à l'échelle) ; null : inconnu.
    public static int[] Physique(string ecran)
    {
        var dm = new DEVMODE();
        dm.dmSize = (short)Marshal.SizeOf(typeof(DEVMODE));
        if (!EnumDisplaySettingsW(ecran, -1, ref dm) || dm.dmPelsWidth <= 0) return null;
        return new[] { dm.dmPositionX, dm.dmPositionY, dm.dmPelsWidth, dm.dmPelsHeight };
    }
}
'@
try { [void][PilouTournage]::SetProcessDpiAwareness(2) } catch { try { [void][PilouTournage]::SetProcessDPIAware() } catch { } }
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

if (-not $Exe) { $Exe = Join-Path $env:USERPROFILE '.claude\compagnon\bureau\PilouBureau.exe' }
if (-not (Test-Path $Exe)) { throw "PilouBureau.exe introuvable ($Exe) : installe ou mets à jour Pilou d'abord." }

# ---- 1. L'écran le plus à gauche
$ecrans = @(foreach ($s in [System.Windows.Forms.Screen]::AllScreens) {
    $p = [PilouTournage]::Physique($s.DeviceName)
    if ($null -eq $p) { $p = @($s.Bounds.X, $s.Bounds.Y, $s.Bounds.Width, $s.Bounds.Height) }
    [pscustomobject]@{ Nom = $s.DeviceName; X = [int]$p[0]; Y = [int]$p[1]; Largeur = [int]$p[2]; Hauteur = [int]$p[3]
                       Principal = $s.Primary; Forms = $s }
})
if ($ecrans.Count -eq 0) { throw "Aucun écran trouvé." }
$ecran = $ecrans | Sort-Object X, Y | Select-Object -First 1
$echelle = [math]::Round(100.0 * $ecran.Largeur / [math]::Max(1, $ecran.Forms.Bounds.Width))

Write-Host ''
Write-Host '=== Tournage de Pilou sur ton écran de gauche ===' -ForegroundColor Cyan
Write-Host ("Écrans trouvés : {0}" -f $ecrans.Count)
foreach ($e in $ecrans) {
    $repere = if ($e -eq $ecran) { '  <-- FILMÉ' } else { '' }
    $principal = if ($e.Principal) { ' (principal)' } else { '' }
    Write-Host ("  {0}{1} : {2} x {3} px à ({4}, {5}){6}" -f $e.Nom, $principal, $e.Largeur, $e.Hauteur, $e.X, $e.Y, $repere)
}
if ($ecrans.Count -eq 1) { Write-Host 'Un seul écran : c''est lui, en entier, qui sera filmé.' -ForegroundColor Yellow }
if ($echelle -ne 100) { Write-Host ("Mise à l'échelle de cet écran : environ {0} %." -f $echelle) }

# Un cadre « ÉCRAN FILMÉ » sur cet écran, 3 secondes, pour ne pas se tromper.
$cadre = New-Object System.Windows.Forms.Form
$cadre.FormBorderStyle = 'None'; $cadre.StartPosition = 'Manual'; $cadre.Bounds = $ecran.Forms.Bounds
$cadre.TopMost = $true; $cadre.ShowInTaskbar = $false; $cadre.BackColor = [System.Drawing.Color]::FromArgb(15, 19, 36); $cadre.Opacity = 0.82
$texte = New-Object System.Windows.Forms.Label
$texte.Dock = 'Fill'; $texte.TextAlign = 'MiddleCenter'; $texte.ForeColor = [System.Drawing.Color]::FromArgb(246, 157, 80)
$texte.Font = New-Object System.Drawing.Font('Segoe UI', 40, [System.Drawing.FontStyle]::Bold)
$texte.Text = "ÉCRAN FILMÉ`n" + ("{0} x {1} px" -f $ecran.Largeur, $ecran.Hauteur)
$cadre.Controls.Add($texte)
$cadre.Show()
$fin = (Get-Date).AddSeconds(3)
while ((Get-Date) -lt $fin) { [System.Windows.Forms.Application]::DoEvents(); Start-Sleep -Milliseconds 50 }
$cadre.Close(); $cadre.Dispose()

Write-Host ''
Write-Host 'Avant de continuer :' -ForegroundColor Yellow
Write-Host '  - ferme ou déplace sur un autre écran TOUT ce qui est personnel sur cet écran (mails, messages, documents…) ;'
Write-Host '  - déplace aussi cette fenêtre PowerShell sur un autre écran ;'
Write-Host '  - active « Ne pas déranger » (les notifications Windows apparaîtraient dans la vidéo).'
if (-not $Oui) {
    $r = Read-Host "C'est bien cet écran qui sera filmé (1 min 30 à 2 min). On y va ? (O/N)"
    if ($r -notmatch '^\s*[oOyY]') { Write-Host 'Rien n''a été filmé.'; return }
}

# ---- 2. ffmpeg
function TrouverFfmpeg {
    $c = Get-Command ffmpeg -ErrorAction SilentlyContinue
    if ($c) { return $c.Source }
    $lien = Join-Path $env:LOCALAPPDATA 'Microsoft\WinGet\Links\ffmpeg.exe'
    if (Test-Path $lien) { return $lien }
    $paquets = Join-Path $env:LOCALAPPDATA 'Microsoft\WinGet\Packages'
    if (Test-Path $paquets) {
        $f = Get-ChildItem $paquets -Directory -Filter 'Gyan.FFmpeg*' -ErrorAction SilentlyContinue |
            ForEach-Object { Get-ChildItem $_.FullName -Recurse -Filter 'ffmpeg.exe' -ErrorAction SilentlyContinue } |
            Select-Object -First 1
        if ($f) { return $f.FullName }
    }
    return ''
}
if ($Ffmpeg -and -not (Test-Path $Ffmpeg)) { throw "ffmpeg introuvable à l'endroit donné : $Ffmpeg" }
if (-not $Ffmpeg) { $Ffmpeg = TrouverFfmpeg }
if (-not $Ffmpeg) {
    if (Get-Command winget -ErrorAction SilentlyContinue) {
        Write-Host 'ffmpeg (le logiciel qui filme) manque : installation avec winget (Gyan.FFmpeg), une minute ou deux…' -ForegroundColor Cyan
        winget install --id Gyan.FFmpeg -e --accept-source-agreements --accept-package-agreements
        $Ffmpeg = TrouverFfmpeg
    }
    if (-not $Ffmpeg) {
        throw "ffmpeg introuvable. Installe-le (winget install --id Gyan.FFmpeg -e), ou télécharge-le et relance avec -Ffmpeg C:\chemin\ffmpeg.exe"
    }
}
Write-Host "ffmpeg : $Ffmpeg"

$racine = Join-Path $env:TEMP ('pilou-tournage-' + [guid]::NewGuid().ToString('N').Substring(0, 8))
$demo = Join-Path $racine 'demo'
New-Item -ItemType Directory -Force $demo | Out-Null

# ---- Ce que sait montrer le Pilou installé : sa version, ses scènes (Défense du bureau, Expéditions, rayon
# Ensembles… s'il les a déjà ; sinon la visite les saute et la chronologie les note « jouee: false »).
$liste = Join-Path $racine 'essais.json'
$test = Start-Process -FilePath $Exe -ArgumentList ('"--essais-disponibles={0}"' -f $liste) -PassThru -WindowStyle Hidden
if (-not $test.WaitForExit(8000)) { try { $test.Kill() } catch { } }
if (-not (Test-Path $liste)) {
    Remove-Item -Recurse -Force $racine -ErrorAction SilentlyContinue
    throw "Ce Pilou est trop ancien pour la visite guidée : clic droit sur Pilou → Version → Chercher une mise à jour, puis relance ce script."
}
$disponibles = [System.IO.File]::ReadAllText($liste) | ConvertFrom-Json
Write-Host ("Pilou {0}" -f $disponibles.version)
$sautees = @($disponibles.etapes | Where-Object { -not $_.jouee } | ForEach-Object { $_.etape })
if ($sautees.Count -gt 0) { Write-Host ("Pas encore dans cette version (sautées) : {0}" -f ($sautees -join ', ')) }

# ---- Dossier de démo : trois sessions fictives (sans BOM)
$utf8 = New-Object System.Text.UTF8Encoding($false)
$t = [DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds()
$sessions = @(
    @{ session = 'demo-api';  libelle = 'api';  enTour = $true;  debutTour = $t - 65000; outil = 'Bash' },
    @{ session = 'demo-site'; libelle = 'site'; finTour = $t - 90000 },
    @{ session = 'demo-docs'; libelle = 'docs'; finTour = $t - 20000 }
)
foreach ($s in $sessions) {
    $e = @{ v = 3; source = 'claude'; t = $t; ttl = 3600000; humeur = 'repos'; rev = 0; outilRev = 0; inquiet = $false; fatigue = $false
            nom = 'Pilou'; niveau = 18; bureau = $true; finRaison = ''; debutOutil = 0; finTour = 0; debutTour = 0; xp = 0
            enTour = $false; outil = ''; attente = '' }
    foreach ($k in $s.Keys) { $e[$k] = $s[$k] }
    [System.IO.File]::WriteAllText((Join-Path $demo "etat-$($s.session).json"), ($e | ConvertTo-Json -Compress), $utf8)
}

$video = Join-Path $racine 'pilou-ecran-gauche.mp4'
$brute = Join-Path $racine 'chronologie-brute.json'
$finale = Join-Path $racine 'chronologie.json'
$avant = @(Get-Process PilouBureau -ErrorAction SilentlyContinue).Count -gt 0
$ff = $null
$visite = $null
$fini = $false
try {
    Write-Host ''
    Write-Host 'Tournage dans 5 secondes : ne touche plus ni à la souris ni au clavier. (Échap ici pour arrêter.)' -ForegroundColor Cyan
    Start-Sleep -Seconds 5

    # ---- 2 bis. Le film : cet écran seulement, souris visible, sans son ; arrêt propre par « q ».
    $l = $ecran.Largeur - ($ecran.Largeur % 2); $h = $ecran.Hauteur - ($ecran.Hauteur % 2)
    $info = New-Object System.Diagnostics.ProcessStartInfo
    $info.FileName = $Ffmpeg
    $modele = '-hide_banner -loglevel error -nostats -y -f gdigrab -framerate {0} -draw_mouse 1 -offset_x {1} -offset_y {2} ' +
        '-video_size {3}x{4} -i desktop -an -c:v libx264 -preset veryfast -crf 20 -pix_fmt yuv420p -movflags +faststart "{5}"'
    $info.Arguments = $modele -f $Ips, $ecran.X, $ecran.Y, $l, $h, $video
    $info.UseShellExecute = $false
    $info.RedirectStandardInput = $true
    $info.CreateNoWindow = $true
    $ff = [System.Diagnostics.Process]::Start($info)
    $debutVideo = [DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds()
    Start-Sleep -Seconds 2
    if ($ff.HasExited) { throw "ffmpeg s'est arrêté tout de suite (code $($ff.ExitCode)) : rien n'est filmé." }
    Write-Host '● Enregistrement en cours…' -ForegroundColor Cyan

    # ---- 3 et 4. Le Pilou de démo prend la place du tien (--redemarrer), en bas de l'écran de gauche, et joue la visite.
    $arguments = @('--redemarrer', ('"--visite-guidee={0}"' -f $brute), '--ecran=gauche', ('"{0}"' -f $demo))
    $visite = Start-Process -FilePath $Exe -ArgumentList $arguments -PassThru
    $limite = (Get-Date).AddSeconds(240)
    $arrete = $false
    while (-not $visite.HasExited -and (Get-Date) -lt $limite) {
        Start-Sleep -Milliseconds 400
        try {
            while ([Console]::KeyAvailable) { if ([Console]::ReadKey($true).Key -eq 'Escape') { $arrete = $true } }
        } catch { }
        if ($arrete) { break }
    }
    if (-not $visite.HasExited) {
        try { $visite.Kill() } catch { }
        if ($arrete) { Write-Host 'Arrêté à ta demande.' -ForegroundColor Yellow }
        else { Write-Host 'La visite guidée a dépassé le temps prévu : arrêtée.' -ForegroundColor Yellow }
    }
    Start-Sleep -Seconds 1
    $fini = -not $arrete
}
finally {
    # Fin du film (« q » : ffmpeg termine proprement le fichier), puis ton Pilou revient, comme avant.
    if ($ff -and -not $ff.HasExited) {
        try { $ff.StandardInput.Write('q'); $ff.StandardInput.Flush() } catch { }
        if (-not $ff.WaitForExit(20000)) { try { $ff.Kill() } catch { } }
    }
    if ($visite -and -not $visite.HasExited) { try { $visite.Kill() } catch { } }
    if ($avant -and -not (Get-Process PilouBureau -ErrorAction SilentlyContinue)) {
        Start-Sleep -Milliseconds 500
        Start-Process -FilePath $Exe
    }
    # Les sessions fictives disparaissent avec le dossier de démo ; la vidéo reste jusqu'au zip.
    Remove-Item -Recurse -Force $demo -ErrorAction SilentlyContinue
}

if (-not (Test-Path $video) -or (Get-Item $video).Length -lt 10000) {
    Remove-Item -Recurse -Force $racine -ErrorAction SilentlyContinue
    throw "La vidéo n'a pas été enregistrée."
}

# ---- 5. Chronologie pour le montage : instant de chaque étape, en secondes depuis le début de la vidéo.
$etapes = @()
if (Test-Path $brute) {
    $lu = [System.IO.File]::ReadAllText($brute) | ConvertFrom-Json
    $etapes = @(foreach ($e in $lu.etapes) {
        [pscustomobject]@{ etape = $e.etape; jouee = [bool]$e.jouee; debut_s = [math]::Round(([double]$e.t - $debutVideo) / 1000.0, 1)
                           t_unix_ms = [int64]$e.t }
    })
}
else {
    Write-Host 'Pas de chronologie (visite interrompue ?) : la vidéo est quand même dans le zip.' -ForegroundColor Yellow
    # Au moins ce qui était prévu, et ce que cette version sait jouer.
    $etapes = @(foreach ($e in $disponibles.etapes) { [pscustomobject]@{ etape = $e.etape; jouee = $false; prevue = [bool]$e.jouee } })
}
$resume = [pscustomobject]@{
    video = 'pilou-ecran-gauche.mp4'
    version_pilou = [string]$disponibles.version
    complete = $fini
    ecran = [pscustomobject]@{ x = $ecran.X; y = $ecran.Y; largeur = $ecran.Largeur; hauteur = $ecran.Hauteur; echelle_pourcent = $echelle; ecrans = $ecrans.Count }
    images_par_seconde = $Ips
    debut_video_unix_ms = $debutVideo
    note = 'debut_s : secondes depuis le début de la vidéo (à une demi-seconde près : démarrage de ffmpeg).'
    etapes = $etapes
    # Pour un carton « Bientôt : … » au montage : ce que cette version n'a pas pu montrer.
    a_venir = @($etapes | Where-Object { -not $_.jouee -and $_.etape -notlike 'erreur*' } | ForEach-Object { $_.etape })
    essais_disponibles = @($disponibles.essais)
    rayons_boutique = @($disponibles.rayons)
}
[System.IO.File]::WriteAllText($finale, ($resume | ConvertTo-Json -Depth 5), $utf8)

$zip = Join-Path ([Environment]::GetFolderPath('Desktop')) 'pilou-ecran-gauche.zip'
if (Test-Path $zip) { Remove-Item $zip -Force }
Compress-Archive -Path $video, $finale -DestinationPath $zip
Remove-Item -Recurse -Force $racine -ErrorAction SilentlyContinue
$mo = [math]::Round((Get-Item $zip).Length / 1MB, 1)
Write-Host ''
Write-Host "Fini : $zip ($mo Mo). Regarde la vidéo si tu veux, puis envoie ce fichier à Claude dans la conversation." -ForegroundColor Cyan
