namespace PilouBureau;

// --essai=fenetre:<nom>[:<détail>…] : ouvre une fenêtre sur le profil de démonstration (en mémoire, rien n'est écrit),
// pour les captures du guide de style (docs/STYLE.md) : avec --captures=<dossier>, chaque fenêtre ouverte est rendue
// en PNG à 100, 125 et 150 % puis l'essai quitte (CapturesEssai.cs).
//   fenetre:boutique[:<rayon>[:<article>]]   la boutique, sur un rayon, un article choisi
//   fenetre:rangees                          « Rangées débloquées » (du niveau 9 au niveau 15)
//   fenetre:prenom                           la question du prénom
//   fenetre:amis[:bas]                       « Amis de Pilou » (amis fictifs, code fictif, rien ne part) ; bas : défilée
//   fenetre:connecteurs[:bas|:<n>]           « Connecteurs de Pilou » (dossier de données jetable) ; défilée en bas, ou de n
//   fenetre:renommer                         la petite boîte de saisie (« Renommer » un ami)
//   fenetre:invite                           le Pilou d'un ami en visite, avec sa bulle
public sealed partial class FenetrePilou
{
    // Fait défiler le contenu d'une fenêtre d'essai : « bas », ou un nombre d'unités depuis le haut.
    private static void Defiler(System.Windows.Window f, string ou)
    {
        f.Dispatcher.BeginInvoke(System.Windows.Threading.DispatcherPriority.Loaded, () =>
        {
            if (Trouver(f) is not { } d) return;
            if (double.TryParse(ou, System.Globalization.NumberStyles.Float, System.Globalization.CultureInfo.InvariantCulture, out var y)) d.ScrollToVerticalOffset(y);
            else d.ScrollToEnd();
        });

        static System.Windows.Controls.ScrollViewer? Trouver(System.Windows.DependencyObject o)
        {
            for (int i = 0; i < System.Windows.Media.VisualTreeHelper.GetChildrenCount(o); i++)
            {
                var e = System.Windows.Media.VisualTreeHelper.GetChild(o, i);
                if (e is System.Windows.Controls.ScrollViewer d) return d;
                if (Trouver(e) is { } t) return t;
            }
            return null;
        }
    }

    private void EssaiFenetre(string quoi)
    {
        var p = quoi.Split(':');
        _profil = Tournage.ProfilDemo(Epoque);
        _xpTotal = TotalXp();
        switch (p[0])
        {
            case "boutique":
            {
                var b = p.Length > 1 ? new FenetreBoutique(this, Math.Max(0, Niveau - 4), p[1]) : new FenetreBoutique(this, Math.Max(0, Niveau - 4));
                b.Show();
                if (p.Length > 2) b.Visiter(p[1], p[2]);
                break;
            }
            case "prenom":
                new FenetrePrenom("").Show();
                break;
            case "amis":
                _carnet = Tournage.CarnetDemo(Epoque);
                _essaiAmis = true;
            {
                var amis = new FenetreListeAmis(this);
                amis.Show();
                if (p.Length > 1) Defiler(amis, p[1]);
                break;
            }
            case "connecteurs":
                if (_registre is not null)
                {
                    var connecteurs = new FenetreDesConnecteurs(this, _registre);
                    connecteurs.Show();
                    if (p.Length > 1) Defiler(connecteurs, p[1]);
                }
                break;
            case "renommer":
                Dispatcher.BeginInvoke(() => Saisie.Demander("Renommer", "Le nom que tu donnes à cet ami (seulement sur ce PC).", "Léo"));
                break;
            case "invite":
            {
                var invite = new FenetreInvite("Léo", 1, sombre: true) { Left = 200, Top = 200 };
                invite.Show();
                invite.Dire("ma plus belle prise ? un brochet doré !", Epoque, 600_000);
                break;
            }
            case "rangees":
                new FenetreRangees(9, 15, _ => { }).Show();
                break;
        }
    }
}
