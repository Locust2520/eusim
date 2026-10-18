#!/usr/bin/env python3
"""Build the full list of AI images for EU Simulator (portraits, Euromons, cinematic slides, UI art)
as one JSON manifest: build/eusim_images.json (+ build/eusim_scenes.json, the cinematic plan).

Each image entry keeps the fields of the old /opt/ordinatrice/imggen jobs (name, model, quality, size, prompt,
refs, input_fidelity, after) plus: category, out (where the result goes in the repo), exists (already made),
and for slides: scene, shot, camera, motion, fr (one-line summary)."""
import json
import os
from functools import lru_cache

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SPECIES = json.load(open(os.path.join(ROOT, 'data/species.json'), encoding='utf-8'))
PORTRAIT_DIR = os.path.join(ROOT, 'assets/art/portraits')
MODEL = 'gpt-image-1.5'
MAGENTA = ('Background: one single flat uniform pure magenta color (#FF00FF) with no gradient, no texture, '
           'no vignette, no frame, no text.')

# ------------------------------------------------------------------ portraits
PT_STYLE = ('Retro 16-bit pixel art character portrait in the style of Nintendo DS JRPG dialogue portraits '
            '(Pokémon Diamond/Pearl, Fire Emblem GBA): bust shot (head and shoulders), facing slightly to the side, '
            'bold dark outlines, limited palette of about 24 colors, clean cel shading, crisp chunky pixels so it '
            'reads like a 96x96 pixel sprite upscaled. ')
PT_LIKENESS = ('Friendly caricature with a slightly bigger head but a faithful, clearly recognizable likeness of the '
               'person in the reference photo: same hairstyle, hair color, face shape, skin tone, facial hair and '
               'typical clothing as in the photo. IMPORTANT: draw glasses ONLY if the person wears glasses in the '
               'reference photo; if they do not wear glasses in the photo, draw NO glasses. ')
EXPRESSIONS = {
    'happy': 'big warm smile, cheerful eyes',
    'angry': 'furious and indignant, frowning eyebrows, mouth open shouting',
    'surprised': 'shocked and astonished, eyebrows raised high, eyes wide open, mouth open in an O',
    'worried': 'anxious and embarrassed, eyebrows tilted up, nervous half-smile, a single drop of sweat on the temple',
    'sulk': 'sulking and pouting: chin raised, eyes half closed looking away, lips pressed in a pout, arms crossed '
            'if visible (the classic "I am not talking to you" face)',
}
# characters without a photo: described in words (they also exist as overworld sprites in the game)
FICTIONAL = {
    'alex': 'Alex, the player character (girl): a cheerful 20-year-old European Commission intern, long brown hair, '
            'light skin, navy blue blazer over a white shirt with a blue tie, navy skirt, red backpack strap on '
            'the shoulder, determined friendly look',
    'max': 'Max, the player character (boy): a cheerful 20-year-old European Commission intern, short dark brown '
           'hair, light skin, navy blue blazer over a white shirt with a blue tie, red backpack strap on the '
           'shoulder, determined friendly look',
    'oliver': 'Oliver, the rival: a cocky but likeable 20-year-old British intern, spiky ash-blond hair, pale skin, '
              'burgundy blazer, white shirt, navy tie, smug grin',
    'cantiniere': 'Mireille, the motherly canteen lady of the European institutions: about 55, tan skin, brown hair '
                  'in a bun, white chef jacket and apron, ladle in hand, warm and stern at the same time',
}
EXTRA_REAL = ['bardella', 'breton', 'erdogan', 'musk', 'putin', 'rutte', 'tusk', 'vance', 'xi', 'zelensky']


@lru_cache(maxsize=1)
def photo_credits():
    # Only image-generation jobs need reference credits; ROM builds use SCENES.
    with open('/opt/ordinatrice/imggen/photo_credits.json', encoding='utf-8') as f:
        return json.load(f)


def photo_url(who):
    c = photo_credits()[who]
    return 'https://commons.wikimedia.org/wiki/Special:FilePath/' + c['file']


def portraits():
    CREDITS = photo_credits()
    have = {f[:-4] for f in os.listdir(PORTRAIT_DIR) if f.endswith('.png')}
    people = sorted({f.rsplit('_', 1)[0] for f in have} | set(EXTRA_REAL)) + list(FICTIONAL)
    out = []
    for who in people:
        base = f'pt_{who}_neutral'
        if who in FICTIONAL:
            e = {'name': base, 'model': MODEL, 'quality': 'medium', 'size': '1024x1024',
                 'prompt': PT_STYLE + 'Original character: ' + FICTIONAL[who] + '. Neutral, calm expression. ' + MAGENTA,
                 'refs': []}
        else:
            e = {'name': base, 'model': MODEL, 'quality': 'medium', 'size': '1024x1024',
                 'prompt': PT_STYLE + PT_LIKENESS + 'Neutral, calm expression. ' + MAGENTA,
                 'refs': [photo_url(who)], 'input_fidelity': 'high',
                 'ref_credit': f"{CREDITS[who]['name']} — {CREDITS[who]['license']} — {CREDITS[who]['url']}"}
        e.update(category='portrait', who=who, expression='neutral',
                 out=f'assets/art/portraits/{who}_neutral.png', exists=f'{who}_neutral' in have)
        out.append(e)
        for ex, desc in EXPRESSIONS.items():
            out.append({
                'name': f'pt_{who}_{ex}', 'model': MODEL, 'quality': 'medium', 'size': '1024x1024',
                'prompt': ('Keep this exact pixel art character portrait: same person, same pixel art style, same '
                           'framing, same pose, same clothes, same accessories (keep glasses only if already present, '
                           'never add glasses), same colors and same flat uniform magenta background. Change ONLY the '
                           'facial expression to: ' + desc + '.'),
                'refs': ['image:' + base], 'input_fidelity': 'high', 'after': [base],
                'category': 'portrait', 'who': who, 'expression': ex,
                'out': f'assets/art/portraits/{who}_{ex}.png', 'exists': f'{who}_{ex}' in have})
    return out


# ------------------------------------------------------------------ Euromons
SHAPES = {
    'quadruped': 'a four-legged animal-like creature', 'biped': 'a two-legged standing creature',
    'blob': 'a round blob-like creature', 'object': 'a living object creature with a face, small arms and feet',
    'insect': 'an insect-like creature', 'serpent': 'a long serpent-like creature', 'flyer': 'a winged flying creature',
    'fish': 'a fish-like creature', 'humanoid': 'a small humanoid creature',
}
CR_STYLE = ('Original cute monster design for a parody Pokémon-like Nintendo DS game about the European Union, drawn '
            'in the exact style of Pokémon Diamond/Pearl battle sprites: pixel art that reads like a 64x64 pixel '
            'sprite upscaled, bold dark outline, limited palette of about 16 colors, simple cel shading, light from '
            'the top-left, full body visible and centered, nothing cropped. ')


def creatures():
    out = []
    for s in SPECIES:
        evo = 'basic stage (small and cute)'
        if any(o.get('evo') and o['evo'].get('into') == s['id'] for o in SPECIES):
            evo = 'evolved stage (bigger, more impressive)' if not s.get('evo') else 'middle evolution stage'
        concept = (f"Creature name: {s['name']}. Category: {s['category']}. Types: {', '.join(s['types'])}. "
                   f"Main color: {s['color']}. Body plan: {SHAPES.get(s['shape'], s['shape'])}, {evo}. "
                   f"Concept (French Pokédex entry, use it for visual jokes and props): \"{s['dex']}\" ")
        front = f"cr_{s['id']}_front"
        out.append({'name': front, 'model': MODEL, 'quality': 'medium', 'size': '1024x1024',
                    'prompt': CR_STYLE + concept + 'Front view, three-quarter, facing slightly to the viewer\'s left, '
                              'as the opponent creature in a battle. No text, no letters. ' + MAGENTA,
                    'refs': [], 'category': 'euromon', 'species': s['id'],
                    'out': f"assets/art/creatures/{s['id']}_front.png", 'exists': False})
        out.append({'name': f"cr_{s['id']}_back", 'model': MODEL, 'quality': 'medium', 'size': '1024x1024',
                    'prompt': ('Keep this exact pixel art creature: same design, colors, style and magenta background. '
                               'Redraw it seen from BEHIND and slightly above, three-quarter back view facing away to '
                               'the viewer\'s right, as the player\'s own creature in a Pokémon battle. Full body, '
                               'nothing cropped, no text.'),
                    'refs': ['image:' + front], 'input_fidelity': 'high', 'after': [front],
                    'category': 'euromon', 'species': s['id'],
                    'out': f"assets/art/creatures/{s['id']}_back.png", 'exists': False})
    return out


# ------------------------------------------------------------------ cinematic slides
SL_STYLE = ('Retro 16-bit pixel art cinematic illustration for a Nintendo DS RPG cutscene, like a 384x256 pixel '
            'image upscaled: limited palette of about 48 colors, clean dark outlines, detailed background, dramatic '
            'lighting, film-like composition. Characters are friendly caricatures (slightly big heads) of the people '
            'in the reference portraits, in the same pixel style. Keep the important subjects inside the central '
            '4:3 area (the image is panned and zoomed slowly). No text, no letters, no numbers, no logos, no speech '
            'bubbles, no UI, no borders. Scene: ')
PLAYER = ('the player character, a young European Commission intern ({look}) wearing a navy blazer, white shirt, '
          'blue tie and a red backpack')
LOOKS = {'alex': 'a girl with long brown hair', 'max': 'a boy with short dark brown hair'}

# scene id, French one-liner, slides: (shot, camera, motion, cast, prompt, uses_player)
SCENES = [
    ('s00_prologue', 'Prologue, 9 mai 1950 : Schuman propose de mettre en commun le charbon et l\'acier.', [
        ('salon', 'wide', 'zoom_in', ['schuman'],
         'Paris, 9 May 1950, the gilded Salon de l\'Horloge at the French foreign ministry, crowded with 1950s '
         'journalists with hats and flash cameras; Robert Schuman at a small lectern reading a sheet of paper. '
         'Warm sepia-tinted palette like an old photograph.', False),
        ('monnet', 'medium', 'pan_left', ['schuman', 'monnet'],
         'Same 1950 room, closer: Robert Schuman reading his declaration while Jean Monnet leans in behind him, '
         'whispering with a knowing smile. Sepia palette, a camera flash lighting the scene.', False),
        ('acier', 'wide', 'zoom_out', [],
         'Symbolic image: a coal mine on the left and a steel mill on the right, connected by a glowing bridge of '
         'light over a river; the smoke from the chimneys curls into a circle of twelve golden stars in a deep blue '
         'evening sky.', False),
        ('carte', 'overhead', 'pan_right', [],
         'A night-time map of Europe seen from space-like height, countries lighting up one after the other in '
         'warm gold, connected by glowing lines, a ring of twelve stars faintly above. Deep blue palette.', False),
    ]),
    ('s01_reveil', 'Lundi 7 h 58 : le stagiaire se réveille avec une heure de retard (changement d\'heure).', [
        ('reveil', 'close', 'zoom_in', [],
         'In a tiny Brussels student studio at morning, {player}, now in a pale blue sleep shirt instead of work '
         'clothes, wakes in panic and reaches toward the bedside alarm. Match the canonical portrait hairstyle '
         'and adult face. Foreground: an old analog alarm clock showing exactly 06:58 (minute hand two ticks '
         'before 12, hour hand just before 7), next to a smartphone reading exactly 07:58 in clear pixel digits. '
         'These clock numerals and phone digits are the only exception to the no-numbers rule. An EU-flag mug, '
         'keys, notebook, crumpled sheets, striped bedding, sunlight through blinds, Brussels rooftops outside. '
         'Crisp pixel clusters, bold dark outlines, clean cel shading matching the other game cinematics.', True),
        ('course', 'wide', 'pan_right', [],
         'Brussels European quarter in the morning: {player} sprinting down a street with a croissant in the mouth '
         'and papers flying, the cross-shaped glass Berlaymont building behind, commuters and cyclists, EU flags.', True),
        ('esplanade', 'medium', 'pan_left', ['oliver'],
         'The esplanade of the European Parliament in Brussels (big curved glass building), morning light: Oliver, '
         'a smug blond British intern in a burgundy blazer, leaning on a railing and tapping his wristwatch.', False),
    ]),
    ('s02_labo', 'Au labo, le professeur Schuman confie un Euromon ; Oliver choisit celui qui bat le tien.', [
        ('oeufs', 'medium', 'zoom_in', ['schuman'],
         'A cosy cluttered office-laboratory inside the European Parliament: Professor Robert Schuman, smiling, '
         'presents three glowing document folders on his desk, each hatching a tiny cute creature: a green sprout '
         'creature, a small lump of coal with eyes, and a yellow atom creature with orbiting electrons.', False),
        ('duel', 'over_shoulder', 'zoom_in', ['oliver'],
         'Over-the-shoulder shot from behind {player}, facing Oliver (smug blond British intern in burgundy blazer) '
         'across the office; sparks of rivalry crackle between them, the three tiny creatures cheering on the desk.',
         True),
    ]),
    ('s03_luxembourg', 'Arrivée au Luxembourg : le viaduc, le Kirchberg, et Juncker qui accueille tout le monde par une bise.', [
        ('viaduc', 'wide', 'pan_right', [],
         'A red-and-white train crossing the stone arch Adolphe Bridge over the green Pétrusse valley in '
         'Luxembourg City, the old town on its cliffs, sunny morning, small EU and Luxembourg flags.', False),
        ('bise', 'medium', 'zoom_in', ['juncker', 'oliver'],
         'Jean-Claude Juncker, beaming, greeting Oliver (blond British intern) with an over-the-top affectionate '
         'double cheek kiss and a playful pat on the head, Oliver blushing and flustered. Kirchberg glass towers behind.',
         False),
        ('arene', 'low_angle', 'tilt_up', ['juncker'],
         'Low-angle shot of a gym-like debate arena with a golden star emblem in Kirchberg, Juncker standing proudly '
         'at the top of the steps, arms open, spotlight beams.', False),
    ]),
    ('s04_schengen', 'À Schengen, sur la Moselle, on fête la fin des contrôles aux frontières.', [
        ('bateau', 'wide', 'pan_right', [],
         'A small white river boat with flags on the Moselle at the village of Schengen where France, Germany and '
         'Luxembourg meet, vineyards on the hills, festive bunting, sunset.', False),
        ('barriere', 'close', 'zoom_out', [],
         'Comedic close shot: a red-and-white border barrier lifting by itself on an empty country road, a lonely '
         'customs officer sadly packing his rubber stamp into a cardboard box, a butterfly crossing freely.', False),
    ]),
    ('s05_bce', 'À Francfort, Lagarde tient le levier du taux directeur sous la tour de la BCE.', [
        ('tour', 'wide', 'tilt_up', [],
         'Night view of Frankfurt: the twin glass towers of the European Central Bank on the river Main, a giant '
         'glowing blue euro symbol sculpture in front, skyline lights reflected in the water.', False),
        ('levier', 'medium', 'zoom_in', ['lagarde'],
         'Christine Lagarde in an elegant white blazer and pearls, smiling confidently, both hands on a giant brass '
         'lever on a futuristic control desk, walls of glowing blue charts going up and down behind her.', False),
        ('pluie', 'wide', 'zoom_out', ['oliver'],
         'Comedic scene in the ECB lobby: euro banknotes slowly raining from the ceiling, Oliver (blond British '
         'intern) jumping to catch them, a security guard watching unimpressed.', False),
    ]),
    ('s06_strasbourg', 'Transhumance : des centaines de malles de députés déménagent à Strasbourg ; Metsola ouvre la séance.', [
        ('malles', 'wide', 'pan_right', [],
         'A train platform with an endless line of grey metal trunks on trolleys, tired MEPs in suits pushing them, '
         'Strasbourg Cathedral\'s pink sandstone spire in the background, pigeons, morning mist.', False),
        ('hemicycle', 'medium', 'zoom_in', ['metsola'],
         'Inside the huge blue Strasbourg hemicycle: Roberta Metsola at the president\'s high desk raising a gavel, '
         'hundreds of tiny MEP seats in a semicircle below, dramatic overhead lights.', False),
    ]),
    ('s07_athenes', 'Athènes : Varoufakis arrive en moto au pied de l\'Acropole pour défier la troïka.', [
        ('acropole', 'wide', 'pan_left', [],
         'The Acropolis and the Parthenon above Athens at golden sunset, white city below, olive trees, a few Greek '
         'and EU flags.', False),
        ('moto', 'medium', 'zoom_in', ['varoufakis'],
         'Yanis Varoufakis grinning on a big motorbike in a leather jacket, no helmet hair blowing, facing three '
         'identical grey-suited faceless bureaucrats with briefcases (the troika), Acropolis behind.', False),
    ]),
    ('s08_brexit', 'Londres : référendum, bus mensonger, et Oliver qui doit choisir entre son pays et l\'équipe.', [
        ('pluie', 'wide', 'pan_right', [],
         'Westminster Palace and Big Ben under heavy London rain, red double-decker bus, black cabs, puddles '
         'reflecting Union Jacks and a few EU flags.', False),
        ('farage', 'medium', 'zoom_in', ['farage'],
         'Nigel Farage grinning with a pint of beer, standing on the open top of a red campaign bus covered in '
         'blank banners, cheering crowd below.', False),
        ('tyrolienne', 'medium', 'pan_left', ['johnson'],
         'Comedic: Boris Johnson with messy blond hair stuck halfway on a zip line above a park, waving two small '
         'Union Jack flags, harness askew, onlookers laughing.', False),
        ('urne', 'close', 'zoom_in', [],
         'Dramatic close-up of a ballot box in a dim polling station, a hand dropping a folded paper, a single '
         'light beam, tense blue-grey palette.', False),
        ('adieu', 'medium', 'zoom_in', ['oliver'],
         'Emotional scene at the Eurostar terminal at St Pancras: Oliver (blond British intern, burgundy blazer) '
         'stops at the gate with his suitcase and looks back at {player} standing on the platform, rain on the glass '
         'roof, soft melancholic light.', True),
    ]),
    ('s09_budapest', 'Budapest : Orbán bloque tout par veto, puis Péter Magyar le détrône.', [
        ('danube', 'wide', 'pan_right', [],
         'The Hungarian Parliament building lit in gold at night on the Danube, chain bridge, reflections on the river.',
         False),
        ('veto', 'medium', 'zoom_in', ['orban'],
         'Viktor Orbán with a smug grin stamping a giant red rubber stamp onto towering stacks of EU documents, '
         'dozens of stamped papers flying around.', False),
        ('foule', 'wide', 'zoom_out', ['magyar'],
         'Péter Magyar on a stage addressing a huge cheering crowd waving Hungarian and EU flags at dusk, '
         'Budapest landmarks behind.', False),
        ('boude', 'medium', 'zoom_in', ['orban'],
         'Comedic: Viktor Orbán sulking alone on a bench, arms crossed, turned away from the viewer, a tiny grey '
         'rain cloud above his head, a pile of unused rubber stamps beside him.', False),
    ]),
    ('s10_qatargate', 'Qatargate : descente de police à l\'aube, sacs de billets, Kaili et Panzeri pris la main dans le sac.', [
        ('aube', 'wide', 'pan_left', [],
         'Place du Luxembourg in Brussels at dawn, the European Parliament behind, blue police lights reflecting on '
         'the cobblestones, unmarked cars arriving, a cat watching.', False),
        ('billets', 'close', 'zoom_in', [],
         'Close-up of an open travel bag and suitcases on a parquet floor overflowing with bundles of banknotes, '
         'flashlight beams crossing, a football with a gold shine rolling nearby.', False),
        ('pris', 'medium', 'zoom_out', ['kaili', 'panzeri'],
         'Eva Kaili and Antonio Panzeri caught by surprise in a living room, each holding a bag of cash, flashlight '
         'beams on them, silhouettes of police officers in the doorway. Comedic "caught red-handed" pose.', False),
    ]),
    ('s11_dgcomp', 'DG COMP : Vestager inflige une amende géante aux géants du numérique, Musk et Breton se disputent un téléphone.', [
        ('amende', 'medium', 'zoom_in', ['vestager'],
         'Margrethe Vestager calmly smiling while signing an enormous scroll-like fine with a fountain pen, a small '
         'knitted elephant on her desk, tiny tech-company mascots trembling in the corner.', False),
        ('dsa', 'medium', 'pan_right', ['musk', 'breton'],
         'Comedic tug-of-war: Elon Musk and Thierry Breton pulling on opposite ends of a giant smartphone, sparks '
         'and emoji-like hearts and angry symbols flying (no letters).', False),
    ]),
    ('s12_tour', 'La Tour des assistants fantômes : des assistants invisibles hantent le Parlement.', [
        ('couloir', 'wide', 'zoom_in', [],
         'A dark spooky office tower corridor at night, flickering lights, translucent ghost office assistants '
         'floating and carrying payslips and coffee, cobwebs on filing cabinets, purple-green palette.', False),
        ('sommet', 'medium', 'zoom_in', ['lepen', 'bardella', 'bayrou'],
         'Top floor of the haunted tower: Marine Le Pen and Jordan Bardella looking innocent next to a big ghost '
         'assistant with a name badge, while François Bayrou peeks nervously from behind a door.', False),
    ]),
    ('s13_paris', 'Paris : Macron fait un discours « en même temps » sur les marches de la Sorbonne.', [
        ('seine', 'wide', 'pan_right', [],
         'Paris at golden hour: the Eiffel Tower, the Seine with bridges and a tour boat, Haussmann roofs.', False),
        ('discours', 'low_angle', 'tilt_up', ['macron'],
         'Low-angle shot: Emmanuel Macron on the steps of the Sorbonne giving a passionate speech, arms wide open, '
         'microphone stand, EU and French flags behind, students listening.', False),
        ('memetemps', 'medium', 'zoom_out', ['macron'],
         'Comedic split image: Emmanuel Macron drawn twice side by side, on the left gesturing left with a blue '
         'background, on the right gesturing right with a red background, both smiling identically ("at the same time").',
         False),
    ]),
    ('s14_sofagate', 'Sofagate : à Ankara, deux fauteuils pour trois, et von der Leyen hérite du canapé.', [
        ('fauteuils', 'medium', 'zoom_in', ['erdogan', 'michel', 'vdl'],
         'Ornate Turkish palace reception room: Recep Tayyip Erdoğan and Charles Michel sitting in two golden '
         'armchairs, Ursula von der Leyen standing beside them with raised eyebrows, making an "ehm" gesture.', False),
        ('canape', 'wide', 'zoom_out', ['vdl'],
         'Ursula von der Leyen sitting alone and very upright on a very long beige sofa far away from the others, '
         'deadpan expression, the huge empty space emphasised.', False),
    ]),
    ('s15_conseil', 'Nuit du Conseil européen : pizzas froides, café, et un accord à 5 h du matin.', [
        ('lanterne', 'wide', 'zoom_in', [],
         'The Europa building in Brussels at night: a glass cube with a giant glowing egg-shaped lantern inside, '
         'colourful patchwork window frames, a few lit windows, limousines waiting.', False),
        ('table', 'overhead', 'pan_right', ['costa', 'merkel', 'draghi', 'kallas'],
         'Overhead shot of a huge round summit table at 4 AM with 27 tired leaders (most as small anonymous '
         'figures; António Costa, Angela Merkel, Mario Draghi and Kaja Kallas recognisable), coffee cups, stacks of '
         'paper, open pizza boxes, a wall clock.', False),
        ('cloche', 'close', 'zoom_in', ['costa'],
         'António Costa, exhausted but triumphant, ringing a small brass bell, dawn light coming through the '
         'windows, papers flying in celebration behind him.', False),
    ]),
    ('s16_champion', 'Au sommet du Berlaymont, von der Leyen attend le stagiaire pour le duel final.', [
        ('berlaymont', 'low_angle', 'tilt_up', [],
         'The cross-shaped glass Berlaymont building in Brussels at sunset seen from below, a row of EU flags '
         'flapping, dramatic orange-purple sky.', False),
        ('bureau', 'medium', 'zoom_in', ['vdl', 'michel'],
         'Top-floor office of the Commission President: Ursula von der Leyen standing confidently by the window '
         'with the city behind, while Charles Michel sulks in the background, arms crossed, turned away.', False),
        ('duel', 'wide', 'zoom_in', ['vdl'],
         'Epic final duel: {player} seen from behind on the left, Ursula von der Leyen on the right, two powerful '
         'cute creatures facing off between them on a shining floor with a giant EU star emblem, energy aura.', True),
        ('pantheon', 'medium', 'pan_right', [],
         'Hall of fame: a long wall of framed photos of former interns, the newest golden frame showing {player} '
         'smiling with their creature, confetti falling.', True),
    ]),
    ('s17_puissances', 'Les grandes puissances débarquent : Air Force One à Anvers, la table de Poutine, un porte-conteneurs au Pirée.', [
        ('airforce', 'wide', 'pan_right', [],
         'A big blue-and-white presidential jumbo jet landing over the port of Antwerp with cranes and containers, '
         'seagulls fleeing, dramatic clouds.', False),
        ('tele', 'medium', 'zoom_in', ['trump', 'putin', 'xi'],
         'A Brussels café: patrons staring at three TV screens on the wall, each showing a news close-up of Donald '
         'Trump, Vladimir Putin and Xi Jinping, a waiter frozen with a tray.', False),
        ('cargo', 'wide', 'pan_left', [],
         'A gigantic container ship sailing into the port of Piraeus near Athens, red containers stacked high, '
         'tugboats, golden evening light.', False),
    ]),
    ('s18_anvers', 'À Anvers, Trump transforme le port en golf et taxe chaque balle ; Rutte applaudit.', [
        ('golf', 'medium', 'zoom_in', ['trump', 'vance', 'rutte'],
         'Donald Trump golfing on a putting green improvised between shipping containers on the Antwerp docks, '
         'JD Vance carrying the golf bag, Mark Rutte clapping enthusiastically.', False),
        ('taxe', 'close', 'zoom_out', ['trump'],
         'Comedic close-up: a golf ball flying through the air with a big round red customs stamp seal stuck on it, '
         'Trump in the background giving a thumbs-up, the river Scheldt below.', False),
    ]),
    ('s19_varsovie', 'Varsovie : Poutine reçoit le stagiaire au bout d\'une table interminable.', [
        ('table', 'wide', 'pan_right', ['putin'],
         'Extremely long white table in a cold marble hall: Vladimir Putin tiny at the far end, {player} tiny at '
         'the near end, absurd distance between them, chandeliers, cold blue light.', True),
        ('regard', 'close', 'zoom_in', ['putin'],
         'Close-up of Vladimir Putin narrowing his eyes behind the table, a single glass of water, hands folded, '
         'cold dramatic lighting.', False),
        ('neige', 'medium', 'pan_left', ['tusk', 'zelensky'],
         'Donald Tusk and Volodymyr Zelensky (olive green outfit) standing side by side in the snow in front of '
         'Warsaw\'s Palace of Culture tower, determined, flags of Poland, Ukraine and the EU.', False),
    ]),
    ('s20_piree', 'Au Pirée, Xi offre un panda en peluche… et rachète le port pendant la conversation.', [
        ('panda', 'medium', 'zoom_in', ['xi'],
         'Xi Jinping smiling warmly and holding out a big plush panda, stacks of red shipping containers behind '
         'on the Piraeus docks, sunny.', False),
        ('sceau', 'wide', 'zoom_out', [],
         'Comedic: a giant red square seal stamp descending from the sky onto the Piraeus harbour, dock workers '
         'looking up in surprise, a plush panda sitting on a bollard.', False),
    ]),
    ('s21_gtout', 'Le sommet « G-Tout » : Trump, Poutine et Xi exigent que l\'Europe choisisse un camp.', [
        ('salle', 'wide', 'zoom_in', ['trump', 'putin', 'xi'],
         'A grand summit hall with a red carpet and chandeliers: Donald Trump, Vladimir Putin and Xi Jinping '
         'seated at a table facing the viewer, a large EU flag behind, cameras flashing.', False),
        ('triptyque', 'close', 'pan_right', ['trump', 'putin', 'xi'],
         'Three-panel image split vertically: left Donald Trump pointing, middle Vladimir Putin frowning, right Xi '
         'Jinping smiling inscrutably, each with a different coloured background (red, grey, gold).', False),
        ('debout', 'low_angle', 'tilt_up', [],
         'Heroic low-angle shot: {player} standing up from a chair with a raised fist, 27 EU member-state flags '
         'rising behind, golden stars swirling, the three leaders tiny and surprised in the foreground.', True),
        ('sortie', 'wide', 'zoom_out', ['trump', 'putin', 'xi'],
         'The three leaders leaving the hall through three separate doors, each turned away and sulking, while '
         'interns cheer in the foreground.', False),
    ]),
    ('s22_fin', 'Fin : cérémonie de fin de stage à Bruxelles, Oliver revient, feux d\'artifice.', [
        ('grandplace', 'wide', 'tilt_up', [],
         'Brussels Grand-Place at night with golden guild houses and the town hall tower, fireworks in blue and '
         'gold forming a ring of stars, a crowd celebrating.', False),
        ('diplome', 'medium', 'zoom_in', ['schuman'],
         'A ceremony stage: Professor Robert Schuman, proud, handing a rolled diploma to {player}, applause, '
         'blue and gold banners.', True),
        ('retour', 'medium', 'zoom_in', ['oliver'],
         'Oliver (blond British intern, burgundy blazer) running back across the square with a blue student scarf '
         'and a suitcase to hug {player}, tears of joy, confetti.', True),
        ('photo', 'wide', 'pan_right', ['juncker', 'lagarde', 'metsola', 'varoufakis', 'farage', 'magyar',
                                         'vestager', 'macron', 'vdl'],
         'Group photo on the steps of the European Parliament: Jean-Claude Juncker, Christine Lagarde, Roberta '
         'Metsola, Yanis Varoufakis, Nigel Farage, Péter Magyar, Margrethe Vestager, Emmanuel Macron and Ursula von '
         'der Leyen, all smiling, some making silly faces.', False),
        ('ciel', 'wide', 'zoom_out', ['schuman', 'monnet'],
         'Post-credits: the translucent smiling faces of Robert Schuman and Jean Monnet in a starry night sky above '
         'a glowing map of Europe, twelve golden stars around them.', False),
    ]),
    ('s23_legendes', 'Après le jeu : les traités légendaires de Rome, Maastricht et Lisbonne s\'éveillent.', [
        ('rome', 'wide', 'zoom_in', [],
         'Rome, the Capitoline square at dusk with the Marcus Aurelius statue: a majestic legendary creature '
         'inspired by the Capitoline she-wolf and a scroll (Treaty of Rome, 1957) rising in golden light.', False),
        ('maastricht', 'wide', 'pan_right', [],
         'Maastricht at night on the river Meuse with the old stone bridge: a legendary dragon-like creature made '
         'of glowing coins and treaty pages emerging from the water (Treaty of Maastricht, 1992).', False),
        ('lisbonne', 'wide', 'tilt_up', [],
         'Lisbon at dawn in front of the white Jerónimos Monastery: a legendary bird creature shaped like a '
         'caravel with sails of treaty pages taking flight over the Tagus (Treaty of Lisbon, 2007).', False),
    ]),
]


def slides():
    out, plan = [], []
    for sid, fr, shots in SCENES:
        plan_s = {'scene': sid, 'fr': fr, 'slides': []}
        for i, (shot, cam, motion, cast, prompt, uses_player) in enumerate(shots, 1):
            variants = ['alex', 'max'] if uses_player else [None]
            for v in variants:
                name = f'cs_{sid}_{i:02d}_{shot}' + (f'_{v}' if v else '')
                p = prompt.replace('{player}', PLAYER.format(look=LOOKS[v]) if v else 'the player')
                refs = ['image:pt_%s_neutral' % c for c in cast] + (['image:pt_%s_neutral' % v] if v else [])
                out.append({'name': name, 'model': MODEL, 'quality': 'high', 'size': '1536x1024',
                            'prompt': SL_STYLE + p + f' Camera: {cam.replace("_", " ")} shot.',
                            'refs': refs, 'input_fidelity': 'low' if refs else None,
                            'after': [r[6:] for r in refs] or None,
                            'category': 'slide', 'scene': sid, 'shot': i, 'camera': cam, 'motion': motion,
                            'out': f'assets/art/slides/{name[3:]}.png', 'exists': False})
                plan_s['slides'].append(name)
        plan.append(plan_s)
    for e in out:
        for k in ('input_fidelity', 'after'):
            if e[k] is None:
                del e[k]
    return out, plan


# ------------------------------------------------------------------ UI / backgrounds
UI_STYLE = ('Retro 16-bit pixel art background for a Nintendo DS game, like a 256x192 pixel image upscaled, '
            'limited palette of about 40 colors, crisp pixels, no text, no people. ')
UI = [
    ('ui_title_sky', '1536x1024', 'Night sky over Brussels for a title screen: deep navy to purple gradient with a '
     'warm orange glow on the horizon, scattered small stars, a faint milky way. Sky ONLY, no buildings, no ground.'),
    ('ui_title_skyline', '1536x1024', 'Silhouette skyline of the Brussels European quarter at dusk (Berlaymont, '
     'Atomium, Parliament, Europa lantern), lit windows and a row of EU flags, along the bottom third; everything '
     'above the skyline is flat pure magenta (#FF00FF).'),
    ('ui_bt_grass', '1536x1024', 'Pokémon Diamond/Pearl style battle background: a grassy meadow with two oval '
     'grass platforms (one far on the right, one near on the left), soft blue sky.'),
    ('ui_bt_indoor', '1536x1024', 'Pokémon Diamond/Pearl style battle background: an EU institution office interior '
     '(wooden floor, tall windows, EU flag), two oval rug platforms (far right, near left).'),
    ('ui_bt_hemicycle', '1536x1024', 'Pokémon Diamond/Pearl style battle background: inside a parliament '
     'hemicycle with blue seats in rows, two round platforms (far right, near left).'),
    ('ui_bt_city', '1536x1024', 'Pokémon Diamond/Pearl style battle background: a European city square with '
     'cobblestones and old facades, two round stone platforms (far right, near left).'),
    ('ui_bt_night', '1536x1024', 'Pokémon Diamond/Pearl style battle background: a moonlit snowy square at night '
     'with a long table hall in the distance, two round platforms (far right, near left).'),
    ('ui_europe_map', '1536x1024', 'Stylised pixel art map of Europe for an in-game town map: sea in blue, land '
     'in green and beige, country borders, mountains and rivers, no labels, no text, no markers.'),
]


def ui():
    return [{'name': n, 'model': MODEL, 'quality': 'high', 'size': size, 'prompt': UI_STYLE + p, 'refs': [],
             'category': 'ui', 'out': f'assets/art/ui/{n[3:]}.png', 'exists': False} for n, size, p in UI]


def main():
    pts = portraits()
    sls, plan = slides()
    uis = ui()
    # Euromons stay procedural (tools/proc_creatures.py); images already made are left out, and references to
    # them point at the PNG shipped alongside in eusim_refs.zip ("file:<name>.png").
    allimg = pts + sls + uis
    done = {e['name']: e for e in allimg if e['exists']}
    images = []
    for e in allimg:
        if e['exists']:
            continue
        e['refs'] = ['file:%s.png' % r[6:] if r.startswith('image:') and r[6:] in done else r for r in e['refs']]
        if 'after' in e:
            e['after'] = [a for a in e['after'] if a not in done]
            if not e['after']:
                del e['after']
        del e['exists']
        images.append(e)
    used = sorted({r[5:-4] for e in images for r in e['refs'] if r.startswith('file:')})
    zpath = os.path.join(ROOT, 'build/eusim_refs.zip')
    import zipfile
    with zipfile.ZipFile(zpath, 'w') as z:
        for n in used:
            z.write(os.path.join(ROOT, done[n]['out']), n + '.png')
    meta = {
        'game': 'EU Simulator (Nintendo DS homebrew)',
        'count': len(images),
        'by_category': {c: sum(1 for e in images if e['category'] == c) for c in ('portrait', 'slide', 'ui')},
        'conventions': {
            'refs': 'A URL is a reference photo (Wikimedia Commons, see ref_credit). "image:<name>" means the output '
                    'of another entry of this file; "after" lists the entries that must be generated first. '
                    '"file:<name>.png" is an image made earlier, provided in eusim_refs.zip.',
            'magenta': 'Portraits need a flat #FF00FF background (it becomes transparency).',
            'slides': '1536x1024, downscaled to 384x256 in game and shown with slow pan/zoom ("motion"). '
                      'Slides with a _alex/_max suffix exist in two versions, one per player character.',
            'out': 'Where to put the PNG in the project.',
        },
    }
    os.makedirs(os.path.join(ROOT, 'build'), exist_ok=True)
    json.dump({'meta': meta, 'images': images}, open(os.path.join(ROOT, 'build/eusim_images.json'), 'w'),
              ensure_ascii=False, indent=1)
    json.dump(plan, open(os.path.join(ROOT, 'build/eusim_scenes.json'), 'w'), ensure_ascii=False, indent=1)
    print(json.dumps(meta['by_category']), 'total', len(images), 'refs zip', len(used),
          'scenes', len(plan), 'slides', sum(len(SCENES[i][2]) for i in range(len(SCENES))))


if __name__ == '__main__':
    main()
