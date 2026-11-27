# Pilou — repères pour une session Claude

Ce fichier est lu au début de chaque session. Il dit l'essentiel ; le détail est dans `docs/`.

- **Qui est Pilou, son univers, sa voix** : [docs/LORE.md](docs/LORE.md)
- **Ce qui a été décidé, et pourquoi** : [docs/DECISIONS.md](docs/DECISIONS.md)
- **Où en est le travail** : [docs/ETAT.md](docs/ETAT.md) — à tenir à jour en fin de session
- **Idées gardées pour plus tard** : [docs/IDEES.md](docs/IDEES.md)

## Le projet en trois lignes

Pilou est un petit compagnon de bureau en pixel art, gratuit, pour Windows et Android. Il vit en bas de
l'écran, mène sa petite vie sans déranger, grandit pendant qu'on travaille, et relaie au passage ce
qui compte (une IA qui attend, un message). Le propriétaire est Antoine ; on lui parle en français.

## Où est quoi

| Dossier | Contenu |
|---|---|
| `apps/PilouBureau/` | L'overlay Windows (WPF, .NET 9), ses tests xunit dans `tests/` |
| `android/` | L'app Android, en Java **sans aucune bibliothèque externe** |
| `assets/` | Ressources communes aux deux : sprites texte, catalogue, campagnes |
| `outils/sprites/` | Générateurs Python des sprites, planches de contrôle, références de rendu |
| `outils/campagnes/` | Validateur des campagnes |
| `outils/video/` | Montage de la vidéo de promo à partir d'un tournage (`monter.py`, plan dans `montage.json`) : [docs/VIDEO.md](docs/VIDEO.md) |
| `plugins/compagnon/` | Le mod Claude Code (hooks → fichiers d'état) |
| `integrations/` | Extensions VS Code et Visual Studio |
| `docs/` | Une page par sujet (campagnes, sprites, Android, connecteurs, amis…) |

## Vérifier avant de pousser

```bash
dotnet build apps/PilouBureau -c Release -p:EnableWindowsTargeting=true   # zéro avertissement
dotnet test apps/PilouBureau/tests -p:EnableWindowsTargeting=true
python3 outils/campagnes/valider.py assets/campagnes                       # zéro erreur
python3 outils/sprites/generer.py && python3 outils/sprites/reference.py   # si un sprite change
```

Android se construit avec Gradle (`android/`) ; sans SDK local, la CI fait foi (job `android`,
captures Robolectric dans l'artefact `captures-ui`).

## Règles qui ne se discutent pas

1. **Jamais d'opposition rouge / vert** (Antoine est deutéranope) : orange, bleu, violet, crème ; tout
   état porte aussi un signe de forme.
2. **Contenu 100 % original** : aucun nom, personnage, logo, niveau ou style repris d'un jeu ou d'une
   marque.
3. **Pilou reste passif** : il ne spamme pas, n'interrompt pas la saisie, se cache en plein écran et en
   visio. Une action du joueur tient en un ou deux gestes. Pas de mode de difficulté.
4. **Vie privée** : rien de personnel dans les captures, vidéos, journaux ni messages entre appareils
   (noms de fichiers sans chemin, pas de titres de fenêtres, pas de ville). Les secrets vont dans le
   coffre DPAPI, jamais dans `reglages.json`.
5. **PC et Android doivent calculer la même chose** : rendu des sprites, catalogue, vitrine, moteur des
   campagnes. Chaque paire a un fichier de référence partagé et un test des deux côtés.
6. **`installer.ps1` sans BOM** (la CI le vérifie) ; les autres `.ps1` lancés comme fichiers gardent
   leur BOM.
7. **Android** : ne jamais retirer `pilou` de sa fenêtre dans `Bulle.java` ; passer par `h.post` ;
   `bordABord` après `setContentView`.
8. **Windows** : la fenêtre de Pilou ne prend pas le focus ; ne pas appeler `SetForegroundWindow` à
   l'ouverture d'un menu WPF (il se referme).

## Git

- Une branche `claude/<sujet>` par changement, une PR vers `main`, corps en français.
- **Committer et pousser systématiquement**, sans demander : chaque changement fini part en commit, puis sur
  la branche, puis en PR.
- **Fusionner dès que la CI est verte**, sans demander (règle d'Antoine). Conflit : fusionner `main` dans la branche,
  garder les deux côtés, jamais de rebase ni de push forcé sur la branche d'un autre.
- Chaque fusion sur `main` publie une version `v0.9.<n>` ; le PC se met à jour seul sous deux heures.
- Messages de commit en français, sans nom de modèle.

## Tester en vrai sur le PC d'Antoine

Dans une session locale, le PC est à disposition pour les tests de bout en bout : lancer l'exe construit,
ouvrir la scène voulue (`--essai=<scène>`), prendre des captures, cliquer comme un joueur. Le faire **chaque
fois qu'un changement se voit à l'écran** (interface, rendu, taille, menus), sans demander, avant de dire
que c'est fini. Captures et vidéos : décor fictif, aucune donnée personnelle (règle 4). Fermer l'exe d'essai
à la fin ; ne pas toucher au Pilou installé ni à ses réglages réels.

## Ce qu'on ne peut pas vérifier depuis le cloud

Rien ne tourne sur un vrai Windows ni un vrai téléphone dans une session cloud. Le dire dans chaque
compte rendu. Sur le PC d'Antoine, on peut lancer l'exe (`--essai=<scène>` pour voir une scène sans
attendre) et tourner une vidéo (`outils/tourner-ecran-gauche.ps1`, décor fictif, aucune donnée réelle).
