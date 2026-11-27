// Ce qui parle à Pilou, sans rien de VS Code (Node seul, aucune dépendance) : où trouver le jeton, quoi
// envoyer, comment. Tout part vers 127.0.0.1 et nulle part ailleurs (docs/EDITEURS.md).
import * as fs from "fs";
import * as http from "http";
import * as os from "os";
import * as path from "path";

export const PortParDefaut = 47821;

export interface Rapport {
  source: "vscode";
  fichier: string;
  erreurs: number;
  avertissements: number;
  message?: string;
  ferme?: boolean;
}

export interface Acces {
  port: number;
  jeton: string;
}

// %USERPROFILE%\.claude\compagnon\reglages.json : Pilou y range le jeton (Connecteurs.JetonApi) et le port.
export function cheminReglages(): string {
  return path.join(os.homedir(), ".claude", "compagnon", "reglages.json");
}

export function lireAcces(portReglage: number, jetonReglage: string, chemin = cheminReglages()): Acces | undefined {
  let jeton = jetonReglage.trim();
  let port = portReglage > 0 ? portReglage : 0;
  if (jeton === "" || port === 0) {
    try {
      const brut = fs.readFileSync(chemin, "utf8").replace(/^﻿/, "");
      const c = JSON.parse(brut)?.Connecteurs ?? {};
      if (jeton === "" && typeof c.JetonApi === "string") jeton = c.JetonApi;
      if (port === 0 && typeof c.PortApi === "number") port = c.PortApi;
    } catch {
      // Pilou pas installé, ou réglages illisibles : rien à faire
    }
  }
  if (port === 0) port = PortParDefaut;
  return jeton === "" ? undefined : { port, jeton };
}

// Nom seul, jamais le chemin.
export function nomFichier(chemin: string): string {
  const i = Math.max(chemin.lastIndexOf("/"), chemin.lastIndexOf("\\"));
  return (i >= 0 ? chemin.slice(i + 1) : chemin).slice(0, 80);
}

// Chemins absolus retirés (réduits au nom), une ligne, 160 caractères au plus. Pilou refait le même nettoyage.
export function nettoyerMessage(m: string): string {
  const s = m
    .replace(/[\u0000-\u001f\u007f]/g, " ")
    .replace(/(file:\/\/\/?)?([A-Za-z]:[\\/]|\\\\|\/)([^\s"'<>|:*?]+[\\/])+([^\s"'<>|:*?\\/]+)/g, "$4")
    .replace(/\s+/g, " ")
    .trim();
  return s.length <= 160 ? s : s.slice(0, 159).trimEnd() + "…";
}

export function memeRapport(a: Rapport | undefined, b: Rapport): boolean {
  return !!a && a.fichier === b.fichier && a.erreurs === b.erreurs && a.avertissements === b.avertissements
    && (a.message ?? "") === (b.message ?? "") && !!a.ferme === !!b.ferme;
}

// POST /diagnostics ; résout le code HTTP (0 : Pilou absent). Ne rejette jamais.
export function envoyer(acces: Acces, r: Rapport): Promise<number> {
  return new Promise((resolve) => {
    const corps = Buffer.from(JSON.stringify(r), "utf8");
    const req = http.request(
      {
        host: "127.0.0.1",
        port: acces.port,
        path: "/diagnostics",
        method: "POST",
        timeout: 2000,
        headers: {
          Authorization: `Bearer ${acces.jeton}`,
          "Content-Type": "application/json; charset=utf-8",
          "Content-Length": corps.length,
        },
      },
      (res) => {
        res.resume();
        resolve(res.statusCode ?? 0);
      },
    );
    req.on("timeout", () => req.destroy());
    req.on("error", () => resolve(0));
    req.end(corps);
  });
}
