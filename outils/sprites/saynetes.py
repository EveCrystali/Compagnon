"""Saynètes de repos : les règles communes au PC et au téléphone (référence ; docs/SPRITES.md, « Saynètes de repos »).

Au calme, Pilou s'occupe tout seul quelques secondes : il lit, compte ses pièces, poursuit son étincelle, s'endort
par étapes… Chaque saynète dure de 3 à 8 s, elle est tirée au sort avec un poids ; les rares (poids 1) tombent environ
une fois sur cent. Certaines dépendent de l'heure, du mois, du stade, d'un objet porté ou du compagnon.

La banque est écrite dans assets/saynetes.txt (lue telle quelle par le PC et le téléphone) :

  saynete <id> <poids> <duree> [conditions…]
  <ms> champ=valeur champ=valeur …         un point clé ; les lignes suivent, dans l'ordre du temps

  conditions   heure=a-b[,c-d]   heures (b exclue ; a > b passe minuit)
               mois=m,n,…        mois (1 à 12)
               stade=a-b         stades (bornes comprises)
               objet=x|y         l'un de ces objets porté
               compagnon         un compagnon porté
               mainlibre         rien dans la main (la saynète y met quelque chose)
               repos             seulement quand tu ne travailles pas
               tourne            peut se jouer en miroir (regard et penché inversés : le bord est de l'autre côté)
               trait=x|y         poids × TRAIT quand l'un de ces traits est parmi les trois dominants (docs/TRAITS.md)
  poids 0      une réaction au monde (freine au bord, lâché, long survol) : jamais tirée au sort, lancée par l'appelant
  continus     assis (0…1000), saut (millièmes d'« ancien pixel »), etire (−1000…1000), penche (millièmes d'ancien
               pixel, vers la droite) : interpolés entre deux points clés, 0 avant le premier
  discrets     expr, regard, regard_y (−1, 0, 1), cligne, baille, salue (0, 1), objets (liste « a,b », « - » : rien) :
               la dernière valeur posée

Raccords : chaque champ continu part de 0 et y revient (pas de coupe franche), avec un temps d'anticipation (il se
ramasse) avant le mouvement et un temps de retombée après ; `verifier()` le contrôle.

  tirer(banque, u, contexte, evite)   l'identifiant tiré (u : 0…9999) parmi les saynètes permises, "" s'il n'y en a pas
  jeu(saynete, d, niveau, sens)       ce que la saynète impose à Pilou d ms après son début (None : finie)

Niveau « aucune » (réglage ✧) : aucune saynète. « Réduites » : la saynète se joue sans saut, étirement ni penché
(posture, regard, visage et objets seulement). Aucun gain (xp, pièces) n'est lié aux saynètes.

Arithmétique entière seulement (divisions arrondies vers le bas). `reference.py` écrit assets/saynetes.txt et
outils/sprites/saynetes-reference.txt ; `SaynetesTests.cs` et `SaynetesTest.java` relisent l'un et l'autre.
"""
import os

COMPLETES, REDUITES, AUCUNE = "completes", "reduites", "aucune"
CONTINUS = ("assis", "saut", "etire", "penche")
DISCRETS = ("expr", "regard", "regard_y", "cligne", "baille", "salue", "objets")
# Expressions qui disent quelque chose d'une session (roue, « ! », croix orange sur l'antenne) : jamais en saynète.
SIGNAUX = ("concentre", "attente", "inquiet", "surpris", "grimace")
TRAIT = 3   # un trait dominant triple le poids des saynètes qui lui ressemblent (aucun gain : le poids seulement)
DEFAUTS = {"expr": "repos", "regard": 0, "regard_y": 0, "cligne": 0, "baille": 0, "salue": 0, "objets": ()}


# ---- Écriture de la banque (aides de dessin du temps)

class S:
    def __init__(self, id_, poids, duree, quand=""):
        self.id, self.poids, self.duree, self.quand = id_, poids, duree, quand
        self.cles = {}

    def a(self, t, **kw):
        self.cles.setdefault(t, {}).update(kw)
        return self

    def bond(self, t, haut=1400, vol=360):
        """Petit bond : il se ramasse, décolle étiré, retombe et s'écrase un peu (même dessin que vie.py, en court)."""
        self.a(t, saut=0, etire=0).a(t + 60, etire=-300, saut=0).a(t + 110, etire=250, saut=0)
        self.a(t + 110 + vol // 2, saut=haut, etire=0).a(t + 110 + vol, saut=0, etire=-350)
        self.a(t + 110 + vol + 90, etire=120).a(t + 110 + vol + 170, etire=0)
        return self

    def secoue(self, t, n=6, pas=70, force=700):
        """Il se secoue : penché à gauche, à droite, de moins en moins."""
        self.a(t, penche=0)
        for i in range(n):
            self.a(t + (i + 1) * pas, penche=(force if i % 2 == 0 else -force) * (n - i) // n)
        self.a(t + (n + 1) * pas, penche=0)
        return self

    def assoit(self, t, ms=450):
        """S'asseoir : il se ramasse un peu, puis se pose."""
        return self.a(t, assis=0, etire=0).a(t + ms // 2, etire=-200).a(t + ms, assis=1000, etire=0)

    def releve(self, t, ms=450):
        """Se relever : il pousse sur ses pattes, s'étire un peu, retombe sur ses pieds."""
        return self.a(t, assis=1000, etire=0).a(t + ms, assis=0, etire=180).a(t + ms + 200, etire=0)


def banque_python():
    b = []
    # Il lit (le livre de la tenue de lecture) : la page, les lignes, un passage qui le fait sourire.
    s = S("lit", 16, 7200, "stade=2-4 mainlibre trait=grand-lecteur|amateur-d-histoires").assoit(0, 600)
    s.a(600, expr="neutre", regard_y=1, objets="tenue-lecture-livre").a(1500, regard=1).a(2300, regard=-1)
    s.a(3100, regard=1).a(3900, regard=-1, cligne=1).a(4050, cligne=0).a(4300, expr="soulage", regard=0)
    s.a(5200, expr="neutre", regard=1).a(6000, objets="-", expr="repos", regard=0, regard_y=0).releve(6200)
    b.append(s)
    # Il compte ses pièces : une, deux, trois, quatre… le compte est bon.
    s = S("compte", 12, 7400, "mainlibre trait=chineur|veinard").assoit(0, 500)
    s.a(500, expr="neutre", regard_y=1)
    for k, t in enumerate((900, 1900, 2900, 3900)):
        s.a(t, objets="sc-pieces-%d" % (k + 1), regard=(1 if k % 2 == 0 else 0))
        s.a(t + 80, etire=-120).a(t + 220, etire=0)
    s.a(4800, expr="soulage", regard=0, regard_y=0).a(5000, etire=200).a(5300, etire=0)
    s.a(6000, objets="-", expr="repos").releve(6400)
    b.append(s)
    # Il poursuit son étincelle, qui file à gauche, à droite, revient sur l'antenne.
    s = S("etincelle", 10, 6600)
    s.a(0, expr="repos").a(200, objets="sc-etincelle-1", regard=-1, regard_y=-1, expr="neutre")
    s.a(800, expr="malice").bond(900, 1300)
    s.a(1700, objets="sc-etincelle-2", regard=-1, regard_y=0)
    s.a(2600, objets="sc-etincelle-3", regard=1, regard_y=-1).bond(2700, 1600)
    s.a(3500, objets="sc-etincelle-4", regard=1, regard_y=0)
    s.a(4300, objets="sc-etincelle-5", regard=0, regard_y=-1).bond(4300, 1100)
    s.a(5000, objets="sc-etincelle-6", expr="fete", regard_y=0).a(5800, objets="-", expr="repos")
    b.append(s)
    # Il s'endort par étapes, assis : clignements lents, bâillement, la tête qui tombe, et le sursaut.
    s = S("endort", 8, 8000, "heure=12-16,20-7 trait=douillet").assoit(0, 500)
    s.a(1400, cligne=1).a(1700, cligne=0).a(2300, baille=1, expr="fatigue").a(3300, baille=0)
    s.a(3700, cligne=1).a(4100, cligne=0).a(4400, expr="dort", etire=0).a(4900, etire=-180).a(5300, etire=-60)
    s.a(5900, etire=-260).a(6300, etire=-260, expr="peur")
    s.a(6420, etire=420).a(6600, etire=-120).a(6760, etire=0).a(6800, expr="repos").releve(7100)
    b.append(s)
    # Il regarde par-dessus le bord : il se penche, découvre le vide, recule.
    s = S("bord", 8, 5600, "tourne")
    s.a(0, penche=0, etire=0).a(250, etire=-200).a(500, etire=0, regard=1, regard_y=1)
    s.a(1000, penche=2000, expr="neutre").a(2300, penche=2300, expr="malice").a(3300, penche=2300)
    s.a(3700, penche=0, regard=0, regard_y=0, expr="repos", etire=150).a(4000, etire=0)
    b.append(s)
    # Il s'étire, un bras en l'air, les yeux fermés.
    s = S("etire", 16, 4400, "trait=leve-tot")
    s.a(0, etire=0).a(350, etire=-300).a(800, etire=650, cligne=1, salue=1, expr="soulage")
    s.a(2000, etire=720).a(2400, etire=-220, salue=0, cligne=0).a(2700, etire=100).a(2950, etire=0)
    s.a(3300, expr="repos")
    b.append(s)
    # Rare : il éternue une bulle d'encre, qui monte et éclate.
    s = S("eternue", 1, 5400)
    s.a(0, etire=0).a(400, expr="neutre", regard_y=-1).a(900, etire=250).a(1150, etire=100)
    s.a(1500, etire=450, expr="fatigue", cligne=1).a(1950, etire=620).a(2100, etire=-600, expr="neutre", cligne=0,
                                                                           objets="sc-encre-1")
    s.secoue(2100, 4, 60, 500).a(2350, etire=120).a(2550, etire=0)
    s.a(2500, objets="sc-encre-2", expr="malice").a(2950, objets="sc-encre-3").a(3400, objets="sc-encre-4")
    s.a(3800, objets="-", expr="joie", regard_y=0).a(4600, expr="repos")
    b.append(s)
    # Il regarde les nuages passer.
    s = S("ciel", 10, 6200, "trait=tete-en-l-air|flaneur")
    s.a(0, etire=0).a(300, etire=-120).a(550, etire=120, regard_y=-1).a(800, etire=0, expr="tendre")
    s.a(2300, cligne=1).a(2500, cligne=0).a(3000, regard=1).a(4100, regard=-1).a(5200, regard=0, regard_y=0)
    s.a(5500, expr="repos")
    b.append(s)
    # Une petite danse, quand tu ne travailles pas.
    s = S("danse", 8, 5800, "repos trait=bon-public")
    s.a(0, expr="repos").a(250, expr="joie", objets="tenue-musique-notes")
    for k, t in enumerate((400, 1250, 2100, 2950, 3800)):
        s.a(t, regard=(1 if k % 2 == 0 else -1)).bond(t, 900 if k % 2 == 0 else 1300, 300)
    s.a(4900, objets="-", regard=0).a(5300, expr="repos")
    b.append(s)
    # Hiver : un flocon descend sur son nez.
    s = S("flocon", 10, 5400, "mois=12,1,2")
    s.a(0, regard_y=-1).a(300, objets="sc-flocon-1").a(1000, objets="sc-flocon-2").a(1700, objets="sc-flocon-3")
    s.a(2400, objets="sc-flocon-4", regard_y=0, expr="neutre", etire=0).a(2500, etire=-150).a(2700, etire=0)
    s.a(3000, objets="-", expr="joie").bond(3100, 1000).a(4600, expr="repos")
    b.append(s)
    # Automne : une feuille lui tombe sur la tête, il se secoue.
    s = S("feuille", 10, 5600, "mois=9,10,11")
    s.a(0, regard_y=-1).a(300, objets="sc-feuille-1").a(900, objets="sc-feuille-2").a(1500, objets="sc-feuille-3")
    s.a(2100, objets="sc-feuille-4", expr="neutre", regard_y=0).secoue(2700, 8, 70, 800)
    s.a(2900, objets="sc-feuille-5").a(3600, objets="-", expr="joie").a(4800, expr="repos")
    b.append(s)
    # Printemps, été : un papillon passe, se pose sur l'antenne, repart.
    s = S("papillon", 10, 6400, "mois=3,4,5,6,7,8")
    s.a(0, expr="repos")
    for k, (t, rx, ry) in enumerate(((300, -1, 0), (1200, -1, -1), (2100, 0, -1), (3000, 1, -1), (3900, 0, -1),
                                     (4900, 1, -1))):
        s.a(t, objets="sc-papillon-%d" % (k + 1), regard=rx, regard_y=ry)
    s.a(1200, expr="tendre").a(3900, expr="joie", cligne=1).a(4100, cligne=0).a(5800, objets="-", regard=0,
                                                                                  regard_y=0, expr="repos")
    b.append(s)
    # Il boit son chocolat ou son café, à petites gorgées.
    s = S("boit", 12, 6000, "objet=tasse-cafe|chocolat-chaud trait=douillet").assoit(0, 500)
    s.a(500, regard_y=1).a(1200, cligne=1, expr="soulage").a(1700, cligne=0).a(2600, cligne=1).a(3100, cligne=0)
    s.a(3400, expr="tendre", regard_y=0).a(4400, expr="repos").releve(4700)
    b.append(s)
    # À la lunette ou aux jumelles : il guette au loin, et tiens ! quelque chose.
    s = S("guette", 12, 6400, "objet=telescope|jumelles trait=voyageur")
    s.a(0, etire=0).a(300, etire=-150).a(600, etire=200, regard=1, regard_y=-1, expr="neutre").a(900, etire=0)
    s.a(2200, regard=-1).a(3400, regard=1).a(3800, expr="neutre").bond(3900, 900).a(4700, expr="joie")
    s.a(5600, regard=0, regard_y=0, expr="repos")
    b.append(s)
    # Avec son compagnon : un regard, un petit bond, un cœur sur l'antenne.
    s = S("compagnon", 12, 5200, "compagnon trait=calin|bon-voisin")
    s.a(0, regard=1).a(400, expr="joie").bond(700, 1000).a(1500, cligne=1).a(1700, cligne=0)
    s.a(2000, objets="etincelle-coeur").bond(2400, 800).a(3600, objets="-").a(4200, regard=0, expr="repos")
    b.append(s)
    # Rare : il salue… personne. Il regarde autour, fait mine de rien.
    s = S("salue", 1, 5000, "tourne")
    s.a(0, regard=1).a(300, salue=1, expr="joie").a(1900, salue=0, expr="neutre", regard=-1).a(2500, regard=1)
    s.a(2900, regard=0, expr="malice", etire=0).a(3200, etire=-150).a(3450, etire=100).a(3700, etire=0).a(4300, expr="repos")
    b.append(s)
    b.extend(second_lot())
    b.extend(reactions())
    return b


def second_lot():
    b = []
    # La nuit : il regarde les étoiles, une étoile filante passe.
    s = S("etoiles", 10, 7000, "heure=21-6 trait=couche-tard")
    s.a(0, etire=0).a(300, etire=-150).a(600, etire=150, regard_y=-1).a(850, etire=0, expr="tendre")
    s.a(1800, regard=-1).a(2600, objets="sc-filante-1", regard=1).a(2900, objets="sc-filante-2")
    s.a(3200, objets="sc-filante-3", expr="joie").a(3600, objets="-", cligne=1).a(4600, cligne=0, expr="tendre")
    s.a(5600, regard=0, regard_y=0).a(6200, expr="repos")
    b.append(s)
    # Il vérifie sa canne : le bouchon danse, rien… et si, un petit tressaut.
    s = S("peche", 10, 7400, "mainlibre trait=pecheur-du-dimanche").assoit(0, 500)
    s.a(500, objets="sc-canne-1", regard=1, regard_y=1, expr="neutre").a(1500, objets="sc-canne-2")
    s.a(2300, objets="sc-canne-1").a(3100, objets="sc-canne-2").a(3900, objets="sc-canne-3", expr="malice", etire=0)
    s.a(4000, etire=250).a(4250, etire=-100).a(4450, etire=0).a(4700, objets="sc-canne-1", expr="soulage")
    s.a(5800, objets="-", regard=0, regard_y=0, expr="repos").releve(6200)
    b.append(s)
    # Il souffle une bulle de savon, la regarde monter, elle éclate.
    s = S("bulles", 8, 5600, "trait=tete-en-l-air")
    s.a(0, etire=0).a(300, etire=-250, expr="malice").a(700, etire=300, objets="sc-bulle-1").a(1000, etire=0)
    s.a(1300, objets="sc-bulle-2", regard_y=-1, expr="tendre").a(2100, objets="sc-bulle-3").a(2900, objets="sc-bulle-4")
    s.a(3100, expr="joie", cligne=1).a(3300, cligne=0, objets="-").bond(3400, 700).a(4400, regard_y=0, expr="repos")
    b.append(s)
    # Il fredonne, les notes montent une à une.
    s = S("fredonne", 10, 5600, "trait=siffloteur")
    s.a(0, expr="soulage", cligne=1)
    for k, t in enumerate((300, 1300, 2300, 3300)):
        s.a(t, objets="sc-note-%d" % (k % 3 + 1), regard=(1 if k % 2 == 0 else -1))
        s.a(t, penche=0).a(t + 250, penche=(400 if k % 2 == 0 else -400)).a(t + 700, penche=0)
    s.a(4300, objets="-", regard=0, cligne=0).a(4700, expr="repos")
    b.append(s)
    # Il tourne sur lui-même, d'un petit bond.
    s = S("pirouette", 8, 4400, "repos")
    s.a(0, expr="malice").a(300, regard=1).bond(400, 1300).a(600, regard=0).a(750, regard=-1).a(900, regard=0)
    s.a(1050, regard=1).a(1250, regard=0).a(1700, expr="joie").a(3000, expr="repos")
    b.append(s)
    # Il s'ébroue : un frisson, il se secoue des pieds à l'antenne.
    s = S("secoue", 8, 4200)
    s.a(0, expr="fatigue", etire=0).a(400, etire=-200).secoue(700, 10, 60, 900).a(1000, etire=150).a(1400, etire=0)
    s.a(1500, expr="joie", cligne=1).a(1800, cligne=0).a(2800, expr="repos")
    b.append(s)
    # Il grignote un biscuit, assis ; il en reste des miettes.
    s = S("grignote", 10, 7000, "mainlibre trait=gourmand").assoit(0, 500)
    s.a(500, objets="sc-biscuit-1", regard_y=1, expr="malice").a(1400, cligne=1, expr="soulage").a(1700, cligne=0)
    s.a(1800, objets="sc-biscuit-2").a(2000, etire=0).a(2150, etire=-120).a(2300, etire=0)
    s.a(3000, objets="sc-biscuit-3").a(3200, etire=-120).a(3350, etire=0).a(3600, expr="joie", regard_y=0)
    s.a(5000, objets="-", expr="repos").releve(5600)
    b.append(s)
    # Il rêvasse : une petite pensée flotte au-dessus de lui.
    s = S("reve", 10, 6800, "trait=tete-en-l-air|amateur-d-histoires").assoit(0, 500)
    s.a(500, regard=-1, regard_y=-1, expr="tendre").a(1100, objets="sc-pensee-1").a(1600, objets="sc-pensee-2")
    s.a(2100, objets="sc-pensee-3").a(3300, cligne=1).a(3500, cligne=0).a(4600, objets="-", regard=0, regard_y=0)
    s.a(4800, expr="repos").releve(5300)
    b.append(s)
    # Il tient en équilibre, penche, se rattrape, fier de lui.
    s = S("equilibre", 8, 5200, "tourne")
    s.a(0, penche=0, etire=0, expr="neutre").a(400, etire=250).a(900, penche=700, etire=300).a(1500, penche=-600)
    s.a(2100, penche=1100, expr="peur").a(2400, penche=1300).a(2700, penche=-300, etire=100, expr="neutre")
    s.a(3100, penche=0, etire=0).a(3300, expr="joie").bond(3400, 700).a(4600, expr="repos")
    b.append(s)
    # Il souffle sur son antenne : l'étincelle vacille, il rit.
    s = S("souffle", 6, 4600)
    s.a(0, etire=0).a(300, regard_y=-1, expr="malice").a(600, etire=-200).a(1000, etire=200, cligne=1)
    s.a(1500, etire=0, cligne=0).secoue(1500, 4, 80, 300).a(2100, expr="joie").a(3200, regard_y=0, expr="repos")
    b.append(s)
    # Le hoquet : hic… hic… hic. Puis plus rien.
    s = S("hoquet", 4, 6200)
    s.a(0, saut=0, etire=0, expr="neutre")
    for t in (500, 1500, 2300, 3600):
        s.a(t, saut=0, etire=0).a(t + 70, saut=700, etire=350).a(t + 180, saut=0, etire=-150).a(t + 300, etire=0)
    s.a(1600, expr="fatigue").a(4200, expr="neutre").a(5000, expr="joie").a(5800, expr="repos")
    b.append(s)
    # Il tend l'oreille : quelque chose à gauche, à droite… rien.
    s = S("ecoute", 8, 5000)
    s.a(0, etire=0).a(300, etire=200, expr="neutre").a(600, regard=-1, etire=250).a(1600, regard=1)
    s.a(2600, regard=0, etire=0).a(2900, expr="malice").a(3800, expr="repos")
    b.append(s)
    # Rare : il trébuche sur rien, tombe assis, fait mine de rien.
    s = S("trebuche", 1, 5600, "tourne")
    s.a(0, penche=0, etire=0, assis=0).a(300, penche=900, etire=-200, expr="peur").a(550, penche=1500, assis=0)
    s.a(700, penche=0, assis=1000, etire=-500).a(850, etire=200).a(1000, etire=0)
    s.a(1600, expr="malice", regard=1).a(2400, regard=-1).a(3000, regard=0, expr="joie").releve(3600)
    s.a(4800, expr="repos")
    b.append(s)
    # Rare : il fait un vœu, les yeux fermés ; un cœur sur l'antenne.
    s = S("voeu", 1, 5400)
    s.a(0, etire=0).a(300, etire=-200).a(700, etire=150, expr="soulage").a(1100, etire=0)
    s.a(1500, objets="sc-filante-1").a(1800, objets="sc-filante-2").a(2100, objets="sc-filante-3")
    s.a(2500, objets="etincelle-coeur", expr="tendre").a(3500, expr="joie").a(4300, objets="-", expr="repos")
    b.append(s)
    return b


def reactions():
    """Réactions au monde (poids 0 : jamais tirées, l'appelant les lance)."""
    b = []
    # Arrivé au bord de l'écran en marchant : il freine, regarde le vide, recule d'un pas.
    s = S("freine", 0, 3000, "tourne")
    s.a(0, etire=0, penche=0).a(80, etire=-350, penche=900).a(250, etire=150, penche=1300, regard=1, regard_y=1)
    s.a(400, etire=0, expr="neutre").a(1500, expr="malice").a(2100, penche=0, regard=0, regard_y=0).a(2500, expr="repos")
    b.append(s)
    # Lâché, une fois retombé : un temps sonné, il se secoue, ça va.
    s = S("lache", 0, 2600)
    s.a(0, expr="fatigue", cligne=1, etire=0).a(350, cligne=0).a(500, etire=-150).secoue(600, 8, 60, 800)
    s.a(1200, etire=0).a(1300, expr="joie").a(2100, expr="repos")
    b.append(s)
    # Long survol : la souris reste sur lui ; il lève les yeux, tente de l'attraper d'un bond, un cœur.
    s = S("survol", 0, 3600)
    s.a(0, regard_y=-1, expr="malice", etire=0).bond(500, 1500).a(1300, objets="etincelle-coeur", expr="joie")
    s.a(2700, objets="-", regard_y=0).a(3100, expr="repos")
    b.append(s)
    return b


def texte_banque(b=None):
    b = banque_python() if b is None else b
    lignes = ["# Saynètes de repos : écrit par outils/sprites/saynetes.py (ne pas modifier à la main).",
              "# saynete <id> <poids> <duree> [conditions] ; puis <ms> champ=valeur … (docs/SPRITES.md)."]
    for s in b:
        lignes.append(("saynete %s %d %d %s" % (s.id, s.poids, s.duree, s.quand)).rstrip())
        for t in sorted(s.cles):
            kv = s.cles[t]
            ordre = [k for k in CONTINUS + DISCRETS if k in kv]
            lignes.append("%d %s" % (t, " ".join("%s=%s" % (k, kv[k]) for k in ordre)))
    return "\n".join(lignes) + "\n"


# ---- Lecture et moteur (même code en C# et en Java)

class Saynete:
    def __init__(self, id_, poids, duree, quand):
        self.id, self.poids, self.duree = id_, poids, duree
        self.heures, self.mois, self.stades, self.objets = [], [], None, []
        self.compagnon = self.mainlibre = self.repos = self.tourne = False
        self.traits = []
        for q in quand:
            k, _, v = q.partition("=")
            if k == "heure":
                self.heures = [tuple(int(x) for x in p.split("-")) for p in v.split(",")]
            elif k == "mois":
                self.mois = [int(x) for x in v.split(",")]
            elif k == "stade":
                a, b = v.split("-")
                self.stades = (int(a), int(b))
            elif k == "objet":
                self.objets = v.split("|")
            elif k == "trait":
                self.traits = v.split("|")
            elif k in ("compagnon", "mainlibre", "repos", "tourne"):
                setattr(self, k, True)
        self.continus = {k: [] for k in CONTINUS}
        self.discrets = {k: [] for k in DISCRETS}


def lire(texte):
    banque = []
    for brut in texte.replace("\r", "").split("\n"):
        l = brut.strip()
        if not l or l.startswith("#"):
            continue
        m = l.split()
        if m[0] == "saynete":
            banque.append(Saynete(m[1], int(m[2]), int(m[3]), m[4:]))
            continue
        s, t = banque[-1], int(m[0])
        for kv in m[1:]:
            k, _, v = kv.partition("=")
            if k in CONTINUS:
                s.continus[k].append((t, int(v)))
            elif k == "objets":
                s.discrets[k].append((t, () if v == "-" else tuple(v.split(","))))
            elif k == "expr":
                s.discrets[k].append((t, v))
            else:
                s.discrets[k].append((t, int(v)))
    return banque


def permise(s, c):
    """c : heure, mois, stade, objets (portés), compagnon, mainlibre, travail, traits (dominants)."""
    if s.heures and not any((a <= c["heure"] < b) if a <= b else (c["heure"] >= a or c["heure"] < b) for a, b in s.heures):
        return False
    if s.mois and c["mois"] not in s.mois:
        return False
    if s.stades and not s.stades[0] <= c["stade"] <= s.stades[1]:
        return False
    if s.objets and not any(o in c["objets"] for o in s.objets):
        return False
    if s.compagnon and not c["compagnon"]:
        return False
    if s.mainlibre and not c["mainlibre"]:
        return False
    if s.repos and c["travail"]:
        return False
    return True


def poids(s, c):
    return s.poids * (TRAIT if any(t in c["traits"] for t in s.traits) else 1)


def tirer(banque, u, c, evite=""):
    ok = [s for s in banque if s.id != evite and s.poids > 0 and permise(s, c)]
    total = sum(poids(s, c) for s in ok)
    if total == 0:
        return ""
    x = u * total // 10000
    for s in ok:
        if x < poids(s, c):
            return s.id
        x -= poids(s, c)
    return ok[-1].id


def cles(table, d):
    if not table:
        return 0
    if d <= table[0][0]:
        return table[0][1] if d == table[0][0] else 0
    for (t0, v0), (t1, v1) in zip(table, table[1:]):
        if d < t1:
            return v0 + (v1 - v0) * (d - t0) // (t1 - t0)
    return table[-1][1]


def jeu(s, d, niveau, sens=1):
    """dict des champs (CONTINUS en millièmes, DISCRETS), ou None si la saynète est finie ou coupée."""
    if niveau == AUCUNE or d < 0 or d >= s.duree:
        return None
    r = {}
    for k in CONTINUS:
        r[k] = cles(s.continus[k], d)
    for k in DISCRETS:
        v = DEFAUTS[k]
        for t, x in s.discrets[k]:
            if t <= d:
                v = x
        r[k] = v
    if niveau != COMPLETES:
        r["saut"] = r["etire"] = r["penche"] = 0
    if s.tourne and sens < 0:
        r["regard"], r["penche"] = -r["regard"], -r["penche"]
    return r


def verifier(banque):
    """Raccords : chaque champ continu part de 0 et y revient avant la fin ; durées de 3 à 8 s ; temps croissants."""
    ids = set()
    for s in banque:
        assert s.id not in ids, s.id
        ids.add(s.id)
        assert (3000 if s.poids else 1500) <= s.duree <= 8000, s.id
        for k, table in s.continus.items():
            if not table:
                continue
            assert table[0][1] == 0, (s.id, k, "départ")
            assert table[-1][1] == 0 and table[-1][0] < s.duree, (s.id, k, "retombée")
            assert all(a[0] < b[0] for a, b in zip(table, table[1:])), (s.id, k, "temps")
        for t, e in s.discrets["expr"]:
            assert e not in SIGNAUX, (s.id, e, "expression de signal")
        fin = jeu(s, s.duree - 1, COMPLETES)
        assert fin["objets"] == () and fin["salue"] == 0 and fin["baille"] == 0 and fin["cligne"] == 0, s.id


# ---- Éveil : sans aucune session d'IA, Pilou est éveillé ; il ne dort que si tu t'absentes, ou la nuit.

NUIT = (0, 6)               # de minuit à 6 h
ABSENT = 10 * 60_000        # 10 min sans clavier ni souris : il s'endort
ABSENT_NUIT = 2 * 60_000    # la nuit, 2 min suffisent


def nuit(heure):
    return NUIT[0] <= heure % 24 < NUIT[1]


def endormi(heure, inactif_ms):
    """Pilou dort-il, sans rien d'autre à faire ? Selon l'absence réelle (PC) et l'heure."""
    return inactif_ms >= ABSENT or (nuit(heure) and inactif_ms >= ABSENT_NUIT)


# ---- Référence partagée

ICI = os.path.dirname(os.path.abspath(__file__))
ASSET = os.path.normpath(os.path.join(ICI, "..", "..", "assets", "saynetes.txt"))
REFERENCE = os.path.join(ICI, "saynetes-reference.txt")

CONTEXTES = [
    dict(heure=10, mois=6, stade=2, objets=(), compagnon=False, mainlibre=True, travail=False, traits=()),
    dict(heure=14, mois=1, stade=1, objets=("tasse-cafe",), compagnon=True, mainlibre=False, travail=True,
         traits=("douillet",)),
    dict(heure=22, mois=10, stade=3, objets=("jumelles", "petit-chat"), compagnon=True, mainlibre=True, travail=False,
         traits=("couche-tard", "grand-lecteur", "pecheur-du-dimanche")),
    dict(heure=6, mois=12, stade=4, objets=("telescope",), compagnon=False, mainlibre=False, travail=False,
         traits=("gourmand", "siffloteur")),
]


def contexte_texte(c):
    return "heure=%d mois=%d stade=%d objets=%s compagnon=%d mainlibre=%d travail=%d traits=%s" % (
        c["heure"], c["mois"], c["stade"], ",".join(c["objets"]) or "-", c["compagnon"], c["mainlibre"], c["travail"],
        ",".join(c["traits"]) or "-")


def jeu_texte(r):
    if r is None:
        return "fini"
    return " ".join("%s=%s" % (k, (",".join(r[k]) or "-") if k == "objets" else r[k]) for k in CONTINUS + DISCRETS)


def reference(banque):
    l = ["# Saynètes de repos (saynetes.py) : relu par SaynetesTests.cs et SaynetesTest.java. Ne pas modifier à la main."]
    for c in CONTEXTES:
        for u in (0, 1, 37, 99, 100, 1234, 2500, 3333, 5000, 6100, 7777, 8800, 9899, 9900, 9950, 9999):
            for evite in ("", "etire"):
                l.append("tirer u=%d evite=%s %s -> %s" % (u, evite or "-", contexte_texte(c), tirer(banque, u, c, evite) or "-"))
    for h in range(24):
        for inactif in (0, 119_999, 120_000, 599_999, 600_000):
            l.append("eveil heure=%d inactif=%d -> %s nuit=%d" % (h, inactif, "dort" if endormi(h, inactif) else "eveille",
                                                                   nuit(h)))
    for s in banque:
        for niveau in (COMPLETES, REDUITES, AUCUNE):
            for sens in (1, -1):
                if sens < 0 and not s.tourne:
                    continue
                for d in list(range(-50, s.duree + 100, 175)) + [s.duree - 1]:
                    l.append("jeu %s %d %s %d -> %s" % (s.id, d, niveau, sens, jeu_texte(jeu(s, d, niveau, sens))))
    return "\n".join(l) + "\n"


def ecrire_reference():
    texte = texte_banque()
    banque = lire(texte)
    verifier(banque)
    with open(ASSET, "w", encoding="utf-8", newline="\n") as f:
        f.write(texte)
    with open(REFERENCE, "w", encoding="utf-8", newline="\n") as f:
        f.write(reference(banque))
    return banque


if __name__ == "__main__":
    b = ecrire_reference()
    print(len(b), "saynètes ;", ASSET, ";", REFERENCE)
