# Test de jeu des campagnes

Ce que les tests vérifient tout seuls avant chaque version, comment les relancer, et ce qu'il reste à
regarder de ses yeux sur un vrai Windows et un vrai téléphone. Le contrat du moteur est
[CAMPAGNES.md](CAMPAGNES.md) ; l'app Android, [ANDROID.md](ANDROID.md).

## Ce qui est couvert automatiquement

### 1. Parcours entiers, rejoués par le moteur (`apps/PilouBureau/tests`)

- **Le simulateur** (`Simu.cs`) rejoue une partie comme le moteur : mêmes check-points, mêmes effets,
  **mêmes tirages** (graine de la partie, compteur de tirages). Il joue **1 500 marches à graine fixe
  par campagne** (choix au hasard, ou guidés vers les fins ; épreuves réussies, ratées ou laissées aux
  dés ; échecs, repos et retour au check-point ; abandons et reprises), puis des marches guidées vers
  toute arête encore jamais vue.
- **La couverture** (`ParcoursTests.Chaque_fin_chaque_noeud_chaque_arete_rejoues_par_le_moteur`) :
  chaque nœud, chaque arête (option, issue d'épreuve, issue de hasard, fin d'attente, fin de repos) et
  chaque fin est atteint ; une option jamais proposée ou une issue jamais tirée fait échouer.
- **Le vrai moteur** rejoue une sélection de ces marches (une par fin, puis de quoi couvrir toutes les
  arêtes, puis des joueurs « moyens »), par le carnet, avec une **horloge simulée** : délais humains
  (secondes, demi-heure, nuit), attentes franchies à l'heure, vérifiées au milieu (« vas-y » refusé,
  toujours en route) et une seconde avant la fin. À chaque pas, la phase et l'état (nœud, variables,
  objets, drapeaux) doivent être ceux du simulateur, et la durée de chaque attente la même.
- **Récompenses** : po et xp acquis = exactement ceux des nœuds traversés, une fois chacun ; plafonds
  par chapitre (40 po, 20 xp) et par campagne (600 po, 300 xp) sur **chaque** marche, échecs compris ;
  le PC verse une fois, et zéro de plus après relecture du profil et réception (deux fois) de ses
  propres messages renvoyés par le téléphone ; souvenir, titre et objet exclusif de la fin présents ;
  rejouer ne rapporte ni po ni xp.
- **Prologue** : assez petit pour une carte complète de ses états (`Carte`, 74 états) : aucune impasse,
  aucune boucle sans sortie, aucun état sans fin atteignable.
- **Conditions et durées** (`Conditions_possibles_et_attentes_dans_les_bornes`) : aucun drapeau,
  objet ou variable testé qui ne soit jamais posé ; les attentes hors 5–30 min, les longues hors 1–3 h
  ou hors fin de chapitre sont listées (sortie du test).

### 2. PC == téléphone

- `android/app/src/test/resources/campagnes-vecteurs.txt` contient maintenant, en plus des cas du
  moteur, **une partie entière par fin des quatre campagnes** (20 parties) et une divergence entre deux
  appareils. Chaque ligne est une décision ou un état (empreinte) ; `CampagnesTest.memesVecteursQueLePc`
  la rejoue avec `Campagnes.java` : mêmes états, mêmes messages, même fil, même signature du carnet.
- Régénérer après un changement voulu du moteur ou d'une campagne :
  `PILOU_REGENERER=1 dotnet test apps/PilouBureau/tests -p:EnableWindowsTargeting=true --filter Le_telephone_rejoue_les_memes_vecteurs`.
  Les parties entières des vraies campagnes y sont comparées **sans la prose** (textes, lieux, ligne « pendant ») :
  une relecture d'orthographe ne les change pas. Les cas plus anciens du prologue comparent aussi ses textes :
  une retouche du prologue demande de régénérer.

### 3. Synchronisation (`SynchroParcoursTests`)

- Le téléphone finit une campagne **PC éteint** ; le PC ne lit que le dernier message, verse une fois ;
  un vieux message en retard et le dernier en double ne changent rien ; le téléphone n'attend plus rien.
- Deux appareils jouent la même partie à tour de rôle avec **40 % de messages perdus**, des doublons et
  des retards : carnets identiques à la fin, une fin, versé une fois.
- **Divergence** au même choix : dans le délai de grâce (10 min), le plus ancien gagne ; au-delà, la base
  la plus avancée l'emporte. Dans les deux cas les carnets se retrouvent identiques et aucun fil ne garde
  le choix perdant.
- **Taille des messages au pire** : 20 fins dans l'historique, trois parties suspendues, la plus longue
  marche de chaque campagne mesurée pas à pas.

### 4. Interfaces

- **Windows** (`InterfacesCampagnesTests`, sans WPF) : chaque humeur, tenue de voyage, décor
  (`decor-<campagne>-<id>`), souvenir, objet exclusif, vignette (`campagne-<id>`) et emblème (`ton-<ton>`)
  référencé se dessine en 1× et en 2× ; les textes les plus longs passent entiers par le fil de la
  fenêtre ; `--essai=campagne:<id>` arrive à une fin en moins de 600 pas de 2,5 s.
- **Android** (`CapturesCampagnesTest`, Robolectric) : pour chaque campagne, le message le plus long,
  le choix le plus chargé, le départ, l'attente, l'épreuve (et son jeu), le repos et la fin, en petit
  téléphone clair, sombre et en grande police (× 1,3). Images `jeu-*.png` dans l'artefact `captures-ui`
  du job `android`, miniatures dans son journal (lignes `CAPTURE`).

## Résultats (novembre 2026)

| Campagne | Nœuds / arêtes couverts | Fins | Attentes et repos par parcours (min / médiane / max) | Choix | Attentes (dont ≥ 1 h) | Message le plus gros |
|---|---|---|---|---|---|---|
| Prologue | 25/25 · 27/27 | 2 | 2 min / 5 min / 55 min | 4 / 4 / 10 | 2–7 (0) | 325 o |
| La Grande Panne | 195/195 · 209/209 | 6 | 7 h 52 / 11 h 30 / 18 h 17 | 31 / 36 / 54 | 15–22 (3–4) | 495 o |
| Le phare éteint | 199/199 · 209/209 | 6 | 11 h 24 / 13 h 51 / 25 h 57 | 32 / 36 / 60 | 17–22 (4–5) | 490 o |
| Petit Nuage | 199/199 · 215/215 | 6 | 11 h 16 / 12 h 49 / 16 h 01 | 31 / 36 / 52 | 15–22 (4) | 484 o |

Les maxima viennent des marches qui échouent souvent (jusqu'à 26 échecs au phare, au hasard) ; sans échec
ni abandon, le phare se joue en 11 h 24 à 14 h 19 d'attente. Au pire (20 fins dans l'historique, trois
parties suspendues), un message fait **1 542 octets de JSON** (limite 2 750), **2 096 chiffrés** (limite
3 800). Le tableau détaillé de chaque campagne s'écrit avec
`PILOU_TEST_JEU=<dossier> dotnet test apps/PilouBureau/tests -p:EnableWindowsTargeting=true --filter ParcoursTests`.

Attentes hors des décisions : seules celles du prologue (1 à 2 min, exprès, pour apprendre le geste). Au phare,
`ch9-a-veille` et `ch9-g-veille`, qui duraient 60–90 min sans fermer le chapitre (un choix suit), ont été ramenées à
20–30 min le 27 novembre ; `ch9-s-veille` et `ch9-f-corne` (60–90 min) mènent droit à une fin et gardent leur durée.
Un script hors dépôt a vérifié qu'aucune autre attente de plus de 30 min ne tombe en milieu de chapitre dans les quatre
campagnes (toutes précèdent le chapitre suivant ou une fin).

## Relancer

```bash
dotnet test apps/PilouBureau/tests -p:EnableWindowsTargeting=true --filter "ParcoursTests|SynchroParcoursTests|InterfacesCampagnesTests"
cd android && ./gradlew testReleaseUnitTest --tests '*CampagnesTest*' --tests '*CapturesCampagnesTest*'   # avec le SDK Android
```

Sans SDK Android, `CampagnesTest` (Java pur) se lance avec `javac`/`java`, `org.json` et JUnit sur le
chemin de classes, les ressources `assets/campagnes` et un `campagnes/index.txt` ; la CI fait foi.
Les tests ajoutés prennent environ 5 s côté PC et 3 s côté Java.

## À vérifier à la main

**Windows** — passé le 27 novembre 2026 sur le PC d'Antoine (Windows 11, deux écrans à 100 %, 96 ppp), exe d'essai
dans un dossier jetable (le Pilou installé et ses réglages n'ont pas été touchés). Les fenêtres ont été rendues par
l'exe lui-même : `--essai=<scène> --captures=<dossier>` écrit chaque fenêtre ouverte en PNG à 100, 125 et 150 %, puis à sa
taille minimale, et liste les défileurs horizontaux (`fenetres.txt`). La souris et le clavier n'ont pas été pilotés
(accès au bureau resté sans réponse) : ce qui demande un geste du joueur reste à faire.

- [x] **ok, après deux corrections** — Fenêtre Aventure, `--essai=campagne:longue` (nouvelle scène : le message le plus
      long des campagnes et le choix à quatre options `ch8-reunion-a` du phare) : aucun défileur horizontal à 1004 × 681
      ni à la taille minimale (840 × 560), rendu à 100, 125 et 150 %. Défauts trouvés et corrigés à la taille minimale :
      la colonne de gauche (portrait, chapitre, sac) passait sous « Bibliothèque / Mettre de côté » (elle défile
      maintenant) ; quatre options écrasaient le fil à zéro hauteur (la zone d'action défile, le fil garde 110 px).
      **Non vérifié** : un vrai passage de Windows à 125 / 150 % (il faudrait changer l'échelle d'Antoine) ; le rendu
      à ces échelles est celui de WPF, sans les messages DPI ni l'arrondi des pixels de l'écran.
- [~] **en partie** — `--essai=campagne:attente`, `retour`, `epreuve`, `fin` : compte à rebours et barre affichés
      (« encore moins d'une minute »), écran d'épreuve et de fin sans débordement, y compris à la taille minimale (la
      fin y défile). **Non vérifié** : jouer chaque épreuve au clavier et à la souris, « laisser faire les dés »
      (Échap) — demande de piloter la souris.
- [~] **en partie** — Bande de décor : jardin, mare, maison, hall de la Grande Panne nets à 100 % ; le dessin fin de
      Pilou est net à l'écran (capture de la fenêtre par Windows, pixels francs). **Non vérifié** : chaque décor un par
      un, le repli « ciel au ton », la netteté à 125 / 150 % sur un vrai écran.
- [x] **ok** — Fermer le PC pendant une attente, le rouvrir après l'heure de retour : profil isolé avec le prologue en
      attente (1 min), exe arrêté net pendant l'attente, relancé après : **une** annonce (« je suis arrivé ! … ▸ La
      mare »), notée aussitôt ; relancé encore : plus de bulle, le signe « ! » seul. Dans les heures calmes
      (22 h – 8 h), Pilou se tait et ne montre que le « ! » : voulu.
- [x] **ok** (sauf l'animation) — Une fin obtenue (prologue fini hors de l'exe, puis deux lancements) : 25 po
      (`PoCampagnes`), 13 xp (`XpTelephone`) et l'objet exclusif `feuille` versés au premier lancement, rien de plus au
      second. **Non vu** : l'envol des po et de l'xp (trop bref pour une capture à heure fixe).

**Autres points Windows** (section « Jamais vérifié » de `ETAT.md`)

- [x] **ok** — Charge du dessin fin, mesurée 60 s sur l'exe d'essai au repos : 4,7 % d'un cœur en dessin fin, 4,5 %
      en dessin d'origine (0,17 % du processeur, 28 cœurs) ; pour mémoire, le Pilou installé : environ 6 % d'un cœur.
- [x] **ok, après correction** — Fenêtre des expéditions (`--essai=expedition:journal`) : rien ne déborde, à
      sa taille normale ni minimale. Défaut corrigé : les ◀ ▶ de l'équipement, désactivés, prenaient le gris clair de
      Windows ; ils ont maintenant l'habit rétro, comme l'Aventure et le journal.
- [x] **ok** — Fenêtre Journal (`--essai=journal`, `complicite`) : page, navigation, ligne de complicité lisibles ;
      à la taille minimale le texte d'une page défile.
- [x] **ok, après correction** — Bulle de Pilou : une phrase plus large que la bulle était coupée net, sans « … »
      (retour d'expédition, mot du jour). Elle passe maintenant à la ligne ; les lignes discrètes (en expédition…)
      finissent par « … ».
- [ ] **non vérifié** — Extensions VS Code et Visual Studio : il faudrait les installer dans les éditeurs d'Antoine.
- Test `Vecteurs_partages_avec_le_telephone` : échouait sur un PC à l'heure de Paris (date convertie à l'heure locale,
  fichier écrit en UTC par la CI). Corrigé : décalage fixe UTC dans le test.

**Téléphone**

- [ ] Captures `jeu-*` de l'artefact : les relire après toute retouche d'écran ou de texte.
- [ ] Notification de retour à l'heure, téléphone en veille et hors ligne ; une seule ; rien si l'app est ouverte.
- [ ] Grande police système (× 1,3) et petit écran : boutons d'options sur deux lignes, rien de coupé.
- [ ] Jouer PC éteint jusqu'à une fin, puis allumer le PC : « attendent ton PC » disparaît, versé une fois.
- [ ] Décider sur les deux appareils au même choix, hors ligne, puis les reconnecter : un seul fil cohérent.
