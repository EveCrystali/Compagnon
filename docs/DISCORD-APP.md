# Fiche de l'application Discord « Pilou »

Textes prêts à coller dans le [Developer Portal](https://discord.com/developers/applications) de
l'application Discord « Pilou » (celle du statut Discord, identifiant `1575620409070592051` dans
`apps/PilouBureau/Reglages.cs`). Même message partout : Pilou est d'abord un petit compagnon de bureau ;
relayer des infos n'est qu'un bonus.

## General Information → Description (≤ 400 caractères)

```
Pilou est un petit compagnon de bureau qui vit en bas de ton écran. Il mène sa petite vie sans te déranger : il joue, mange, pêche, cuisine et grandit pendant que tu travailles. Hauts faits, mini-jeux, quêtes, expéditions, boutique pour le personnaliser, visites chez tes amis : tout est optionnel. Et au passage, branché à tes applis, il te prévient quand une IA t'attend. Windows et Android.
```

## Tags (5 au plus)

```
compagnon
pixel art
mini-jeux
productivité
IA
```

## Statut (Rich Presence)

L'infobulle de la grande image (`large_text`, ≤ 128 caractères) est fixée dans
`apps/PilouBureau/Discord.cs` : « Pilou, petit compagnon qui vit en bas de l'écran ». L'image `pilou`
est à téléverser dans *Rich Presence → Art Assets* sous ce nom.
