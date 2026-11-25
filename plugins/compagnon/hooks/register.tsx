import { atom, read, update } from 'claude-code'
import type { EngineInterface, Register } from 'claude-code'

import type { Humeur } from '../types'

// Compagnon : une petite créature (Pilou par défaut) dans un widget de l'app de bureau,
// ouvert à la demande, et Pilou de bureau (overlay) par-dessus la fenêtre de Claude.
// Nom, XP, énergie, souvenirs : partagés entre sessions ($.store). Humeur : propre à la session.
// Rien n'est écrit dans la conversation ni transmis à Claude.

const PANE = 'compagnon'
const NOM_DEFAUT = 'Pilou'
const SOMMEIL_MS = 20 * 60_000
const MAX_SOUVENIRS = 6

const humeur = atom({ plugin: 'compagnon', key: 'humeur' } as const, 'repos' as Humeur, { shape: 'humeur-1' })
// Incrémenté à chaque réaction : le dessin repart de zéro pour l'humeur passagère.
const rev = atom({ plugin: 'compagnon', key: 'rev' } as const, 0, { shape: 'rev-1' })
const enTour = atom({ plugin: 'compagnon', key: 'enTour' } as const, false, { shape: 'enTour-1' })
const outil = atom({ plugin: 'compagnon', key: 'outil' } as const, '', { shape: 'outil-1' })
const outilRev = atom({ plugin: 'compagnon', key: 'outilRev' } as const, 0, { shape: 'outilRev-1' })
const inquiet = atom({ plugin: 'compagnon', key: 'inquiet' } as const, false, { shape: 'inquiet-1' })
const ouvert = atom({ plugin: 'compagnon', key: 'ouvert' } as const, false, { shape: 'ouvert-1' })
const nom = atom({ plugin: 'compagnon', key: 'nom' } as const, NOM_DEFAUT, { shape: 'nom-1' })
const xp = atom({ plugin: 'compagnon', key: 'xp' } as const, 0, { shape: 'xp-1' })
const energie = atom({ plugin: 'compagnon', key: 'energie' } as const, 80, { shape: 'energie-1' })
// Statut de la session, publié pour la bulle de Pilou de bureau.
const libelle = atom({ plugin: 'compagnon', key: 'libelle' } as const, '', { shape: 'libelle-1' })
// Titre de la session dans l'app (enregistré dans le transcript, ligne « custom-title »).
const titre = atom({ plugin: 'compagnon', key: 'titre' } as const, '', { shape: 'titre-1' })
const debutTour = atom({ plugin: 'compagnon', key: 'debutTour' } as const, 0, { shape: 'debutTour-1' })
const finTour = atom({ plugin: 'compagnon', key: 'finTour' } as const, 0, { shape: 'finTour-1' })
// '' fini normalement · 'interrompu' · 'erreur'
const finRaison = atom({ plugin: 'compagnon', key: 'finRaison' } as const, '', { shape: 'finRaison-1' })
// '' · 'permission' (demande d'autorisation affichée) · 'question' (AskUserQuestion, ExitPlanMode)
const attente = atom({ plugin: 'compagnon', key: 'attente' } as const, '', { shape: 'attente-1' })
const debutOutil = atom({ plugin: 'compagnon', key: 'debutOutil' } as const, 0, { shape: 'debutOutil-1' })
const QUESTIONS = new Set(['AskUserQuestion', 'ExitPlanMode'])
// Commits et tests au vert de cette session : Pilou de bureau en tire ses quêtes.
const commits = atom({ plugin: 'compagnon', key: 'commits' } as const, 0, { shape: 'commits-1' })
const tests = atom({ plugin: 'compagnon', key: 'tests' } as const, 0, { shape: 'tests-1' })
const souvenirs = atom({ plugin: 'compagnon', key: 'souvenirs' } as const, [] as string[], { shape: 'souvenirs-1' })

const TEST = /\b(dotnet\s+test|npm\s+(run\s+)?test|pytest|jest|vitest|mstest|vstest|cargo\s+test|go\s+test|claude\s+plugin\s+test)\b/i
const COMMIT = /\bgit\b(\s+-\S+(\s+\S+)?)*\s+commit\b/

// Pilou de bureau (overlay WPF) : chaque session publie son état dans ~/.claude/compagnon/,
// l'overlay lit ces fichiers et y dépose ses caresses. ~/.claude, pas AppData : l'app Claude
// (MSIX) virtualise son AppData, que l'overlay ne verrait pas.
let dossierBureau = ''
let idSession = ''
let sale = false
let dossierCourant = ''
const marquer = () => {
  sale = true
}

const niveau = (points: number) => Math.floor(Math.sqrt(points / 5)) + 1
const borne = (n: number) => Math.max(0, Math.min(100, Math.round(n)))

function heure(ms: number) {
  try {
    return new Intl.DateTimeFormat('fr-FR', { hour: '2-digit', minute: '2-digit', hour12: false }).format(
      new Date(ms),
    )
  } catch {
    return new Date(ms).toISOString().slice(11, 16)
  }
}

// Relit le magasin partagé et recopie ce qui a changé (une autre session a pu écrire).
async function synchroniser($: EngineInterface) {
  const [n, x, en, so] = await Promise.all([
    $.store.get('nom'),
    $.store.get('xp'),
    $.store.get('energie'),
    $.store.get('souvenirs'),
  ])
  const nomLu = typeof n === 'string' && n.trim() !== '' ? n : NOM_DEFAUT
  if ((await read($, nom)) !== nomLu) {
    await update($, nom, () => nomLu)
    marquer()
  }
  if (typeof x === 'number' && (await read($, xp)) !== x) {
    await update($, xp, () => x)
    marquer()
  }
  if (typeof en === 'number' && (await read($, energie)) !== en) await update($, energie, () => en)
  if (Array.isArray(so)) {
    const liste = so.filter((s): s is string => typeof s === 'string').slice(0, MAX_SOUVENIRS)
    if ((await read($, souvenirs)).join('\n') !== liste.join('\n')) await update($, souvenirs, () => liste)
  }
}

// Gain d'XP / d'énergie et souvenir, écrits dans le magasin partagé puis recopiés ici.
async function vivre($: EngineInterface, gain: { xp?: number; energie?: number; souvenir?: string }) {
  await synchroniser($)
  if (gain.xp) {
    const v = (await read($, xp)) + gain.xp
    await $.store.set('xp', v)
    await update($, xp, () => v)
  }
  if (gain.energie) {
    const v = borne((await read($, energie)) + gain.energie)
    await $.store.set('energie', v)
    await update($, energie, () => v)
    marquer()
  }
  if (gain.souvenir) {
    const ligne = `${heure(await $.clock.now())} ${gain.souvenir}`
    const v = [ligne, ...(await read($, souvenirs))].slice(0, MAX_SOUVENIRS)
    await $.store.set('souvenirs', v)
    await update($, souvenirs, () => v)
  }
}

// Le compagnon ne doit jamais gêner : toute réaction qui échoue est ignorée.
async function discret(travail: () => Promise<unknown>) {
  try {
    await travail()
  } catch {
    // rien : une réaction perdue vaut mieux qu'un outil bloqué
  }
}

async function reagir($: EngineInterface, h: Humeur) {
  await update($, humeur, () => h)
  await update($, rev, n => n + 1)
  marquer()
}

async function publier($: EngineInterface) {
  if (dossierBureau === '' || !sale) return
  sale = false
  const etat = {
    v: 3,
    source: 'claude',
    session: idSession,
    t: await $.clock.now(),
    ...(await propsCreature($)),
    libelle: (await read($, titre)) || (await read($, libelle)) || dossierCourant,
    debutTour: await read($, debutTour),
    finTour: await read($, finTour),
    finRaison: await read($, finRaison),
    attente: await read($, attente),
    debutOutil: await read($, debutOutil),
    xp: await read($, xp),
    commits: await read($, commits),
    tests: await read($, tests),
    bureau: (await $.store.get('bureau')) !== false,
  }
  await $.fs.write(`${dossierBureau}/etat-${idSession}.json`, JSON.stringify(etat))
}

// Caresses données sur le Pilou de bureau : un compteur dans un fichier. Une seule session
// la compte : chacune pose son jeton dans le magasin partagé, relit un instant plus tard,
// et seule celle dont le jeton est resté agit.
async function caressesBureau($: EngineInterface) {
  if (dossierBureau === '') return
  const chemin = `${dossierBureau}/caresses.txt`
  if (!(await $.fs.exists(chemin))) return
  const n = Number.parseInt(String(await $.fs.read(chemin)).trim(), 10)
  const vues = await $.store.get('caressesVues')
  if (!Number.isFinite(n) || n === vues) return
  await $.store.set('caressesVues', n)
  await $.store.set('caressesJeton', `${idSession}:${n}`)
  await $.clock.sleep(600)
  if ((await $.store.get('caressesJeton')) !== `${idSession}:${n}`) return
  if (typeof vues === 'number' && n > vues) await caresser($)
}

// XP gagnée aux petits jeux de Pilou de bureau : total cumulé dans bonus.txt. Même jeton
// que les caresses, pour qu'une seule session la crédite.
async function bonusBureau($: EngineInterface) {
  if (dossierBureau === '') return
  const chemin = `${dossierBureau}/bonus.txt`
  if (!(await $.fs.exists(chemin))) return
  const n = Number.parseInt(String(await $.fs.read(chemin)).trim(), 10)
  const lu = await $.store.get('bonusVus')
  const vus = typeof lu === 'number' ? lu : 0
  if (!Number.isFinite(n) || n <= vus) return
  await $.store.set('bonusVus', n)
  await $.store.set('bonusJeton', `${idSession}:${n}`)
  await $.clock.sleep(600)
  if ((await $.store.get('bonusJeton')) !== `${idSession}:${n}`) return
  await vivre($, { xp: n - vus, souvenir: `+${n - vus} xp en jouant` })
  await reagir($, 'fete')
}

// Dernier titre donné à la session : lu à la fin du transcript (256 Ko suffisent, il y est réécrit souvent).
async function lireTitre($: EngineInterface) {
  const chemin = (await $.session.info()).transcriptPath
  if (!chemin) return
  const { size } = await $.fs.stat(chemin)
  const offset = Math.max(0, size - 262_144)
  const bout = String(await $.fs.read(chemin, { offset, length: size - offset }))
  const trouves = [...bout.matchAll(/"customTitle":("(?:[^"\\]|\\.)*")/g)]
  const dernier = trouves[trouves.length - 1]
  if (!dernier) return
  const lu = JSON.parse(dernier[1]!) as unknown
  if (typeof lu !== 'string' || lu.trim() === '') return
  const court = lu.trim().length > 40 ? `${lu.trim().slice(0, 39)}…` : lu.trim()
  if ((await read($, titre)) !== court) {
    await update($, titre, () => court)
    marquer()
  }
}

async function lancerBureau($: EngineInterface) {
  if (dossierBureau === '' || (await $.store.get('bureau')) === false) return
  const exe = `${dossierBureau}/bureau/PilouBureau.exe`
  if (!(await $.fs.exists(exe))) return
  // explorer rend la main tout de suite ; l'overlay est à instance unique.
  await $.process.run(['explorer.exe', exe.split('/').join('\\')], { timeoutMs: 10_000 })
}

async function renommer($: EngineInterface, nouveau: string) {
  const propre = nouveau.trim().slice(0, 24)
  if (propre === '') return
  await $.store.set('nom', propre)
  await update($, nom, () => propre)
  await vivre($, { souvenir: `s'appelle désormais ${propre}` })
  await reagir($, 'fete')
  if (await read($, ouvert)) await $.ui.open({ id: PANE, title: propre })
}

async function ouvrir($: EngineInterface) {
  await $.store.set('visible', true)
  const r = await $.ui.open({ id: PANE, title: await read($, nom), placement: 'widget' })
  await update($, ouvert, () => r.isPlaced)
}

async function cacher($: EngineInterface) {
  await $.store.set('visible', false)
  await $.ui.close({ id: PANE })
  await update($, ouvert, () => false)
}

async function caresser($: EngineInterface) {
  const reveil = (await read($, humeur)) === 'dort'
  dernierMessage = await $.clock.now()
  await reagir($, 'caresse')
  await vivre($, { xp: 1, energie: reveil ? 10 : 3, souvenir: reveil ? 'réveillé par une caresse' : undefined })
}

// Dernier message de la personne (horloge du moteur) : au-delà de 20 min, la créature somnole.
let dernierMessage = 0
let appels = 0

async function propsCreature($: EngineInterface) {
  return {
    humeur: await read($, humeur),
    rev: await read($, rev),
    enTour: await read($, enTour),
    outil: await read($, outil),
    outilRev: await read($, outilRev),
    inquiet: await read($, inquiet),
    fatigue: (await read($, energie)) < 25,
    nom: await read($, nom),
    niveau: niveau(await read($, xp)),
  }
}

// Un message qui dit de quoi parle la session : au moins 3 mots et 15 caractères, pas une commande.
export const parlant = (texte: string) =>
  texte.length >= 15 && texte.split(' ').filter(m => m !== '').length >= 3 && !texte.startsWith('/')

const jauge = (v: number, n = 10) => '▰'.repeat(Math.round((v / 100) * n)) + '▱'.repeat(n - Math.round((v / 100) * n))

export const register: Register = on => {
  on('session.start', async ($, e, next) => {
    const r = await next(e)
    dossierCourant = e.cwd.split(/[\\/]/).filter(x => x !== '').pop() ?? ''
    await $.command.register({ name: 'compagnon', description: 'Ouvrir / fermer le compagnon · /compagnon nom <x> pour le renommer' })
    dernierMessage = await $.clock.now()
    await synchroniser($)
    // Le widget s'ouvre à la demande (/compagnon) ; Pilou de bureau est l'affichage par défaut.
    if ((await $.store.get('visible')) === true) await ouvrir($)
    await discret(async () => {
      const home = (await $.env.get('USERPROFILE')) ?? (await $.env.get('HOME'))
      if (home === undefined) return
      dossierBureau = `${home.split('\\').join('/')}/.claude/compagnon`
      idSession = (await $.session.id()).slice(0, 8)
      // Rechargé en plein tour : pas d'heure de début connue, on prend maintenant.
      if ((await read($, enTour)) && (await read($, debutTour)) === 0) {
        const maintenant = await $.clock.now()
        await update($, debutTour, () => maintenant)
      }
      await discret(() => lireTitre($))
      marquer()
      await publier($)
      void discret(() => lancerBureau($))
    })
    $.clock.every(400, () => discret(() => publier($)))
    // Sommeil et récupération : une vérification toutes les 30 s ; resynchro du magasin toutes les 5 s.
    $.clock.every(30_000, async () => {
      const maintenant = await $.clock.now()
      marquer()
      await discret(() => lireTitre($))
      const h = await read($, humeur)
      if (h !== 'dort' && !(await read($, enTour)) && maintenant - dernierMessage >= SOMMEIL_MS) {
        await reagir($, 'dort')
        await vivre($, { souvenir: 's’est endormi' })
      } else if (h === 'dort' && maintenant % 120_000 < 30_000) {
        await vivre($, { energie: 2 })
      }
    })
    $.clock.every(5000, () =>
      discret(async () => {
        await synchroniser($)
        await caressesBureau($)
        await bonusBureau($)
      }),
    )
    return r
  })

  on('session.attach', async ($, e, next) => {
    const r = await next(e)
    if (!(await read($, ouvert)) && (await $.store.get('visible')) === true) await ouvrir($)
    return r
  })

  on('command.run', { command: 'compagnon' }, async ($, e) => {
    const args = e.args.trim()
    const m = /^nom\s+(.+)$/i.exec(args)
    if (m) {
      await renommer($, m[1]!)
      return { text: `Le compagnon s'appelle désormais ${await read($, nom)}.`, isTextDisplayOnly: true as const }
    }
    if (/^bureau$/i.test(args)) {
      const actif = (await $.store.get('bureau')) === false
      await $.store.set('bureau', actif)
      marquer()
      await publier($)
      if (actif) await lancerBureau($)
      return {
        text: actif ? `${await read($, nom)} se promène sur le bureau.` : `${await read($, nom)} quitte le bureau (reste le widget).`,
        isTextDisplayOnly: true as const,
      }
    }
    if (args !== '')
      return { text: 'Usage : /compagnon (widget) · /compagnon bureau (overlay) · /compagnon nom <x>', isTextDisplayOnly: true as const }
    if (await read($, ouvert)) {
      await cacher($)
      return { text: `${await read($, nom)} se cache (clic droit ou /compagnon pour le rappeler).`, isTextDisplayOnly: true as const }
    }
    await ouvrir($)
    return { text: `${await read($, nom)} est là.`, isTextDisplayOnly: true as const }
  })

  on('prompt.submit', async ($, e, next) => {
    await discret(async () => {
      dernierMessage = await $.clock.now()
      // Libellé de secours (sans titre d'app) : un premier message parlant, pas « oui » ou « continue ».
      if ((await read($, libelle)) === '') {
        const court = e.text.replace(/\s+/g, ' ').trim()
        if (parlant(court)) await update($, libelle, () => (court.length > 34 ? `${court.slice(0, 33)}…` : court))
      }
      if ((await read($, humeur)) === 'dort') {
        await reagir($, 'soulage')
        await vivre($, { energie: 5, souvenir: 'réveillé par un message' })
      }
    })
    return next(e)
  })

  on('turn.start', async ($, e, next) => {
    await discret(async () => {
      await update($, enTour, () => true)
      const maintenant = await $.clock.now()
      await update($, debutTour, () => maintenant)
      await update($, attente, () => '')
      marquer()
    })
    return next(e)
  })

  // Demande d'autorisation affichée : Claude attend la personne.
  on('classic.Notification', async ($, e, next) => {
    await discret(async () => {
      if (e.notification_type === 'permission_prompt') {
        await update($, attente, () => 'permission')
        marquer()
      }
    })
    return next(e)
  })

  // L'outil s'exécute pour de bon : l'autorisation, s'il en fallait une, est donnée.
  on('tool.run', async ($, e, next) => {
    await discret(async () => {
      if ((await read($, attente)) === 'permission') {
        await update($, attente, () => '')
        marquer()
      }
    })
    return next(e)
  })

  on('turn.complete', async ($, e, next) => {
    const r = await next(e)
    if (e.agentId !== undefined) return r
    await update($, enTour, () => false)
    await update($, outil, () => '')
    await update($, attente, () => '')
    const fin = await $.clock.now()
    await update($, finTour, () => fin)
    await update($, finRaison, () => (e.isAborted ? 'interrompu' : 'reason' in e && e.reason === 'error' ? 'erreur' : ''))
    marquer()
    // Une grimace ou une fête en cours a la priorité sur le soulagement.
    const h = await read($, humeur)
    if (h !== 'grimace' && h !== 'fete') await reagir($, 'soulage')
    await vivre($, { xp: 1, energie: -1 })
    return r
  })

  on('tool.call', async ($, e, next) => {
    await discret(async () => {
      await update($, outil, () => e.tool)
      await update($, outilRev, n => n + 1)
      const debut = await $.clock.now()
      await update($, debutOutil, () => debut)
      if (QUESTIONS.has(e.tool)) await update($, attente, () => 'question')
      marquer()
    })
    const r = await next(e)
    await discret(async () => {
      await update($, outil, () => '')
      if ((await read($, attente)) !== '') await update($, attente, () => '')
      marquer()
      if (r.isError) {
        await reagir($, 'grimace')
        await vivre($, { souvenir: `grimace : ${e.tool} en erreur` })
      } else if (r.deny === undefined && e.tool === 'Bash') {
        const cmd = e.command
        if (COMMIT.test(cmd)) {
          await update($, commits, n => n + 1)
          await reagir($, 'fete')
          await vivre($, { xp: 5, energie: 4, souvenir: 'a fêté un commit' })
        } else if (TEST.test(cmd)) {
          await update($, tests, n => n + 1)
          await reagir($, 'fete')
          await vivre($, { xp: 2, souvenir: 'tests au vert' })
        }
      }
      appels += 1
      if (appels % 6 === 0) await vivre($, { energie: -1 })
    })
    return r
  })

  on('session.measure', async ($, e, next) => {
    const r = await next(e)
    const v = e.rateLimits.some(l => l.percentUsed >= 85)
    if ((await read($, inquiet)) !== v) {
      await update($, inquiet, () => v)
      marquer()
    }
    return r
  })

  on('ui.message', async ($, e, next) => {
    if (!String(e.module).endsWith('creature.tsx')) return next(e)
    const d = e.data as { type?: unknown } | null
    if (d?.type === 'caresse') await caresser($)
    return {}
  })

  on('ui.close', async ($, e, next) => {
    const r = await next(e)
    if (e.id === PANE) {
      await discret(async () => {
        await update($, ouvert, () => false)
        if (e.origin.kind === 'person') await $.store.set('visible', false)
      })
    }
    return r
  })

  // Le widget (ou le panneau déplié).
  on('ui.render', { component: 'Pane', requestId: PANE }, async ($, e) => {
    const table = $.ui.resolve(e)
    const { Box, Text, Button, Input } = table
    const Client = 'Client' in table ? table.Client : undefined
    const p = await propsCreature($)
    const widget = e.props.placement === 'widget'
    const bords = e.props.anchoredEdges ?? []
    const creature = Client ? (
      <Client
        key="pilou"
        module="./creature.tsx"
        props={{ ...p, taille: widget ? 'widget' : 'grand', droite: bords.includes('right'), bas: bords.includes('bottom') }}
        width="100%"
      />
    ) : (
      <Text color="#6cb6ff" bold>{`▐● ◡ ●▌ ${p.nom}`}</Text>
    )
    if (widget) return <Box flexDirection="column">{creature}</Box>

    const points = await read($, xp)
    const n = niveau(points)
    const plancher = 5 * (n - 1) ** 2
    const plafond = 5 * n ** 2
    const progression = ((points - plancher) / Math.max(1, plafond - plancher)) * 100
    const en = await read($, energie)
    const liste = await read($, souvenirs)
    return (
      <Box flexDirection="column" rowGap={1}>
        {creature}
        <Box flexDirection="column">
          <Text>
            <Text color="#6cb6ff" bold>{`niv ${n}  `}</Text>
            <Text color="#6cb6ff">{jauge(progression)}</Text>
            <Text dimColor>{`  ${points} xp`}</Text>
          </Text>
          <Text>
            <Text color="#f69d50" bold>{'énergie '}</Text>
            <Text color="#f69d50">{jauge(en)}</Text>
            <Text dimColor>{`  ${en} %`}</Text>
          </Text>
        </Box>
        {liste.length > 0 && (
          <Box flexDirection="column">
            <Text dimColor>souvenirs</Text>
            {liste.map(s => (
              <Text dimColor>{`  ${s}`}</Text>
            ))}
          </Box>
        )}
        <Box flexDirection="row" columnGap={1}>
          <Button key="caresser" onPress={() => void caresser($)}>♥ Caresser</Button>
          <Button key="cacher" plain dimColor onPress={() => void cacher($)}>Cacher</Button>
        </Box>
        <Input key="nom" placeholder={`Renommer ${p.nom} (Entrée)`} submitLabel="renommer" onSubmit={t => void renommer($, t)} />
      </Box>
    )
  })

  // Clic droit : cacher / montrer, renommer.
  on('ui.render', { component: 'ContextMenu' }, async ($, e, next) => {
    if (e.props.link !== undefined || e.props.selection !== undefined || e.props.code !== undefined) return next(e)
    const { Box, Button } = $.ui.resolve(e)
    const n = await read($, nom)
    const visible = await read($, ouvert)
    return (
      <Box flexDirection="column">
        {visible ? (
          <Button key="compagnon-cacher" onPress={() => void cacher($)}>{`✦ Cacher ${n}`}</Button>
        ) : (
          <Button key="compagnon-montrer" onPress={() => void ouvrir($)}>{`✦ Montrer ${n}`}</Button>
        )}
        <Button key="compagnon-renommer" onPress={() => void $.prompt.fill({ text: '/compagnon nom ', mode: 'replace' })}>
          {`✦ Renommer ${n}`}
        </Button>
      </Box>
    )
  })
}
