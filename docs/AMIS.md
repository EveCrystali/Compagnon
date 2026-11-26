# Amis et visites

Pilou peut avoir des amis : d'autres Pilou, sur les PC d'autres personnes. Quand il s'ennuie, il prend
son baluchon, salue, sort par le bord de l'écran et va passer cinq à dix minutes chez l'un d'eux. Chez
toi, une pancarte le remplace ; chez l'ami, il entre par le bord, frappe, salue, raconte sa vie, joue,
puis rentre avec un petit cadeau. Un clic sur la pancarte le rappelle.

Code : `apps/PilouBureau/Amis.cs` (logique pure, testée par `tests/AmisTests.cs`),
`FenetreAmis.cs` (relais, animation, fenêtre « Amis de Pilou »), `FenetreInvite.cs` (l'invité),
sprites dans `outils/sprites/visites_sprites.py`. Téléphone : `android/.../Amis.java` (mêmes
dérivations) et la carte « Amis de Pilou » de l'Accueil (lecture seule).

## Se faire des amis

Clic droit sur Pilou → **Amis…**. La fenêtre montre ton **code ami** (`PILOU-7F3K-9QXA-M2HT`, avec
son QR code) : tu le donnes à ton ami, il le tape dans *Ajouter un ami*, tu fais de même avec le sien.

- L'amitié devient active quand **chacun a ajouté l'autre**, ou quand l'un **accepte** la demande de
  l'autre (*Demandes reçues*).
- Ce code est **distinct du code de groupe** (16 signes, qui relie tes propres appareils) : un ami ne
  voit jamais tes sessions ni ton XP de groupe.
- La liste montre, pour chaque ami : le nom de son Pilou (ou le **surnom** que tu lui donnes, ici
  seulement), son niveau, son stade, s'il est **en ligne** (● bleu) ou **vu il y a…** (○ gris),
  « en attente » (◌ orange) tant qu'il ne t'a pas ajouté, et des cœurs ♥ d'amitié (visites et
  caresses partagées). *Aller voir*, *Renommer*, *Retirer*.
- 30 amis au plus.

## Une visite

```
chez toi                                     chez l'ami
──────────────────────────────────────────   ──────────────────────────────────────────
1. il s'ennuie, ou « Aller voir Léo »
2. baluchon, salut, « je vais voir Léo ! »
   il court jusqu'au bord de l'écran   ──visite──▶  3. il entre par le bord, avec SES couleurs,
4. pancarte « chez Léo · ↩ 14 h 20 »   ◀─accueil──     son stade, sa variante, ses objets ;
   (les statuts des sessions restent              toc toc, il salue
   dans la bulle ; clic = rappeler)               4. il raconte (anecdotes), Pilou répond ;
                                                     tape m'en cinq, ballon, danse, course ;
                                       ◀─caresse──   un clic sur lui = une caresse (cœurs,
                                                     +2 xp chacun, 5 fois par jour)
5. au bout de 5 à 10 min (tiré au hasard),
   ou au rappel                        ──fin/rappel─▶ 5. « au revoir ! », il ressort par le bord
6. il revient par le bord, valise à la main :
   « je suis rentré ! » + 8 à 15 po et 5 xp
   (deux cadeaux par jour au plus) ;
   quête « Rends visite à un ami »
```

- **Spontanée** : rien ne tourne (aucune IA au travail ni en attente), pas de jeu, personne au clavier
  depuis une minute ; une chance sur quinze par minute ; **deux fois par jour au plus** ; seulement chez
  un ami **en ligne** qui **accepte les visites** et qui est **libre** (chez lui, sans invité, pas en
  plein écran).
- **Manuelle** : *Aller voir* dans la fenêtre Amis (ami en ligne, qui accepte, libre).
- **Rappel** : clic sur la pancarte, ou clic droit → *Rappeler Pilou*. Il rentre tout de suite ; chez
  l'ami, l'invité dit « oh, on m'appelle à la maison ! » et s'en va.
- **Refus** : visites coupées, heures calmes, plein écran / présentation / visio, ami lui-même parti,
  invité déjà là (**un seul à la fois**) : Pilou fait demi-tour et dit pourquoi.
- **Ami déconnecté** : chacun envoie un « ici » toutes les 90 s pendant la visite. Sans réponse à sa
  visite après 2 min 30, ou sans nouvelles pendant 5 min, Pilou rentre seul ; l'invité quitte aussi
  l'écran de l'hôte de son côté.
- **Discrétion** : pas de départ en plein écran, présentation ou visio ; si l'hôte y passe pendant la
  visite, l'invité s'en va poliment (« tu as l'air occupé, je repasserai ! »).
- Une visite n'est pas gardée d'un lancement à l'autre : si le PC redémarre, Pilou est rentré.

## Réglages (fenêtre Amis, section Visites)

| Réglage | Par défaut | Effet |
|---|---|---|
| Accepter les visites | oui | sinon, les visites sont refusées (« ne reçoit pas ») |
| Mon Pilou peut partir en visite | oui | départs spontanés ; *Aller voir* reste possible |
| Partager mes anecdotes | oui | sinon, l'invité ne raconte que son niveau |
| Heures calmes | 22 h – 8 h | aucune visite, ni rendue ni reçue (21–9, 20–8, ou jamais) |

## Ce qui est partagé, et rien d'autre

Avec chaque ami, et seulement lui :

- le **nom** de Pilou, son **niveau**, son **stade** et sa **variante**, sa **couleur**, les **objets
  portés** (un identifiant par emplacement) et son **accessoire** ;
- s'il **accepte** les visites et s'il est **libre** (présence, toutes les 10 min et à chaque
  changement) ;
- si *Partager mes anecdotes* est coché : sa **plus belle prise** (nom du poisson), son **dernier plat
  découvert**, sa **dernière quête réussie** (le texte de la quête), son **dernier succès** (le nom),
  l'**état du ciel** chez lui (pluie, neige… jamais la ville) et son **stade** s'il a évolué en Nimbus ou
  Astral ;
- les messages de la visite elle-même (visite, accueil, refus, ici, rappel, fin, caresse).

**Jamais** : titres de fenêtres, sessions Claude/Codex, outils, connecteurs, contenu des annonces,
ville, nom du PC, XP de groupe. Les anecdotes sont fabriquées à partir de la liste ci-dessus
(`Amis.FaitsDe`), et le test `AnecdotesSansDonneePrivee` vérifie que rien d'autre ne sort. À la
réception, tout est borné et nettoyé (`Amis.Borner`) : nom ≤ 24 signes, emplacements connus,
identifiants `a-z0-9-`, niveau ≤ 999, stade 1–4.

## Transport et sécurité

Le relais est **ntfy** (celui du téléphone et du groupe, `ntfy.sh` par défaut). Il ne voit que des
textes chiffrés et des noms de sujets aléatoires.

- **Identité** : chaque PC tire une paire de clés **ECDH P-256**. Le code ami est l'**empreinte** de
  la clé publique (SHA-256 → 12 signes de l'alphabet sans 0/O/1/I/L, ≈ 59 bits). La clé privée reste
  dans un coffre DPAPI (`amis/secrets.bin`, lisible seulement par ce compte Windows) ; `amis.json`
  garde la liste, jamais la clé privée.
- **Pourquoi P-256 et pas X25519** : .NET n'offre pas X25519 sans dépendance, alors que P-256 est
  dans .NET (`ECDiffieHellman`) et dans Java (`KeyAgreement "ECDH"`) sans rien ajouter. Un code court
  ne peut pas porter une clé publique (91 octets) : il en porte l'empreinte, ce qui suffit à la
  vérifier.
- **Demande d'ami** : déposée dans la **boîte** du code de l'ami — sujet
  `pilou-` + HMAC-SHA256(code, `pilou-ami-boite-v1`)[:24 hex], chiffrée en AES-256-GCM avec la clé
  HMAC-SHA256(code, `pilou-ami-cle-v1`). Elle porte le code et la clé publique de l'expéditeur ; une
  clé qui ne redonne pas le code annoncé est ignorée (on ne peut pas se faire passer pour quelqu'un
  sans sa clé privée).
- **Paire** : les deux amis calculent le même secret ECDH ; le sujet de la paire est
  `pilou-` + HMAC-SHA256(secret, `pilou-paire-sujet-v1|A|B`)[:24 hex] et sa clé
  HMAC-SHA256(secret, `pilou-paire-cle-v1|A|B`), A et B les deux codes rangés dans l'ordre. Quelqu'un
  qui connaîtrait les deux codes ne lit pas leurs échanges.
- **Format** : base64(nonce 12 octets ‖ chiffré ‖ étiquette 16 octets), comme le téléphone.
- **Lecture** : une seule requête pour la boîte et toutes les paires, toutes les minutes (toutes les
  15 s pendant une visite ou juste après une demande) ; identifiants déjà lus mémorisés ; un message
  de plus de 10 min relu au démarrage ne relance pas une visite.
- **Vecteur commun PC / téléphone** : `AmisTests.VecteurCommunAvecLeTelephone` et
  `AmisTest.memesDerivationsQueLePc` (sujet de boîte, clé de boîte, sujet et clé de paire pour un
  secret fixe, empreinte). Le téléphone ne reçoit pas encore de visite : il affiche ce que le PC lui
  en dit (liste d'amis, « parti chez Léo · retour vers 14 h 20 »).

## Essais

`PilouBureau.exe --devant --essai=visite:depart` (puis `arrivee`, `jeu`, `retour`) : une visite chez
un ami fictif « Léo » (Nimbus ambre, chapeau de pirate), sans réseau et sans rien créditer.

## Sprites

`baluchon` (main, se balance), `valise` (main, au retour), `pancarte` (objet seul, le texte est écrit
par-dessus), `coeurs-amitie` (effet au-dessus de la tête ; cœurs orange et bleus, jamais rouges).
Planche : `outils/sprites/visites_sprites.py`, régénérée avec `python3 outils/sprites/generer.py`.
