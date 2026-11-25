import type { ClientModule, ClientPointerEvent } from 'claude-code'

// Pilou : une goutte d'encre bleue à antenne, dont l'étincelle orange dit ce qu'il fait.
// Dessiné en demi-blocs (deux « pixels » par cellule), animé sur l'horloge de la surface.
// Chaque humeur porte un signe de forme (yeux, bouche, étincelle, effet), pas seulement une couleur.

type Expr = 'repos' | 'concentre' | 'attente' | 'grimace' | 'fete' | 'soulage' | 'dort' | 'inquiet' | 'caresse'
type Props = {
  taille: 'widget' | 'grand' | 'mini'
  humeur: string
  rev: number
  enTour: boolean
  outil: string
  outilRev: number
  inquiet: boolean
  fatigue: boolean
  nom: string
  niveau: number
  droite?: boolean
  bas?: boolean
}
type Idle = '' | 'saut' | 'clin' | 'antenne'
type Etat = {
  t: number
  rev: number
  tRev: number
  outilRev: number
  tOutil: number
  cligneFin: number
  clignePlus: number
  regard: number
  regardPlus: number
  idle: Idle
  idleDebut: number
  idlePlus: number
  caresse: number
}
type Cellule = { ch: string; fg?: string; bg?: string; bold?: boolean; dim?: boolean }

// Palette deutéranopie : bleus, orange, neutres. Lisible sur fond sombre et clair.
const BLEU = { base: '#6cb6ff', clair: '#b4dbff', ombre: '#4a8fdc' }
const ORANGE = { base: '#f69d50', clair: '#ffc89a', ombre: '#d9803a' }
const ENCRE = '#1c2128'
const GRIS = '#768390'
const BRUME = '#adbac7'
const ETINCELLE = '#f69d50'
// Nom : un bleu un peu plus soutenu, lisible aussi sur fond clair.
const NOM = '#539bf5'

const W = 18
const H = 10
const DUREES: Partial<Record<string, number>> = { grimace: 2600, fete: 3200, soulage: 2400, caresse: 2400 }
const ROUE = ['◐', '◓', '◑', '◒']

// Yeux gauche, droit, bouche.
const VISAGES: Record<Expr, [string, string, string]> = {
  repos: ['●', '●', '◡'],
  concentre: ['◉', '◉', '─'],
  attente: ['•', '•', 'o'],
  grimace: ['>', '<', '≈'],
  fete: ['^', '^', '▽'],
  soulage: ['◠', '◠', '◡'],
  dort: ['─', '─', 'o'],
  inquiet: ['○', '○', '~'],
  caresse: ['◠', '◠', 'ω'],
}
const MOTS: Record<Expr, string> = {
  repos: 'tranquille',
  concentre: 'réfléchit',
  attente: 'patiente…',
  grimace: 'aïe !',
  fete: 'youpi !',
  soulage: 'ouf',
  dort: 'zzz',
  inquiet: 'quota !',
  caresse: '♥',
}

const hasard = (a: number, b: number) => a + Math.random() * (b - a)

function expression(p: Props, s: Etat): Expr {
  if (s.t - s.caresse < 2400) return 'caresse'
  if (p.humeur === 'dort') return 'dort'
  const duree = DUREES[p.humeur]
  if (duree !== undefined && s.t - s.tRev < duree) return p.humeur as Expr
  if (p.outil !== '' && s.t - s.tOutil > 6000) return 'attente'
  if (p.enTour) return 'concentre'
  if (p.inquiet) return 'inquiet'
  return 'repos'
}

function etincelle(x: Expr, t: number): Cellule {
  const c = (ch: string): Cellule => ({ ch, fg: ETINCELLE, bold: true })
  switch (x) {
    case 'concentre':
      return c(ROUE[Math.floor(t / 150) % 4]!)
    case 'attente':
      return c(ROUE[Math.floor(t / 400) % 4]!)
    case 'grimace':
      return c('✕')
    case 'fete':
      return c(['★', '✦', '✧'][Math.floor(t / 120) % 3]!)
    case 'soulage':
      return c('✧')
    case 'dort':
      return { ch: '·', fg: GRIS }
    case 'inquiet':
      return Math.floor(t / 300) % 2 === 0 ? c('!') : { ch: ' ' }
    case 'caresse':
      return c('♥')
    default:
      return c(Math.floor(t / 900) % 2 === 0 ? '✦' : '✧')
  }
}

function yeux(x: Expr, p: Props, s: Etat): [string, string, string] {
  let [g, d, b] = VISAGES[x]
  const cligne = s.t < s.cligneFin && (x === 'repos' || x === 'inquiet' || x === 'concentre' || x === 'attente')
  if (x === 'repos' && p.fatigue) [g, d] = ['▄', '▄']
  if (cligne) [g, d] = ['─', '─']
  if (x === 'repos' && s.idle === 'clin' && s.t - s.idleDebut < 500) d = '─'
  return [g, d, b]
}

// La créature en grille de cellules W × H.
function sprite(x: Expr, p: Props, s: Etat): Cellule[][] {
  const g: Cellule[][] = Array.from({ length: H }, () => Array.from({ length: W }, () => ({ ch: ' ' })))
  const poser = (cx: number, cy: number, c: Cellule) => {
    if (cx >= 0 && cx < W && cy >= 0 && cy < H) g[cy]![cx] = c
  }
  const libre = (cx: number, cy: number) => cx >= 0 && cx < W && cy >= 0 && cy < H && g[cy]![cx]!.ch === ' '
  const t = s.t
  const depuis = t - s.tRev
  const teinte = x === 'inquiet' ? ORANGE : BLEU

  // Respiration (étirement), saut de fête, petit saut d'ennui, tremblement de grimace.
  const periode = x === 'dort' ? 4200 : x === 'concentre' || x === 'attente' ? 1600 : 2600
  const b = Math.sin((2 * Math.PI * t) / periode)
  let rx = 6.2 - 0.2 * b
  let ry = 5.1 + 0.3 * b
  let saut = 0
  let dx = 0
  if (x === 'fete') saut = Math.abs(Math.sin((Math.PI * depuis) / 450)) * 3
  if (x === 'caresse') {
    rx += 0.4
    ry -= 0.4
  }
  if (x === 'repos' && s.idle === 'saut' && t - s.idleDebut < 600) saut = Math.sin((Math.PI * (t - s.idleDebut)) / 600) * 1.6
  if (x === 'grimace' && depuis < 900) dx = Math.floor(t / 100) % 2 === 0 ? 0.8 : -0.8
  const sol = 16.6 - saut
  const cx = 8.5 + dx
  const cy = sol - ry
  const ex = Math.round(cx - 0.5)

  // Pixels : couleur ou rien. Reflet en haut à gauche, ombre en bas.
  const pixel = (px: number, py: number): string | undefined => {
    const u = (px + 0.5 - cx) / rx
    const v = (py + 0.5 - cy) / ry
    if (u * u + v * v <= 1) {
      if (u < -0.3 && v < -0.35 && u * u + v * v > 0.5) return teinte.clair
      if (v > 0.62) return teinte.ombre
      return teinte.base
    }
    const pied = Math.round(sol)
    if (py === pied && [ex - 3, ex - 2, ex + 2, ex + 3].includes(px)) return teinte.ombre
    return undefined
  }
  for (let r = 0; r < H; r++) {
    for (let c = 0; c < W; c++) {
      const haut = pixel(c, 2 * r)
      const bas = pixel(c, 2 * r + 1)
      if (haut && bas) g[r]![c] = haut === bas ? { ch: '█', fg: haut } : { ch: '▀', fg: haut, bg: bas }
      else if (haut) g[r]![c] = { ch: '▀', fg: haut }
      else if (bas) g[r]![c] = { ch: '▄', fg: bas }
    }
  }

  // Ombre portée : rétrécit quand il saute.
  const k = Math.round(saut)
  for (let c = ex - 4 + k; c <= ex + 4 - k; c++) if (libre(c, H - 1)) poser(c, H - 1, { ch: '▀', fg: GRIS, dim: true })

  // Visage, qui suit le regard.
  const ey = Math.floor((cy - 1.6) / 2)
  const regard = x === 'attente' ? Math.round(Math.sin(t / 700)) : x === 'repos' || x === 'inquiet' ? s.regard : 0
  const [og, od, bouche] = yeux(x, p, s)
  const face = (ch: string): Cellule => ({ ch, fg: ENCRE, bg: teinte.base, bold: true })
  poser(ex - 2 + regard, ey, face(og))
  poser(ex + 2 + regard, ey, face(od))
  poser(ex + regard, ey + 1, face(bouche))
  if (x === 'caresse' || x === 'fete') {
    poser(ex - 3 + regard, ey + 1, { ch: '▀', fg: ORANGE.clair, bg: teinte.base })
    poser(ex + 3 + regard, ey + 1, { ch: '▀', fg: ORANGE.clair, bg: teinte.base })
  }

  // Antenne : tige qui se balance, étincelle au bout.
  const sommet = Math.floor((cy - ry + 0.5) / 2)
  const vitesse = s.idle === 'antenne' && t - s.idleDebut < 1500 ? 110 : x === 'concentre' ? 300 : 650
  const balance = x === 'dort' ? 0 : Math.round(Math.sin(t / vitesse) * 0.9)
  poser(ex, sommet - 1, { ch: balance === 0 ? '│' : balance > 0 ? '╱' : '╲', fg: teinte.ombre })
  poser(ex + balance, sommet - 2, etincelle(x, t))

  // Effets autour, dans les cases libres seulement.
  const effet = (c: number, r: number, cel: Cellule) => {
    if (libre(c, r)) poser(c, r, cel)
  }
  if (x === 'dort') {
    const n = Math.floor(t / 700) % 4
    const zz: [number, number, string][] = [[13, 2, 'z'], [14, 1, 'z'], [15, 0, 'Z']]
    zz.slice(0, n).forEach(([c, r, ch]) => effet(c, r, { ch, fg: BRUME, bold: ch === 'Z' }))
  }
  if (x === 'fete') {
    const places: [number, number][] = [[1, 2], [16, 3], [2, 6], [15, 7], [0, 4], [17, 1], [3, 0], [13, 0]]
    places.forEach(([c, r], i) => {
      const ch = ['✦', '✧', '·', ' '][(Math.floor(t / 150) + i) % 4]!
      effet(c, r, { ch, fg: i % 2 === 0 ? ETINCELLE : BLEU.base, bold: true })
    })
  }
  if (x === 'caresse') {
    const cd = Math.min(t - s.caresse, depuis)
    effet(13, 3 - (Math.floor(cd / 350) % 4), { ch: '♥', fg: ETINCELLE, bold: true })
    effet(3, 2 - (Math.floor((cd + 500) / 350) % 3), { ch: '♥', fg: ETINCELLE })
  }
  if (x === 'attente') {
    const n = Math.floor(t / 400) % 4
    for (let i = 0; i < n; i++) effet(15 + i, ey, { ch: '·', fg: GRIS, bold: true })
  }
  if (x === 'soulage') {
    const n = Math.floor(depuis / 350)
    if (n < 3) effet(13 + n, ey - n, { ch: n === 0 ? '∘' : '°', fg: BRUME })
  }
  if (x === 'inquiet') effet(ex + 6, ey - 1 + (Math.floor(t / 400) % 3), { ch: '•', fg: BLEU.clair, bold: true })
  return g
}

// Une rangée de cellules en segments de même style.
function segments(rangee: Cellule[]): Cellule[] {
  const out: Cellule[] = []
  for (const c of rangee) {
    const d = out[out.length - 1]
    if (d && d.fg === c.fg && d.bg === c.bg && d.bold === c.bold && d.dim === c.dim) d.ch += c.ch
    else out.push({ ...c })
  }
  return out
}

const Creature: ClientModule<Props, Etat> = (props, surface) => {
  const { Box, Text } = surface.elements
  const mini = props.taille === 'mini'
  const pas = mini ? 150 : 100
  let s = surface.state
  if (s === undefined) {
    surface.every(pas, () => {
      const e = surface.state
      if (!e) return
      const t = e.t + pas
      const n: Etat = { ...e, t }
      if (t >= e.clignePlus) {
        n.cligneFin = t + 160
        n.clignePlus = t + hasard(2500, 6500)
      }
      if (t >= e.regardPlus) {
        n.regard = [-1, 0, 0, 1][Math.floor(Math.random() * 4)]!
        n.regardPlus = t + hasard(1800, 5000)
      }
      if (t >= e.idlePlus) {
        n.idle = (['saut', 'clin', 'antenne'] as const)[Math.floor(Math.random() * 3)]!
        n.idleDebut = t
        n.idlePlus = t + hasard(9000, 18000)
      }
      surface.setState(n)
    })
    s = {
      t: 0,
      rev: props.rev,
      tRev: 0,
      outilRev: props.outilRev,
      tOutil: 0,
      cligneFin: 0,
      clignePlus: hasard(1500, 4000),
      regard: 0,
      regardPlus: hasard(2000, 4000),
      idle: '',
      idleDebut: 0,
      idlePlus: hasard(8000, 14000),
      caresse: -1e9,
    }
    surface.setState(s)
  } else if (s.rev !== props.rev || s.outilRev !== props.outilRev) {
    // Nouvel évènement : l'horloge de l'humeur repart.
    s = {
      ...s,
      rev: props.rev,
      tRev: s.rev !== props.rev ? s.t : s.tRev,
      outilRev: props.outilRev,
      tOutil: s.outilRev !== props.outilRev ? s.t : s.tOutil,
    }
    surface.setState(s)
  }

  const caresser = () => {
    const e = surface.state
    if (!e) return
    surface.setState({ ...e, caresse: e.t })
    surface.post({ type: 'caresse' })
  }
  surface.onPointer((ev: ClientPointerEvent) => {
    if (ev.type === 'down' && ev.button === 'left') caresser()
  })
  surface.onKey(ev => {
    if (ev.key === 'return' || ev.key === 'enter' || ev.key === 'space' || ev.key === ' ') caresser()
  })

  const x = expression(props, s)
  const mot = MOTS[x]

  if (mini) {
    // Une ligne : ▐ ● ◡ ● ▌ ✦  Pilou · réfléchit
    const teinte = x === 'inquiet' ? ORANGE.base : BLEU.base
    const [og, od, bouche] = yeux(x, props, s)
    const tip = etincelle(x, s.t)
    return (
      <Box flexDirection="row">
        <Text mono>
          <Text mono color={teinte}>▐</Text>
          <Text mono color={ENCRE} backgroundColor={teinte} bold>{` ${og}${bouche}${od} `}</Text>
          <Text mono color={teinte}>▌</Text>
          <Text mono color={tip.fg} bold={tip.bold}>{tip.ch}</Text>
          <Text mono color={NOM} bold>{` ${props.nom}`}</Text>
          <Text mono dimColor>{` · ${mot}`}</Text>
        </Text>
      </Box>
    )
  }

  const grille = sprite(x, props, s)
  const cols = surface.columns || W
  const decalage = props.droite ? Math.max(0, cols - W) : Math.max(0, Math.floor((cols - W) / 2))
  const marge = ' '.repeat(decalage)
  const statut = `${props.nom} · niv ${props.niveau} · ${mot}`
  const margeStatut = ' '.repeat(
    props.droite ? Math.max(0, cols - statut.length) : Math.max(0, Math.floor((cols - statut.length) / 2)),
  )
  const vide = props.bas ? Math.max(0, (surface.rows || 0) - H - 1) : 0

  return (
    <Box flexDirection="column">
      {Array.from({ length: vide }, (_, i) => (
        <Box key={`v${i}`}>
          <Text mono> </Text>
        </Box>
      ))}
      {grille.map((rangee, r) => (
        <Box key={`r${r}`} flexDirection="row">
          <Text mono>
            {marge}
            {segments(rangee).map(sg => (
              <Text mono color={sg.fg} backgroundColor={sg.bg} bold={sg.bold} dimColor={sg.dim}>
                {sg.ch}
              </Text>
            ))}
          </Text>
        </Box>
      ))}
      <Box key="statut" flexDirection="row">
        <Text mono>
          {margeStatut}
          <Text mono color={NOM} bold>{props.nom}</Text>
          <Text mono dimColor>{` · niv ${props.niveau} · ${mot}`}</Text>
        </Text>
      </Box>
    </Box>
  )
}

export default Creature
