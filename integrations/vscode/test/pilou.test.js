// Tests sans VS Code (node --test) : jeton lu dans reglages.json, nom seul, chemins retirés, envoi HTTP local.
const test = require("node:test");
const assert = require("node:assert");
const fs = require("fs");
const http = require("http");
const os = require("os");
const path = require("path");
const p = require("../out/pilou.js");

test("jeton et port lus dans reglages.json (BOM toléré), réglage prioritaire", () => {
  const dossier = fs.mkdtempSync(path.join(os.tmpdir(), "pilou-"));
  const chemin = path.join(dossier, "reglages.json");
  fs.writeFileSync(chemin, "\uFEFF" + JSON.stringify({ Connecteurs: { JetonApi: "abc", PortApi: 50000 } }));
  assert.deepStrictEqual(p.lireAcces(0, "", chemin), { port: 50000, jeton: "abc" });
  assert.deepStrictEqual(p.lireAcces(1234, "xyz", chemin), { port: 1234, jeton: "xyz" });
  assert.strictEqual(p.lireAcces(0, "", path.join(dossier, "absent.json")), undefined);
  assert.deepStrictEqual(p.lireAcces(0, "j", path.join(dossier, "absent.json")), { port: p.PortParDefaut, jeton: "j" });
});

test("nom seul, chemins retirés du message", () => {
  assert.strictEqual(p.nomFichier("C:\\Users\\a\\src\\Program.cs"), "Program.cs");
  assert.strictEqual(p.nomFichier("/home/a/x/app.ts"), "app.ts");
  assert.strictEqual(p.nettoyerMessage("Cannot find module '/home/a/projet/lib/util.ts'\n(ts)"), "Cannot find module 'util.ts' (ts)");
  assert.strictEqual(p.nettoyerMessage("dans C:\\Users\\a\\Foo.cs"), "dans Foo.cs");
  assert.ok(p.nettoyerMessage("x".repeat(400)).length <= 160);
});

test("POST /diagnostics avec le jeton, Pilou absent sans erreur", async () => {
  let recu;
  const serveur = http.createServer((req, res) => {
    let corps = "";
    req.on("data", (c) => (corps += c));
    req.on("end", () => {
      recu = { url: req.url, auth: req.headers.authorization, corps: JSON.parse(corps) };
      res.writeHead(202).end('{"recu":true}');
    });
  });
  await new Promise((r) => serveur.listen(0, "127.0.0.1", r));
  const port = serveur.address().port;
  const r = { source: "vscode", fichier: "a.ts", erreurs: 2, avertissements: 1 };
  assert.strictEqual(await p.envoyer({ port, jeton: "t" }, r), 202);
  assert.deepStrictEqual(recu, { url: "/diagnostics", auth: "Bearer t", corps: r });
  await new Promise((r) => serveur.close(r));
  assert.strictEqual(await p.envoyer({ port, jeton: "t" }, r), 0);
});
