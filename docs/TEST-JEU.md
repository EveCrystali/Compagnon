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
| Le phare éteint | 199/199 · 209/209 | 6 | 11 h 24 / 14 h 23 / 25 h 57 | 32 / 36 / 60 | 17–22 (4–6) | 490 o |
| Petit Nuage | 199/199 · 215/215 | 6 | 11 h 16 / 12 h 49 / 16 h 01 | 31 / 36 / 52 | 15–22 (4) | 484 o |

Les maxima viennent des marches qui échouent souvent (jusqu'à 26 échecs au phare, au hasard) ; sans échec
ni abandon, le phare se joue en 11 h 24 à 14 h 38 d'attente. Au pire (20 fins dans l'historique, trois
parties suspendues), un message fait **1 542 octets de JSON** (limite 2 750), **2 096 chiffrés** (limite
3 800). Le tableau détaillé de chaque campagne s'écrit avec
`PILOU_TEST_JEU=<dossier> dotnet test apps/PilouBureau/tests -p:EnableWindowsTargeting=true --filter ParcoursTests`.

Attentes hors des décisions : celles du prologue durent 1 à 2 min (exprès, pour apprendre le geste) ;
au phare, `ch9-a-veille` et `ch9-g-veille` (60–90 min) ne sont pas en fin de chapitre.

## Relancer

```bash
dotnet test apps/PilouBureau/tests -p:EnableWindowsTargeting=true --filter "ParcoursTests|SynchroParcoursTests|InterfacesCampagnesTests"
cd android && ./gradlew testReleaseUnitTest --tests '*CampagnesTest*' --tests '*CapturesCampagnesTest*'   # avec le SDK Android
```

Sans SDK Android, `CampagnesTest` (Java pur) se lance avec `javac`/`java`, `org.json` et JUnit sur le
chemin de classes, les ressources `assets/campagnes` et un `campagnes/index.txt` ; la CI fait foi.
Les tests ajoutés prennent environ 5 s côté PC et 3 s côté Java.

## À vérifier à la main (rien ne tourne ici sur un vrai appareil)

**Windows**

- [ ] Fenêtre Aventure, `--essai=campagne:lecture` : le message le plus long (phare, 107 mots) et un
      choix à quatre options de 60 caractères (phare, `ch8-reunion-a`) tiennent sans barre horizontale,
      à 100 %, 125 % et 150 % d'échelle, fenêtre à sa taille minimale (840 × 560).
- [ ] `--essai=campagne:attente`, `retour`, `epreuve`, `fin` : compte à rebours, annonce une seule fois,
      chaque épreuve jouable au clavier et à la souris, « laisser faire les dés » (Échap).
- [ ] Bande de décor : chaque décor s'affiche net en dessin fin ; repli « ciel au ton » si un sprite manque.
- [ ] Fermer le PC pendant une attente, le rouvrir après l'heure de retour : Pilou revient, une annonce.
- [ ] Une fin obtenue : po et xp s'envolent une fois, l'objet exclusif est dans l'inventaire.

**Téléphone**

- [ ] Captures `jeu-*` de l'artefact : les relire après toute retouche d'écran ou de texte.
- [ ] Notification de retour à l'heure, téléphone en veille et hors ligne ; une seule ; rien si l'app est ouverte.
- [ ] Grande police système (× 1,3) et petit écran : boutons d'options sur deux lignes, rien de coupé.
- [ ] Jouer PC éteint jusqu'à une fin, puis allumer le PC : « attendent ton PC » disparaît, versé une fois.
- [ ] Décider sur les deux appareils au même choix, hors ligne, puis les reconnecter : un seul fil cohérent.
