// Pilou pour VS Code : compte les erreurs et avertissements du fichier actif et les envoie à l'API locale de
// Pilou (POST http://127.0.0.1:47821/diagnostics). Pilou regroupe et décide seul s'il dit quelque chose.
// Envoi seulement quand le compte ou le fichier change (750 ms après le dernier changement), et une fois par
// minute tant que la fenêtre a le focus, pour qu'il sache que l'éditeur est toujours là.
import * as vscode from "vscode";
import { Acces, envoyer, lireAcces, memeRapport, nettoyerMessage, nomFichier, Rapport } from "./pilou";

const Attente = 750;
const Battement = 60_000;

let dernier: Rapport | undefined;
let minuterie: NodeJS.Timeout | undefined;
let acces: Acces | undefined;

function reglages() {
  const c = vscode.workspace.getConfiguration("pilou");
  return {
    actif: c.get<boolean>("actif", true),
    port: c.get<number>("port", 0),
    jeton: c.get<string>("jeton", ""),
    message: c.get<boolean>("envoyerMessage", false),
  };
}

// Documents qui ne sont pas des fichiers de travail (sortie, paramètres, diff git…) : ignorés.
const Schemas = new Set(["file", "untitled", "vscode-remote", "vscode-vfs", "vscode-notebook-cell"]);

function rapport(): Rapport | undefined {
  const ed = vscode.window.activeTextEditor;
  if (!ed || !Schemas.has(ed.document.uri.scheme)) return undefined;
  const diags = vscode.languages.getDiagnostics(ed.document.uri);
  const erreurs = diags.filter((d) => d.severity === vscode.DiagnosticSeverity.Error);
  const avertissements = diags.filter((d) => d.severity === vscode.DiagnosticSeverity.Warning).length;
  const fichier = ed.document.isUntitled ? "sans titre" : nomFichier(ed.document.fileName);
  const r: Rapport = { source: "vscode", fichier, erreurs: erreurs.length, avertissements };
  if (reglages().message && erreurs.length > 0) {
    const premiere = [...erreurs].sort((a, b) => a.range.start.line - b.range.start.line)[0];
    r.message = nettoyerMessage(premiere.message);
  }
  return r;
}

async function poster(r: Rapport, force: boolean): Promise<void> {
  if (!force && memeRapport(dernier, r)) return;
  const reg = reglages();
  acces ??= lireAcces(reg.port, reg.jeton);
  if (!acces) return; // Pilou pas installé (pas de jeton) : silence
  let code = await envoyer(acces, r);
  if (code === 401) {
    // Jeton renouvelé dans Pilou : on le relit une fois.
    acces = lireAcces(reg.port, reg.jeton);
    if (acces) code = await envoyer(acces, r);
  }
  if (code === 202) dernier = r;
}

function planifier(): void {
  if (minuterie) clearTimeout(minuterie);
  minuterie = setTimeout(() => {
    minuterie = undefined;
    if (!reglages().actif || !vscode.window.state.focused) return;
    const r = rapport();
    // Pas d'éditeur de texte (terminal, panneau) : Pilou garde le dernier fichier, rien à envoyer.
    if (r) void poster(r, false);
  }, Attente);
}

export function activate(context: vscode.ExtensionContext): void {
  context.subscriptions.push(
    vscode.languages.onDidChangeDiagnostics((e) => {
      const ed = vscode.window.activeTextEditor;
      if (ed && e.uris.some((u) => u.toString() === ed.document.uri.toString())) planifier();
    }),
    vscode.window.onDidChangeActiveTextEditor(() => planifier()),
    vscode.window.onDidChangeWindowState((w) => {
      // Fenêtre retrouvée : elle redevient l'éditeur le plus récent pour Pilou.
      if (w.focused) {
        dernier = undefined;
        planifier();
      }
    }),
    vscode.workspace.onDidChangeConfiguration((e) => {
      if (!e.affectsConfiguration("pilou")) return;
      acces = undefined;
      dernier = undefined;
      if (!reglages().actif) void fermer();
      else planifier();
    }),
  );
  const battement = setInterval(() => {
    if (!reglages().actif || !vscode.window.state.focused) return;
    const r = rapport();
    if (r) void poster(r, true);
  }, Battement);
  context.subscriptions.push({ dispose: () => clearInterval(battement) });
  planifier();
}

async function fermer(): Promise<void> {
  if (dernier) await poster({ source: "vscode", fichier: "", erreurs: 0, avertissements: 0, ferme: true }, true);
  dernier = undefined;
}

export function deactivate(): Promise<void> {
  if (minuterie) clearTimeout(minuterie);
  return fermer();
}
