# Les traits de personnalité

> « RPG oui, mais de personnalité : pas de statistiques à optimiser. Pilou évolue à travers ce que fait le joueur,
> jamais sans lui. » (Antoine, 28 novembre 2026, `DECISIONS.md`, « Lien avec le joueur »)

À force de vivre avec quelqu'un, Pilou lui ressemble un peu. Il attrape des **traits** : couche-tard, pêcheur du
dimanche, câlin, tête en l'air… On ne les choisit pas, on les **découvre**. Un trait acquis **ne se perd pas**. Pilou en
porte **trois « dominants »** à la fois, qui changent lentement.

## Ce qu'un trait change, et ce qu'il ne change pas

| Change | Ne change jamais |
|---|---|
| Des **mots** : une annonce dite une seule fois, puis des répliques quand le trait est dominant | L'XP, les pièces, l'énergie, les expéditions, la boutique : **aucun chiffre, aucun bonus** |
| Ce que montre **« Pilou et moi »** : les trois dominants, les traits découverts, les autres en silhouette « ? » | La cadence : au plus trois mots par jour sur PC, un le soir sur téléphone (`PRESENCE.md`) |
| Plus tard, des **saynètes** (autre chantier) : `Traits.Dominants` est prévu pour ça | Les amis : un trait ne sort pas du groupe chiffré des appareils du joueur |

L'interface ne dit **jamais comment obtenir** un trait. Les conditions ci-dessous sont pour qui maintient le jeu.

## Les vingt traits

Définis dans [`assets/traits.txt`](../assets/traits.txt), commun au PC et au téléphone. Un trait naît quand assez de
**jours du journal de Pilou** remplissent sa condition : c'est une habitude, pas un coup d'éclat.

| N° | Trait | Naît de | Jours |
|---|---|---|---|
| 1 | Couche-tard | encore là après 23 h | 8 |
| 2 | Lève-tôt | déjà là entre 5 h et 7 h 30 | 8 |
| 3 | Pêcheur du dimanche | une prise, un samedi ou un dimanche | 4 |
| 4 | Gourmand | un plat cuisiné | 8 |
| 5 | Grand lecteur | la lecture comme activité principale (20 min au moins) | 5 |
| 6 | Codeur au long cours | le code comme activité principale (3 h au moins) | 10 |
| 7 | Casanier | une demi-heure ensemble, sans expédition ni visite | 30 |
| 8 | Voyageur | un départ en expédition | 5 |
| 9 | Câlin | cinq caresses dans la journée | 7 |
| 10 | Tête en l'air | des retrouvailles après cinq jours sans page de journal | 3 |
| 11 | Siffloteur | la musique comme activité principale (30 min au moins) | 5 |
| 12 | Bon joueur | trois petits jeux gagnés | 6 |
| 13 | Bon voisin | une visite chez un ami | 4 |
| 14 | Douillet | deux soins dans la journée | 7 |
| 15 | Flâneur | une demi-heure ensemble, un samedi ou un dimanche | 6 |
| 16 | Amateur d'histoires | un message de campagne reçu | 6 |
| 17 | Barbouilleur | le dessin comme activité principale (20 min au moins) | 4 |
| 18 | Bon public | la vidéo comme activité principale (30 min au moins) | 5 |
| 19 | Veinard | une prise rare | 3 |
| 20 | Chineur | un achat à la boutique | 6 |

- Le **numéro** est la place du trait dans le message entre appareils (un bit). Il ne change jamais et ne se réutilise
  pas ; un nouveau trait prend le numéro suivant (60 au plus).
- **Condition** : des faits du jour reliés par `&` (`pc>=1&we=1`). Les faits sont ceux du journal
  (`Presence.FaitsDuJour` : `mn tv am ta jx ca so pc pq cu qu ce vi nv mg ma`, et les textes `ac px cx me cf mo ex ob`),
  plus `we` (1 le samedi et le dimanche), `sem` (1 lundi … 7 dimanche) et `abs` (jours écoulés depuis la page précédente).
- Un seul fait a été ajouté au journal pour les traits : `ma` (1 si la personne était là entre 5 h et 7 h 30).
- **Vie privée** (règle 4) : un trait ne lit que ces faits-là. Ni titre de fenêtre, ni nom de fichier ou de logiciel, ni
  ville. « Tenir son journal » coupé : plus aucun fait n'est noté, donc plus aucun trait ne naît ; les traits déjà acquis
  restent.

## Dominants

Trois au plus, parmi les traits acquis : ceux dont la condition a été remplie le plus souvent pendant les **28 jours
d'avant le lundi de la semaine en cours**, rapportés à leur seuil ; à égalité, le plus petit numéro. Ils ne bougent donc
qu'**une fois par semaine**, et une semaine ne pèse qu'un quart : le changement est lent, sans rien garder en mémoire.

`Traits.Dominants(état, aujourd'hui)` (PC : `FenetrePilou.TraitsDominants()` ; téléphone :
`PresenceTel.traitsDominants(contexte)`) est la fonction publique prévue pour les saynètes.

## Les mots

[`assets/presence/traits.txt`](../assets/presence/traits.txt), même format que `mots.txt` :

- `annonce-<trait>` : **une** phrase par trait. Pilou la dit à son **bonjour** (PC) ou comme **mot du jour**
  (téléphone), une seule fois dans tout le groupe. Un trait par jour au plus ; une date à fêter ou un nouveau palier de
  complicité passent d'abord, le trait attend le lendemain. « Pilou me parle : jamais » : le trait n'est pas annoncé, il
  se voit seulement dans « Pilou et moi ».
- `trait-<trait>` : trois répliques au moins. Chaque trait dominant **déjà annoncé** ajoute sa famille à la rotation du
  moteur de présence, au poids d'une pensée rare : environ un mot sur quatre quand trois traits dominent. Aucune
  réplique ne dit l'heure qu'il est : elle peut tomber le matin comme le soir.
- Voix de [`LORE.md`](LORE.md) : le trait est **celui de Pilou** (« je suis devenu couche-tard. c'est toi qui m'as
  appris, je précise »), jamais un jugement sur le joueur. Ni reproche, ni conseil, ni chiffre, ni trou à remplir
  (pas même le prénom). Le test `Chaque_trait_a_son_annonce_ses_repliques_et_la_voix_de_Pilou` le vérifie.

## Où les voir

- **PC** : clic droit → Journal… → **Ses traits…** ouvre la fenêtre « Pilou et moi » (`FenetreTraits.cs`) : à gauche les
  dominants, à droite les vingt cases. `FenetrePilou.OuvrirTraits()` est prêt pour une ligne du menu (le menu est tenu
  par un autre chantier).
- **Téléphone** : la carte « Pilou et moi » de l'Accueil : les dominants, puis « n traits découverts ▾ » qui déplie la
  grille.
- **Jamais la couleur seule** : un dominant a un cadre orange **et** une étoile ★ devant son nom ; un trait inconnu a la
  silhouette « ? », un cadre pointillé **et** « ? ? ? ».
- **Icônes** : `trait-<identifiant>` et `trait-inconnu`, 16 × 16 (32 × 32 en dessin fin), dessinées par
  `outils/sprites/traits_sprites.py` ; planche de contrôle : `python3 outils/sprites/planches_traits.py`.

## Entre appareils

Comme les succès : **union**, par des valeurs qui ne font que monter. Le message de présence gagne une ligne

```
tr <traits acquis, hexadécimal> <traits annoncés, hexadécimal>
```

fusionnée par « ou » binaire (idempotent, sans ordre). Un ancien appareil l'ignore. Les faits du journal étant déjà
fusionnés jour par jour, deux appareils qui se parlent au moins une fois par semaine découvrent les mêmes traits et
voient les mêmes dominants. Limite : un appareil resté plus de sept jours sans synchroniser ne reçoit pas les faits plus
anciens (le message n'en porte que sept jours) ; il reçoit quand même les traits acquis ailleurs, mais ses dominants
peuvent différer quelque temps.

## Fichiers

| | |
|---|---|
| `assets/traits.txt` | la définition, commune |
| `assets/presence/traits.txt` | annonces et répliques |
| `apps/PilouBureau/Traits.cs` | le moteur (sans WPF) |
| `android/.../Traits.java` | sa copie exacte |
| `apps/PilouBureau/FenetreTraits.cs`, `FenetrePresence.cs` | la fenêtre « Pilou et moi », la découverte, l'annonce |
| `android/.../PresenceVue.java`, `PresenceTel.java` | la carte de l'Accueil, la découverte, l'annonce |
| `outils/sprites/traits_sprites.py`, `planches_traits.py` | les icônes et leur planche |

## Tests

- C# (`tests/TraitsTests.cs`) : définition sans ligne ignorée, une annonce et trois répliques par trait, voix de Pilou
  (tournures interdites, aucun chiffre, aucun trou), une icône par trait, **un trait naît d'une habitude**, chaque trait
  peut naître, **un trait acquis ne se perd pas** (journal vidé, fichier relu), journal en pause, **union entre
  appareils** (désordre, doublons), ancien message, **trois dominants au plus, stables dans la semaine**, **annonce une
  seule fois, au bonjour**, répliques des seuls dominants.
- **Vecteurs partagés** : `android/app/src/test/resources/traits-vecteurs.txt`, écrits par le PC
  (`PILOU_REGENERER=1 dotnet test apps/PilouBureau/tests`), rejoués ligne à ligne par `TraitsTest.java` (définition,
  mesures, acquis, dominants, états entiers, mots, bits).
- Captures : PC, `--essai=traits` (données de démonstration, rien n'est écrit) ; téléphone, `CapturesTraitsTest`
  (1078 × 2400, clair et sombre : aucun trait, carte repliée, carte dépliée), dans l'artefact `captures-ui`.

## Pas vérifié sur un vrai appareil

La fenêtre « Pilou et moi » n'a été vue que par le rendu hors écran de l'exe d'essai (100, 125 et 150 %), pas sur un
Windows réglé à 125 % ou 150 %. La carte du téléphone n'a été vue que par Robolectric. La naissance d'un trait au fil
de vraies semaines, et son annonce entre deux vrais appareils, restent à observer. Les seuils sont une première
estimation, à revoir après quelques semaines d'usage réel.
