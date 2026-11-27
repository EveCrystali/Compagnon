# Tourne la vidéo de présentation de Pilou sur ton VRAI écran de GAUCHE, tout seul, et prépare un zip à envoyer.
#   powershell -ExecutionPolicy Bypass -File .\tourner-ecran-gauche.ps1
#   (options : -Ffmpeg C:\chemin\ffmpeg.exe · -Exe C:\chemin\PilouBureau.exe · -Ips 30 · -Oui pour ne pas demander
#    · -SansDecor pour filmer ton vrai bureau derrière Pilou au lieu du décor fictif)
#
# Ce que fait le script, dans l'ordre :
#   1. trouve l'écran le plus à gauche (pixels physiques, mise à l'échelle comprise), te le montre (cadre
#      « ÉCRAN FILMÉ » quelques secondes) et te demande de confirmer : c'est lui, et lui seul, qui est filmé ;
#   2. vérifie ffmpeg (sinon l'installe avec winget : Gyan.FFmpeg) et filme cet écran (ddagrab, sinon gdigrab, 30 i/s, souris
#      visible, H.264, sans son) en arrière-plan ;
#   3. réduit cette fenêtre PowerShell, puis remplace pour un moment ton Pilou par un Pilou de démonstration, en
#      grand, posé en bas de cet écran devant un DÉCOR de tournage (un faux bureau : fond dégradé, fausses fenêtres,
#      fausse barre des tâches avec horloge et icône de Pilou) qui cache tout ce qui est à toi. Il joue une visite
#      guidée d'environ 1 min 10 (2 min 25 avec les scènes récentes) : promenade, une IA qui attend, le vrai menu
#      clic droit et ses sous-menus, la boutique, la fenêtre Amis, le clavier, la photo, une visite chez Léo, la
#      pluie, deux petits jeux, l'évolution, puis (si ta version les a) le rayon Ensembles, la Défense du bureau,
#      les Expéditions, la pêche et la cuisine, l'Aventure (lecture, retour, personnage qui parle, épreuve, fin),
#      un petit mot de Pilou, l'annonce d'un palier de complicité avec le Journal, et enfin le menu de l'icône
#      près de l'horloge. La souris bouge toute seule : n'y touche pas ;
#   4. attend la fin réelle de la visite (signal de fin), arrête le film, rouvre cette fenêtre, relance ton Pilou
#      habituel et crée pilou-ecran-gauche.zip sur le Bureau : la vidéo + chronologie.json (pour chaque étape, son
#      début et sa fin, et les rectangles à cadrer au montage) + erreurs.txt si quelque chose a raté.
# Rien de personnel : le Pilou de démo lit trois sessions FICTIVES (« api », « site », « docs ») dans un dossier
# temporaire, avec un profil, des amis (Léo, Maya, Sam, Noé) et un code ami fictifs, en mémoire. Ton profil
# (XP, po, objets), tes amis, tes connecteurs et tes réglages ne sont ni lus ni modifiés. Aucun réseau.
# Le décor cache l'écran filmé, mais mets quand même « Ne pas déranger » (une notification Windows passerait
# devant). Arrêter en cours de route : Alt+Tab vers cette fenêtre, puis Échap (ou Ctrl+C).
# Il faut une version de Pilou qui connaît --visite-guidee (menu de Pilou → Version → Chercher une mise à jour).
# Les scènes plus récentes (Défense du bureau, Expéditions, rayon Ensembles, pêche, cuisine, Aventure, mot,
# complicité et Journal) sont jouées si la
# version installée les a, sautées sinon : chronologie.json dit pour chaque étape « jouee » vrai ou faux,
# et donne la version de Pilou (version_pilou) et la liste de ce qui manque (a_venir).
param(
    [string]$Ffmpeg = '',
    [string]$Exe = '',
    [int]$Ips = 30,
    [switch]$Oui,
    [switch]$SansDecor
)
$ErrorActionPreference = 'Stop'

# ---- 0. Pixels physiques : le script se déclare « conscient de la mise à l'échelle » avant de lire les écrans.
Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
public static class PilouTournageV2
{
    [DllImport("shcore.dll")] public static extern int SetProcessDpiAwareness(int valeur);
    [DllImport("user32.dll")] public static extern bool SetProcessDPIAware();
    // Cette fenêtre PowerShell (console classique ou Terminal) : réduite pendant le film, rouverte après.
    [DllImport("kernel32.dll")] public static extern IntPtr GetConsoleWindow();
    [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();
    [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr fenetre, int commande);
    [DllImport("user32.dll")] public static extern bool IsIconic(IntPtr fenetre);
    [DllImport("user32.dll")] public static extern bool IsWindowVisible(IntPtr fenetre);

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
try { [void][PilouTournageV2]::SetProcessDpiAwareness(2) } catch { try { [void][PilouTournageV2]::SetProcessDPIAware() } catch { } }
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

if (-not $Exe) { $Exe = Join-Path $env:USERPROFILE '.claude\compagnon\bureau\PilouBureau.exe' }
if (-not (Test-Path $Exe)) { throw "PilouBureau.exe introuvable ($Exe) : installe ou mets à jour Pilou d'abord." }

# ---- 1. L'écran le plus à gauche
$ecrans = @(foreach ($s in [System.Windows.Forms.Screen]::AllScreens) {
    $p = [PilouTournageV2]::Physique($s.DeviceName)
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
if ($SansDecor) {
    Write-Host '  - ferme ou déplace sur un autre écran TOUT ce qui est personnel sur cet écran (mails, messages, documents…) ;'
}
else {
    Write-Host '  - un décor de bureau FICTIF couvrira cet écran pendant le film (tes icônes et ta barre des tâches n''y seront pas) ;'
}
Write-Host '  - cette fenêtre PowerShell sera réduite pendant le film, puis rouverte ;'
Write-Host '  - active « Ne pas déranger » (les notifications Windows apparaîtraient dans la vidéo).'
if (-not $Oui) {
    $r = Read-Host "C'est bien cet écran qui sera filmé (environ 1 min 45). On y va ? (O/N)"
    if ($r -notmatch '^\s*[oOyY]') { Write-Host 'Rien n''a été filmé.'; return }
}
# La fenêtre où tu viens de répondre (console classique ou Terminal Windows) : réduite pendant le film.
$fenetresConsole = @(@([PilouTournageV2]::GetConsoleWindow(), [PilouTournageV2]::GetForegroundWindow()) |
    Where-Object { $_ -ne [IntPtr]::Zero } | Select-Object -Unique)

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

# ---- 2 bis. Comment filmer. ddagrab (Desktop Duplication, sur la carte graphique) d'abord : gdigrab recopie l'écran
# par BitBlt 30 fois par seconde, et sur un vrai Windows (2560 × 1440, novembre 2026) cela a figé l'interface de Pilou
# près de deux minutes en pleine visite. ddagrab numérote les sorties à sa façon : on garde celle qui a la taille de
# l'écran filmé, et seulement s'il n'y en a qu'une (deux écrans identiques : on ne sait pas lequel, retour à gdigrab).
function SortieDdagrab {
    $essai = Join-Path $env:TEMP ('pilou-sortie-' + [guid]::NewGuid().ToString('N').Substring(0, 8) + '.png')
    $trouvees = @()
    Add-Type -AssemblyName System.Drawing
    for ($i = 0; $i -lt 6; $i++) {
        $p = Start-Process -FilePath $Ffmpeg -PassThru -WindowStyle Hidden -ArgumentList @('-hide_banner', '-loglevel', 'error', '-y',
            '-f', 'lavfi', '-i', "ddagrab=output_idx=${i}:framerate=5,hwdownload,format=bgra", '-frames:v', '1', ('"{0}"' -f $essai))
        if (-not $p.WaitForExit(8000)) { try { $p.Kill() } catch { } }
        if (-not (Test-Path $essai)) { break }   # plus de sortie (ou pas de ddagrab dans ce ffmpeg)
        try {
            $image = [System.Drawing.Image]::FromFile($essai)
            if ($image.Width -eq $ecran.Largeur -and $image.Height -eq $ecran.Hauteur) { $trouvees += $i }
            $image.Dispose()
        } catch { }
        Remove-Item $essai -Force -ErrorAction SilentlyContinue   # une image du vrai bureau : jamais gardée
    }
    if ($trouvees.Count -eq 1) { return $trouvees[0] }
    return -1
}
$sortieDda = SortieDdagrab
$nvenc = [bool](& $Ffmpeg -hide_banner -encoders 2>$null | Select-String 'h264_nvenc')
if ($sortieDda -ge 0) { Write-Host ("Capture : ddagrab (sortie {0}){1}" -f $sortieDda, $(if ($nvenc) { ', encodage NVENC' } else { '' })) }
else { Write-Host 'Capture : gdigrab (ddagrab indisponible pour cet écran)' }

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
$lignes = Join-Path $racine 'chronologie-brute.jsonl'
$erreurs = Join-Path $racine 'erreurs.txt'
$finale = Join-Path $racine 'chronologie.json'
$avant = @(Get-Process PilouBureau -ErrorAction SilentlyContinue).Count -gt 0
$ff = $null
$visite = $null
$arrete = $false
$depasse = $false
$codeSortie = $null
$reduites = @()
# Durée prévue par cet exe (scènes qu'il sait jouer), plus une marge large : on attend la vraie fin, pas une montre.
$prevue = 130.0
if ($disponibles.PSObject.Properties['duree_s']) { $prevue = [double]$disponibles.duree_s }
$attente = [math]::Max(240, [math]::Ceiling($prevue) + 120)

# La visite est-elle allée au bout ? (l'overlay écrit « complete » dans sa chronologie, au fil de l'eau)
function VisiteComplete {
    if (-not (Test-Path $brute)) { return $false }
    try { return [bool](([System.IO.File]::ReadAllText($brute) | ConvertFrom-Json).complete) } catch { return $false }
}

try {
    Write-Host ''
    Write-Host 'Tournage dans 5 secondes : ne touche plus ni à la souris ni au clavier.' -ForegroundColor Cyan
    Write-Host '(Pour arrêter : Alt+Tab vers cette fenêtre, puis Échap.)'
    Start-Sleep -Seconds 5

    # ---- 2 bis. Le film : cet écran seulement, souris visible, sans son ; arrêt propre par « q ».
    $l = $ecran.Largeur - ($ecran.Largeur % 2); $h = $ecran.Hauteur - ($ecran.Hauteur % 2)
    $info = New-Object System.Diagnostics.ProcessStartInfo
    $info.FileName = $Ffmpeg
    $modele = '-hide_banner -loglevel error -nostats -y -f gdigrab -framerate {0} -draw_mouse 1 -offset_x {1} -offset_y {2} ' +
        '-video_size {3}x{4} -i desktop -an -c:v libx264 -preset veryfast -crf 20 -pix_fmt yuv420p -movflags +faststart "{5}"'
    if ($sortieDda -ge 0 -and $nvenc) {
        $modele = '-hide_banner -loglevel error -nostats -y -f lavfi -i ddagrab=output_idx=' + $sortieDda + ':framerate={0}:draw_mouse=1 ' +
            '-an -c:v h264_nvenc -preset p5 -rc vbr -cq 18 -movflags +faststart "{5}"'
    }
    elseif ($sortieDda -ge 0) {
        $modele = '-hide_banner -loglevel error -nostats -y -f lavfi -i ddagrab=output_idx=' + $sortieDda + ':framerate={0}:draw_mouse=1,hwdownload,format=bgra ' +
            '-an -c:v libx264 -preset veryfast -crf 20 -pix_fmt yuv420p -movflags +faststart "{5}"'
    }
    $info.Arguments = $modele -f $Ips, $ecran.X, $ecran.Y, $l, $h, $video
    $info.UseShellExecute = $false
    $info.RedirectStandardInput = $true
    $info.CreateNoWindow = $true
    $ff = [System.Diagnostics.Process]::Start($info)
    $debutVideo = [DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds()
    Start-Sleep -Seconds 1
    if ($ff.HasExited) { throw "ffmpeg s'est arrêté tout de suite (code $($ff.ExitCode)) : rien n'est filmé." }
    Write-Host '● Enregistrement en cours…' -ForegroundColor Cyan

    # Cette fenêtre PowerShell se range (elle revient à la fin) : elle n'apparaît pas dans la vidéo.
    foreach ($f in $fenetresConsole) {
        if ([PilouTournageV2]::IsWindowVisible($f) -and -not [PilouTournageV2]::IsIconic($f)) {
            [void][PilouTournageV2]::ShowWindow($f, 6)   # SW_MINIMIZE
            $reduites += $f
        }
    }

    # ---- 3 et 4. Le Pilou de démo prend la place du tien (--redemarrer), en bas de l'écran de gauche, devant son
    # décor, et joue la visite. On attend sa vraie fin : il quitte de lui-même après avoir écrit « complete ».
    $arguments = @('--redemarrer', ('"--visite-guidee={0}"' -f $brute), '--ecran=gauche')
    if ($SansDecor) { $arguments += '--sans-decor' }
    $arguments += ('"{0}"' -f $demo)
    $visite = Start-Process -FilePath $Exe -ArgumentList $arguments -PassThru
    $null = $visite.Handle   # sans lui, Windows PowerShell 5.1 perd le code de sortie
    $limite = (Get-Date).AddSeconds($attente)
    $finVue = $null
    while (-not $visite.HasExited -and (Get-Date) -lt $limite) {
        Start-Sleep -Milliseconds 500
        try {
            while ([Console]::KeyAvailable) { if ([Console]::ReadKey($true).Key -eq 'Escape') { $arrete = $true } }
        } catch { }
        if ($arrete) { break }
        # Signal de fin écrit mais l'overlay traîne à quitter : on lui laisse 10 s.
        if ($null -eq $finVue -and (VisiteComplete)) { $finVue = Get-Date }
        if ($null -ne $finVue -and ((Get-Date) - $finVue).TotalSeconds -gt 10) { break }
    }
    if ($visite.HasExited) { try { $codeSortie = $visite.ExitCode } catch { } }
    else {
        try { $visite.Kill() } catch { }
        if ($arrete) { Write-Host 'Arrêté à ta demande.' -ForegroundColor Yellow }
        elseif ($null -eq $finVue) {
            $depasse = $true
            Write-Host ("La visite guidée n'a pas fini en {0} s : arrêtée." -f $attente) -ForegroundColor Yellow
        }
    }
    Start-Sleep -Seconds 1
}
finally {
    # Fin du film (« q » : ffmpeg termine proprement le fichier), puis ton Pilou et cette fenêtre reviennent.
    if ($ff -and -not $ff.HasExited) {
        try { $ff.StandardInput.Write('q'); $ff.StandardInput.Flush() } catch { }
        if (-not $ff.WaitForExit(20000)) { try { $ff.Kill() } catch { } }
    }
    if ($visite -and -not $visite.HasExited) { try { $visite.Kill() } catch { } }
    foreach ($f in $reduites) { [void][PilouTournageV2]::ShowWindow($f, 9) }   # SW_RESTORE
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

# ---- 5. Chronologie pour le montage, en secondes depuis le début de la vidéo et en pixels de la vidéo : chaque
# étape (début, fin, jouée ou non) et ses rectangles d'intérêt successifs (zone : ce qui compte à l'image ; zoom :
# le cadre 16:9 qui la contient, pour un zoom ou un panoramique en 1920 × 1080).
function Secondes($t) { if ($null -eq $t) { return $null } return [math]::Round(([double]$t - $debutVideo) / 1000.0, 2) }
function Rectangle($z) {
    if ($null -eq $z) { return $null }
    return [pscustomobject]@{ x = [int]$z.x - $ecran.X; y = [int]$z.y - $ecran.Y; largeur = [int]$z.largeur; hauteur = [int]$z.hauteur }
}
$lu = $null
if (Test-Path $brute) { try { $lu = [System.IO.File]::ReadAllText($brute) | ConvertFrom-Json } catch { $lu = $null } }
$complete = $false
$erreursOverlay = @()
if ($null -ne $lu) {
    $complete = [bool]$lu.complete
    $etapes = @(foreach ($e in $lu.etapes) {
        $cadres = @(foreach ($c in $e.cadres) {
            [pscustomobject]@{ quoi = [string]$c.quoi; debut_s = (Secondes $c.debut); fin_s = (Secondes $c.fin)
                               zone = (Rectangle $c.zone); zoom = (Rectangle $c.zoom) }
        })
        [pscustomobject]@{ etape = [string]$e.etape; jouee = [bool]$e.jouee; debut_s = (Secondes $e.t); fin_s = (Secondes $e.fin)
                           t_unix_ms = [int64]$e.t; cadres = $cadres }
    })
    $erreursOverlay = @(foreach ($x in $lu.erreurs) { [pscustomobject]@{ etape = [string]$x.etape; t_s = (Secondes $x.t); message = [string]$x.message } })
}
else {
    Write-Host 'Pas de chronologie (la visite n''a pas démarré ?) : la vidéo est quand même dans le zip.' -ForegroundColor Yellow
    # Au moins ce qui était prévu, et ce que cette version sait jouer.
    $etapes = @(foreach ($e in $disponibles.etapes) { [pscustomobject]@{ etape = $e.etape; jouee = $false; prevue = [bool]$e.jouee } })
}
# Fin anormale : ce que le script sait, en tête d'erreurs.txt (l'overlay y a déjà noté ses propres erreurs).
$anormale = (-not $complete) -and (-not $arrete)
if ($anormale) {
    $derniere = @($etapes | Where-Object { $_.jouee } | Select-Object -Last 1)
    $nomDerniere = 'aucune'
    if ($derniere.Count -gt 0) { $nomDerniere = $derniere[0].etape }
    $raison = 'l''overlay s''est arrêté avant la fin'
    if ($depasse) { $raison = "la visite n'a pas fini en $attente s (arrêtée)" }
    $resumeErreur = @(
        ('Fin anormale de la visite guidée : {0}.' -f $raison),
        ('Pilou {0} · dernière étape commencée : {1} · code de sortie : {2}' -f $disponibles.version, $nomDerniere, $codeSortie),
        ''
    ) -join [Environment]::NewLine
    $deja = ''
    if (Test-Path $erreurs) { $deja = [System.IO.File]::ReadAllText($erreurs) }
    if (-not $deja) { $deja = '(aucune erreur notée par Pilou : arrêt brutal, ou version sans journal d''erreurs)' + [Environment]::NewLine }
    [System.IO.File]::WriteAllText($erreurs, $resumeErreur + $deja, $utf8)
    Write-Host ('La visite s''est arrêtée avant la fin ({0}) : erreurs.txt est dans le zip.' -f $nomDerniere) -ForegroundColor Yellow
}
$resume = [pscustomobject]@{
    video = 'pilou-ecran-gauche.mp4'
    version_pilou = [string]$disponibles.version
    complete = $complete
    arretee_a_la_main = $arrete
    decor = -not $SansDecor
    ecran = [pscustomobject]@{ x = $ecran.X; y = $ecran.Y; largeur = $ecran.Largeur; hauteur = $ecran.Hauteur; echelle_pourcent = $echelle; ecrans = $ecrans.Count }
    images_par_seconde = $Ips
    debut_video_unix_ms = $debutVideo
    note = ('debut_s, fin_s : secondes depuis le début de la vidéo (à une demi-seconde près : démarrage de ffmpeg). ' +
            'cadres : rectangles successifs de chaque étape, en pixels de la vidéo ; zone = ce qui compte, zoom = cadre 16:9 qui la contient.')
    etapes = $etapes
    erreurs = $erreursOverlay
    # Pour un carton « Bientôt : … » au montage : ce que cette version n'a pas pu montrer.
    a_venir = @($etapes | Where-Object { -not $_.jouee -and $_.etape -notlike 'erreur*' } | ForEach-Object { $_.etape })
    essais_disponibles = @($disponibles.essais)
    rayons_boutique = @($disponibles.rayons)
}
[System.IO.File]::WriteAllText($finale, ($resume | ConvertTo-Json -Depth 8), $utf8)

$zip = Join-Path ([Environment]::GetFolderPath('Desktop')) 'pilou-ecran-gauche.zip'
if (Test-Path $zip) { Remove-Item $zip -Force }
$contenu = @($video, $finale)
if (Test-Path $erreurs) { $contenu += $erreurs }
if ($anormale -and (Test-Path $lignes)) { $contenu += $lignes }   # le journal brut, ligne par ligne, pour comprendre
Compress-Archive -Path $contenu -DestinationPath $zip
Remove-Item -Recurse -Force $racine -ErrorAction SilentlyContinue
$mo = [math]::Round((Get-Item $zip).Length / 1MB, 1)
Write-Host ''
Write-Host "Fini : $zip ($mo Mo). Regarde la vidéo si tu veux, puis envoie ce fichier à Claude dans la conversation." -ForegroundColor Cyan
