using PilouBureau;
using Xunit;

// Tournage d'une vidéo sur un vrai écran (outils/tourner-ecran-gauche.ps1) : écran choisi, options, mode démo.
public class TournageTests
{
    [Fact]
    public void LEcranLePlusAGaucheEstCeluiAuPlusPetitX()
    {
        var ecrans = new[]
        {
            new CadreEcran(0, 0, 2560, 1440),          // principal
            new CadreEcran(-1920, 180, 1920, 1080),    // à gauche, plus bas
            new CadreEcran(2560, 0, 1920, 1080),       // à droite
        };
        Assert.Equal(1, Tournage.PlusAGauche(ecrans));
        Assert.Equal(2, Tournage.PlusADroite(ecrans));
        Assert.Equal(0, Tournage.Choisir("principal", ecrans));
        Assert.Equal(1, Tournage.Choisir("gauche", ecrans));
    }

    [Fact]
    public void AEgaliteLePlusHautGagneEtAucunEcranDonneMoinsUn()
    {
        var empiles = new[] { new CadreEcran(-1920, 1080, 1920, 1080), new CadreEcran(-1920, 0, 1920, 1080), new CadreEcran(0, 0, 1920, 1080) };
        Assert.Equal(1, Tournage.PlusAGauche(empiles));
        Assert.Equal(-1, Tournage.PlusAGauche(Array.Empty<CadreEcran>()));
        // Un seul écran : c'est lui, quel que soit le choix.
        var seul = new[] { new CadreEcran(0, 0, 3840, 2160) };
        Assert.Equal(0, Tournage.Choisir("gauche", seul));
        Assert.Equal(0, Tournage.Choisir("droite", seul));
    }

    [Fact]
    public void LesOptionsDeTournageSontLuesEtRetirees()
    {
        var (o, reste) = OptionsTournage.Analyser(new[]
            { "--visite-guidee=C:\\Temp\\chrono.json", "--ecran=Gauche", "--devant", @"C:\Temp\demo" });
        Assert.True(o.Visite);
        Assert.Equal("C:\\Temp\\chrono.json", o.Chronologie);
        Assert.Equal("gauche", o.Ecran);
        Assert.Null(o.Placer);
        Assert.Equal(new[] { "--devant", @"C:\Temp\demo" }, reste);

        var (p, r2) = OptionsTournage.Analyser(new[] { "--placer=-1700, 900", "--visite-guidee" });
        Assert.Equal((-1700, 900), p.Placer);
        Assert.True(p.Visite);
        Assert.Null(p.Chronologie);
        Assert.Empty(r2);
    }

    [Fact]
    public void UneValeurInvalideEstIgnoreeMaisRetiree()
    {
        var (o, reste) = OptionsTournage.Analyser(new[] { "--ecran=milieu", "--placer=12", "--placer=a,b", "dossier" });
        Assert.Equal(OptionsTournage.Aucune, o);
        Assert.Equal(new[] { "dossier" }, reste);
        Assert.Equal(OptionsTournage.Aucune, OptionsTournage.Analyser(Array.Empty<string>()).Options);
    }

    [Fact]
    public void LaVisiteGuideeResteUnPilouPrincipal()
    {
        // Elle prend la place du Pilou habituel (--redemarrer) : pas le verrou des essais.
        var l = Lancement.Analyser(new[] { "--redemarrer", "--visite-guidee=c.json", "--ecran=gauche", "demo" });
        Assert.Equal(ModeLancement.Principal, l.Mode);
        Assert.True(l.Redemarrer);
        // Les essais acceptent aussi l'écran choisi.
        Assert.Equal(ModeLancement.Essai, Lancement.Analyser(new[] { "--essai=etoile", "--ecran=gauche" }).Mode);
    }

    [Fact]
    public void LeDerouleTientEntreUneMinuteEtDemieEtDeuxMinutesSansTempsMort()
    {
        // Tout joué : 90 à 120 s ; sans les scènes récentes : au moins une minute.
        Assert.InRange(Tournage.Duree, 90, 120);
        Assert.InRange(Tournage.DureeDeBase, 60, Tournage.Duree);
        var noms = Tournage.Etapes.Select(e => e.Nom).ToList();
        Assert.Equal(noms.Count, noms.Distinct().Count());
        foreach (var n in new[] { "menu", "boutique", "amis", "icone", "clavier", "photo", "visite-jeu", "meteo", "etoile", "tape", "evolution" })
            Assert.Contains(n, noms);
        // Des étapes courtes et enchaînées : 2,5 à 4 s, jusqu'à 8 s quand il y a plusieurs choses à montrer.
        Assert.All(Tournage.Etapes, e => Assert.InRange(e.Secondes, 2.5, 8));
        Assert.True(Tournage.Etapes.Count(e => e.Secondes > 4) <= 6);
        Assert.Equal(8, Tournage.DureeDe("menu"));
        Assert.Equal(0, Tournage.DureeDe("inconnue"));
        // L'évolution laisse finir son animation (4,2 s).
        Assert.True(Tournage.DureeDe("evolution") >= 4.2);
    }

    [Fact]
    public void LeProfilDemoNEcritRien()
    {
        var dossier = Path.Combine(Path.GetTempPath(), "pilou-tournage-" + Guid.NewGuid().ToString("N"));
        try
        {
            var p = Tournage.ProfilDemo(1_700_000_000_000);
            Assert.True(p.EnMemoire);
            Assert.Equal(Tournage.NiveauDemo, Profil.Niveau(p.Xp));
            p.Xp += 500;
            p.Bourse.PoGagnes += 100;
            p.Ecrire(dossier);
            Assert.False(File.Exists(Profil.Chemin(dossier)));
            Assert.False(Directory.Exists(dossier));
            // Un profil ordinaire, lui, s'écrit (et le drapeau ne part pas dans le fichier).
            var vrai = new Profil { Xp = 3 };
            vrai.Ecrire(dossier);
            Assert.True(File.Exists(Profil.Chemin(dossier)));
            Assert.DoesNotContain("EnMemoire", File.ReadAllText(Profil.Chemin(dossier)));
            Assert.False(Profil.Lire(dossier).EnMemoire);
        }
        finally
        {
            if (Directory.Exists(dossier)) Directory.Delete(dossier, true);
        }
    }

    [Fact]
    public void LeProfilDemoPorteDesObjetsQuIlPossede()
    {
        var p = Tournage.ProfilDemo(1);
        Assert.NotEmpty(p.Bourse.Equipe);
        Assert.All(p.Bourse.Equipe.Values, port => Assert.Contains(port.Id, p.Bourse.Inventaire));
        Assert.All(p.Bourse.Inventaire, id => Assert.NotNull(Boutique.Trouver(id)));
        Assert.True(p.Bourse.PoGagnes > p.Bourse.PoDepenses);
        Assert.Equal(1, p.Evolution.Migre); // pas de migration (qui écrirait le profil)
        Assert.False(p.Evolution.Due(Tournage.NiveauDemo)); // pas d'évolution surprise : c'est la visite qui la montre
    }

    [Fact]
    public void LesAmisDemoSontFictifs()
    {
        var c = Tournage.CarnetDemo(1_700_000_000_000);
        Assert.Equal("PILOU-ABCD-2345-WXYZ", Amis.Formater(c.Moi.Code));
        Assert.Equal("", c.Moi.Privee);
        Assert.Contains(c.Amis, a => a.Code == Tournage.AmiDemo && a.Etat == EtatAmi.Actif && Amis.EnLigne(a, 1_700_000_000_000));
        Assert.Contains(c.Amis, a => a.Etat == EtatAmi.Recue);
        Assert.All(c.Amis, a => Assert.True(Amis.Valide(a.Code)));
    }

    [Fact]
    public void LesReglagesDeTournageCoupentLeReseauEtLaMiseAJour()
    {
        var r = new Reglages { DossierPartage = @"\\nas\pilou", Telephone = "ABCDEFGH23456789", Webhook = "https://exemple", MiseAJourAuto = true };
        Tournage.Regler(r);
        Assert.Equal("", r.DossierPartage);
        Assert.Equal("", r.Telephone);
        Assert.Equal("", r.Webhook);
        Assert.False(r.MiseAJourAuto);
        Assert.False(r.Connecteurs.Api);
        Assert.False(r.DiscordStatut);
        Assert.False(r.CacherPleinEcran);
        Assert.True(r.IconeNotification);
        // Bulle courte : ce que Pilou dit et l'IA qui attend, pas le détail des sessions.
        Assert.Equal(ModeBulle.Masquee, r.Bulle);
    }

    [Fact]
    public void LaChronologieDonneChaqueEtapeEtSonInstant()
    {
        var json = Tournage.Chronologie(new[] { new Moment("accueil", 1000), new Moment("menu", 4000), new Moment("defense", 18000, false) }, "0.9.42");
        using var d = System.Text.Json.JsonDocument.Parse(json);
        Assert.Equal("0.9.42", d.RootElement.GetProperty("version").GetString());
        var e = d.RootElement.GetProperty("etapes");
        Assert.Equal(3, e.GetArrayLength());
        Assert.Equal("menu", e[1].GetProperty("etape").GetString());
        Assert.Equal(4000, e[1].GetProperty("t").GetInt64());
        Assert.True(e[1].GetProperty("jouee").GetBoolean());
        Assert.False(e[2].GetProperty("jouee").GetBoolean());
    }

    [Fact]
    public void LesScenesInconnuesSontSauteesSansTempsMort()
    {
        // Aucune optionnelle : la visite fait la durée de base, et les sautées démarrent où l'on en est.
        var sans = Tournage.Planifier(e => !e.Optionnelle);
        Assert.Equal(Tournage.Etapes.Count, sans.Count);
        var icone = sans.Single(x => x.Etape.Nom == "icone");
        var defense = sans.Single(x => x.Etape.Nom == "defense");
        Assert.False(defense.Jouee);
        Assert.Equal(icone.Debut, defense.Debut);
        Assert.Equal(Tournage.DureeDeBase, sans[^1].Debut + sans[^1].Etape.Secondes);
        // Tout disponible : chaque étape commence à la fin de la précédente.
        var tout = Tournage.Planifier(_ => true);
        Assert.Equal(Tournage.Duree, tout[^1].Debut + tout[^1].Etape.Secondes);
        // Les nouvelles scènes viennent après les menus et la boutique.
        int boutique = Tournage.Etapes.ToList().FindIndex(e => e.Nom == "boutique");
        Assert.All(Tournage.Etapes.Select((e, i) => (e, i)).Where(x => x.e.Optionnelle), x => Assert.True(x.i > boutique));
    }

    [Fact]
    public void UneSceneEstConnueSiLExeSaitLaJouer()
    {
        Assert.True(Tournage.EssaiConnu("etoile"));
        Assert.True(Tournage.EssaiConnu("meteo:pluie:parapluie"));
        Assert.True(Tournage.EssaiConnu("stade:3"));
        Assert.False(Tournage.EssaiConnu("stade:"));
        Assert.False(Tournage.EssaiConnu("inconnue"));
        // Toutes les étapes de base sont jouables avec cet exe.
        Assert.All(Tournage.Etapes.Where(e => !e.Optionnelle), e => Assert.True(Tournage.Disponible(e)));
        Assert.All(Tournage.Etapes.Where(e => e.Scene is not null && !e.Optionnelle), e => Assert.True(Tournage.EssaiConnu(e.Scene!)));
        // Le rayon Ensembles n'est montré que s'il existe dans la boutique de cet exe.
        var ensembles = Tournage.Etapes.Single(e => e.Nom == "boutique-ensembles");
        Assert.Equal(Tournage.RayonEnsembles() is not null, Tournage.Disponible(ensembles));
    }

    [Fact]
    public void LesEssaisDisponiblesDonnentVersionScenesEtRayons()
    {
        using var d = System.Text.Json.JsonDocument.Parse(Tournage.Disponibles("0.9.42"));
        var r = d.RootElement;
        Assert.Equal("0.9.42", r.GetProperty("version").GetString());
        var essais = r.GetProperty("essais").EnumerateArray().Select(x => x.GetString()).ToList();
        Assert.Contains("visite:jeu", essais);
        Assert.Contains("meteo:*", essais);
        Assert.Contains(Boutique.Tete, r.GetProperty("rayons").EnumerateArray().Select(x => x.GetString()));
        Assert.Equal(Tournage.Etapes.Count, r.GetProperty("etapes").GetArrayLength());
    }
}
