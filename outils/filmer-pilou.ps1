# Filme Pilou pour la vidéo de présentation, sans rien de personnel.
#   powershell -ExecutionPolicy Bypass -File .\filmer-pilou.ps1
# Ce qui est enregistré : uniquement la fenêtre de Pilou (ses pixels et sa bulle, fond transparent),
# image par image, par l'overlay lui-même. Ni l'écran, ni tes fenêtres, ni tes vraies sessions :
# Pilou lit ici un dossier temporaire avec trois sessions fictives (« api », « site », « docs »).
# Résultat : pilou-film.zip sur le Bureau, à envoyer à Claude dans la conversation.
param([double]$Duree = 6, [int]$Ips = 15)
$ErrorActionPreference = 'Stop'
$exe = Join-Path $env:USERPROFILE '.claude\compagnon\bureau\PilouBureau.exe'
if (-not (Test-Path $exe)) { throw "PilouBureau.exe introuvable ($exe) : installe ou mets à jour Pilou d'abord." }

$racine = Join-Path $env:TEMP ("pilou-film-" + [guid]::NewGuid().ToString('N').Substring(0, 8))
$demo = Join-Path $racine 'demo'
$images = Join-Path $racine 'images'
New-Item -ItemType Directory -Force $demo, $images | Out-Null

# Trois sessions fictives pour la bulle.
$t = [DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds()
@(
  @{ session = 'demo-api';  libelle = 'api';  enTour = $true;  debutTour = $t - 65000; outil = 'Bash'; attente = '' },
  @{ session = 'demo-site'; libelle = 'site'; enTour = $false; debutTour = 0; outil = ''; attente = 'permission'; debutOutil = $t - 2000 },
  @{ session = 'demo-docs'; libelle = 'docs'; enTour = $false; finTour = $t - 20000; outil = ''; attente = '' }
) | ForEach-Object {
  $e = @{ v = 3; source = 'claude'; t = $t; ttl = 3600000; humeur = 'repos'; rev = 0; outilRev = 0; inquiet = $false; fatigue = $false;
          nom = 'Pilou'; niveau = 12; bureau = $true; finRaison = ''; debutOutil = 0; finTour = 0; xp = 0 } + $_
  ($e | ConvertTo-Json -Compress) | Set-Content -Encoding UTF8 (Join-Path $demo "etat-$($_.session).json")
}

# Les scènes : expressions, jeux, pêche, cuisine, stades, évolution, tenues, objets.
$scenes = @('aucun', 'etoile', 'bulles', 'tape', 'etourdi', 'niveau', 'peche', 'mord', 'prise', 'cuisine',
  'stade:1', 'stade:2', 'stade:3', 'stade:4', 'evolution',
  'tenue:code', 'tenue:tableur', 'tenue:jeu-mmo', 'tenue:musique', 'tenue:nuit',
  'objet:chapeau-pirate', 'objet:petit-chat', 'objet:aura', 'objet:parapluie')
$i = 0
foreach ($s in $scenes) {
  $i++
  $nom = $s -replace '[:]', '-'
  Write-Host ("[{0}/{1}] {2}" -f $i, $scenes.Count, $s)
  $dossier = Join-Path $images $nom
  $arguments = @("--film=$dossier", "--duree=$Duree", "--ips=$Ips")
  if ($s -ne 'aucun') { $arguments += "--essai=$s" }
  $arguments += $demo
  Start-Process -FilePath $exe -ArgumentList $arguments -Wait -WindowStyle Hidden
}

$zip = Join-Path ([Environment]::GetFolderPath('Desktop')) 'pilou-film.zip'
if (Test-Path $zip) { Remove-Item $zip }
Compress-Archive -Path (Join-Path $images '*') -DestinationPath $zip
Remove-Item -Recurse -Force $racine
$mo = [math]::Round((Get-Item $zip).Length / 1MB, 1)
Write-Host "Fini : $zip ($mo Mo). Envoie ce fichier à Claude dans la conversation." -ForegroundColor Cyan
