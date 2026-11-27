# PilouBureau

Overlay WPF de Pilou : il dessine le compagnon en pixel art sur le bas de l'écran, lit les états
de sessions dans `%USERPROFILE%\.claude\compagnon\etat-*.json` et porte les intégrations (Codex,
Discord, webhook). Comportements : `plugins/compagnon/README.md` § Pilou de bureau ; entrées et
format : `docs/BRANCHER.md`.

| Fichier | Rôle |
|---|---|
| `Program.cs` | point d'entrée : overlay, `--signal`, `--brancher` / `--debrancher` |
| `Etats.cs` | format d'état v3, choix de la session suivie |
| `Statut.cs` | lignes de la bulle |
| `Signal.cs` | événements d'autres logiciels → état |
| `Integrations.cs` | branchement Codex (`~/.codex/hooks.json`) |
| `Discord.cs` | statut Discord (Rich Presence), webhook |
| `FenetrePilou.cs`, `FenetreIntegrations.cs`, `Jeux.cs`, `Scene.cs`, `Pixels.cs` | fenêtre, dessin, jeux |
| `Placement.cs` | géométrie sans WPF (testée) : repères de la fenêtre, côté de la place, éléments posés à côté de Pilou en miroir exact, pêche (canne dans la main, fil du bout de la canne au bouchon), cuisine, bornage à l'écran courant (X négatif compris), sortie par le bord, bande de la Défense ; essais `--essai=peche:gauche\|droite` (aussi `mord:`, `prise:`, `cuisine:`, `tape:`, `etoile:`, `bulles:`) : Pilou collé à ce bord de son écran ; rendus de contrôle : `PILOU_PLANCHES_BORDS=<dossier> dotnet test --filter PlanchesBords` |
| `Campagnes.cs`, `FenetreCampagne.cs` | campagnes (`docs/CAMPAGNES.md`) : moteur sans WPF (rejeu du journal, tirages, fusion entre appareils, messages ; même comportement que `Campagnes.java`, vecteurs partagés régénérés par `PILOU_REGENERER=1 dotnet test`) ; carnet dans le profil, synchro par le relais, récompenses versées une fois ; pas encore d'interface : `--essai=campagne:prologue` déroule une campagne en accéléré dans la bulle |
| `Gestes.cs`, `Notifications.cs` | Pilou au clavier, appareil photo, filtre et file des notifications (sans WPF, testés) |
| `Crochets.cs`, `SourceNotifsWindows.cs`, `FenetreGestes.cs` | crochet clavier (compte seulement), presse-papiers et dossier Captures, lecteur de notifications, menu et bulle (`docs/NOTIFICATIONS.md`) |
| `Instance.cs`, `InstanceWindows.cs` | instance unique : relancer l'exe ramène Pilou (ou remplace un Pilou figé), `--redemarrer`, `--apres-maj` ; les essais (`--essai`, `--film`, `--instantane`) tournent à côté |
| `Tournage.cs`, `FenetreVisite.cs`, `DecorTournage.cs` | tournage (`outils/tourner-ecran-gauche.ps1`) : `--visite-guidee[=chronologie.json]` (mode démo en mémoire, dossier de démo obligatoire ; journal au fil de l'eau `chronologie.jsonl`, cadrages pour le montage, `erreurs.txt`), `--ecran=gauche\|droite\|principal`, `--placer=x,y`, `--sans-decor` (sans le faux bureau), `--essais-disponibles=<fichier>` ; une nouvelle scène `--essai=` s'ajoute aussi à `Tournage.EssaisConnus` |
| `ZoneNotification.cs`, `MenuNotification.cs`, `FenetreRelais.cs` | icône près de l'horloge (Shell_NotifyIcon, menu natif), fenêtre relais, « Redémarrer Pilou » |
| `Icone.cs`, `pilou.ico` | icône tirée du rendu de Pilou (16 à 48 px) ; régénérer : `PILOU_ICONE=ecrire dotnet test --filter Icone` |
| `identite/` | package d'identité optionnel (`-p:IdentitePackage=true`), non utilisé par défaut |
| `tests/` | tests xunit de la logique sans WPF |
