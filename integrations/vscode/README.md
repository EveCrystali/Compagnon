# Pilou — erreurs du fichier ouvert (VS Code)

Montre à [Pilou](https://github.com/EveCrystali/Compagnon), ton compagnon de bureau, combien d'erreurs et
d'avertissements a le fichier ouvert : « ⚠ 3 erreurs · 2 avert. · Program.cs », une petite grimace
quand ça empire, « ✓ propre ! » quand tu repasses à zéro. Il se tait le reste du temps.

- Envoie à `http://127.0.0.1:47821/diagnostics` (l'API locale de Pilou, rien d'autre) : le **nom** du
  fichier (jamais son chemin), les deux comptes et, seulement si `pilou.envoyerMessage` est coché, le
  premier message d'erreur sans ses chemins.
- Le jeton est lu dans `%USERPROFILE%\.claude\compagnon\reglages.json` ; sinon, colle-le dans
  `pilou.jeton` (Pilou → clic droit → Connecteurs… → Copier le jeton).
- Aucune dépendance à l'exécution, aucune télémétrie.

Installer, ce qui est envoyé, confidentialité : [docs/EDITEURS.md](https://github.com/EveCrystali/Compagnon/blob/main/docs/EDITEURS.md).

Licence : celle du dépôt Compagnon.
