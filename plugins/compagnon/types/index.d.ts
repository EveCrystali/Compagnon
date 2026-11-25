// Ce que la créature exprime. Les humeurs « passagères » (grimace, fete, soulage, caresse)
// retombent seules au bout de quelques secondes, dans le module de dessin.
export type Humeur = 'repos' | 'concentre' | 'grimace' | 'fete' | 'soulage' | 'dort' | 'caresse'

declare module 'claude-code' {
  interface PluginState {
    compagnon: {
      // Local à la session : ce qui se passe ici.
      humeur: Shaped<Humeur>
      rev: Shaped<number>
      enTour: Shaped<boolean>
      outil: Shaped<string>
      outilRev: Shaped<number>
      inquiet: Shaped<boolean>
      ouvert: Shaped<boolean>
      // Statut de la session pour la bulle de Pilou de bureau.
      libelle: Shaped<string>
      titre: Shaped<string>
      debutTour: Shaped<number>
      finTour: Shaped<number>
      finRaison: Shaped<string>
      attente: Shaped<string>
      debutOutil: Shaped<number>
      // Recopie du magasin partagé ($.store), relue toutes les quelques secondes.
      nom: Shaped<string>
      xp: Shaped<number>
      energie: Shaped<number>
      souvenirs: Shaped<string[]>
    }
  }
}
