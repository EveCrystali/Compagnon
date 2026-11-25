import { expect, mock, test } from 'claude-code/testing'
import type { On } from 'claude-code'

const PANE = {
  plugin: 'compagnon',
  component: 'Pane',
  requestId: 'compagnon',
  props: {
    title: 'Pilou',
    isFocused: false,
    bodyColumns: 24,
    placement: 'widget',
    anchoredEdges: ['bottom', 'right'],
    scroll: { offset: 0, bodyRows: 12 },
    view: {},
  },
} as const

type PropsCreature = { humeur?: string; nom?: string; niveau?: number; taille?: string; droite?: boolean }

// Le moteur sous le mod : horloge et magasin en mémoire, ouverture de panneau acceptée.
function moteur(on: On, depart: Record<string, unknown> = {}) {
  const horloge = mock.clock(on, { now: 1_795_000_000_000 })
  const magasin: Record<string, unknown> = { ...depart }
  on('store.get', (_, e) => ({ value: magasin[e.key] }))
  on('store.set', (_, e) => {
    magasin[e.key] = e.value
    return { value: undefined }
  })
  const ouvertures: unknown[] = []
  on('command.register', () => ({ value: { command: 'compagnon' } }))
  on('ui.open', (_, e) => {
    ouvertures.push(e)
    return { value: { isPlaced: true } }
  })
  on('ui.close', () => ({ value: undefined }))
  on('session.start', (_, e) => ({ cwd: e.cwd }))
  return { horloge, magasin, ouvertures }
}

async function creature(ui: { find: (q: { type: string }) => Promise<{ props?: Record<string, unknown> } | undefined> }) {
  const c = await ui.find({ type: 'Client' })
  return c?.props?.props as PropsCreature | undefined
}

test('le widget dessine la créature, au repos, ancrée à droite', async ($, on) => {
  const { ouvertures } = moteur(on, { visible: true })
  await $.session.start({ cwd: '/', surface: 'desktop', isInteractive: true })
  expect(ouvertures).toHaveLength(1)
  expect(ouvertures[0]).toMatchObject({ id: 'compagnon', placement: 'widget' })

  const ui = await $.ui.mount({ ...PANE, surface: 'desktop' })
  const p = await creature(ui)
  expect(p).toMatchObject({ humeur: 'repos', nom: 'Pilou', niveau: 1, taille: 'widget', droite: true })
  // L'animation tourne sans démonter le module.
  await ui.advance(3000)
  expect(await ui.find({ type: 'Client' })).toBeDefined()
  await ui.unmount()

  // Déplié (dock) : jauges et boutons en plus de la créature.
  const grand = await $.ui.mount({ ...PANE, surface: 'desktop', props: { ...PANE.props, placement: 'dock', anchoredEdges: undefined } })
  expect((await creature(grand))?.taille).toBe('grand')
  expect(await grand.find({ type: 'Button', key: 'caresser' })).toBeDefined()
  await grand.unmount()
})

test("un outil en erreur le fait grimacer, un commit réussi le fait fêter", async ($, on) => {
  moteur(on)
  let echec = true
  on('tool.call', () => (echec ? { isError: true, result: 'boom', text: 'boom' } : { result: {} }))
  await $.session.start({ cwd: '/', surface: 'desktop', isInteractive: true })

  await $.tool.call({ tool: 'Bash', command: 'dotnet test' })
  let ui = await $.ui.mount({ ...PANE, surface: 'desktop' })
  expect((await creature(ui))?.humeur).toBe('grimace')
  await ui.unmount()

  echec = false
  await $.tool.call({ tool: 'Bash', command: 'git commit -m "feat: x"' })
  ui = await $.ui.mount({ ...PANE, surface: 'desktop' })
  expect((await creature(ui))?.humeur).toBe('fete')
  await ui.unmount()
})

test('sans message depuis 20 min il somnole, une caresse le réveille', async ($, on) => {
  const { horloge } = moteur(on)
  await $.session.start({ cwd: '/', surface: 'desktop', isInteractive: true })

  await horloge.advance(10 * 60_000)
  let ui = await $.ui.mount({ ...PANE, surface: 'desktop' })
  expect((await creature(ui))?.humeur).toBe('repos')
  await ui.unmount()

  await horloge.advance(11 * 60_000)
  ui = await $.ui.mount({ ...PANE, surface: 'desktop' })
  expect((await creature(ui))?.humeur).toBe('dort')

  await ui.post({ type: 'caresse' })
  expect((await creature(ui))?.humeur).toBe('caresse')
  await ui.unmount()
})

test('le nom vient du magasin partagé et /compagnon nom le change', async ($, on) => {
  const { magasin } = moteur(on, { nom: 'Brindille', xp: 45 })
  await $.session.start({ cwd: '/', surface: 'desktop', isInteractive: true })

  let ui = await $.ui.mount({ ...PANE, surface: 'desktop' })
  expect(await creature(ui)).toMatchObject({ nom: 'Brindille', niveau: 4 })
  await ui.unmount()

  await $.command.run({
    command: 'compagnon',
    args: 'nom Zéphyr',
    origin: { kind: 'composer' },
    presentation: { isFullscreen: false, columns: 100 },
  })
  expect(magasin.nom).toBe('Zéphyr')
  ui = await $.ui.mount({ ...PANE, surface: 'desktop' })
  expect((await creature(ui))?.nom).toBe('Zéphyr')
  await ui.unmount()
})

test("l'état est publié pour Pilou de bureau, une grimace comprise", async ($, on) => {
  const { horloge } = moteur(on)
  mock.env(on, { USERPROFILE: 'C:\\Users\\essai' })
  on('session.id', () => ({ value: 'abcdef1234' }))
  on('fs.exists', () => ({ value: false }))
  const ecrits: Record<string, string> = {}
  on('fs.write', (_, e) => {
    ecrits[e.path] = e.text
    return { value: undefined }
  })
  on('tool.call', () => ({ isError: true, result: 'boom', text: 'boom' }))
  on('classic.Notification', () => ({}))
  // Le titre de l'app est relu à la fin du transcript.
  const lignes = [{ type: 'custom-title', customTitle: 'Ancien titre' }, { type: 'custom-title', customTitle: 'Mod "compagnon" animé' }]
  const transcript = lignes.map(l => JSON.stringify(l)).join(String.fromCharCode(10))
  on('session.info', () => ({ value: { transcriptPath: 'C:/t.jsonl' } as never }))
  on('fs.stat', () => ({ value: { kind: 'file', size: transcript.length, mtimeMs: 0, isLink: false } }))
  on('fs.read', () => ({ value: transcript }))
  await $.session.start({ cwd: '/', surface: 'desktop', isInteractive: true })
  // Le moteur rend le chemin à sa façon (antislashs sous Windows, résolu ailleurs) : on cherche le fichier par son nom.
  const chemin = Object.keys(ecrits).find(k => /[\\/]\.claude[\\/]compagnon[\\/]etat-abcdef12\.json$/.test(k)) ?? ''
  expect(JSON.parse(ecrits[chemin] ?? '{}')).toMatchObject({ session: 'abcdef12', source: 'claude', humeur: 'repos', bureau: true })

  await $.tool.call({ tool: 'Bash', command: 'dotnet test' })
  await horloge.advance(500)
  expect(JSON.parse(ecrits[chemin] ?? '{}')).toMatchObject({ humeur: 'grimace', nom: 'Pilou', libelle: 'Mod "compagnon" animé' })

  // Une demande d'autorisation : la bulle dira « attend ta permission ».
  await $.classic.Notification({ message: 'Claude needs your permission', notification_type: 'permission_prompt' })
  await horloge.advance(500)
  expect(JSON.parse(ecrits[chemin] ?? '{}')).toMatchObject({ attente: 'permission' })
})

test("le widget ne s'ouvre pas d'office, et rien au-dessus de la saisie", async ($, on) => {
  const { ouvertures } = moteur(on)
  await $.session.start({ cwd: '/', surface: 'desktop', isInteractive: true })
  expect(ouvertures).toHaveLength(0)
  const ui = await $.ui.mount({ plugin: 'compagnon', component: 'AbovePrompt', surface: 'desktop', props: {} as never })
  expect(await ui.find({ type: 'Client' })).toBeUndefined()
  await ui.unmount()
})

test('une caresse sur Pilou de bureau est comptée une fois', async ($, on) => {
  const { horloge, magasin } = moteur(on, { visible: true, xp: 0 })
  mock.env(on, { USERPROFILE: 'C:\\Users\\essai' })
  on('session.id', () => ({ value: 'abcdef1234' }))
  let compteur = '1'
  on('fs.exists', (_, e) => ({ value: e.path.endsWith('caresses.txt') }))
  on('fs.read', () => ({ value: compteur }))
  on('fs.write', () => ({ value: undefined }))
  await $.session.start({ cwd: '/', surface: 'desktop', isInteractive: true })

  // Premier passage : le compteur sert de point de départ, pas de caresse.
  await horloge.advance(5700)
  expect(magasin.caressesVues).toBe(1)
  expect(magasin.xp).toBe(0)

  compteur = '2'
  await horloge.advance(5700)
  expect(magasin.xp).toBe(1)
  const ui = await $.ui.mount({ ...PANE, surface: 'desktop' })
  expect((await creature(ui))?.humeur).toBe('caresse')
  await ui.unmount()

  // Rien de neuf : pas de nouvelle caresse.
  await horloge.advance(5700)
  expect(magasin.xp).toBe(1)
})

test("l'XP des petits jeux de bureau est créditée une fois", async ($, on) => {
  const { horloge, magasin } = moteur(on, { xp: 3 })
  mock.env(on, { USERPROFILE: 'C:\\Users\\essai' })
  on('session.id', () => ({ value: 'abcdef1234' }))
  let total = '10'
  on('fs.exists', (_, e) => ({ value: e.path.endsWith('bonus.txt') }))
  on('fs.read', () => ({ value: total }))
  on('fs.write', () => ({ value: undefined }))
  await $.session.start({ cwd: '/', surface: 'desktop', isInteractive: true })

  await horloge.advance(5700)
  expect(magasin.xp).toBe(13)
  total = '25'
  await horloge.advance(5700)
  expect(magasin.xp).toBe(28)
  await horloge.advance(5700)
  expect(magasin.xp).toBe(28)
})
