namespace PilouBureau;

// ------------------------------------------------------------------------------------------------------
// Éditeurs (Visual Studio, VS Code) : les extensions de integrations/ envoient le compte d'erreurs et
// d'avertissements du fichier actif à l'API locale (POST /diagnostics). Rien ne quitte la machine ; le chemin
// n'est jamais gardé, seulement le nom du fichier. Ce connecteur n'a rien à relever : il porte l'interrupteur
// et les réglages, Pilou fait le reste (Diagnostics.cs, FenetreDiagnostics.cs). Doc : docs/EDITEURS.md.
// ------------------------------------------------------------------------------------------------------
public sealed class ConnecteurEditeurs : Connecteur
{
    public const string Cle = "editeurs";

    public override string Id => Cle;
    public override string Nom => "Éditeurs (Visual Studio, VS Code)";
    public override string Description =>
        "Erreurs et avertissements du fichier ouvert : « ⚠ 3 erreurs · 2 avert. · Program.cs », une grimace quand ça " +
        "empire, « ✓ propre ! » quand tu repasses à zéro. Il se tait le reste du temps. Il faut l'extension de ton éditeur.";
    public override string Signe => "⚠";
    // Rien à relever : l'extension parle à l'API locale. L'interrupteur reste celui des réglages des connecteurs.
    public override ModeConnecteur Mode => ModeConnecteur.Passif;
    public override bool ActifParDefaut => true;

    public override string Aide =>
        "1. Télécharge l'extension dans la dernière release : pilou-vscode.vsix (VS Code) ou PilouVisualStudio.vsix " +
        "(Visual Studio 2022).\n" +
        "2. VS Code : Extensions → « … » → Installer depuis un VSIX. Visual Studio : double-clic sur le .vsix, puis redémarre VS.\n" +
        "3. L'extension lit seule le jeton de l'API locale dans reglages.json (ou colle-le dans ses réglages).\n" +
        "Ce qui est envoyé, et seulement à 127.0.0.1 : le nom du fichier, les deux comptes et, si tu coches la case, " +
        "le premier message d'erreur. Détails : docs/EDITEURS.md.";

    public override IReadOnlyList<ReglageConnecteur> Reglages { get; } = new[]
    {
        new ReglageConnecteur("nom", "Nom du fichier dans la bulle", TypeReglage.Case, "sinon « fichier actif »", "oui"),
        new ReglageConnecteur("message", "Premier message d'erreur", TypeReglage.Case, "tronqué à 60 caractères", "non"),
    };
}
