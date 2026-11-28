using System.Windows;
using System.Windows.Controls;
using System.Windows.Media;

namespace PilouBureau;

// Le menu clic droit « Sept portes » (plan et règles : PlanMenu.cs ; choix d'Antoine : docs/AUDIT-MENU.md).
// Reconstruit à chaque ouverture. Un premier niveau court, rangé par intention ; une zone « En ce moment » de deux
// lignes au plus, à place fixe ; les choix courts à plat sous un titre plutôt que dans un sous-menu de plus.
// Chaque porte porte un signe de forme dans la colonne d'icône ; les choix exclusifs ont un rond, les cases un carré.
public sealed partial class FenetrePilou
{
    private void Remplir(ContextMenu menu)
    {
        menu.Items.Clear();
        menu.Items.Add(BandeauBoutique());

        var moments = MomentsMaintenant();
        if (moments.Count > 0)
        {
            menu.Items.Add(Titre(PlanMenu.TitreMoment));
            foreach (var m in moments) menu.Items.Add(LigneMoment(m));
            menu.Items.Add(Titre(PlanMenu.TitreToujours));
        }

        menu.Items.Add(PorteSoin(moments.Contains(EnCeMoment.Soin)));
        menu.Items.Add(PorteAventure());
        menu.Items.Add(PorteExpedition());
        menu.Items.Add(PorteJouer());
        menu.Items.Add(Signe(Entree(PlanMenu.Journal.Titre, () => OuvrirJournal()), PlanMenu.Journal.Signe));
        menu.Items.Add(new Separator());
        menu.Items.Add(PorteApparence());
        menu.Items.Add(PorteSeMontre());
        menu.Items.Add(PorteSeCache());
        menu.Items.Add(PorteProgres());
        menu.Items.Add(PorteAmis());
        menu.Items.Add(PorteReglages());
        menu.Items.Add(new Separator());
        menu.Items.Add(Signe(Entree(PlanMenu.Cacher.Titre, () => _cacheJusque = Maintenant + 10 * 60_000), PlanMenu.Cacher.Signe));
        var quitter = Signe(Entree(PlanMenu.Quitter.Titre, () => Application.Current.Shutdown()), PlanMenu.Quitter.Signe);
        quitter.ToolTip = "Pilou revient à la prochaine session";
        menu.Items.Add(quitter);
    }

    // ---- Briques

    // Titre de section : petites capitales violettes suivies de pointillés ; ni survol ni clavier.
    private static MenuItem Titre(string texte)
    {
        var m = new MenuItem { Header = texte.ToUpperInvariant(), Focusable = false, IsHitTestVisible = false };
        m.SetResourceReference(StyleProperty, "MenuTitreStyle");
        return m;
    }

    // Ligne d'information grisée, non cliquable.
    private static MenuItem Info(string texte) => new() { Header = texte, IsEnabled = false };

    private static readonly FontFamily PoliceSignes = new("Segoe UI Symbol, Segoe UI Emoji, Consolas");

    // Le signe d'une porte, dans la colonne d'icône. sansSigne : préfixe à ôter d'un libellé qui le portait déjà.
    private static MenuItem Signe(MenuItem m, string signe, string? sansSigne = null)
    {
        if (sansSigne is not null && m.Header is string h && h.StartsWith(sansSigne, StringComparison.Ordinal))
            m.Header = h[sansSigne.Length..];
        m.Icon = new TextBlock
        {
            Text = signe,
            FontFamily = PoliceSignes,
            FontSize = 12.5,
            HorizontalAlignment = HorizontalAlignment.Center,
            VerticalAlignment = VerticalAlignment.Center,
        };
        return m;
    }

    // Un choix exclusif (rond) : dans un sous-menu (Choix) ou à plat sous un titre (ChoixAPlat).
    private static MenuItem Rond(MenuItem m)
    {
        m.Tag = "rond";
        return m;
    }

    private void ChoixAPlat<T>(ItemsControl parent, string titre, (string Nom, T Valeur)[] options, T actuel, Action<T> choisir)
    {
        parent.Items.Add(Titre(titre));
        foreach (var it in Choix(titre, options, actuel, choisir).Items.Cast<MenuItem>().ToList())
        {
            ((MenuItem)it.Parent).Items.Remove(it);
            parent.Items.Add(it);
        }
    }

    // ---- Bandeau : la seule porte vers la boutique

    private MenuItem BandeauBoutique()
    {
        var b = BandeauMenu();
        int neufs = NouveautesBoutique();
        b.ToolTip = neufs > 0 ? $"Ouvrir la boutique · {neufs} nouveauté{(neufs > 1 ? "s" : "")}" : "Ouvrir la boutique";
        // Le bandeau prend la colonne d'icône : seul le curseur ► reste à sa gauche, au survol.
        if (b.Header is FrameworkElement h) h.Margin = new Thickness(-23, 1, 0, 1);
        if (b.Header is FrameworkElement bandeau && neufs > 0)
        {
            // Les nouveautés, que montrait la ligne « Boutique (n nouveautés) », sous le bandeau.
            b.Header = null; // le bandeau change de parent : l'entrée le lâche d'abord
            bandeau.Margin = new Thickness(0);
            var pile = new StackPanel { Margin = new Thickness(-23, 1, 0, 1) };
            pile.Children.Add(bandeau);
            var ligne = new TextBlock
            {
                Text = $"✦ {neufs} nouveauté{(neufs > 1 ? "s" : "")} à la boutique",
                Margin = new Thickness(2, 3, 0, 0),
                FontSize = 11.5,
            };
            pile.Children.Add(ligne);
            b.Header = pile;
        }
        return b;
    }

    // ---- En ce moment

    private bool SoinUrgent()
    {
        var e = SoinsMaintenant();
        return !e.Vacances && (Soins.Boudeur(e) || Soins.Manques(e).Count > 0);
    }

    private IReadOnlyList<EnCeMoment> MomentsMaintenant()
    {
        bool soin = false;
        try { soin = SoinUrgent(); }
        catch (Exception x) when (x is not OutOfMemoryException) { }
        return PlanMenu.Moments(
            attend: _retour.Signe,
            expedition: Exp.Courante is not null,
            visite: _visites.Sortie is { Etape: Etape.Depart or Etape.Absent },
            soin: soin,
            jeu: _jeuEnCours != Jeu.Aucun);
    }

    private MenuItem LigneMoment(EnCeMoment quoi)
    {
        MenuItem m = quoi switch
        {
            EnCeMoment.Attend => Entree("Il t'attend : lui répondre…", OuvrirAventure),
            EnCeMoment.Expedition => Retitrer(MenuExpedition(), "En expédition · voir ou rappeler"),
            EnCeMoment.Visite => Entree($"Rappeler Pilou de chez {(_visites.Sortie is { } s ? MesAmis.Trouver(s.Ami)?.Nom : null) ?? "un ami"}", Rappeler),
            EnCeMoment.Soin => Entree($"{Majuscule(EtatSoinsCourt())} : prendre soin", PrendreSoin),
            _ => Entree("Arrêter le jeu", () => Arreter("")),
        };
        Signe(m, PlanMenu.Signe(quoi));
        m.Tag = "moment";
        return m;
    }

    private static MenuItem Retitrer(MenuItem m, string titre)
    {
        m.Header = titre;
        return m;
    }

    private static string Majuscule(string s) => s == "" ? s : char.ToUpperInvariant(s[0]) + s[1..];

    // ---- ⚔ Expédition : les lieux, l'équipement, l'en-cas, le journal (ou, en route : voir, rappeler)

    private MenuItem PorteExpedition()
    {
        var m = MenuExpedition();
        if (Exp.Courante is null) m.Header = $"{PlanMenu.Expedition.Titre} · ⚡ {Jauge.Affiche(Exp.Energie)}";
        return Signe(m, PlanMenu.Expedition.Signe, sansSigne: "⚔ ");
    }

    // ---- ♥ Prendre soin

    private string EtatSoinsCourt()
    {
        var e = SoinsMaintenant();
        return PlanMenu.EtatSoins(e.Vacances, Soins.Boudeur(e), Soins.Amadoue(e), Soins.Rayonnant(e), Soins.Manques(e).FirstOrDefault());
    }

    private MenuItem PorteSoin(bool dansLeMoment)
    {
        var e = SoinsMaintenant();
        var m = Signe(Entree(PlanMenu.TitreSoin(EtatSoinsCourt(), dansLeMoment), PrendreSoin), PlanMenu.Soin.Signe);
        m.ToolTip = Soins.Resume(e) + "\nUn clic : repas, toilette et câlin. Pour une caresse : un clic sur Pilou.";
        return m;
    }

    // ---- ✉ Aventure : la fenêtre, directement

    private MenuItem PorteAventure()
    {
        string etat = "";
        try { etat = EtatAventureCourt(); }
        catch (Exception x) when (x is not OutOfMemoryException) { }
        var titre = _retour.Signe ? "Aventure · ! il t'attend…" : etat == "" ? PlanMenu.Aventure.Titre : $"Aventure · {etat}…";
        var m = Signe(Entree(titre, OuvrirAventure), PlanMenu.Aventure.Signe);
        if (CampagneOccupe && _campEtat is { } c) m.ToolTip = Aventure.LigneBulle(c);
        return m;
    }

    // ---- ► Jouer : les jeux, les carnets, les réglages de Défense

    private MenuItem PorteJouer()
    {
        var m = Signe(new MenuItem { Header = PlanMenu.Jouer.Titre }, PlanMenu.Jouer.Signe);
        m.Items.Add(Entree("Petit jeu au hasard", () => Demarrer(JeuAuHasard(), Maintenant)));
        bool ouvert = Acces.JeuOuvert("defense", Niveau);
        m.Items.Add(Entree(ouvert ? "Défense du bureau" : $"Défense du bureau — niveau {Acces.NiveauJeu("defense")}", () => LancerDefense()));
        // Pêcher, Cuisiner, puis Carnet de pêche et Livre de recettes (Peche.cs).
        var peche = MenusPeche().ToList();
        m.Items.Add(peche[0]);
        m.Items.Add(peche[1]);
        m.Items.Add(Titre("Carnets"));
        foreach (var c in peche.Skip(2)) m.Items.Add(c);
        if (_profil.Defense.Meilleur > 0)
            m.Items.Add(Info($"Record de Défense : {_profil.Defense.Meilleur} (vague {_profil.Defense.MeilleureVague})"));
        m.Items.Add(new Separator());
        var defense = new MenuItem { Header = "Réglages de Défense" };
        ChoixAPlat(defense, "Largeur de la bande", new[] { ("Tout l'écran", 1.0), ("Deux tiers", 0.66), ("Moitié", 0.5) },
            _reglages.DefenseLargeur, v => _reglages.DefenseLargeur = v);
        defense.Items.Add(new Separator());
        defense.Items.Add(Case("Réduire les flashs", _reglages.DefenseFlashsReduits, v => _reglages.DefenseFlashsReduits = v));
        m.Items.Add(defense);
        return m;
    }

    // ---- ◐ Apparence

    private MenuItem PorteApparence()
    {
        var m = Signe(new MenuItem { Header = PlanMenu.Apparence.Titre }, PlanMenu.Apparence.Signe);
        var accessoires = new MenuItem { Header = "Accessoire" };
        foreach (var a in new[] { Accessoire.Saison, Accessoire.Aucun, Accessoire.Feuille, Accessoire.Noeud, Accessoire.Casque,
                     Accessoire.Bonnet, Accessoire.Lunettes, Accessoire.Couronne, Accessoire.ChapeauPeche, Accessoire.Toque,
                     Accessoire.Tablier, Accessoire.EtoileMer })
        {
            bool possede = a is Accessoire.Saison or Accessoire.Aucun || Possede(Recompenses.IdAccessoire(a));
            var item = Rond(new MenuItem
            {
                Header = possede ? Nom(a) : $"{Nom(a)} — boutique",
                IsCheckable = true,
                IsChecked = _reglages.Accessoire == a,
                IsEnabled = possede,
            });
            item.Click += (_, _) =>
            {
                _reglages.Accessoire = a;
                _reglages.Ecrire(_dossier);
            };
            accessoires.Items.Add(item);
        }
        m.Items.Add(accessoires);

        // Couleur : celles qu'on possède (boutique) ; le bleu de base est toujours là.
        var couleurs = new MenuItem { Header = "Couleur" };
        var porteeCouleur = EquipeCourant().GetValueOrDefault(PilouBureau.Boutique.Couleur, "");
        var bleu = Rond(new MenuItem { Header = "Bleu ciel", IsCheckable = true, IsChecked = porteeCouleur == "" });
        bleu.Click += (_, _) => Equiper(PilouBureau.Boutique.Couleur, "");
        couleurs.Items.Add(bleu);
        foreach (var a in PilouBureau.Boutique.Catalogue.Where(a => a.Slot == PilouBureau.Boutique.Couleur && Possede(a.Id)))
        {
            var c = Rond(new MenuItem { Header = a.Nom, IsCheckable = true, IsChecked = porteeCouleur == a.Id });
            c.Click += (_, _) => Equiper(PilouBureau.Boutique.Couleur, a.Id);
            couleurs.Items.Add(c);
        }
        couleurs.Items.Add(new Separator());
        couleurs.Items.Add(Entree("D'autres couleurs à la boutique…", () => OuvrirBoutique(PilouBureau.Boutique.Couleur)));
        m.Items.Add(couleurs);

        // Ce qu'il porte : un clic retire l'objet (parapluie compris), sans passer par la boutique.
        var portes = EquipeCourant()
            .Where(kv => kv.Value != "" && PilouBureau.Boutique.SurPilou(kv.Key) && kv.Key != PilouBureau.Boutique.Effet)
            .OrderBy(kv => kv.Key).ToList();
        if (portes.Count > 0)
        {
            var garde = new MenuItem { Header = $"Ce qu'il porte ({portes.Count})" };
            foreach (var (slot, id) in portes)
            {
                var nom = PilouBureau.Boutique.Trouver(id)?.Nom ?? id;
                garde.Items.Add(Entree($"✕ Retirer : {nom}", () => { Equiper(slot, ""); Dire($"{nom} rangé", 2500); }));
            }
            if (portes.Count > 1)
            {
                garde.Items.Add(new Separator());
                garde.Items.Add(Entree("✕ Tout retirer", () =>
                {
                    foreach (var (slot, _) in portes) Equiper(slot, "");
                    Dire("tout est rangé", 2500);
                }));
            }
            m.Items.Add(garde);
        }
        m.Items.Add(MenuForme());
        if (Possede(PilouBureau.Boutique.TraineeEtoiles))
            m.Items.Add(Case("Traînée d'étoiles", EquipeCourant().GetValueOrDefault(PilouBureau.Boutique.Effet) == PilouBureau.Boutique.TraineeEtoiles,
                v => Equiper(PilouBureau.Boutique.Effet, v ? PilouBureau.Boutique.TraineeEtoiles : "")));

        ChoixAPlat(m, "Taille", new[] { ("Petit", 0.75), ("Normal", 1.0), ("Grand", 1.3) }, _reglages.Taille,
            v => { _reglages.Taille = v; AppliquerTaille(); });
        var fin = Case("Dessin fin", _reglages.DessinFin, v =>
        {
            _reglages.DessinFin = v;
            if (_jeuEnCours != Jeu.Aucun) Arreter(""); // ce qui est posé autour de Pilou a été mesuré pour l'autre dessin
            AppliquerTaille();
        });
        fin.ToolTip = "Pilou dessiné deux fois plus fin, en pixels nets à toutes les mises à l'échelle. Décoché : le dessin d'origine.\n"
                      + MesuresDessin();
        m.Items.Add(fin);
        return m;
    }

    // Forme affichée : la plus grande atteinte, ou un stade déjà atteint.
    private MenuItem MenuForme()
    {
        var ev = _profil.Evolution;
        int atteint = Math.Max(1, ev.StadeAtteint);
        var m = new MenuItem { Header = "Forme affichée" };
        var auto = Rond(new MenuItem { Header = "La plus grande atteinte", IsCheckable = true, IsChecked = ev.StadeAffiche == 0 });
        auto.Click += (_, _) => ChoisirForme(0);
        m.Items.Add(auto);
        foreach (var s in Acces.Stades.Where(s => s.Stade <= atteint))
        {
            var f = Rond(new MenuItem { Header = s.Nom, IsCheckable = true, IsChecked = ev.StadeAffiche == s.Stade });
            f.Click += (_, _) => ChoisirForme(s.Stade);
            m.Items.Add(f);
        }
        return m;
    }

    // ---- ◎ Il se montre : bulle, paroles, mouvements, retour d'aventure, sons

    private MenuItem PorteSeMontre()
    {
        var m = Signe(new MenuItem { Header = PlanMenu.SeMontre.Titre }, PlanMenu.SeMontre.Signe);
        ChoixAPlat(m, "Bulle", new[] { ("Détaillée", ModeBulle.Detaillee), ("Compacte (détail au survol)", ModeBulle.Compacte), ("Seulement quand on t'attend", ModeBulle.Masquee) },
            _reglages.Bulle, v => _reglages.Bulle = v);
        AvecPresence(e => ChoixAPlat(m, "Il me parle", new[] { ("Peu (un mot par jour)", "peu"), ("Normalement (trois mots par jour au plus)", "normal"), ("Jamais", "jamais") },
            e.Parle, v =>
            {
                e.Parle = v;
                _presenceChange = true;
                EcrirePresence();
            }));
        m.Items.Add(Titre("Il bouge"));
        m.Items.Add(Case("Se promène", _reglages.Promenade, v => _reglages.Promenade = v));
        m.Items.Add(Case("Suit la souris du regard", _reglages.SuitSouris, v => _reglages.SuitSouris = v));
        m.Items.Add(Case("Petits jeux (de temps en temps)", _reglages.Jeux, v => _reglages.Jeux = v));
        AvecPresence(e => m.Items.Add(Case("Petits gestes de complicité (signe, clin d'œil, sieste tardive)", e.Gestes, v =>
        {
            e.Gestes = v;
            EcrirePresence();
        })));
        ChoixAPlat(m, "Retour d'aventure", new[] { ("Un petit saut et une bulle (une fois)", "bulle"), ("Seulement le signe « ! »", "signe") },
            _reglages.AnnonceAventure == "signe" ? "signe" : "bulle", v => _reglages.AnnonceAventure = v);
        var calme = _reglages.CalmeDebut == _reglages.CalmeFin ? "jamais" : $"{_reglages.CalmeDebut} h – {_reglages.CalmeFin} h";
        m.Items.Add(Info($"Heures calmes (réglage des amis) : {calme}"));
        m.Items.Add(Info("Plein écran, présentation, visio : l'annonce attend"));
        ChoixAPlat(m, "Sons", new[] { ("Aucun", "aucun"), ("Discrets", "discrets"), ("Normaux", "normaux") }, _reglages.Sons,
            v => { _reglages.Sons = v; Sons.Jouer(Son.Caresse); });
        // La musique de l'Aventure (docs/SONS.md) ; lue en direct, elle change sans redémarrer.
        ChoixAPlat(m, PlanMenu.TitreMusique, PlanMenu.ChoixMusique.ToArray(), _reglages.Musique, v => _reglages.Musique = v);
        return m;
    }

    // La présence (complicité, paroles, journal, prénom) peut manquer : une erreur ne casse pas le menu.
    private void AvecPresence(Action<EtatPresence> faire)
    {
        try { faire(Pres); }
        catch (Exception x) when (x is not OutOfMemoryException) { _presenceErreurs++; }
    }

    // ---- ◌ Il se cache

    private MenuItem PorteSeCache()
    {
        var m = Signe(new MenuItem { Header = PlanMenu.SeCache.Titre }, PlanMenu.SeCache.Signe);
        if (_discret)
            m.Items.Add(Info(_raisonDiscret switch
            {
                "presentation" => "En ce moment : caché (présentation)",
                "visio" => "En ce moment : caché (visio)",
                "reunion" => "En ce moment : caché (réunion à l'agenda)",
                _ => "En ce moment : caché (plein écran)",
            }));
        m.Items.Add(Case("En plein écran (jeu, vidéo)", _reglages.CacherPleinEcran, v => _reglages.CacherPleinEcran = v));
        m.Items.Add(Case("En présentation", _reglages.CacherPresentation, v => _reglages.CacherPresentation = v));
        m.Items.Add(Case("En visio (caméra ou micro)", _reglages.CacherVisio, v => _reglages.CacherVisio = v));
        m.Items.Add(new Separator());
        try
        {
            var e = SoinsMaintenant();
            var vacances = Case("Vacances (tout est figé)", e.Vacances, v => FaireSoin("vacances", v ? "1" : "0"));
            vacances.ToolTip = "Ni faim, ni bouderie, ni gains pendant les vacances";
            m.Items.Add(vacances);
        }
        catch (Exception x) when (x is not OutOfMemoryException) { }
        m.Items.Add(new Separator());
        m.Items.Add(Entree("Se cacher 10 min", () => _cacheJusque = Maintenant + 10 * 60_000));
        return m;
    }

    // ---- ★ Progrès

    private MenuItem PorteProgres()
    {
        var m = Signe(new MenuItem { Header = PlanMenu.Progres.Titre }, PlanMenu.Progres.Signe);
        m.Items.Add(MenuNiveaux());
        var evolution = MenuEvolution();
        if (_profil.Evolution.Variantes.Count > 0)
            evolution.Items.Add(Info("Variantes : " + string.Join(", ", _profil.Evolution.Variantes.OrderBy(kv => kv.Key)
                .Select(kv => $"{Acces.NomStade(kv.Key)} {Soins.NomVariante(kv.Value)}"))));
        m.Items.Add(evolution);
        m.Items.Add(MenuQuetes());
        var stats = StatsActuelles(_activite);
        m.Items.Add(MenuMetiers(stats));
        m.Items.Add(MenuSucces(stats));
        AvecPresence(e =>
        {
            var t = e.Totaux();
            int suivant = t.Palier + 1 < Presence.Seuils.Length ? Presence.Seuils[t.Palier + 1] : -1;
            m.Items.Add(new Separator());
            m.Items.Add(Info($"Complicité : {Presence.NomPalier(t.Palier)} · {t.Jours} jour{(t.Jours > 1 ? "s" : "")} ensemble"
                             + (suivant > 0 ? $" · {JaugeComplicite(t.Points, Presence.Seuils[t.Palier], suivant)}" : " · ★")));
        });
        return m;
    }

    private MenuItem MenuMetiers(Stats stats)
    {
        var m = new MenuItem { Header = "Métiers" };
        m.Items.Add(Info(_tenue != "" ? $"En ce moment : {Activites.Signe(_tenue)} {Activites.Nom(_tenue)}" : "En ce moment : rien de reconnu"));
        m.Items.Add(new Separator());
        foreach (var me in Metiers.Tous)
        {
            var sec = Metiers.Secondes(me, stats.Secondes); // heures de tout le groupe
            int n = Metiers.Niveau(me, sec);
            m.Items.Add(new MenuItem { Header = $"{me.Nom} — {Metiers.Grades[n]} · {Metiers.Progres(me, sec)}", IsEnabled = sec > 0 });
        }
        return m;
    }

    private MenuItem MenuSucces(Stats stats)
    {
        var m = new MenuItem { Header = $"Succès ({_profil.Succes.Count}/{Succes.Tous.Count})" };
        foreach (var d in Succes.Tous)
        {
            bool ok = _profil.Succes.Contains(d.Id);
            var progres = ok ? "" : Succes.Progres(d, stats);
            m.Items.Add(new MenuItem
            {
                Header = (ok ? "✓  " : "·  ") + $"{d.Nom} — {d.Description}" + (progres == "" ? "" : $" ({progres})"),
                IsEnabled = ok,
            });
        }
        return m;
    }

    // ---- ⇄ Amis et appareils

    private MenuItem PorteAmis()
    {
        var m = Signe(new MenuItem { Header = PlanMenu.Amis.Titre }, PlanMenu.Amis.Signe);
        m.Items.Add(Entree("Amis…", OuvrirAmis));
        var groupe = new MenuItem { Header = "Groupe d'appareils" };
        RemplirGroupe(groupe);
        if (Telephone.Valide(_reglages.Telephone))
            groupe.Items.Add(Info(_telEnvoi < 0 ? $"Dernier envoi au téléphone : aucun{(_telEtat == "" ? "" : $" · {_telEtat}")}"
                : $"Dernier envoi au téléphone : il y a {Statut.Duree(Epoque - _telEnvoi)} · {(_telEtat == "" ? "ok" : _telEtat)}"));
        m.Items.Add(groupe);
        m.Items.Add(MenuConnecteurs());
        m.Items.Add(MenuIntegrations());
        m.Items.Add(MenuNotifications());
        return m;
    }

    private MenuItem MenuNotifications()
    {
        var m = new MenuItem { Header = "Notifications Windows" };
        m.Items.Add(Case("Dans la bulle", _reglages.NotifsWindows, v =>
        {
            _reglages.NotifsWindows = v;
            AppliquerGestes();
        }));
        if (_reglages.NotifsWindows) m.Items.Add(Info("État : " + (_sourceNotifs?.Etat ?? "démarrage…")));
        m.Items.Add(Choix("Applis", new[] { ("Toutes", ModeApps.Toutes), ("Toutes sauf celles cochées", ModeApps.Sauf), ("Seulement celles cochées", ModeApps.Seulement) },
            _reglages.NotifsMode, v => _reglages.NotifsMode = v));
        var apps = _appsVues.Union(_reglages.NotifsApps, StringComparer.OrdinalIgnoreCase).OrderBy(a => a, StringComparer.OrdinalIgnoreCase).ToList();
        if (apps.Count == 0) m.Items.Add(Info("(les applis apparaîtront ici à leur première notification)"));
        foreach (var a in apps)
            m.Items.Add(Case(a, _reglages.NotifsApps.Contains(a, StringComparer.OrdinalIgnoreCase), v =>
            {
                _reglages.NotifsApps.RemoveAll(x => string.Equals(x, a, StringComparison.OrdinalIgnoreCase));
                if (v) _reglages.NotifsApps.Add(a);
            }));
        m.Items.Add(new Separator());
        m.Items.Add(Case("Masquer le contenu (seulement « 1 message de X »)", _reglages.NotifsMasquer, v => _reglages.NotifsMasquer = v));
        m.Items.Add(Entree("Paramètres Windows : Ne pas déranger…", () => Ouvrir("ms-settings:notifications")));
        m.Items.Add(Entree("Comment ça marche (et ce qui manque)…", () => Ouvrir("https://github.com/EveCrystali/Compagnon/blob/main/docs/NOTIFICATIONS.md")));
        return m;
    }

    // ---- ⚙ Réglages

    // Une page pour le joueur, rangée comme ce menu (docs/MODE-EMPLOI.md).
    private const string ModeEmploi = "https://github.com/EveCrystali/Compagnon/blob/main/docs/MODE-EMPLOI.md";

    private MenuItem PorteReglages()
    {
        var m = Signe(new MenuItem { Header = PlanMenu.Reglages.Titre }, PlanMenu.Reglages.Signe);
        AvecPresence(e =>
        {
            var prenom = e.Prenom;
            var nommer = Entree(prenom == "" ? "Lui dire comment je m'appelle…" : $"Mon prénom pour Pilou : {prenom} — changer…", DemanderPrenom);
            nommer.ToolTip = "Le prénom reste entre tes appareils (groupe chiffré), jamais chez tes amis";
            m.Items.Add(nommer);
            if (prenom != "")
                m.Items.Add(Entree("Oublier mon prénom", () => Quotidien(() =>
                {
                    e.ChoisirPrenom("", (long)Epoque);
                    _presenceUrgent = true;
                    EcrirePresence();
                    Dire("c'est oublié. tu restes « toi », c'est très bien", 4000);
                })));
            var journal = Case("Tenir son journal (rien de personnel)", e.JournalActif, v =>
            {
                e.JournalActif = v;
                EcrirePresence();
            });
            journal.ToolTip = "Les faits du jour, rien de personnel : ni fenêtre, ni fichier, ni message";
            m.Items.Add(journal);
        });
        m.Items.Add(new Separator());
        m.Items.Add(MenuActivitesObservees());
        var clavier = Case("Il tape avec moi au clavier", _reglages.GesteClavier, v =>
        {
            _reglages.GesteClavier = v;
            AppliquerGestes();
        });
        clavier.ToolTip = "Il compte les frappes, jamais lesquelles";
        m.Items.Add(clavier);
        m.Items.Add(Case("Appareil photo à chaque capture d'écran", _reglages.GestePhoto, v =>
        {
            _reglages.GestePhoto = v;
            AppliquerGestes();
        }));
        m.Items.Add(Choix("Thème de la bulle", new[] { ("Comme Windows", ThemeBulle.Auto), ("Clair", ThemeBulle.Clair), ("Sombre", ThemeBulle.Sombre) },
            _reglages.Theme, v => { _reglages.Theme = v; _themeLu = -1e9; }));
        m.Items.Add(new Separator());
        m.Items.Add(Case("Démarrer avec Windows", Demarrage.Actif(), Demarrage.Regler));
        m.Items.Add(Case("Icône près de l'horloge", _reglages.IconeNotification, v =>
        {
            _reglages.IconeNotification = v;
            if (_zoneNotif is not null) _zoneNotif.IconeVisible = v;
        }));
        var partage = Entree(string.IsNullOrWhiteSpace(_reglages.DossierPartage) ? "Partager l'XP par un dossier…" : "XP partagée par un dossier — changer…", ChoisirPartage);
        partage.ToolTip = string.IsNullOrWhiteSpace(_reglages.DossierPartage)
            ? "Un dossier commun à tes PC (OneDrive, partage réseau…). Pour un code entre appareils : Amis et appareils ▸ Groupe d'appareils."
            : $"Dossier : {_reglages.DossierPartage}";
        m.Items.Add(partage);
        m.Items.Add(new Separator());
        m.Items.Add(Entree("Mode d'emploi…", () => Ouvrir(ModeEmploi)));
        m.Items.Add(MenuVersion());
        m.Items.Add(Entree("Redémarrer Pilou", Redemarrer));
        return m;
    }

    private MenuItem MenuActivitesObservees()
    {
        var m = new MenuItem { Header = "Activités observées" };
        m.Items.Add(Case("Pilou regarde mes fenêtres (rien ne sort du PC)", _reglages.Activites, v =>
        {
            _reglages.Activites = v;
            if (!v) _tenue = "";
        }));
        m.Items.Add(new Separator());
        foreach (var a in Activites.Toutes)
            m.Items.Add(Case($"{Activites.Signe(a)}  {Activites.Nom(a)}", !_reglages.ActivitesCoupees.Contains(a), v =>
            {
                if (v) _reglages.ActivitesCoupees.Remove(a);
                else if (!_reglages.ActivitesCoupees.Contains(a)) _reglages.ActivitesCoupees.Add(a);
            }));
        m.Items.Add(new Separator());
        m.Items.Add(Entree("Ajouter mes logiciels… (activites.json)", OuvrirRegles));
        return m;
    }
}
