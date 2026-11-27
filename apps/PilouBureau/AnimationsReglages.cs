namespace PilouBureau;

// Réglages des animations des campagnes (fenêtre Aventure, bouton « ✧ ») : gardés dans reglages.json, jamais pendant
// un tournage ni un essai (profil en mémoire).
public sealed partial class FenetrePilou
{
    internal string AnimationsCampagnes
    {
        get => _reglages.AnimationsCampagnes;
        set
        {
            _reglages.AnimationsCampagnes = value;
            SauverAnimations();
        }
    }

    internal bool TexteInstantane
    {
        get => _reglages.TexteInstantane;
        set
        {
            _reglages.TexteInstantane = value;
            SauverAnimations();
        }
    }

    private void SauverAnimations()
    {
        if (_essaiCamp is null && !_demo) _reglages.Ecrire(_dossier);
    }
}
