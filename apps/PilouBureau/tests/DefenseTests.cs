using PilouBureau;
using Xunit;

// Défense du bureau : collisions, vagues, score, gains bornés, déterminisme, démo, et le dessin.
public class DefenseTests
{
    private const int W = 960, H = 216;

    private static PartieDefense Partie(ulong graine = 7)
    {
        var p = new PartieDefense(W, H, graine);
        p.Commencer();
        return p;
    }

    private static void Avancer(PartieDefense p, double secondes)
    {
        for (int i = 0; i < (int)Math.Round(secondes * 60); i++) p.Avancer(1 / 60.0);
    }

    // Une partie vide de bugs, sauf ceux qu'on pose (et pas de tirs des bugs : aucune formation).
    private static PartieDefense Vide()
    {
        var p = Partie();
        p.ViderVague();
        p.Tirs.Clear();
        p.VagueSansFin = true;
        return p;
    }

    [Fact]
    public void Disposition_de_la_bande()
    {
        var p = Partie();
        Assert.Equal(PhaseDefense.Jeu, p.Phase);
        Assert.Equal(1, p.Vague);
        Assert.Equal(PartieDefense.ViesDepart, p.Vies);
        Assert.Equal(p.Colonnes * p.Rangs(1), p.Vivants);
        Assert.InRange(p.Abris.Count, 3, 7);
        // Les abris sont sous la formation et au-dessus de Pilou ; la ligne du bureau est sous les abris.
        double basFormation = p.Bugs.Max(b => b.Y + b.Ht);
        Assert.All(p.Abris, a => Assert.True(a.Y > basFormation + 20));
        Assert.All(p.Abris, a => Assert.True(a.Y + a.Hauteur < p.LigneBureau));
        Assert.True(p.LigneBureau < p.HautJoueur);
        // Fenêtre puis post-it, sans se chevaucher, dans la bande.
        Assert.True(p.Abris[0].EstFenetre);
        Assert.False(p.Abris[1].EstFenetre);
        for (int i = 1; i < p.Abris.Count; i++) Assert.True(p.Abris[i].X > p.Abris[i - 1].X + p.Abris[i - 1].Largeur);
        Assert.True(p.Abris[^1].X + p.Abris[^1].Largeur < W);
    }

    [Fact]
    public void Une_etincelle_abat_un_bug_et_compte_ses_points()
    {
        var p = Vide();
        var bug = p.PoserBug(SorteBug.Scarabee, 100, 60);
        p.PoserTir(109, 80, ami: true);
        Avancer(p, 0.2);
        Assert.False(bug.Vivant);
        Assert.Equal(30, p.Score);
        Assert.Equal(1, p.BugsTues);
        Assert.Equal(1, p.Combo);
        Assert.Contains(EvenementDefense.Touche, p.Evenements());
    }

    [Fact]
    public void Le_blinde_tient_deux_coups()
    {
        var p = Vide();
        var bug = p.PoserBug(SorteBug.Blinde, 200, 60);
        p.PoserTir(209, 80, true);
        Avancer(p, 0.2);
        Assert.True(bug.Vivant);
        Assert.Equal(1, bug.Pv);
        Assert.Equal("defense-blinde-fele", DessinDefense.IdBug(bug));
        Assert.Contains(EvenementDefense.Fele, p.Evenements());
        p.PoserTir(bug.X + 9, 80, true); // la formation a bougé entre-temps
        Avancer(p, 0.2);
        Assert.False(bug.Vivant);
        Assert.Equal(5 + 40, p.Score);
    }

    [Fact]
    public void Le_diviseur_se_coupe_en_deux()
    {
        var p = Vide();
        var bug = p.PoserBug(SorteBug.Diviseur, 300, 60);
        p.PoserTir(309, 80, true);
        Avancer(p, 0.2);
        Assert.False(bug.Vivant);
        var minis = p.Bugs.Where(b => b.Vivant && b.Sorte == SorteBug.Mini).ToList();
        Assert.Equal(2, minis.Count);
        Assert.True(minis[0].Vx * minis[1].Vx < 0); // partent chacun de leur côté
        Assert.Equal(PhaseDefense.Jeu, p.Phase); // la vague n'est pas finie tant qu'ils vivent
    }

    [Fact]
    public void Un_tir_des_bugs_coute_une_vie_puis_Pilou_est_protege_un_moment()
    {
        var p = Vide();
        p.Placer(500);
        p.PoserTir(500, p.HautJoueur - 10, ami: false);
        Avancer(p, 0.4);
        Assert.Equal(PartieDefense.ViesDepart - 1, p.Vies);
        Assert.True(p.Invuln > 0);
        Assert.Contains(EvenementDefense.Blesse, p.Evenements());
        // Pendant l'invulnérabilité, un second tir ne coûte rien.
        p.PoserTir(500, p.HautJoueur - 10, false);
        Avancer(p, 0.4);
        Assert.Equal(PartieDefense.ViesDepart - 1, p.Vies);
    }

    [Fact]
    public void Le_bouclier_absorbe_un_coup()
    {
        var p = Vide();
        p.Placer(500);
        p.PoserBonus(494, p.HautJoueur - 2, SorteBonus.Bouclier);
        Avancer(p, 0.1);
        Assert.True(p.Bouclier > 0);
        p.PoserTir(500, p.HautJoueur - 10, false);
        Avancer(p, 0.4);
        Assert.Equal(PartieDefense.ViesDepart, p.Vies);
        Assert.Equal(0, p.Bouclier);
        Assert.Contains(EvenementDefense.BouclierUse, p.Evenements());
    }

    [Fact]
    public void Plus_de_vies_fin_de_partie()
    {
        var p = Vide();
        p.Placer(500);
        for (int i = 0; i < PartieDefense.ViesDepart; i++)
        {
            p.PoserTir(500, p.HautJoueur - 10, false);
            Avancer(p, 2);
        }
        Assert.Equal(0, p.Vies);
        Assert.Equal(PhaseDefense.Fin, p.Phase);
        Assert.Contains("vies", p.Fin);
    }

    [Fact]
    public void Les_abris_s_effritent_sous_les_tirs_des_bugs_mais_laissent_passer_Pilou()
    {
        var p = Vide();
        var a = p.Abris[0];
        int avant = a.Restant;
        double x = a.X + a.Largeur / 2;
        p.Placer(x);
        p.PoserTir(x, a.Y - 12, ami: false);
        Avancer(p, 0.3);
        Assert.True(a.Restant < avant);
        Assert.Equal(PartieDefense.ViesDepart, p.Vies);
        Assert.DoesNotContain(p.Tirs, t => !t.Ami);
        // L'étincelle de Pilou traverse son propre abri (fenêtre ou post-it).
        int reste = a.Restant;
        p.PoserTir(x, a.Y + a.Hauteur + 4, ami: true);
        Avancer(p, 0.16);
        Assert.Contains(p.Tirs, t => t.Ami && t.Y < a.Y);
        Assert.Equal(reste, a.Restant);
        // À force, une colonne de l'abri tombe.
        for (int i = 0; i < 40; i++)
        {
            p.PoserTir(x, a.Y - 12, false);
            Avancer(p, 0.1);
        }
        var (_, c) = a.CaseSous(x, a.Y);
        Assert.All(Enumerable.Range(0, a.Lignes), r => Assert.Equal(0, a.Pv[r, c]));
    }

    [Fact]
    public void La_formation_descend_aux_bords_puis_envahit_le_bureau()
    {
        var p = Partie();
        p.Immortel = true;
        double y0 = p.Bugs.Min(b => b.Y);
        double sens = p.SensFormation;
        Avancer(p, 30);
        Assert.True(p.Bugs.Where(b => b.Vivant).Min(b => b.Y) > y0);
        Assert.True(p.SensFormation != sens || p.Bugs.Min(b => b.Y) > y0 + 7);
        // Sans tirer, elle finit par toucher la ligne du bureau ; au passage, elle mange les abris.
        int abris = p.Abris.Sum(a => a.Restant);
        Avancer(p, 300);
        Assert.Equal(PhaseDefense.Fin, p.Phase);
        Assert.Contains("envahi", p.Fin);
        Assert.True(p.Abris.Sum(a => a.Restant) < abris);
    }

    [Fact]
    public void Vague_finie_bonus_puis_vague_suivante_et_boss_toutes_les_cinq()
    {
        var p = Vide();
        p.VagueSansFin = false;
        Avancer(p, 0.1);
        Assert.Equal(PhaseDefense.EntreVagues, p.Phase);
        Assert.Equal(1, p.VaguesFinies);
        Assert.Equal(50, p.Score);
        Avancer(p, PartieDefense.PauseVagues + 0.2);
        Assert.Equal(PhaseDefense.Jeu, p.Phase);
        Assert.Equal(2, p.Vague);
        p.SauterA(5);
        Assert.NotNull(p.Boss);
        Assert.True(PartieDefense.VagueDeBoss(5));
        Assert.False(PartieDefense.VagueDeBoss(4));
        Assert.Equal(0, p.Vivants);
        // Le boss tombe sous les étincelles (on tire en continu, sans risque).
        p.Immortel = true;
        p.Tirer = true;
        for (int i = 0; i < 60 * 120 && p.Boss is not null; i++)
        {
            p.Viser(p.Boss.X + BossDefense.L / 2);
            p.Avancer(1 / 60.0);
        }
        Assert.Null(p.Boss);
        Assert.Equal(1, p.BossVaincus);
        Assert.Contains(EvenementDefense.BossVaincu, p.Evenements());
    }

    [Fact]
    public void Les_vagues_se_corsent()
    {
        var p = Partie();
        int bugs1 = p.Vivants;
        double v1 = p.VitesseFormation();
        p.SauterA(4);
        Assert.True(p.Vivants >= bugs1);
        Assert.True(p.VitesseFormation() > v1);
        p.SauterA(8);
        Assert.Contains(p.Bugs, b => b.Sorte == SorteBug.Blinde);
        Assert.Contains(p.Bugs, b => b.Sorte == SorteBug.Diviseur);
        // Des moucherons rapides arrivent par le haut.
        p.Immortel = true;
        Avancer(p, 7);
        Assert.Contains(p.Bugs, b => b.Vivant && b.Sorte == SorteBug.Rapide);
    }

    [Fact]
    public void Cadence_limitee()
    {
        var p = Vide();
        p.Tirer = true;
        Avancer(p, 1.0);
        int tirs = p.Evenements().Count(e => e == EvenementDefense.Tir);
        Assert.InRange(tirs, 3, 4); // une étincelle toutes les 0,3 s, même en mitraillant
        // Un clic bref entre deux images tire quand même (une seule fois).
        p.Tirer = false;
        Avancer(p, 1.0);
        p.Evenements();
        p.Appuyer();
        Avancer(p, 0.5);
        Assert.Equal(1, p.Evenements().Count(e => e == EvenementDefense.Tir));
    }

    [Fact]
    public void Tir_double_et_ralenti()
    {
        var p = Vide();
        p.Placer(400);
        p.PoserBonus(394, p.HautJoueur - 2, SorteBonus.Double);
        Avancer(p, 0.05);
        Assert.True(p.Double > 0);
        p.Tirs.Clear();
        p.Appuyer();
        Avancer(p, 0.05);
        Assert.Equal(2, p.Tirs.Count(t => t.Ami));

        // Ralenti : la formation avance moins vite.
        var a = Partie(3);
        var b = Partie(3);
        b.Ralentir(PartieDefense.DureeRalenti);
        double ax = a.Bugs[0].X, bx = b.Bugs[0].X;
        Avancer(a, 1);
        Avancer(b, 1);
        Assert.True(Math.Abs(b.Bugs[0].X - bx) < Math.Abs(a.Bugs[0].X - ax) * 0.6);
    }

    [Fact]
    public void Combo_multiplie_les_points()
    {
        var p = Vide();
        for (int i = 0; i < 6; i++)
        {
            p.PoserBug(SorteBug.Ver, 40 + i * 40, 60);
            p.PoserTir(49 + i * 40, 80, true);
        }
        Avancer(p, 0.2);
        Assert.Equal(6, p.Combo);
        // Quatre vers à × 1, puis × 1,5 dès le cinquième d'affilée.
        Assert.Equal(4 * 10 + 2 * 15, p.Score);
        Assert.Equal(1.5, p.Multiplicateur);
        // Sans bug abattu pendant 2,5 s, le combo retombe.
        Avancer(p, PartieDefense.DureeCombo + 0.2);
        Assert.Equal(0, p.Combo);
        Assert.Equal(6, p.ComboMax);
    }

    [Fact]
    public void Pause_fige_tout_et_repart_d_ou_on_etait()
    {
        var p = Partie();
        Avancer(p, 1);
        p.Pause(true);
        var e = p.Empreinte();
        Assert.Equal(PhaseDefense.Pause, p.Phase);
        Avancer(p, 5);
        Assert.Equal(e, p.Empreinte());
        p.Pause(false);
        Assert.Equal(PhaseDefense.Jeu, p.Phase);
        p.Abandonner();
        Assert.Equal(PhaseDefense.Fin, p.Phase);
    }

    private static string Jouer(ulong graine, double secondes, int images = 60)
    {
        var p = new PartieDefense(W, H, graine);
        var pilote = new PiloteDemo(graine);
        p.Commencer();
        for (int i = 0; i < (int)(secondes * images); i++)
        {
            pilote.Jouer(p, 1.0 / images);
            p.Avancer(1.0 / images);
        }
        return p.Empreinte() + "|" + p.Score;
    }

    [Fact]
    public void Meme_graine_meme_partie()
    {
        Assert.Equal(Jouer(42, 40), Jouer(42, 40));
        Assert.NotEqual(Jouer(42, 40), Jouer(43, 40));
        // Le temps avance par pas fixes : 60 ou 120 images par seconde donnent la même partie... sans pilote.
        var a = Partie(9);
        var b = Partie(9);
        a.Tirer = b.Tirer = true;
        for (int i = 0; i < 600; i++) a.Avancer(1 / 60.0);
        for (int i = 0; i < 1200; i++) b.Avancer(1 / 120.0);
        Assert.Equal(a.Empreinte(), b.Empreinte());
    }

    [Fact]
    public void La_demo_joue_vraiment()
    {
        var p = new PartieDefense(W, H, 5);
        var pilote = new PiloteDemo(5);
        p.Commencer();
        for (int i = 0; i < 90 * 60 && p.VaguesFinies == 0 && p.Phase != PhaseDefense.Fin; i++)
        {
            pilote.Jouer(p, 1 / 60.0);
            p.Avancer(1 / 60.0);
        }
        Assert.True(p.Score > 300);
        Assert.True(p.VaguesFinies >= 1 || p.Phase == PhaseDefense.Fin);
    }

    // ---- Gains

    [Fact]
    public void Gains_d_une_partie_comme_les_autres_jeux()
    {
        Assert.Equal(0, GainsDefense.Xp(0, 0));
        Assert.Equal(1, GainsDefense.Xp(40, 0));
        Assert.Equal(3000 / 150 + 2 * 3, GainsDefense.Xp(3000, 3));
        Assert.Equal(PartieDefense.XpMax, GainsDefense.Xp(1_000_000, 40));
        Assert.Equal(0, GainsDefense.Po(0, 0));
        Assert.Equal(3000 / 600 + 3 / 2, GainsDefense.Po(3000, 3));
        Assert.Equal(GainsDefense.PoPartieMax, GainsDefense.Po(1_000_000, 40));
        // Du même ordre que Chasse aux bugs (30 xp) et une quête du jour (20 à 40 po).
        Assert.True(PartieDefense.XpMax <= 30);
        Assert.True(GainsDefense.PoJourMax <= 40);
    }

    [Fact]
    public void Plafond_quotidien_puis_remise_a_zero_le_lendemain()
    {
        var e = new EtatDefense();
        var jour = new DateTime(2026, 11, 26, 14, 0, 0);
        int xp = 0, po = 0;
        ResultatDefense r = null!;
        for (int i = 0; i < 10; i++)
        {
            r = GainsDefense.Crediter(e, jour, 20_000, 8, 9, 1);
            xp += r.Xp;
            po += r.Po;
        }
        Assert.Equal(GainsDefense.XpJourMax, xp);
        Assert.Equal(GainsDefense.PoJourMax, po);
        Assert.True(r.Plafond);
        Assert.Equal(0, r.Xp);
        Assert.Equal(10, e.Parties);
        Assert.Equal(10, e.Boss);
        var demain = GainsDefense.Crediter(e, jour.AddDays(1), 3000, 3, 4, 0);
        Assert.Equal(GainsDefense.Xp(3000, 3), demain.Xp);
        Assert.False(demain.Plafond);
    }

    [Fact]
    public void Record_et_plus_haute_vague()
    {
        var e = new EtatDefense();
        var t = new DateTime(2026, 11, 26);
        Assert.True(GainsDefense.Crediter(e, t, 1000, 1, 2, 0).Record);
        Assert.False(GainsDefense.Crediter(e, t, 800, 1, 2, 0).Record);
        Assert.True(GainsDefense.Crediter(e, t, 5000, 9, 10, 1).Record);
        Assert.False(GainsDefense.Crediter(e, t, 0, 0, 1, 0).Record);
        Assert.Equal(5000, e.Meilleur);
        Assert.Equal(10, e.MeilleureVague);
    }

    [Fact]
    public void Succes_de_la_defense()
    {
        Stats S(EtatDefense d) => new(new Dictionary<string, long>(), 0, 0, 0, new DateTime(2026, 11, 26, 14, 0, 0), "", Defense: d);
        Assert.DoesNotContain(Succes.Nouveaux(S(new EtatDefense()), Array.Empty<string>()), d => d.Id is "rempart" or "pare-feu" or "gardien");
        var ids = Succes.Nouveaux(S(new EtatDefense { MeilleureVague = 10, Boss = 1, Meilleur = 12_000 }), Array.Empty<string>()).Select(d => d.Id).ToList();
        Assert.Contains("rempart", ids);
        Assert.Contains("pare-feu", ids);
        Assert.Contains("gardien", ids);
        var rempart = Succes.Tous.First(d => d.Id == "rempart");
        Assert.Equal("vague 7 / 10", Succes.Progres(rempart, S(new EtatDefense { MeilleureVague = 7 })));
    }

    [Fact]
    public void Ouvert_au_niveau_des_jeux_de_tir()
    {
        Assert.Equal(Acces.NiveauJeu("chasse"), Acces.NiveauJeu("defense"));
        Assert.False(Acces.JeuOuvert("defense", 4));
        Assert.True(Acces.JeuOuvert("defense", 5));
    }

    // ---- Dessin

    private static readonly Lazy<Banque> B = new(() => Banque.DepuisDossier(Path.Combine(Racine(), "assets")));

    public static string Racine()
    {
        var d = new DirectoryInfo(AppContext.BaseDirectory);
        while (d is not null && !File.Exists(Path.Combine(d.FullName, "assets", "index.txt"))) d = d.Parent;
        return d!.FullName;
    }

    [Fact]
    public void Sprites_de_la_defense_dans_la_banque()
    {
        foreach (var id in new[] { "bug-scarabee", "bug-araignee", "bug-ver", "bug-prod", "defense-blinde", "defense-blinde-fele",
                     "defense-diviseur", "defense-mini", "defense-rapide", "defense-tir", "defense-etincelle", "defense-bonus-double",
                     "defense-bonus-bouclier", "defense-bonus-ralenti", "vie" })
            Assert.True(B.Value[id] is not null, id);
        foreach (var s in Enum.GetValues<SorteBug>())
        {
            var bug = new BugDefense { Sorte = s };
            var sp = B.Value[DessinDefense.IdBug(bug)]!;
            Assert.Equal((int)bug.L, sp.W);
            Assert.Equal((int)bug.Ht, sp.H);
        }
        Assert.Equal(36, B.Value["bug-prod"]!.W); // dessiné × 2 : 72 × 44, la taille du boss
    }

    [Fact]
    public void Textes_tous_dessinables()
    {
        foreach (var texte in new[] { "DÉFENSE", "DU BUREAU", "SOURIS OU FLÈCHES / Q D : BOUGER", "ÉCHAP, CLIC DROIT OU X : QUITTER",
                     "FLASHS RÉDUITS : OUI (F)", "PARTIE TERMINÉE", "! UNE IA T'ATTEND", "PLAFOND DU JOUR ATTEINT : REVIENS DEMAIN",
                     "LES BUGS ONT ENVAHI LE BUREAU !", "VAGUE 5 : BUG DE PROD", "COMBO 12 X1.5", "+12 XP    +4 PO" })
            Assert.All(texte.Where(c => c != '(' && c != ')'), c => Assert.True(Police.Connu(c), $"« {c} » dans {texte}"));
    }

    [Fact]
    public void Zones_cliquables_dans_la_bande()
    {
        var f = DessinDefense.Fermer(W);
        Assert.True(f.X + f.Largeur <= W && f.Y + f.Hauteur <= PartieDefense.Hud);
        var r = DessinDefense.Rejouer(W, H);
        var q = DessinDefense.Quitter(W, H);
        Assert.True(r.X + r.Largeur < q.X);
        Assert.True(q.Y + q.Hauteur < H);
        Assert.True(DessinDefense.Flashs(W, H).Y + 9 < H);
    }

    public static (uint[] Px, Geometrie Geo) Pilou(PartieDefense p, double t, ResultatDefense? r = null)
    {
        var a = DessinDefense.AllurePilou(new Allure(), p, t, r);
        var px = RenduPilou.Rendre(a, B.Value, out var geo);
        return (px, geo);
    }

    public static ToileDefense Rendre(PartieDefense p, double t, VueDefense? v = null)
    {
        var o = new ToileDefense(p.W, p.H);
        var (px, geo) = Pilou(p, t, v?.Resultat);
        DessinDefense.Dessiner(o, p, B.Value, px, geo, t, v ?? new VueDefense());
        return o;
    }

    [Fact]
    public void Dessin_sans_rouge_ni_vert_a_chaque_phase()
    {
        var p = new PartieDefense(W, H, 11);
        var images = new List<ToileDefense> { Rendre(p, 0) };
        p.Commencer();
        p.SauterA(8);
        p.PoserBonus(300, 120, SorteBonus.Ralenti);
        p.PoserTir(400, 120, false);
        p.PoserTir(410, 120, true);
        images.Add(Rendre(p, 1000, new VueDefense { IaAttend = true, Alerte = 1 }));
        p.SauterA(5);
        images.Add(Rendre(p, 2000));
        p.Abandonner();
        images.Add(Rendre(p, 3000, new VueDefense { Resultat = new ResultatDefense(12, 4, true, true) }));
        foreach (var o in images)
        {
            Assert.Contains(o.Px, c => c >> 24 == 255);
            foreach (var c in o.Px.Distinct())
            {
                int r = (int)(c >> 16 & 255), g = (int)(c >> 8 & 255), b = (int)(c & 255);
                if (c >> 24 < 40) continue;
                Assert.False(g > r * 1.25 + 10 && g > b * 1.25 + 10, $"vert : {c:x8}");
                Assert.False(r > g * 2 + 10 && r > b * 2 + 10, $"rouge : {c:x8}");
            }
        }
    }

    [Fact]
    public void Flashs_reduits_rien_ne_clignote()
    {
        var p = Partie(4);
        p.Placer(500);
        p.PoserTir(500, p.HautJoueur - 10, false);
        Avancer(p, 0.3);
        Assert.True(p.Invuln > 0);
        var v = new VueDefense { FlashsReduits = true, Alerte = 1, Flash = 1 };
        // Deux instants d'une même scène : Pilou clignote normalement ; flashs réduits, il pâlit sans clignoter.
        int Ecart(VueDefense vue)
        {
            var ia = Rendre(p, 1000, vue).Px;
            var ib = Rendre(p, 1090, vue).Px;
            int n = 0, x0 = (int)p.JoueurX - 24, y0 = (int)p.Sol - 56;
            for (int y = Math.Max(0, y0); y < H; y++)
            for (int x = x0; x < x0 + 48; x++)
                if (ia[y * W + x] != ib[y * W + x]) n++;
            return n;
        }
        int normal = Ecart(new VueDefense()), reduit = Ecart(new VueDefense { FlashsReduits = true });
        Assert.True(normal > 200, normal.ToString());
        Assert.True(reduit < normal / 3, $"{reduit} / {normal}");
        var a = Rendre(p, 1000, v);
        // Ni voile clair ni cadre orange.
        Assert.Equal(Rendre(p, 1000, new VueDefense { FlashsReduits = true }).Px, a.Px);
    }
}
