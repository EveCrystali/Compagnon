# Expéditions de Pilou

Une petite aventure qui se joue toute seule. On choisit un lieu (un clic), Pilou part avec son baluchon et son
épée en bois, une pancarte le remplace, et l'expédition se résout seule : combats contre des créatures, pièges,
coffres, rencontres, parfois un boss. Il revient avec quelques pièces d'or, un peu d'XP, parfois un butin
introuvable en boutique — et parfois bredouille, un peu cabossé. Un journal de quelques lignes raconte
l'aventure. Pas de mode de difficulté, rien à surveiller, rien de punitif.

Logique : `apps/PilouBureau/Expeditions.cs` (sans WPF, testée par `tests/ExpeditionsTests.cs`). Sur le PC :
`FenetreExpedition.cs` (départ, pancarte, retour, énergie) et `FenetreExpeditions.cs` (la petite fenêtre rétro).
Téléphone (lecture seule) : `Etat.java`, `PageAccueil.java`. Dessins : `outils/sprites/expedition_sprites.py`.

## Partir

- **Clic droit sur Pilou → « ⚔ Partir en expédition… »** : les lieux ouverts par le niveau, chacun avec son coût
  d'énergie, sa durée et son risque (◆◆◇◇◇) ; un clic sur un lieu, il part. Le même sous-menu donne
  l'équipement, un en-cas de route et le journal.
- **Icône près de l'horloge → « Partir en expédition… »** : la fenêtre des expéditions.
- **Téléphone** : carte « ⚔ Expédition » sur l'Accueil (en route, retour vers…, énergie, dernier journal) et
  « ⚡ » à côté de l'XP. Lecture seule : l'expédition appartient à l'appareil qui la lance, et faire partir Pilou
  depuis le téléphone demanderait de choisir quel PC l'héberge (plusieurs PC du groupe reçoivent les mêmes
  messages) ; on le garde pour plus tard.

| Lieu | Niveau | ⚡ | Durée | Risque | Boss | Butin du lieu |
|---|---|---|---|---|---|---|
| ▼ Caverne des câbles | 1 | 15 | 20 min | ◆◇◇◇◇ | bug géant | torche |
| ♣ Forêt des onglets | 5 | 25 | 40 min | ◆◆◇◇◇ | slime de cache | slime apprivoisé |
| ▲ Tour du tampon | 10 | 35 | 1 h | ◆◆◆◇◇ | golem de tickets | bouclier-couvercle |
| ≈ Marais des mises à jour | 15 | 45 | 1 h 30 | ◆◆◆◆◇ | hydre des dépendances | casque-passoire |
| ☁ Citadelle du nuage | 25 | 60 | 2 h | ◆◆◆◆◆ | gargouille de latence | carte au trésor |

Créatures (toutes inventées) : bug géant, slime de cache, spectre 404, golem de tickets, hydre des dépendances,
gargouille de latence.

## On ne peut pas en abuser

- **Énergie ⚡** (0 à 100) : chaque départ en coûte.
- **Repos** : 30 min après chaque retour (ou rappel).
- **Trois expéditions par jour** au plus, **pour tout le groupe d'appareils** : chaque appareil publie ses départs
  du jour et la fin de son repos (compteur du groupe, `Groupe.Compteur.ExpJour/ExpNombre/ExpLibre`, et le
  profil du dossier partagé) ; un PC voit donc que Pilou est déjà parti depuis l'autre PC.
- **Pas pendant une visite** (ni chez un ami, ni avec un invité), ni pendant une évolution. Et inversement : en
  expédition, pas de visite (l'ami lit « ne reçoit pas en ce moment »), pas de petit jeu, pas de geste.

## L'énergie

| Source | Gain | Plafond |
|---|---|---|
| Attente | ≈ +5 / h | jusqu'à 50 seulement |
| **Travail productif** : temps passé dans une appli de travail (code, tableur, écriture, mail, diaporama, lecture, dessin), la personne présente | +1 toutes les 6 min | 40 / jour (avec les deux lignes suivantes) |
| Une IA finit (« ✓ fini », Claude, Codex…) | +1, au plus toutes les 3 min | (même plafond) |
| Une quête réussie | +2 | (même plafond) |
| Plat cuisiné | +6 (inventé +4, brûlé +1) | 40 / jour (repas) |
| En-cas des soins | croquettes +2, pomme +4, soupe +5, gâteau +6 | (même plafond) |
| En-cas de route (boutique, rayon Spéciaux) | galette de route +15 (60 po), jus d'étoile +30 (110 po, niveau 5) | (même plafond) |

Jamais au nombre de frappes : seul le temps compte, et un appel compte au plus une minute. Pilou **boudeur**
(soins négligés) : tout se recharge deux fois moins vite. Acheter de l'énergie ne rapporte jamais de po : un ⚡
de galette coûte 4 po, une expédition en rend moins de 0,4 par ⚡.

La jauge s'affiche dans le bandeau niveau / XP / po du menu, de la boutique et de l'info-bulle (« ⚡ 42/100 »),
dans la fenêtre des expéditions et sur l'Accueil du téléphone.

## La résolution

Au départ, Pilou tire une graine (`expedition|<appareil>|<identifiant>`, FNV-1a puis xorshift : la même partout,
d'une version de .NET à l'autre). Au retour, l'aventure se rejoue de cette graine : 3 à 6 événements selon le
lieu (combat 38 %, piège 22 %, coffre 22 %, rencontre 12 %, feu de camp 6 %), le dernier est un boss une fois
sur deux. Pilou part avec trois cœurs : un combat ou un piège raté en coûte un, un boss deux ; une rencontre ou
un feu de camp en rend un.

- **Victoire ★** (au moins deux cœurs, boss battu s'il y en avait un) : les po trouvées + une prime, l'XP du lieu,
  les éclats, parfois le butin exclusif, le trophée du boss la première fois.
- **À moitié ◐** (un seul cœur, ou boss perdu) : 60 % des po et de l'XP.
- **Défaite ✕** : rien que 1 à 3 xp de consolation ; Pilou rentre en grimaçant, un pansement sur la tête pendant
  20 min. C'est tout.
- **Rappel ↩** (clic sur la pancarte → Rappeler) : il fait demi-tour, les mains vides ; le départ reste compté.

Les chances d'un combat : 80 % − 7 points par force de la bête (+1 pour un boss) − 1,5 point par rang de risque,
+0,6 point par niveau d'avance (6 au plus) + l'équipement ; d'un piège : 75 % − 2,5 points par rang de risque.

### Équipement léger

Un **outil** et un **talisman** parmi les objets possédés (fenêtre des expéditions, ◀ ▶). Ils aident un peu,
jamais beaucoup (8 points au plus chacun) :

- outils : épée en bois (toujours là), épée en mousse (combat +5), baguette (combat +3, butin +2), lanterne
  (pièges +6), parapluie (pièges +4), canne à pêche dorée (butin +4), torche (combat +3, pièges +5) ;
- talismans : médaille (combat +3), auréole (pièges +4), collier de perles (butin +4), couronne de laurier
  (combat +2, pièges +2), bouclier-couvercle (combat +5), carte au trésor (butin +6).

### Butin exclusif

Introuvable en boutique (`Boutique.Trouver` le connaît, `Boutique.Acheter` le refuse) : torche, slime apprivoisé,
bouclier-couvercle, casque-passoire, carte au trésor. Il se porte comme un objet acheté (inventaire partagé dans
le groupe). Chance sur victoire : 1,5 à 4 % selon le lieu (un peu plus avec du butin en équipement), celui du lieu
d'abord, jamais en double. Les **éclats de cristal ◆** (10 à 18 % des coffres selon le lieu) se forgent par 25 en un butin
exclusif manquant (40 po quand tout est déjà là). **Trophées** : un par boss, la première fois qu'il est battu.

## Équilibre (simulation de 10 000 expéditions par lieu, niveau du lieu + 2, sans équipement)

| Lieu | Victoire | À moitié | Défaite | po moy. | xp moy. | butin rare* | exclusif | 3 par jour |
|---|---|---|---|---|---|---|---|---|
| Caverne des câbles | 80,0 % | 15,0 % | 5,0 % | 5,4 | 2,7 | 37,8 % | 1,34 % | 16 po, 8 xp |
| Forêt des onglets | 70,3 % | 20,3 % | 9,3 % | 7,7 | 3,3 | 34,3 % | 1,22 % | 23 po, 10 xp |
| Tour du tampon | 64,6 % | 22,7 % | 12,6 % | 9,1 | 5,0 | 31,2 % | 1,44 % | 27 po, 15 xp |
| Marais des mises à jour | 58,3 % | 23,5 % | 18,1 % | 11,5 | 5,4 | 31,1 % | 1,86 % | 35 po, 16 xp |
| Citadelle du nuage | 46,5 % | 25,2 % | 28,3 % | 12,6 | 6,3 | 28,5 % | 1,94 % | 38 po, 19 xp |

\* éclat, objet exclusif ou trophée (la quête « Rapporte N butins rares »). Avec les éclats forgés, le butin
exclusif tombe en tout autour de 2,5 à 3 % des expéditions.

Une journée type (≈ 120 ⚡ : 50 d'attente, 60 de travail, un plat) donne 16 à 27 po et 8 à 15 xp : de l'ordre
d'une ou deux parties de pêche (une prise ≈ 5 xp, et ≈ 9 po par prise via la quête « Pêche N prises »). Une
torche et un bouclier-couvercle font passer la Tour du tampon de 64,6 % à 72,4 % de victoires.
Chiffres recalculés par `dotnet test --filter Equilibre --logger "console;verbosity=detailed"`.

## Le groupe et le téléphone

- **Pas de double gain** : l'expédition appartient à l'appareil qui la lance. Ses po vont dans le compteur G de
  cet appareil (`Bourse.PoGagnes`), son XP dans son `Profil.Xp` ; le résultat est marqué « crédité » (un
  redémarrage ou une relecture ne paie jamais deux fois) ; les autres appareils ne voient que ce compteur, pris
  au maximum (relais) ou une fois par machine (dossier partagé). Les gains passent par le × 0,6 de la bouderie
  (× 1,2 s'il rayonne), comme tous les autres.
- **Téléphone** : le PC publie `expedition` dans son état (énergie, `en`/`repos`/`pret`, lieu, heure de retour,
  dernier journal, expéditions restantes) ; l'app l'affiche, sans rien lancer.

## Quêtes

Proposées après une première expédition : « Termine N expéditions » (jour, semaine, mois), « Bats N boss en
expédition » (semaine, mois), « Rapporte N butins rares d'expédition » (semaine, mois).

## Discrétion

L'expédition tourne en fond, heures calmes comprises. Les animations (départ, retour) suivent l'auto-masquage
en plein écran, présentation et visio. Au retour, aucune fenêtre ne s'ouvre : Pilou le dit dans sa bulle et un
petit coffre attend près de lui ; un clic dessus ouvre le journal.

## Essayer sans attendre

```
PilouBureau.exe --devant --essai=expedition:depart     (départ, puis pancarte)
PilouBureau.exe --devant --essai=expedition:absent     (la pancarte)
PilouBureau.exe --devant --essai=expedition:retour     (retour victorieux, boss battu)
PilouBureau.exe --devant --essai=expedition:defaite    (retour cabossé)
PilouBureau.exe --devant --essai=expedition:journal    (la fenêtre, journal ouvert)
```

Un état d'essai à part : rien n'est écrit ni crédité. Les quatre scènes principales sont dans la visite filmée
(`Tournage.EssaisConnus`).
