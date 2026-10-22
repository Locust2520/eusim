#!/usr/bin/env python3
"""Generates data/species.json (100 Euromons) with automatic learnsets from type move pools."""
import json, os
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
D = os.path.join(ROOT, 'data')
moves = json.load(open(os.path.join(D, 'moves.json'), encoding='utf-8'))
MV = {m['id']: m for m in moves}

ARCH = {
    'bal': [1, 1, 1, 1, 1, 1], 'phys': [1, 1.4, 1, .6, .9, 1.1], 'spec': [1, .6, .9, 1.4, 1.1, 1],
    'tank': [1.3, .9, 1.4, .7, 1.2, .5], 'fast': [.9, 1.1, .7, 1.1, .8, 1.4], 'wall': [1.5, .6, 1.1, .7, 1.4, .7],
    'glass': [.8, 1.3, .6, 1.3, .6, 1.4], 'mixed': [1, 1.2, .9, 1.2, .9, .9],
}

# id, name, types, total, arch, growth, catch, evo, category, color, shape, dex
S = [
 ('verdeal', "GreenDeer", ['VERT'], 309, 'spec', 'parabolic', 45, (16, 'fit55'), "Green Deal", 'green', 'quadruped', "Born with the 2019 Green Deal. A sprout shoots up every time an emissions standard is voted."),
 ('fit55', 'Fit55', ['VERT'], 405, 'spec', 'parabolic', 45, (36, 'neutralis'), "Climate Goal", 'green', 'quadruped', "It trains to cut its emissions by 55% by 2030. It counts every calorie."),
 ('neutralis', 'Neutralis', ['VERT', 'FEDERAL'], 525, 'spec', 'parabolic', 45, None, "Neutrality", 'green', 'quadruped', "It aims for carbon neutrality in 2050. Until then, it plants a tree with every step."),
 ('charbonnet', "Coalbonnet", ['INDUSTRIE'], 309, 'phys', 'parabolic', 45, (16, 'hautfourno'), "Coal", 'black', 'biped', "A small heap of coal from the 1951 ECSC. It blackens everything it touches, enthusiastically."),
 ('hautfourno', "Furnacio", ['INDUSTRIE'], 405, 'phys', 'parabolic', 45, (36, 'cecagon'), "Blast Furnace", 'orange', 'biped', "Its chimney spits sparks when it gets angry. It dreams of full employment."),
 ('cecagon', "Steelagon", ['INDUSTRIE', 'FEDERAL'], 525, 'phys', 'parabolic', 45, None, "Pooled Steel", 'grey', 'biped', "Forged in pooled coal and steel. It is proof that peace can be manufactured."),
 ('atomino', 'Atomino', ['ENERGIE'], 309, 'fast', 'parabolic', 45, (16, 'euratome'), "Atom", 'yellow', 'blob', "A curious little atom, born of the 1957 Euratom treaty. It can't sit still."),
 ('euratome', 'Euratome', ['ENERGIE'], 405, 'fast', 'parabolic', 45, (36, 'fissionix'), "Reactor", 'yellow', 'blob', "Its electrons spin so fast it lights up a whole room. Energy saving optional."),
 ('fissionix', 'Fissionix', ['ENERGIE', 'TECHNO'], 525, 'fast', 'parabolic', 45, None, 'Fission', 'cyan', 'blob', "It splits in two when it's upset. It and the Greens are no longer on speaking terms."),
 ('tampono', "Stampon", ['JURIDIQUE'], 280, 'tank', 'medium', 255, (14, 'paraphor'), "Stamp", 'brown', 'object', "A living stamp that approves everything it meets. It has already stamped its own trainer."),
 ('paraphor', "Initialor", ['JURIDIQUE'], 390, 'tank', 'medium', 120, (32, 'ratifix'), "Signature Book", 'red', 'object', "It initials every page at the bottom right. It needs four hours per treaty."),
 ('ratifix', 'Ratifix', ['JURIDIQUE', 'FEDERAL'], 495, 'tank', 'medium', 45, None, 'Ratification', 'red', 'object', "It only moves when 27 national parliaments have said yes. So it sleeps a lot."),
 ('amendon', 'Amendon', ['TECHNO'], 260, 'bal', 'fast', 255, (20, 'amendomax'), "Amendment", 'white', 'insect', "It multiplies by the thousand with every bill. Parliament sometimes receives 2,000 per report."),
 ('amendomax', 'Amendomax', ['TECHNO', 'POPULISTE'], 420, 'bal', 'fast', 90, None, "Filibuster", 'white', 'insect', "It tables so many amendments that it blocks the whole sitting. A well-honed technique."),
 ('cookiz', 'Cookiz', ['NUMERIQUE'], 270, 'fast', 'medium', 200, (22, 'consentor'), "Cookie Banner", 'tan', 'blob', "It has appeared in front of every door since the 2018 GDPR. Rejecting it is never enough."),
 ('consentor', 'Consentor', ['NUMERIQUE', 'JURIDIQUE'], 450, 'spec', 'medium', 60, None, "Consent", 'tan', 'blob', "It asks for your consent to everything, then for consent to the consent itself. It's very polite."),
 ('usbece', "Usbeecee", ['NUMERIQUE'], 400, 'fast', 'medium', 90, None, "Charger", 'grey', 'serpent', "Mandatory on all devices since late 2024. It put a whole drawer of cables out of work."),
 ('bouchatach', "Tethercap", ['VERT'], 330, 'tank', 'fast', 190, None, "Bottle Cap", 'blue', 'object', "It hasn't left its bottle since July 2024. It hits your nose when you drink."),
 ('pailleplast', "Strawraith", ['VERT', 'FANTOME'], 380, 'glass', 'slow', 25, None, "Lost Straw", 'pink', 'serpent', "Banned since 2021, it was thought extinct. It haunts fast-food restaurants at night."),
 ('courbana', "Curvanana", ['AGRICOLE'], 300, 'phys', 'fast', 190, None, "Banana", 'yellow', 'serpent', "A 1994 regulation sets its quality. It spends its life measuring its own curvature."),
 ('roamy', 'Roamy', ['NUMERIQUE'], 290, 'fast', 'fast', 190, (24, 'roamfree'), "Free roaming", 'cyan', 'flyer', "It travels everywhere at no extra cost since June 2017. It calls its mum from every border."),
 ('roamfree', 'Roamfree', ['NUMERIQUE', 'DIPLO'], 455, 'fast', 'fast', 75, None, "Borderless", 'cyan', 'flyer', "It visited all 27 countries in one weekend and live-posted everything. No surcharge."),
 ('erasmouse', 'Erasmouse', ['SOCIAL'], 285, 'fast', 'medium', 190, (20, 'erasmusplus'), "Student", 'beige', 'quadruped', "This little rodent goes abroad for a semester and comes back bilingual. Born in 1987."),
 ('erasmusplus', 'Erasmus+', ['SOCIAL', 'LIBERAL'], 460, 'fast', 'medium', 60, None, "Exchange", 'beige', 'quadruped', "It has lived in 12 flatshares and cooks pasta in 9 languages."),
 ('eurolo', "Eurorolo", ['MONETAIRE'], 290, 'bal', 'medium', 190, (25, 'eurozone'), "Coin", 'gold', 'object', "A €2 coin that has rolled everywhere since 2002. It has 27 possible national sides."),
 ('eurozone', 'Eurozone', ['MONETAIRE', 'FEDERAL'], 470, 'bal', 'medium', 60, None, "Single Currency", 'gold', 'object', "Twenty countries share its strength. When one coughs, the others get a fever."),
 ('schengeon', "Schengeon", ['DIPLO'], 420, 'fast', 'medium', 90, None, "Free Movement", 'blue', 'flyer', "Born on a boat on the Moselle in 1985. No border can hold it back."),
 ('glyphosaure', "Glyphosaur", ['AGRICOLE', 'LOBBY'], 440, 'phys', 'slow', 75, None, 'Herbicide', 'olive', 'quadruped', "Reauthorised for ten years in 2023. Weeds tremble as it passes."),
 ('lobbyrax', 'Lobbyrax', ['LOBBY'], 290, 'mixed', 'medium', 190, (18, 'lobbyron'), "Canvasser", 'black', 'humanoid', "It roams the corridors with a briefcase bigger than itself. It doesn't lobby, it “informs”."),
 ('lobbyron', 'Lobbyron', ['LOBBY'], 405, 'mixed', 'medium', 90, (38, 'lobbyzilla'), "Influencer", 'black', 'humanoid', "It knows the number of every parliamentary assistant. And their allergies."),
 ('lobbyzilla', 'Lobbyzilla', ['LOBBY', 'SOUVERAIN'], 530, 'mixed', 'medium', 45, None, "Mega-lobby", 'black', 'humanoid', "One of Brussels' 25,000 lobbyists, in giant form. It rewrites laws in its sleep."),
 ('transhumon', 'Transhumon', ['TECHNO'], 300, 'tank', 'medium', 190, (30, 'transhumax'), "Iron Trunk", 'grey', 'object', "An iron trunk that goes Brussels–Strasbourg twelve times a year. It gets travel sick."),
 ('transhumax', 'Transhumax', ['TECHNO', 'DIPLO'], 470, 'tank', 'medium', 75, None, "Relocation", 'grey', 'object', "It carries an entire parliament in its belly. Cost of the trip: don't ask."),
 ('changheure', "Clockback", ['TECHNO', 'FANTOME'], 450, 'spec', 'slow', 45, None, "Clock Change", 'purple', 'object', "Parliament voted to abolish it in 2019. Yet it still comes back twice a year."),
 ('diesgate', "Dieselgate", ['INDUSTRIE', 'LOBBY'], 430, 'phys', 'medium', 75, None, "Fraud", 'grey', 'object', "It has cheated on tests since 2015: clean on the test bench, smoky on the road."),
 ('spitzen', 'Spitzen', ['FEDERAL'], 460, 'phys', 'slow', 45, None, "Lead Candidate", 'blue', 'humanoid', "It campaigns for the presidency… then someone else is appointed instead."),
 ('interpreton', "Interpreton", ['DIPLO'], 300, 'spec', 'fast', 150, None, "Interpreter", 'teal', 'humanoid', "It speaks 24 languages, always with a two-second delay."),
 ('trilogon', 'Trilogon', ['JURIDIQUE', 'DIPLO'], 470, 'spec', 'slow', 45, None, 'Trilogue', 'purple', 'blob', "Three heads: Parliament, Council, Commission. They reach agreement around 4 a.m."),
 ('comitologue', "Comitologist", ['TECHNO'], 420, 'wall', 'slow', 75, None, "Comitology", 'grey', 'humanoid', "Nobody knows exactly what it does. Yet it sits on 300 committees."),
 ('paperasse_mon', "Redtapor", ['TECHNO'], 260, 'tank', 'fast', 255, (18, 'archivor'), "Form", 'white', 'object', "A pile of forms in triplicate. There's always one page missing."),
 ('archivor', 'Archivor', ['TECHNO', 'JURIDIQUE'], 430, 'tank', 'fast', 90, None, 'Archives', 'brown', 'object', "It keeps everything, even sticky notes from 1958. Filing system: alphabetical and emotional."),
 ('agrikolo', "Agricolo", ['AGRICOLE'], 290, 'tank', 'medium', 190, (18, 'pactor'), "Small Farmer", 'green', 'biped', "It gets a CAP payment for each hectare. It counts its hectares every morning."),
 ('pactor', "CAPtor", ['AGRICOLE'], 410, 'tank', 'medium', 90, (36, 'megapac'), "CAP", 'green', 'biped', "It swallows a third of the European budget without flinching. It's always hungry."),
 ('megapac', "MegaCAP", ['AGRICOLE', 'SOUVERAIN'], 525, 'tank', 'medium', 45, None, "Farm Policy", 'green', 'biped', "When it blocks the motorway with its tractors, even the Council negotiates."),
 ('tracteuron', "Tractoron", ['AGRICOLE', 'INDUSTRIE'], 440, 'tank', 'medium', 75, None, "Protest", 'red', 'object', "It parks in front of Parliament at every reform. Horn-honking guaranteed."),
 ('fromajus', "Cheeson", ['AGRICOLE'], 300, 'tank', 'fast', 190, (26, 'appellatio'), "Cheese", 'yellow', 'blob', "A little raw-milk cheese that smells very strong. It's proud of its terroir."),
 ('appellatio', "PDOsaur", ['AGRICOLE', 'JURIDIQUE'], 460, 'tank', 'fast', 75, None, "PDO", 'yellow', 'blob', "Protected by a designation of origin. Any imitation is taken to court."),
 ('pralinou', "Pralino", ['SOCIAL'], 310, 'bal', 'fast', 190, None, 'Praline', 'brown', 'blob', "A very kind Belgian chocolate. It melts when you pay it a compliment."),
 ('frituron', "Fryon", ['SOCIAL', 'INDUSTRIE'], 360, 'phys', 'fast', 150, None, "Belgian Fry", 'yellow', 'insect', "Fried twice, as it should be. It flatly refuses to be called “French”."),
 ('pigeonix', 'Pigeonix', ['POPULISTE'], 250, 'fast', 'fast', 255, None, 'Pigeon', 'grey', 'flyer', "It lives on Place du Luxembourg and steals lobbyists' fries. It knows all the gossip."),
 ('manneken', 'Manneken', ['SOCIAL', 'FANTOME'], 400, 'spec', 'medium', 60, None, "Little Fellow", 'bronze', 'humanoid', "A little 55 cm statue with more costumes than the whole of Parliament."),
 ('atomiom', 'Atomiom', ['ENERGIE', 'TECHNO'], 480, 'spec', 'slow', 45, None, 'Atomium', 'silver', 'blob', "Nine steel spheres linked as a crystal, since Expo 58. It shines over Brussels at night."),
 ('stagion', "Internix", ['SOCIAL'], 250, 'fast', 'parabolic', 255, (16, 'contractuel'), "Intern", 'blue', 'humanoid', "It works a lot and isn't paid. It says it's “a learning experience”."),
 ('contractuel', "Tempurion", ['SOCIAL', 'TECHNO'], 380, 'bal', 'parabolic', 120, (34, 'titularis'), "Temp Agent", 'blue', 'humanoid', "Its contract ends in three months. It has been renewing it for six years."),
 ('titularis', "Tenuris", ['TECHNO', 'FEDERAL'], 500, 'wall', 'parabolic', 45, None, "Civil servant", 'navy', 'humanoid', "It passed the EPSO competition. It fears nothing any more, except pension reform."),
 ('populo', "Grumbleon", ['POPULISTE'], 270, 'phys', 'medium', 200, (20, 'tribun'), "Grumbler", 'red', 'biped', "It's against. Against what doesn't matter, it's against."),
 ('tribun', "Tribunon", ['POPULISTE'], 400, 'phys', 'medium', 90, (36, 'demagogor'), "Orator", 'red', 'biped', "It climbs onto every table to harangue the crowd. Even in the canteen."),
 ('demagogor', "Demagogor", ['POPULISTE', 'SOUVERAIN'], 520, 'phys', 'medium', 45, None, "Demagogue", 'red', 'biped', "It promises everything to everyone. Its promises evaporate at dawn."),
 ('fakeon', 'Fakeon', ['NUMERIQUE', 'POPULISTE'], 410, 'spec', 'fast', 75, None, "Fake News", 'orange', 'flyer', "It changes shape depending on who's looking at it. It's very widely shared."),
 ('trollbot', 'Trollbot', ['NUMERIQUE'], 280, 'glass', 'fast', 190, (24, 'botfarm'), "Fake Account", 'grey', 'object', "A little robot that comments on everything in capitals. It has never slept."),
 ('botfarm', 'Botfarm', ['NUMERIQUE', 'LOBBY'], 450, 'glass', 'fast', 60, None, "Troll Farm", 'grey', 'object', "Ten thousand accounts in a single box. Elections know it well."),
 ('algoritmo', "Algorithmo", ['NUMERIQUE'], 300, 'spec', 'medium', 150, (30, 'iact'), "Algorithm", 'cyan', 'serpent', "It learns from everything you do. It already knows what you're going to catch."),
 ('iact', "AIAct", ['NUMERIQUE', 'JURIDIQUE'], 480, 'spec', 'medium', 45, None, "Regulated AI", 'cyan', 'serpent', "The world's first regulation on artificial intelligence (2024) brought it into line."),
 ('inflaton', 'Inflaton', ['MONETAIRE'], 290, 'tank', 'medium', 190, (28, 'hyperflaton'), 'Inflation', 'pink', 'blob', "It swells a little every month. Households keep a close eye on it."),
 ('hyperflaton', 'Hyperflaton', ['MONETAIRE'], 460, 'tank', 'medium', 60, None, 'Hyperinflation', 'pink', 'blob', "So big it blocks the streets. The ECB raises rates to make it slim down."),
 ('spreadon', 'Spreadon', ['MONETAIRE', 'POPULISTE'], 420, 'glass', 'medium', 90, None, "Rate Gap", 'red', 'serpent', "It stretches with every clumsy statement by a central banker."),
 ('cryptou', 'Cryptou', ['MONETAIRE', 'NUMERIQUE'], 290, 'glass', 'erratic' if False else 'fast', 190, (30, 'mica'), "Cryptocurrency", 'orange', 'object', "It's worth a fortune in the morning and nothing at night. It loves roller coasters."),
 ('mica', 'MiCA', ['MONETAIRE', 'JURIDIQUE'], 460, 'bal', 'fast', 60, None, "Regulated Crypto", 'orange', 'object', "The MiCA regulation made it wear a tie. It's calmer now."),
 ('austerix', "Austerix", ['MONETAIRE', 'SOUVERAIN'], 440, 'wall', 'slow', 75, None, "Balanced Budget", 'black', 'biped', "It never spends anything, not even its energy. Its cry: “Schwarze Null!”"),
 ('troikat', "Troicat", ['MONETAIRE', 'DIPLO'], 470, 'mixed', 'slow', 45, None, "Troika", 'grey', 'quadruped', "Three cats: ECB, Commission, IMF. Together they inspect other people's accounts."),
 ('vetoad', 'Vetoad', ['SOUVERAIN'], 300, 'tank', 'medium', 190, (30, 'vetoadmax'), 'Veto', 'green', 'quadruped', "A toad that croaks “no!” at every proposal. It takes just one to block everything."),
 ('vetoadmax', 'Vetoadmax', ['SOUVERAIN', 'POPULISTE'], 480, 'tank', 'medium', 60, None, "Unanimity", 'green', 'quadruped', "It demands unanimity for every decision, then refuses it itself."),
 ('frontierex', "Borderix", ['SOUVERAIN'], 400, 'tank', 'medium', 90, None, "Barrier", 'brown', 'object', "It reappears whenever border checks are mentioned. It has its own sentry box."),
 ('brexitt', 'Brexitt', ['SOUVERAIN', 'POPULISTE'], 420, 'fast', 'medium', 60, None, "Exit", 'navy', 'flyer', "It wanted to leave in 2016, left in 2020, and sometimes regrets it. It often leaves battles."),
 ('referendo', "Referendo", ['POPULISTE', 'SOUVERAIN'], 410, 'spec', 'medium', 75, None, 'Consultation', 'white', 'object', "A ballot box that asks simple questions about complicated problems."),
 ('assistome', "Ghostaide", ['FANTOME'], 300, 'spec', 'medium', 150, (30, 'emploifictif'), "Ghost assistant", 'lavender', 'humanoid', "Paid by Parliament, it has never set foot there. Nobody has ever seen it work."),
 ('emploifictif', "Ghostjob", ['FANTOME', 'LOBBY'], 470, 'spec', 'medium', 60, None, "Fake Job", 'lavender', 'humanoid', "It has a badge, a contract and a payslip. But no office."),
 ('sacabillet', "Cashbag", ['LOBBY', 'FANTOME'], 450, 'phys', 'slow', 30, None, "Bag of Cash", 'green', 'object', "Found full of banknotes in a Brussels flat in December 2022."),
 ('valisette', "Caseling", ['LOBBY'], 300, 'tank', 'fast', 190, None, "Briefcase", 'brown', 'object', "A small suitcase that passes from hand to hand at the foot of Parliament."),
 ('gazoduc', "Pipelino", ['ENERGIE', 'SOUVERAIN'], 440, 'tank', 'slow', 60, None, 'Pipeline', 'grey', 'serpent', "1,200 km long under the sea. Its tap is controlled by someone else."),
 ('eolion', "Windion", ['ENERGIE', 'VERT'], 330, 'fast', 'medium', 150, (32, 'offshorion'), "Wind Turbine", 'white', 'flyer', "Its blades spin as soon as you blow on it. It hates windless days."),
 ('offshorion', 'Offshorion', ['ENERGIE', 'VERT'], 480, 'fast', 'medium', 60, None, "Offshore Wind", 'white', 'flyer', "It lives off the North Sea coast and powers entire cities."),
 ('solario', 'Solario', ['ENERGIE', 'VERT'], 410, 'spec', 'medium', 90, None, "Solar Panel", 'blue', 'object', "It sleeps at night and works hard by day, especially in Spain."),
 ('plafonnor', "Capnor", ['ENERGIE', 'MONETAIRE'], 420, 'wall', 'medium', 75, None, "Price Cap", 'red', 'object', "It stops prices from rising too high. Its neck hurts from all the pushing."),
 ('tarifaux', "Tariffix", ['POPULISTE'], 300, 'phys', 'medium', 190, (30, 'tarifator'), "Tariff", 'orange', 'quadruped', "It taxes everything that passes in front of it. Even dead leaves."),
 ('tarifator', "Tariffator", ['POPULISTE', 'MONETAIRE'], 480, 'phys', 'medium', 60, None, "Trade War", 'orange', 'quadruped', "It brandishes a giant board of taxes. The figures change every morning."),
 ('terrara', "Rarium", ['INDUSTRIE', 'NUMERIQUE'], 450, 'tank', 'slow', 45, None, "Rare Earths", 'purple', 'object', "A little pebble that every phone depends on. Its exports are being watched."),
 ('pandiplo', 'Pandiplo', ['DIPLO'], 410, 'wall', 'slow', 45, None, "Panda Diplomat", 'white', 'quadruped', "On loan to a European zoo for a few years. It eats bamboo and trade agreements."),
 ('censourson', "Censorcub", ['FANTOME', 'POPULISTE'], 420, 'spec', 'slow', 30, None, "Content Unavailable", 'yellow', 'quadruped', "This yellow bear cub is not visible in any region. Its entry has been removed."),
 ('pigeon_lux', "Kirchgeon", ['JURIDIQUE', 'FLYER'] if False else ['JURIDIQUE', 'DIPLO'], 380, 'fast', 'medium', 150, None, "Lawyer Pigeon", 'grey', 'flyer', "It nests on the Court of Justice towers in Kirchberg and coos in Latin."),
 ('schumark', 'Schumark', ['FEDERAL', 'DIPLO'], 430, 'bal', 'slow', 45, None, "Declaration", 'blue', 'humanoid', "It recites the declaration of 9 May 1950 to anyone who will listen. It appears on Europe Day."),
 ('nobelix', 'Nobelix', ['DIPLO', 'FEDERAL'], 470, 'wall', 'slow', 30, None, "Nobel Prize", 'gold', 'object', "A medal awarded to the European Union in 2012. It shines with pride."),
 ('bruxellair', "Drizzels", ['TECHNO', 'VERT'], 320, 'spec', 'fast', 190, None, "Drizzle", 'grey', 'flyer', "A little Brussels cloud. It rains on you 200 days a year."),
 ('dejeunix', 'Lunchix', ['SOCIAL', 'LOBBY'], 340, 'bal', 'fast', 150, None, "Business Lunch", 'red', 'blob', "A three-hour working lunch. More gets decided there than in the chamber."),
 ('mercosaur', 'Mercosaur', ['AGRICOLE', 'DIPLO'], 480, 'tank', 'slow', 45, None, "Trade Deal", 'green', 'quadruped', "It has been under negotiation since 1999. When it takes one step forward, the tractors push it back."),
 ('romulus', 'Romulus', ['JURIDIQUE', 'FEDERAL'], 600, 'bal', 'slow', 3, None, "Treaty of Rome", 'marble', 'humanoid', "Born on 25 March 1957 on the Capitol. It founded the European Economic Community."),
 ('maastrichtor', "Maastrix", ['MONETAIRE', 'FEDERAL'], 600, 'mixed', 'slow', 3, None, "Maastricht Treaty", 'gold', 'serpent', "Born in the Netherlands in 1992. It created the Union and dreamed up the euro."),
 ('lisbonia', 'Lisbonia', ['JURIDIQUE', 'DIPLO'], 600, 'spec', 'slow', 3, None, "Treaty of Lisbon", 'blue', 'flyer', "Signed in 2007, it took over most of a constitution that never saw the light of day."),
 ('constitutio', 'Constitutio', ['FEDERAL', 'FANTOME'], 640, 'spec', 'slow', 1, None, 'Constitution', 'white', 'flyer', "Rejected by referendum in France and the Netherlands in 2005. It flees as soon as you approach."),
 ('draghizord', 'Draghizord', ['MONETAIRE', 'TECHNO'], 620, 'spec', 'slow', 3, None, 'Whatever it takes', 'navy', 'humanoid', "It knows only one move, and it always succeeds. It saved the euro with one sentence."),
]
assert len(S) == 100, len(S)

SIGNATURE = {
    'romulus': ['traite_rome'], 'maastrichtor': ['traite_maastricht'], 'lisbonia': ['traite_lisbonne'],
    'constitutio': ['constitution', 'disparition'], 'draghizord': ['whatever'],
    'vetoad': ['veto'], 'vetoadmax': ['veto', 'article_7'], 'brexitt': ['article_50', 'bus_rouge'],
    'trilogon': ['trilogue'], 'changheure': ['reunion', 'disparition'], 'tarifator': ['droits_douane', 'tremendous'],
    'tarifaux': ['droits_douane'], 'terrara': ['terres_rares'], 'pandiplo': ['rival_systemique', 'soft_power'],
    'gazoduc': ['robinet_gaz', 'longue_table'], 'sacabillet': ['sac_billets', 'petits_fours'],
    'bouchatach': ['bouchon_attache'], 'courbana': ['banane_courbe'], 'usbece': ['usb_c'],
    'cookiz': ['cookie'], 'roamy': ['roaming'], 'erasmouse': ['erasmus'], 'eurolo': ['piece_euro'],
    'glyphosaure': ['glyphosate'], 'transhumon': ['paperasse'], 'iact': ['ia_act'], 'fakeon': ['fake_news'],
    'austerix': ['austerite'], 'troikat': ['austerite', 'plan_relance'], 'spitzen': ['spitzen'],
    'interpreton': ['interprete'], 'assistome': ['emploi_fictif'], 'emploifictif': ['fantome_payroll', 'sms_efface'],
    'neutralis': ['neutralite'], 'fit55': ['fit_for_55'], 'cecagon': ['airbus'], 'fissionix': ['fusion'],
    'ratifix': ['arret_cjue'], 'amendon': ['amendement'], 'amendomax': ['trilogue'], 'atomiom': ['fission'],
    'eurozone': ['quantitative'], 'tracteuron': ['tracteur'], 'megapac': ['pac', 'moisson'], 'pactor': ['pac'],
    'schengeon': ['marche_unique'], 'mercosaur': ['accord', 'tracteur'], 'nobelix': ['accord', 'soft_power'],
    'schumark': ['drapeau_etoile', 'integration'], 'demagogor': ['tweet_majuscules'], 'tribun': ['megaphone'],
    'populo': ['slogan'], 'botfarm': ['troll', 'fake_news'], 'trollbot': ['troll'], 'mica': ['rgpd'],
    'censourson': ['hantise', 'disparition'], 'pailleplast': ['hantise'], 'manneken': ['hantise'],
}


def stats(total, arch):
    w = ARCH[arch]
    s = sum(w)
    b = [max(10, round(total * x / s)) for x in w]
    b[0] += total - sum(b)
    return b


def learnset(sp):
    sid, types, total = sp[0], sp[2], sp[3]
    lv_max = 60 if total >= 450 else 45
    pool = []
    for t in types:
        pool += [m for m in moves if m['type'] == t and m['id'] not in
                 ('constitution', 'traite_rome', 'traite_maastricht', 'traite_lisbonne', 'whatever',
                  'terres_rares', 'longue_table', 'rival_systemique', 'chantage_groenland')]
    dmg = sorted([m for m in pool if m['cat'] != 'status'], key=lambda m: (m['power'], m['id']))
    st = [m for m in pool if m['cat'] == 'status']
    out = [(1, 'amendement' if 'TECHNO' not in types else 'paperasse')]
    if dmg:
        out.append((1, dmg[0]['id']))
    later = dmg[1:]
    n = len(later)
    for i, m in enumerate(later):
        lv = 5 + round((lv_max - 5) * (i + 1) / (n + 1))
        out.append((lv, m['id']))
    for i, m in enumerate(st[:2]):
        out.append((8 + i * 14, m['id']))
    if total < 350:
        out.append((4, 'reunion' if 'FANTOME' not in types else 'disparition'))
    for i, mid in enumerate(SIGNATURE.get(sid, [])):
        out.append((1 if total >= 600 else 10 + i * 12, mid))
    seen, res = set(), []
    for lv, mid in sorted(out):
        if mid in seen or mid not in MV:
            continue
        seen.add(mid)
        res.append([lv, mid])
    return res[:14]


out = []
for num, sp in enumerate(S, 1):
    sid, name, types, total, arch, growth, catch, evo, cat, color, shape, dex = sp
    e = None
    if evo:
        e = {'level': evo[0], 'into': evo[1]}
    exp = max(40, total // 4) if not evo else max(40, total // 5)
    out.append({'id': sid, 'num': num, 'name': name, 'types': types, 'base': stats(total, arch), 'growth': growth,
                'catch': catch, 'exp': exp, 'evo': e, 'moves': learnset(sp), 'dex': dex, 'category': cat,
                'color': color, 'shape': shape})
json.dump(out, open(os.path.join(D, 'species.json'), 'w'), ensure_ascii=False, indent=1)
# checks
ids = {s['id'] for s in out}
for s in out:
    assert len(s['name']) <= 12, s['name']
    if s['evo']:
        assert s['evo']['into'] in ids, s['evo']
print('species', len(out))
