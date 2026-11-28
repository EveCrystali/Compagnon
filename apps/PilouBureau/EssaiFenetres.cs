namespace PilouBureau;

// --essai=fenetre:<nom>[:<détail>…] : ouvre une fenêtre sur le profil de démonstration (en mémoire, rien n'est écrit),
// pour les captures du guide de style (docs/STYLE.md) : avec --captures=<dossier>, chaque fenêtre ouverte est rendue
// en PNG à 100, 125 et 150 % puis l'essai quitte (CapturesEssai.cs).
//   fenetre:boutique[:<rayon>[:<article>]]   la boutique, sur un rayon, un article choisi
//   fenetre:rangees                          « Rangées débloquées » (du niveau 9 au niveau 15)
//   fenetre:prenom                           la question du prénom
public sealed partial class FenetrePilou
{
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
            case "rangees":
                new FenetreRangees(9, 15, _ => { }).Show();
                break;
        }
    }
}
