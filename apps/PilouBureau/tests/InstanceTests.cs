using PilouBureau;
using Xunit;

// Instance unique : relancer l'exe ramène le Pilou qui tourne ; --redemarrer le remplace ; un Pilou figé est remplacé.
public class InstanceTests
{
    private sealed class Faux : IAutreInstance
    {
        public bool Libre, Repond = true, QuitteSeul, ForceMarche = true;
        private bool _force, _quitter;
        public readonly List<string> Journal = new();

        public bool Prendre() => Libre;

        public bool Attendre(TimeSpan delai)
        {
            Journal.Add($"attendre {delai.TotalSeconds}");
            return _force ? ForceMarche : QuitteSeul || _quitter;
        }

        public bool DemanderAfficher()
        {
            Journal.Add("afficher");
            return Repond;
        }

        public bool DemanderQuitter()
        {
            Journal.Add("quitter");
            _quitter = Repond;
            return Repond;
        }

        public void Forcer()
        {
            Journal.Add("forcer");
            _force = true;
        }
    }

    private static Lancement L(params string[] args) => Lancement.Analyser(args);

    [Fact]
    public void ModesDeLaLigneDeCommande()
    {
        Assert.Equal(ModeLancement.Signal, L("--signal", "codex", "fin").Mode);
        Assert.Equal(ModeLancement.Signal, L("--dossier=x", "--signal", "codex").Mode);
        Assert.Equal(ModeLancement.Brancher, L("--brancher", "codex").Mode);
        Assert.Equal(ModeLancement.Brancher, L("--debrancher", "codex").Mode);
        Assert.Equal(ModeLancement.Principal, L("--brancher").Mode);
        Assert.Equal(ModeLancement.Essai, L(@"--film=C:\f", "--duree=4").Mode);
        Assert.Equal(ModeLancement.Essai, L("--instantane=a.png").Mode);
        Assert.Equal(ModeLancement.Essai, L("--devant", "--essai=clavier").Mode);
        Assert.Equal(ModeLancement.Principal, L().Mode);
        Assert.Equal(ModeLancement.Principal, L("--devant").Mode);
        Assert.Equal(ModeLancement.Principal, L(@"C:\dossier").Mode);
    }

    [Fact]
    public void OptionsDInstance()
    {
        Assert.True(L("--redemarrer").Redemarrer);
        Assert.True(L("--apres-maj", @"C:\d").ApresMaj);
        Assert.False(L().Redemarrer || L().ApresMaj);
        // Un essai n'arrête ni n'attend jamais le Pilou habituel.
        Assert.False(L("--redemarrer", "--essai=photo").Redemarrer);
        Assert.Equal(new[] { @"C:\d", "--devant" }, Lancement.Reste(new[] { "--apres-maj", @"C:\d", "--redemarrer", "--devant" }));
    }

    [Fact]
    public void PremierPilouDemarre()
    {
        var f = new Faux { Libre = true };
        Assert.Equal(Issue.Demarrer, Instance.Decider(L(), f));
        Assert.Empty(f.Journal);
    }

    [Fact]
    public void RelancerRameneLExistantSansEnCreerUnDeuxieme()
    {
        var f = new Faux();
        Assert.Equal(Issue.Rendre, Instance.Decider(L(), f));
        Assert.Equal(new[] { "afficher" }, f.Journal);
    }

    [Fact]
    public void UnPilouFigeEstRemplace()
    {
        var f = new Faux { Repond = false };
        Assert.Equal(Issue.Demarrer, Instance.Decider(L(), f));
        Assert.Equal(new[] { "afficher", "forcer", "attendre 5" }, f.Journal);
    }

    [Fact]
    public void RemplacementImpossibleOnNInsistePas()
    {
        var f = new Faux { Repond = false, ForceMarche = false };
        Assert.Equal(Issue.Rendre, Instance.Decider(L(), f));
    }

    [Fact]
    public void RedemarrerArreteProprementPuisPrendLaPlace()
    {
        var f = new Faux();
        Assert.Equal(Issue.Demarrer, Instance.Decider(L("--redemarrer"), f));
        Assert.Equal(new[] { "quitter", "attendre 10" }, f.Journal);
    }

    [Fact]
    public void RedemarrerUnPilouQuiNeRepondPlus()
    {
        var f = new Faux { Repond = false };
        Assert.Equal(Issue.Demarrer, Instance.Decider(L("--redemarrer"), f));
        Assert.Equal(new[] { "quitter", "forcer", "attendre 5" }, f.Journal);
    }

    [Fact]
    public void ApresMajAttendQueLAncienneVersionQuitte()
    {
        var f = new Faux { QuitteSeul = true };
        Assert.Equal(Issue.Demarrer, Instance.Decider(L("--apres-maj"), f));
        Assert.Equal(new[] { "attendre 15" }, f.Journal);
    }

    [Fact]
    public void ApresMajAncienneVersionBloquee()
    {
        var f = new Faux();
        Assert.Equal(Issue.Demarrer, Instance.Decider(L("--apres-maj"), f));
        Assert.Equal(new[] { "attendre 15", "forcer", "attendre 5" }, f.Journal);
    }
}
