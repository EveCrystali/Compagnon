using System.Windows;
using System.Windows.Controls;
using System.Windows.Media;

namespace PilouBureau;

// Expéditions sur le PC (docs/EXPEDITIONS.md, logique dans Expeditions.cs) : la jauge d'énergie qui se remplit
// en travaillant, en mangeant et un peu à l'attente ; le départ (baluchon, épée en bois), la pancarte pendant
// l'absence (les statuts des sessions restent dans la bulle), le retour (fier, ou cabossé avec un pansement),
// un petit coffre près de Pilou tant que le journal n'est pas lu. Jamais de fenêtre qui s'ouvre toute seule.
public sealed partial class FenetrePilou
{
    private const double DepartExpMs = 4500, RetourExpMs = 4500;
    private EtatExpedition? _essaiExp;
    private double _expDepart = -1, _expRetour = -1;   // début des animations (Maintenant), -1 : aucune
    private double _expX0, _expRetourX;
    private int _expSens = 1;
    private bool _expAppui;
    private Resultat? _expAnime;
    private double _expEnergieLue = -1e12, _expEcrit = -1e12;
    private bool _expAEcrire;
    private Pixels? _badgeJournal;
    private FenetreExpeditions? _fenetreExp;

    // Ce que l'appareil sait de ses expéditions (en essai : un état à part, jamais écrit).
    private EtatExpedition Exp => _essaiExp ?? _profil.Expedition;

    // Pilou n'est pas là pour autre chose : parti, ou en train de partir ou de revenir.
    internal bool EnExpedition => Exp.Courante is not null || _expRetour >= 0;

    private bool Boudeur => _profil.Soins.Base is not null && Soins.Boudeur(SoinsMaintenant());

    // Les autres appareils du groupe (relais et dossier partagé), relus au plus toutes les 5 s ; rien en essai.
    private ExpeditionsAutres AutresExpeditions()
    {
        if (_essaiExp is not null) return ExpeditionsAutres.Aucun;
        if (_expAutres is { } c && Maintenant - c.T < 5000) return c.Autres;
        var autres = Expeditions.Autres(GroupeMem.Compteurs.Select(k => (k.ExpJour, k.ExpNombre, k.ExpLibre))
            .Concat(_profil.AutresDuDossier(DossierPartage).Select(p => (p.Expedition.Jour, p.Expedition.Nombre, p.Expedition.Libre))), DateTime.Now);
        _expAutres = (Maintenant, autres);
        return autres;
    }

    private (double T, ExpeditionsAutres Autres)? _expAutres;

    private void EcrireExpedition(bool tout_de_suite = true)
    {
        if (_essaiExp is not null) return;
        if (!tout_de_suite && Maintenant - _expEcrit < 120_000)
        {
            _expAEcrire = true;
            return;
        }
        _expEcrit = Maintenant;
        _expAEcrire = false;
        _profil.Ecrire(DossierPartage);
    }

    // Pourquoi Pilou ne peut pas partir maintenant (visite, invité), "" s'il le peut.
    private string Occupation() =>
        _visites.Sortie is not null ? "Pilou est en visite chez un ami"
        : _visites.Venue is not null ? "Pilou a de la visite"
        : _evolutionDebut >= 0 ? "Pilou est en pleine évolution"
        : "";

    // ---- Énergie : attente, travail, repas

    private void Recharger(double gagne, string ou = "")
    {
        if (gagne <= 0) return;
        EcrireExpedition(false);
        if (ou != "" && gagne >= 1) Flotter($"+{Math.Round(gagne)} ⚡", 1, new Point(TeteX + 10, TeteY - 44));
    }

    // Toutes les 2 s (Activites) : le temps passé dans une appli de travail, la personne présente. Jamais les frappes.
    private void EnergieTravail(string activite, bool present, double dt)
    {
        if (!present || Array.IndexOf(Vivacite.Travail, activite) < 0) return;
        Recharger(Jauge.Travailler(Exp.Energie, dt, DateTime.Now, Boudeur));
    }

    private void EnergieTour() => Recharger(Jauge.Tour(Exp.Energie, Epoque, DateTime.Now, Boudeur));

    private void EnergieQuete(int n)
    {
        double g = 0;
        for (int i = 0; i < n; i++) g += Jauge.Quete(Exp.Energie, DateTime.Now, Boudeur);
        Recharger(g);
    }

    private void EnergieRepas(string objet) => Recharger(Jauge.Manger(Exp.Energie, objet, DateTime.Now, Boudeur), "repas");

    // En-cas de route (boutique) : le meilleur d'abord.
    private void DonnerEnCas()
    {
        foreach (var id in new[] { "jus-etoile", "galette-route" })
        {
            if (_profil.Bourse.Consommables.GetValueOrDefault(id) <= 0) continue;
            if (Jauge.Affiche(Exp.Energie) >= Jauge.Max)
            {
                Dire("je suis plein d'énergie ⚡, garde-le pour plus tard", 3000);
                return;
            }
            _profil.Bourse.Consommables[id]--;
            Manger(id);
            double g = Jauge.Manger(Exp.Energie, id, DateTime.Now, Boudeur);
            EcrireExpedition();
            if (g >= 1) Flotter($"+{Math.Round(g)} ⚡", 1, new Point(TeteX + 10, TeteY - 44));
            Dire(g >= 1 ? $"miam ! ⚡ {Jauge.Affiche(Exp.Energie)}" : "miam ! (assez mangé pour aujourd'hui : plus d'énergie)", 3000);
            return;
        }
        OuvrirBoutique(PilouBureau.Boutique.Speciaux);
    }

    private int EnCasEnReserve => _profil.Bourse.Consommables.GetValueOrDefault("galette-route") + _profil.Bourse.Consommables.GetValueOrDefault("jus-etoile");

    // ---- Suivi (toutes les 300 ms, Lire) : attente, retour, gains

    private void SuivreExpedition()
    {
        var e = Exp;
        if (Maintenant - _expEnergieLue > 30_000)
        {
            _expEnergieLue = Maintenant;
            Recharger(Jauge.Avancer(e.Energie, Epoque, Boudeur));
        }
        if (_expAEcrire && Maintenant - _expEcrit > 120_000) EcrireExpedition();
        // Une expédition finie (même PC éteint pendant ce temps) : résolue une fois, créditée une fois.
        if (Expeditions.Avancer(e, Epoque, Bourse().Inventaire) is { } r)
        {
            Crediter(r);
            Revenir(r);
        }
        else if (e.Dernier is { Credite: false } d) Crediter(d);
        if (_expRetour >= 0 && Maintenant - _expRetour >= RetourExpMs) Rentre();
    }

    private void Crediter(Resultat r)
    {
        if (_essaiExp is not null)
        {
            r.Credite = true;
            return;
        }
        var (po, xp, forge) = Expeditions.Crediter(_profil, r, BonusSoins);
        EcrireExpedition();
        _bourseCache = null;
        _xpTotal = TotalXp();
        if (r.Issue != Denouement.Rappel) Signaler("expedition", 1);
        if (r.Boss) Signaler("expedition:boss", 1);
        if (r.Rares > 0) Signaler("expedition:rare", r.Rares);
        if (forge != "") Dire($"◆ 25 éclats de cristal : Pilou a forgé {Expeditions.NomCourt(forge).ToLowerInvariant()} !", 5000);
        _expGains = (po, xp);
        VerifierNiveau();
    }

    private (int Po, int Xp) _expGains;

    // ---- Départ

    internal string? PartirExpedition(string lieu)
    {
        var l = Expeditions.Trouver(lieu);
        if (l is null) return "lieu inconnu";
        var refus = Expeditions.Refus(Exp, l, Niveau, Epoque, DateTime.Now, AutresExpeditions(), Occupation());
        if (refus is not null)
        {
            Dire(refus, 3500);
            return refus;
        }
        if (_jeuEnCours != Jeu.Aucun) Arreter("");
        var x = Expeditions.Partir(Exp, l, Niveau, Epoque, DateTime.Now, AutresExpeditions(), IdAppareil, Expeditions.NouvelId(), Occupation());
        if (x is null) return "impossible de partir";
        EcrireExpedition();
        _expDepart = Maintenant;
        _expX0 = _x;
        _expRetourX = _x;
        _expSens = Placement.SensSortie(_x, _zone.Left, _zone.Right);
        _geste = Geste.Rien;
        _expAnime = null;
        Dire($"en route pour {Expeditions.De(l.Nom)} ! −{l.Cout} ⚡ (reste {Jauge.Affiche(Exp.Energie)}) · retour vers {Amis.Heure(DateTime.Now.AddMinutes(l.Minutes))}", 5000);
        return null;
    }

    internal void RappelerExpedition()
    {
        if (Expeditions.Rappeler(Exp, Epoque) is not { } r) return;
        EcrireExpedition();
        Revenir(r);
        Dire("tu m'as appelé ? je fais demi-tour !", 3500);
    }

    private void Revenir(Resultat r)
    {
        _expAnime = r;
        _expRetour = Maintenant;
        // Rappelé pendant le départ : il fait demi-tour là où il est ; sinon il revient par le bord de l'écran.
        if (_expDepart >= 0 && Maintenant - _expDepart < DepartExpMs) _expRetourX = _x;
        else
        {
            var (min, max) = Placement.BornesPieds(_zone.Left, _zone.Right, K);
            _expX0 = _zoneConnue ? Math.Clamp(_x, min, max) : _x;
            _expRetourX = Placement.Sortie(_expSens, _zone.Left, _zone.Right, K);
        }
        _expDepart = -1;
    }

    // Fin de l'animation de retour : ce qu'il dit, ce qu'il a gagné, le coffre du journal.
    private void Rentre()
    {
        var r = _expAnime;
        _expRetour = -1;
        _expAnime = null;
        _x = _expX0;
        _tSaut = Maintenant;
        if (r is null || r.Issue == Denouement.Rappel) return;
        var (po, xp) = _essaiExp is not null ? (r.Po, r.Xp) : _expGains;
        _expGains = (0, 0);
        if (po > 0) FlotterPo($"+{po} po");
        if (xp > 0) Flotter($"+{xp} xp", 1, new Point(TeteX - 18, TeteY - 30));
        if (r.Issue == Denouement.Defaite)
        {
            Dire("je suis rentré… bredouille et un peu cabossé (clic sur le coffre : le journal)", 5000);
        }
        else
        {
            _salueJusque = Maintenant + 1800;
            var butin = r.Objet != "" ? $" et {Expeditions.NomCourt(r.Objet).ToLowerInvariant()} !" : r.Trophee != "" ? " et un trophée !" : "";
            Dire($"je suis rentré{(r.Issue == Denouement.Victoire ? " en héros" : "")} : {po} po{butin} (clic sur le coffre : le journal)", 5500);
        }
        PublierSortie($"{Expeditions.SigneIssue(r.Issue)} Pilou est rentré d'expédition", $"{Expeditions.NomIssue(r.Issue)} · {po} po");
    }

    // ---- Animation (comme une visite : départ, pancarte, retour)

    // Pendant une expédition, Pilou ne se promène pas. Renvoie s'il y a quelque chose à animer.
    private bool ExpeditionBouge(double dt, out bool marche)
    {
        marche = false;
        if (!EnExpedition) return false;
        double sortie = Placement.Sortie(_expSens, _zone.Left, _zone.Right, K);
        if (_expRetour >= 0)
        {
            double k = Math.Clamp((Maintenant - _expRetour) / (RetourExpMs - 900), 0, 1);
            _x = _expRetourX + (_expX0 - _expRetourX) * k;
            marche = k < 1;
        }
        else if (_expDepart >= 0 && Maintenant - _expDepart < DepartExpMs)
        {
            double k = Math.Clamp((Maintenant - _expDepart - 1200) / (DepartExpMs - 1200), 0, 1);
            _x = _expX0 + (sortie - _expX0) * k;
            marche = k > 0;
        }
        else
        {
            // Absent : la pancarte reste là où il était.
            if (_expDepart < 0 && _expX0 == 0) _expX0 = _x;
            var (min, max) = Placement.BornesPieds(_zone.Left, _zone.Right, K);
            _x = Math.Clamp(_expX0, min, max);
            _expX0 = _x;
            _expRetourX = sortie;
        }
        return true;
    }

    private bool ExpeditionAbsent => Exp.Courante is not null && _expRetour < 0 && !(_expDepart >= 0 && Maintenant - _expDepart < DepartExpMs);

    // Ce que l'expédition change à la pose : baluchon et épée en bois, pancarte, pansement au retour d'une défaite.
    private void HabillerExpedition(Pose p, double t)
    {
        var plus = new List<string>();
        if (Exp.Courante is { } x && _expRetour < 0)
        {
            double d = Maintenant - _expDepart;
            if (_expDepart >= 0 && d < DepartExpMs)
            {
                plus.Add("baluchon");
                plus.Add(Expeditions.EpeeBois);
                p.Regard = _expSens;
                p.Salue = d < 1200;
                p.Course = d > 1200;
                p.Expr = Expr.Fete;
            }
            else p.Pancarte = $"en expédition\n↩ {Amis.Heure(DateTime.Now.AddMilliseconds(x.Fin - Epoque))}";
        }
        else if (_expRetour >= 0 && _expAnime is { } r)
        {
            plus.Add("baluchon");
            p.Regard = -_expSens;
            if (r.Issue == Denouement.Defaite)
            {
                plus.Add("pansement");
                p.Expr = Expr.Grimace;
            }
            else
            {
                plus.Add(Expeditions.EpeeBois);
                p.Expr = Expr.Fete;
            }
        }
        // Cabossé : un pansement sur la tête quelque temps après une défaite.
        if (_expRetour < 0 && Exp.Courante is null && Exp.Dernier is { Issue: Denouement.Defaite } dern && Epoque - dern.Fin < Expeditions.Cabosse
            && Epoque >= dern.Fin)
            plus.Add("pansement");
        if (plus.Count > 0) p.Soins = p.Soins.Concat(plus).ToList();
    }

    // Ligne de la bulle pendant l'absence (les statuts des sessions restent affichés dessous).
    private string LigneExpedition()
    {
        if (Exp.Courante is not { } x) return "";
        return "⚔ " + Expeditions.Ligne(Exp, DateTime.Now.AddMilliseconds(x.Fin - Epoque)) + " (clic sur la pancarte : détails)";
    }

    // Petit coffre près de Pilou tant que le journal du retour n'est pas lu (un clic l'ouvre). Rien d'autre.
    private void AnimerExpedition(double t)
    {
        bool montrer = Exp.Dernier is { } d && !Exp.DernierLu && d.Issue != Denouement.Rappel && !EnExpedition && _jeuEnCours == Jeu.Aucun
                       && Epoque - d.Fin < 12 * 3_600_000;
        if (montrer && _badgeJournal is null)
        {
            _badgeJournal = Pixels.Sprite("coffre-expedition", 2);
            if (_badgeJournal is null) return;
            _badgeJournal.Cursor = System.Windows.Input.Cursors.Hand;
            _badgeJournal.ToolTip = "Journal d'expédition — clic pour le lire";
            _badgeJournal.MouseLeftButtonUp += (_, e) =>
            {
                e.Handled = true;
                OuvrirExpeditions(true);
            };
            _jeu.Children.Add(_badgeJournal);
        }
        else if (!montrer && _badgeJournal is not null)
        {
            _jeu.Children.Remove(_badgeJournal);
            _badgeJournal = null;
        }
        if (_badgeJournal is null) return;
        if (Bandeau.Anime) _badgeJournal.Changer("coffre-expedition", t);
        Canvas.SetLeft(_badgeJournal, Placement.ACote(_aGauche, CoteJeu, 34, _badgeJournal.Width));
        Canvas.SetTop(_badgeJournal, TeteY + 22 + (Bandeau.Anime ? Math.Round(Math.Sin(t / 600) * 2) : 0));
    }

    // ---- Menus et fenêtre

    private MenuItem MenuExpedition()
    {
        var e = Exp;
        int energie = Jauge.Affiche(e.Energie);
        var m = new MenuItem { Header = e.Courante is { } x ? $"⚔ En expédition · retour vers {Amis.Heure(DateTime.Now.AddMilliseconds(x.Fin - Epoque))}"
            : $"⚔ Partir en expédition… · ⚡ {energie}" };
        if (e.Courante is not null)
        {
            m.Items.Add(Entree("Voir l'expédition…", () => OuvrirExpeditions(false)));
            m.Items.Add(Entree("↩ Rappeler Pilou (il rentre les mains vides)", RappelerExpedition));
            return m;
        }
        var autres = AutresExpeditions();
        int reste = Expeditions.Restantes(e, DateTime.Now, autres);
        double libre = Expeditions.LibreA(e, autres);
        string etat = reste <= 0 ? "plus d'expédition aujourd'hui (3 par jour)"
            : Epoque < libre ? $"Pilou se repose encore {Statut.Duree(libre - Epoque)} · {reste} restante{(reste > 1 ? "s" : "")} aujourd'hui"
            : $"⚡ {energie}/100 · {reste} expédition{(reste > 1 ? "s" : "")} possible{(reste > 1 ? "s" : "")} aujourd'hui";
        m.Items.Add(new MenuItem { Header = etat, IsEnabled = false });
        foreach (var l in Expeditions.Lieux)
        {
            var refus = Expeditions.Refus(e, l, Niveau, Epoque, DateTime.Now, autres, Occupation());
            bool ferme = Niveau < l.Niveau;
            var item = Entree(ferme ? $"{l.Signe}  {l.Nom} — niveau {l.Niveau}"
                : $"{l.Signe}  {l.Nom}  ·  ⚡ {l.Cout}  ·  {Expeditions.Duree(l.Minutes)}  ·  risque {Expeditions.Risque(l)}", () => PartirExpedition(l.Id));
            item.IsEnabled = refus is null;
            item.ToolTip = refus ?? l.Accroche;
            m.Items.Add(item);
        }
        m.Items.Add(new Separator());
        var arme = Expeditions.OutilDe(e.Arme)?.Nom ?? "Épée en bois";
        var talisman = Expeditions.OutilDe(e.Talisman)?.Nom ?? "aucun talisman";
        m.Items.Add(Entree($"Équipement : {arme} · {talisman}…", () => OuvrirExpeditions(false)));
        int encas = EnCasEnReserve;
        m.Items.Add(Entree(encas > 0 ? $"Donner un en-cas de route (+⚡) · {encas} en réserve" : "En-cas de route (+⚡) : à la boutique…", DonnerEnCas));
        if (e.Dernier is { Issue: not Denouement.Rappel })
            m.Items.Add(Entree($"Journal d'expédition{(e.DernierLu ? "" : " (nouveau)")}…", () => OuvrirExpeditions(true)));
        return m;
    }

    internal void OuvrirExpeditions(bool journal)
    {
        if (journal) LireJournal();
        if (_fenetreExp is { IsVisible: true })
        {
            _fenetreExp.Rafraichir();
            _fenetreExp.Activate();
            return;
        }
        try
        {
            _fenetreExp = new FenetreExpeditions(this);
            _fenetreExp.Closed += (_, _) => _fenetreExp = null;
            if (_demo) PoserPresDePilou(_fenetreExp); // visite guidée : à côté de Pilou (FenetreVisite.cs)
            _fenetreExp.Show();
        }
        catch (InvalidOperationException)
        {
            // fenêtre principale en cours de fermeture
        }
    }

    private void LireJournal()
    {
        if (Exp.DernierLu) return;
        Exp.DernierLu = true;
        EcrireExpedition(false);
    }

    // Pour la fenêtre des expéditions.
    internal EtatExpedition EtatExpeditions => Exp;
    internal ExpeditionsAutres ExpeditionsDuGroupe => AutresExpeditions();
    internal string OccupationExpedition => Occupation();
    internal int NiveauExpedition => Niveau;
    internal double EpoqueExpedition => Epoque;
    internal IReadOnlyCollection<string> ObjetsPossedes => Bourse().Inventaire;
    internal int SoldeExpedition => Bourse().Solde;

    internal void ChoisirOutil(string emplacement, string id)
    {
        if (emplacement == "arme") Exp.Arme = id;
        else Exp.Talisman = id;
        EcrireExpedition();
    }

    // ---- Essais sans attendre : --essai=expedition:depart|retour|defaite|journal

    private void EssaiExpedition(string quoi)
    {
        _essaiExp = new EtatExpedition { Energie = { Valeur = 80, T = Epoque }, Arme = "lanterne", Talisman = "medaille" };
        var l = Expeditions.Lieux[2];
        double e = Epoque;
        // Une graine qui donne l'issue voulue (le tirage est déterministe : on cherche, on ne truque pas).
        Resultat Chercher(Denouement voulu) => Enumerable.Range(0, 2000)
            .Select(i => Expeditions.Resoudre(new Expedition
            {
                Id = $"essai-{i}", Lieu = l.Id, Fin = e, Graine = Expeditions.GraineDe("essai", $"essai-{i}"), Niveau = 12,
                Arme = "lanterne", Talisman = "medaille",
            }, Array.Empty<string>()))
            .First(r => r.Issue == voulu && (voulu != Denouement.Victoire || r.Boss));
        switch (quoi)
        {
            case "depart":
                _essaiExp.Energie.Valeur = 100;
                PartirExpedition(Expeditions.Lieux[0].Id); // ouvert dès le niveau 1
                break;
            case "absent":
                _essaiExp.Courante = new Expedition { Id = "essai", Lieu = l.Id, Debut = e, Fin = e + 50 * 60_000 };
                _expX0 = _x;
                break;
            case "retour":
            case "defaite":
            {
                var r = Chercher(quoi == "retour" ? Denouement.Victoire : Denouement.Defaite);
                r.Credite = true;
                _essaiExp.Dernier = r;
                _essaiExp.DernierLu = false;
                _expX0 = _x;
                _expSens = Placement.SensSortie(_x, _zone.Left, _zone.Right);
                Revenir(r);
                break;
            }
            case "journal":
            {
                var r = Chercher(Denouement.Victoire);
                r.Credite = true;
                _essaiExp.Dernier = r;
                _essaiExp.DernierLu = false;
                OuvrirExpeditions(true);
                break;
            }
        }
    }
}
