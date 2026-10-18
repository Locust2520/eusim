#!/usr/bin/env python3
"""data/trainers.json and data/encounters.json"""
import json, os
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
D = os.path.join(ROOT, 'data')
T = []


def t(id, name, cls, party, intro, defeat, win='', sprite='fonctionnaire', portrait=None, money=40, ai=1, music=None):
    T.append(dict(id=id, name=name, cls=cls, party=party, intro=intro, defeat=defeat, win=win, sprite=sprite,
                  portrait=portrait, money=money, ai=ai, music=music))


# ---- chapter 1-2
t('stagiaire_hugo', 'Hugo', 'Stagiaire', [['amendon', 4], ['pigeonix', 5]],
  "Hé, le nouveau ! Ici, on règle tout par un débat. Montre-moi ce que tu vaux !",
  "Argh… J'aurais dû relire mes notes de synthèse.", "Ha ! Retourne à la photocopieuse !", 'stagiaire', money=15, ai=0)
for st, (rv, pl) in {'v': ('charbonnet', 'verdeal'), 'c': ('atomino', 'charbonnet'), 'a': ('verdeal', 'atomino')}.items():
    t(f'oliver1_{st}', 'Oliver', 'Rival', [[rv, 5]],
      "Alors, {P}, on teste nos Euromons ? Mine is obviously better.", "What?! C'était un coup de chance !",
      "Easy. Comme prévu.", 'oliver', 'oliver', 30, 1, 'rival')
    t(f'oliver2_{st}', 'Oliver', 'Rival', [['pigeonix', 8], ['erasmouse', 8], [rv, 10]],
      "{P} ! Tu as déjà un badge ? Pas grave, je vais te le faire regretter.", "Not again… Bon, à Francfort, tu verras.",
      "Ha ! Le Luxembourg me réussit.", 'oliver', 'oliver', 40, 1, 'rival')
    evo1 = {'charbonnet': 'hautfourno', 'atomino': 'euratome', 'verdeal': 'fit55'}[rv]
    t(f'oliver3_{st}', 'Oliver', 'Rival', [['pigeonix', 16], ['erasmouse', 17], ['eurolo', 16], [evo1, 19]],
      "Je viens de visiter la BCE. J'ai tout compris à la politique monétaire. Presque tout.",
      "Bloody hell… Tu progresses vraiment vite, {P}.", "Comme on dit à la City : time is money.", 'oliver', 'oliver', 60, 1, 'rival')
    evo2 = {'charbonnet': 'hautfourno', 'atomino': 'euratome', 'verdeal': 'fit55'}[rv]
    t(f'oliver4_{st}', 'Oliver', 'Rival', [['pigeonix', 30], ['erasmusplus', 31], ['eurozone', 31], ['brexitt', 32], [evo2, 34]],
      "{P}… c'est notre dernier débat. Après, je rentre à Londres. Pour de bon. Allez, one last time !",
      "Good game, {P}. Au moins, je pars avec le panache.", "Je pars sur une victoire. C'est déjà ça.", 'oliver', 'oliver', 80, 2, 'rival')
    final = {'charbonnet': 'cecagon', 'atomino': 'fissionix', 'verdeal': 'neutralis'}[rv]
    t(f'oliver5_{st}', 'Oliver', 'Rival', [['brexitt', 62], ['erasmusplus', 62], ['eurozone', 63], ['roamfree', 63], ['iact', 64], [final, 66]],
      "{P} ! I'm back. Enfin… je demande à revenir. Rejoin ? Mais d'abord, un débat pour l'honneur !",
      "Bon. Je remplis le formulaire d'adhésion. Il fait 35 chapitres…", "Ha ! Comme quoi, sortir rend plus fort. Ou pas.", 'oliver', 'oliver', 120, 2, 'rival')
t('r1_stagiaire', 'Léa', 'Stagiaire', [['erasmouse', 5], ['amendon', 6]], "Moi aussi je suis stagiaire ! Non payée, comme toi. Débattons, ça console.",
  "Bon… je retourne faire des photocopies.", "", 'stagiaire_f', money=20, ai=0)
t('r1_fonctionnaire', 'M. Dupont', 'Fonctionnaire', [['paperasse_mon', 6], ['paperasse_mon', 6], ['comitologue', 7]],
  "Halte ! Votre formulaire de randonnée A-38 est-il visé ?", "Bon, je vous le vise. Mais en triple exemplaire.", "", 'fonctionnaire', money=30)
t('r1_agriculteur', 'Gérard', 'Agriculteur', [['agrikolo', 7], ['courbana', 7]],
  "La PAC, c'est ma vie ! Et mon tracteur, c'est ma famille. Allez, on débat !", "Faudra que j'en parle au syndicat…", "", 'agriculteur', money=30)
t('lux_banquier', 'Pierre-Henri', 'Banquier privé', [['eurolo', 9], ['valisette', 10]],
  "Bienvenue au Luxembourg. Discrétion absolue. Ce débat n'a jamais eu lieu.", "Ce débat n'a définitivement jamais eu lieu.", "", 'banquier', money=60)
t('lux_fiscaliste', 'Maître Klein', 'Fiscaliste', [['valisette', 10], ['paperasse_mon', 10], ['eurolo', 11]],
  "Un rescrit fiscal ? Je vous en rédige un en cinq minutes. Mais d'abord, un débat.", "Mes montages… effondrés !", "", 'avocat', money=60)
t('juncker', 'Jean-Claude Juncker', 'Champion d\'arène', [['eurolo', 12], ['inflaton', 12], ['spreadon', 14]],
  "Ah, un jeune stagiaire ! Viens, viens, que je te tapote la joue. Puis on débat, comme au bon vieux temps de l'Eurogroupe.",
  "Bravo ! Tu mérites le Badge Rescrit. Et ça, ce n'est pas confidentiel !", "Allez, ne fais pas cette tête, je plaisante… à moitié.",
  'juncker', 'juncker', 100, 2, 'gym_leader')
t('r2_touriste', 'Kevin', 'Touriste', [['roamy', 11], ['pigeonix', 11]], "Je fais la Moselle à vélo ! Et je débats en roaming, gratuitement !",
  "Même sans frais d'itinérance, j'ai tout perdu.", "", 'touriste', money=40)
t('r2_banquier', 'Hans', 'Analyste', [['inflaton', 12], ['eurolo', 12]], "Les marchés anticipent ma victoire à 87 %.",
  "Les marchés se sont trompés. Comme d'habitude.", "", 'banquier', money=60)
t('r2_vigneron', 'Jean-Marc', 'Vigneron', [['agrikolo', 12], ['fromajus', 12], ['courbana', 13]],
  "Mon crémant est AOP. Mes Euromons aussi. Ou presque.", "Bon, je vous offre un verre quand même.", "", 'agriculteur', money=50)
t('bce_trader', 'Karl', 'Trader', [['cryptou', 15], ['eurolo', 16]], "Achète bas, revends haut, débats fort !", "Krach ! Je suis à découvert !", "", 'banquier', money=80)
t('bce_economiste', 'Dr. Sofia', 'Économiste', [['inflaton', 16], ['spreadon', 16]],
  "Selon mon modèle, vous perdez. Mon modèle n'a jamais tort. Sauf en 2008.", "Je vais devoir réviser mes prévisions.", "", 'fonctionnaire_f', money=80)
t('lagarde', 'Christine Lagarde', 'Championne d\'arène', [['cryptou', 17], ['inflaton', 18], ['eurozone', 20]],
  "Bienvenue à la Banque centrale européenne. Ici, je fixe les taux… et le rythme du débat. Mes attaques dépendent du taux directeur du jour !",
  "Formidable. Vous méritez le Badge Euro. Et rassurez-vous : je ne suis pas là pour réduire votre spread.",
  "La stabilité des prix, c'est aussi la stabilité des victoires.", 'lagarde', 'lagarde', 110, 2, 'gym_leader')
t('r3_militant', 'Inès', 'Militante climat', [['eolion', 16], ['solario', 17]], "Chaque débat perdu, c'est un degré de plus ! Allez !",
  "Bon, au moins c'était neutre en carbone.", "", 'militant', money=40)
t('r3_journaliste', 'Tom', 'Journaliste', [['fakeon', 17], ['pigeonix', 17]], "Une exclusivité ! « Un stagiaire perd lamentablement » !",
  "Je change le titre : « Un stagiaire gagne lamentablement bien ».", "", 'journaliste', money=50)
t('r3_viticulteur', 'Albert', 'Viticulteur', [['fromajus', 18], ['agrikolo', 18], ['tracteuron', 19]],
  "Le Rhin, c'est la frontière ? Non, c'est le vin des deux côtés ! On trinque après le débat.", "Santé quand même !", "", 'agriculteur', money=50)
t('stras_depute1', 'Député Muller', 'Eurodéputé', [['amendon', 21], ['amendomax', 22]], "J'ai déposé 2 000 amendements ce matin. Le premier vous concerne.",
  "Mes amendements sont rejetés en bloc…", "", 'depute', money=80)
t('stras_depute2', 'Députée Rossi', 'Eurodéputée', [['interpreton', 22], ['transhumon', 22]],
  "La session a lieu à Strasbourg, nos malles sont arrivées, débattons !", "Je repars à Bruxelles. Avec mes malles.", "", 'deputee', money=80)
t('metsola', 'Roberta Metsola', 'Championne d\'arène', [['amendomax', 23], ['interpreton', 23], ['spitzen', 25]],
  "Silence dans l'hémicycle ! La séance est ouverte. Je donne la parole à… vous. Puis je vous la reprends.",
  "Adopté ! Le Badge Hémicycle vous est attribué à la majorité absolue.", "La séance est levée. Revenez à la prochaine session.",
  'metsola', 'metsola', 120, 2, 'gym_leader')
t('ath_economiste', 'Nikos', 'Économiste', [['inflaton', 26], ['referendo', 27]], "La dette, c'est comme la moussaka : ça se digère mal.",
  "OXI à cette défaite !", "", 'journaliste', money=80)
t('troika_bce', 'Agent Troïka (BCE)', 'Troïka', [['austerix', 27], ['eurozone', 27]], "Inspection des comptes ! Vos Euromons dépensent trop.",
  "Rapport d'inspection : défavorable.", "", 'banquier', money=90)
t('troika_fmi', 'Agent Troïka (FMI)', 'Troïka', [['spreadon', 27], ['hyperflaton', 28]], "Le Fonds monétaire international recommande… votre défaite.",
  "Révision de nos prévisions : à la baisse.", "", 'fonctionnaire', money=90)
t('varoufakis', 'Yanis Varoufakis', 'Champion d\'arène', [['erasmusplus', 28], ['manneken', 29], ['contractuel', 31]],
  "Je suis arrivé à moto, sans cravate. Comme en 2015 face à l'Eurogroupe. On débat, et on vote : OXI ou NAI ?",
  "OXI… pardon, NAI : tu as gagné. Prends le Badge OXI, camarade.", "Le peuple a parlé. Et le peuple, c'est moi.",
  'varoufakis', 'varoufakis', 130, 2, 'gym_leader')
t('lon_tabloid', 'Rédacteur en chef', 'Tabloïd', [['fakeon', 31], ['pigeonix', 31], ['trollbot', 32]],
  "UNE : « Bruxelles veut interdire les bananes courbes » ! C'est faux ? Pas grave, ça fait vendre.",
  "Demain en une : « Défaite historique ».", "", 'journaliste', money=90)
t('lon_johnson', 'Boris Johnson', 'Ex-Premier ministre', [['pigeonix', 32], ['fakeon', 33], ['referendo', 34]],
  "Hello ! J'étais correspondant à Bruxelles, vous savez. J'en ai écrit des choses… plus ou moins vraies. Get debate done !",
  "Crikey. Bon, j'avais un autre article sur les concombres droits, de toute façon.", "", 'johnson', 'johnson', 120, 2)
t('farage', 'Nigel Farage', 'Champion d\'arène', [['tribun', 34], ['vetoadmax', 34], ['brexitt', 36]],
  "Vous ne riez plus maintenant, hein ? Bienvenue au pub. Un débat, une pinte, et l'Article 50.",
  "Bon. Prenez le Badge Article 50. On n'en a plus besoin, nous.", "Take back control ! Du débat, en tout cas.",
  'farage', 'farage', 140, 2, 'gym_leader')
t('bud_douanier', 'Gábor', 'Garde-frontière', [['frontierex', 36], ['vetoad', 36]], "Contrôle ! Votre Euromon a-t-il un visa ?",
  "Passez. Mais je le note.", "", 'douanier', money=90)
t('bud_conseiller', 'Conseiller spécial', 'Conseiller', [['austerix', 37], ['demagogor', 37]],
  "Le Premier ministre ne reçoit personne. Sauf ceux qui me battent. Et ça n'arrive jamais.", "Ça vient d'arriver.", "", 'depute', money=90)
t('orban', 'Viktor Orbán', 'Champion d\'arène', [['vetoadmax', 38], ['frontierex', 38], ['austerix', 39], ['demagogor', 40]],
  "Vous voulez mon accord ? L'unanimité est requise. Et je ne suis jamais d'accord. Attention : je peux poser mon VETO à chaque tour.",
  "Bon… Je sors prendre un café. Pendant ce temps, prenez ce Badge Veto. Officiellement, je me suis abstenu.",
  "Veto ! Veto ! Et re-veto !", 'orban', 'orban', 150, 3, 'gym_leader')
t('lobby_sbire1', 'Lobbyiste du pétrole', 'Team Lobby', [['lobbyron', 36], ['diesgate', 37]], "Vous n'avez pas votre badge d'accès ? Ça tombe bien, nous non plus.",
  "Je vais devoir déclarer cette rencontre au registre de transparence…", "", 'lobbyiste', money=100)
t('lobby_sbire2', 'Lobbyiste de la tech', 'Team Lobby', [['botfarm', 37], ['trollbot', 36], ['algoritmo', 37]],
  "Notre algorithme a prédit votre défaite. Accepter les cookies ?", "Erreur 403 : défaite.", "", 'lobbyiste_f', money=100)
t('lobby_sbire3', 'Lobbyiste « de l\'étranger »', 'Team Lobby', [['valisette', 38], ['sacabillet', 38]],
  "Une petite valise pour votre vote ? Non ? Alors un débat.", "Je n'ai jamais rien donné à personne. Notez-le.", "", 'lobbyiste', money=120)
t('lobbychef', 'Le Lobbyiste en chef', 'Chef de la Team Lobby', [['sacabillet', 40], ['botfarm', 40], ['diesgate', 41], ['glyphosaure', 41], ['lobbyzilla', 43]],
  "Bienvenue au cœur du pouvoir, stagiaire. Ici, on n'écrit pas les lois : on les « suggère ». Et toi, tu vas signer ma suggestion.",
  "Impossible… Un simple stagiaire, non rémunéré… a vaincu le lobby. Je me retire. Dans le privé. Ah, j'y suis déjà.",
  "Merci pour cette contribution à notre consultation publique.", 'lobbychef', None, 200, 3, 'boss')
t('avocat_tech1', 'Avocat de Big Tech', 'Avocat', [['consentor', 40], ['iact', 40]], "Mon client conteste l'amende de 4,34 milliards. Et ce débat.",
  "Nous ferons appel.", "", 'avocat', money=120)
t('avocat_tech2', 'Juriste concurrence', 'Juriste', [['archivor', 41], ['appellatio', 41]], "Abus de position dominante ? Moi ? Je ne suis que dominant.",
  "Amende acceptée…", "", 'avocat', money=120)
t('vestager', 'Margrethe Vestager', 'Championne d\'arène', [['consentor', 42], ['iact', 42], ['appellatio', 43], ['ratifix', 44]],
  "Google, Apple… j'ai infligé des milliards d'amendes. Votre équipe respecte-t-elle les règles de concurrence ? Vérifions.",
  "Pas d'abus de position dominante détecté. Le Badge Amende est à vous.", "Amende ! 4 % de votre chiffre d'affaires.",
  'vestager', 'vestager', 160, 3, 'gym_leader')
for i, (fl, party) in enumerate({'1a': [['assistome', 38]], '1b': [['assistome', 38], ['pailleplast', 38]],
                                 '2a': [['changheure', 39], ['assistome', 39]], '2b': [['manneken', 40], ['assistome', 40]],
                                 '3a': [['emploifictif', 41]], '3b': [['pailleplast', 41], ['emploifictif', 41]]}.items()):
    t(f'fantome_{fl}', 'Assistant fantôme', 'Fantôme', party, "Bouh… Je travaille ici… depuis 2009… enfin, sur le papier…",
      "Je retourne… à mon contrat… fictif…", "", 'fantome', money=60)
t('fantome_boss', 'Le Contrat Vide', 'Esprit des emplois fictifs', [['changheure', 43], ['sacabillet', 43], ['emploifictif', 45]],
  "JE SUIS… LA SOMME DE TOUS LES CONTRATS QUI N'ONT JAMAIS EU DE BUREAU…", "Mes… fiches de paie… s'effacent…", "", 'fantome', None, 150, 3, 'boss')
t('par_enarque', 'Énarque', 'Haut fonctionnaire', [['titularis', 44], ['comitologue', 44]], "J'ai fait l'ENA. Enfin, l'INSP. Bref, je sais tout.",
  "Je vais rédiger une note sur cet échec.", "", 'fonctionnaire_f', money=140)
t('par_ministre', 'Ministre délégué', 'Ministre', [['spitzen', 44], ['schumark', 45]], "Je suis ministre depuis… ce matin. Débattons avant le prochain remaniement.",
  "Remanié !", "", 'depute', money=140)
t('macron', 'Emmanuel Macron', 'Champion d\'arène', [['erasmusplus', 45], ['spitzen', 46], ['eurozone', 46], ['schumark', 47], ['nobelix', 48]],
  "Bienvenue à la Sorbonne ! Ici, j'ai parlé d'Europe souveraine en 2017… et en 2024. Je vais vous parler pendant deux heures. Et en même temps, débattre.",
  "Formidable ! Vous incarnez l'autonomie stratégique. Prenez le Badge Sorbonne… et en même temps, mes félicitations.",
  "Je dissous… votre équipe !", 'macron', 'macron', 180, 3, 'gym_leader')
# Council (Elite 4) + champion
t('merkel', 'Angela Merkel', 'Conseil européen', [['austerix', 50], ['titularis', 50], ['offshorion', 51], ['cecagon', 51], ['ratifix', 52]],
  "Wir schaffen das. Ensemble, on y arrivera. Mais d'abord, vous devez me battre. Prenez votre temps : j'ai seize ans d'expérience.",
  "Vous avez réussi. Wir haben es geschafft.", "", 'merkel', 'merkel', 220, 3, 'council')
t('draghi', 'Mario Draghi', 'Conseil européen', [['eurozone', 51], ['hyperflaton', 51], ['mica', 52], ['troikat', 52], ['draghizord', 54]],
  "Je ferai tout ce qu'il faut pour gagner ce débat. Whatever it takes. Et croyez-moi : ce sera suffisant.",
  "Mon rapport recommandait 800 milliards d'investissements par an. Investissez-les dans votre équipe.", "", 'draghi', 'draghi', 220, 3, 'council')
t('kallas', 'Kaja Kallas', 'Conseil européen', [['schengeon', 52], ['lisbonia' if False else 'trilogon', 52], ['pandiplo', 53], ['roamfree', 53], ['nobelix', 54]],
  "Haute représentante pour les affaires étrangères. Ma diplomatie est ferme. Mon bouclier balte, aussi.",
  "Une victoire nette. L'Europe aura besoin de gens comme vous face au reste du monde.", "", 'kallas', 'kallas', 220, 3, 'council')
t('costa', 'António Costa', 'Président du Conseil européen', [['interpreton', 53], ['transhumax', 53], ['mercosaur', 54], ['trilogon', 54], ['schumark', 55], ['ratifix', 55]],
  "Il est 23 h 59. Mon objectif : finir ce sommet avant minuit. Pour la première fois de l'histoire !",
  "Il est… 4 h 37 du matin. Comme d'habitude. Bravo, vous pouvez monter au Berlaymont.", "", 'costa', 'costa', 230, 3, 'council')
t('vdl', 'Ursula von der Leyen', 'Présidente de la Commission', [['neutralis', 56], ['eurozone', 56], ['iact', 57], ['lobbyzilla', 57], ['schumark', 57], ['emploifictif', 58]],
  "Bienvenue au treizième étage du Berlaymont. J'habite ici, vous savez : j'ai une chambre à côté de mon bureau. Alors, voyons si vous méritez la directive.",
  "Team Europe… Vous êtes le meilleur stagiaire que la Commission ait jamais eu. La directive sur l'heure est à vous !",
  "Je vous enverrai un SMS. Ou peut-être pas.", 'vdl', 'vdl', 300, 3, 'champion')
# Powers (chapter 11)
t('vance_t', 'JD Vance', 'Vice-président', [['fakeon', 55], ['tarifaux', 56], ['demagogor', 57]],
  "Je suis venu à Munich vous expliquer la démocratie. Maintenant, je viens à Anvers vous expliquer le débat.",
  "Bon. Je retourne écrire un discours.", "", 'vance', 'vance', 200, 3, 'powers')
t('trump', 'Donald Trump', 'Président américain', [['tarifaux', 58], ['fakeon', 59], ['brexitt', 59], ['lobbyzilla', 60], ['demagogor', 60], ['tarifator', 62]],
  "TREMENDOUS ! Le plus beau débat de tous les temps, tout le monde le dit. Je mets 200 % de droits de douane sur vos Euromons. Peut-être 15. On verra.",
  "C'ÉTAIT TRUQUÉ ! Bon… on fait un deal. 15 %. C'est mon dernier mot. Pour aujourd'hui.",
  "J'ai gagné ! Comme toujours ! Personne ne gagne mieux que moi.", 'trump', 'trump', 300, 3, 'powers')
t('putin', 'Vladimir Poutine', 'Président russe', [['gazoduc', 59], ['frontierex', 59], ['botfarm', 60], ['vetoadmax', 60], ['austerix', 61], ['censourson', 62]],
  "Asseyez-vous. Non, plus loin. Encore plus loin. Voilà. À six mètres, la conversation est plus… stratégique. Vos attaques mettront un tour à arriver.",
  "Le gaz… est coupé… de mon côté. Intéressant.", "L'hiver vient. Pour vous.", 'putin', 'putin', 300, 3, 'powers')
t('xi', 'Xi Jinping', 'Président chinois', [['pandiplo', 59], ['terrara', 60], ['iact', 60], ['hyperflaton', 60], ['diesgate', 61], ['trilogon', 62]],
  "Bienvenue. Nous sommes partenaires. Et concurrents. Et rivaux systémiques. Tout dépend du tour.",
  "Hmm. Un partenaire à respecter. Je retire les contrôles sur les terres rares… pour l'instant.", "Contenu indisponible dans votre région.",
  'xi', 'xi', 300, 3, 'powers')
t('trump_final', 'Donald Trump', 'Sommet G-Tout', [['tarifator', 63], ['lobbyzilla', 63], ['demagogor', 64]],
  "MOI D'ABORD. Le sommet, c'est mon idée. Enfin, je crois.", "Sad !", "", 'trump', 'trump', 200, 3, 'final')
t('putin_final', 'Vladimir Poutine', 'Sommet G-Tout', [['gazoduc', 63], ['vetoadmax', 64], ['censourson', 64]],
  "Je préférais la longue table.", "…", "", 'putin', 'putin', 200, 3, 'final')
t('xi_final', 'Xi Jinping', 'Sommet G-Tout', [['terrara', 64], ['pandiplo', 64], ['trilogon', 65]],
  "Le dernier mot sera… systémique.", "Nous reparlerons dans cinquante ans.", "", 'xi', 'xi', 200, 3, 'final')

json.dump(T, open(os.path.join(D, 'trainers.json'), 'w'), ensure_ascii=False, indent=1)

E = {
    'bxl_parc': (14, [('amendon', 2, 4, 30), ('pigeonix', 2, 4, 30), ('cookiz', 3, 4, 15), ('stagion', 3, 5, 15), ('paperasse_mon', 3, 4, 8), ('pralinou', 4, 5, 2)]),
    'route1': (12, [('amendon', 4, 6, 20), ('paperasse_mon', 4, 6, 15), ('agrikolo', 5, 7, 20), ('courbana', 5, 7, 15), ('erasmouse', 5, 7, 15), ('populo', 5, 7, 10), ('roamy', 6, 7, 5)]),
    'lux_parc': (12, [('eurolo', 8, 10, 30), ('fromajus', 8, 10, 20), ('valisette', 9, 11, 20), ('bouchatach', 9, 11, 20), ('trollbot', 9, 11, 10)]),
    'schengen': (14, [('roamy', 10, 13, 30), ('interpreton', 10, 13, 25), ('pigeonix', 10, 12, 25), ('frituron', 11, 13, 15), ('schengeon', 13, 14, 5)]),
    'route2': (12, [('courbana', 10, 13, 20), ('fromajus', 10, 13, 20), ('agrikolo', 10, 13, 20), ('cookiz', 11, 13, 15), ('frituron', 11, 14, 15), ('glyphosaure', 13, 14, 5), ('pralinou', 11, 13, 5)]),
    'ffm_parc': (12, [('eurolo', 14, 16, 25), ('inflaton', 14, 16, 25), ('cryptou', 15, 17, 20), ('lobbyrax', 14, 16, 20), ('spreadon', 16, 17, 5), ('atomiom', 17, 17, 5)]),
    'route3': (12, [('eolion', 15, 19, 25), ('solario', 16, 19, 20), ('agrikolo', 15, 18, 15), ('usbece', 16, 19, 15), ('roamy', 16, 18, 15), ('tracteuron', 18, 19, 5), ('bruxellair', 16, 18, 5)]),
    'stras_parc': (12, [('transhumon', 19, 22, 30), ('amendon', 19, 22, 20), ('interpreton', 20, 22, 20), ('fakeon', 21, 23, 15), ('comitologue', 22, 23, 5), ('dejeunix', 20, 22, 10)]),
    'ath_parc': (12, [('erasmouse', 25, 28, 25), ('inflaton', 25, 28, 20), ('referendo', 26, 29, 20), ('populo', 25, 28, 20), ('troikat', 28, 29, 5), ('solario', 26, 28, 10)]),
    'lon_parc': (12, [('pigeonix', 30, 33, 25), ('bruxellair', 30, 33, 20), ('trollbot', 30, 33, 20), ('fakeon', 31, 33, 20), ('brexitt', 33, 34, 5), ('tribun', 31, 33, 10)]),
    'bud_parc': (12, [('vetoad', 34, 37, 30), ('frontierex', 34, 37, 20), ('tracteuron', 34, 37, 20), ('populo', 34, 36, 20), ('gazoduc', 37, 38, 5), ('austerix', 36, 37, 5)]),
    'par_parc': (12, [('pralinou', 40, 43, 20), ('fromajus', 40, 43, 15), ('erasmusplus', 41, 43, 15), ('plafonnor', 41, 43, 15), ('solario', 40, 43, 15), ('frituron', 40, 42, 10), ('nobelix', 43, 44, 5), ('dejeunix', 40, 42, 5)]),
    'fantome': (15, [('assistome', 36, 40, 50), ('pailleplast', 37, 40, 20), ('manneken', 37, 40, 20), ('changheure', 39, 40, 10)]),
    'anvers': (12, [('tarifaux', 52, 56, 30), ('valisette', 52, 55, 20), ('lobbyron', 53, 56, 20), ('mercosaur', 55, 56, 10), ('hyperflaton', 53, 56, 20)]),
    'varsovie': (12, [('gazoduc', 52, 56, 25), ('eolion', 52, 55, 20), ('plafonnor', 53, 56, 20), ('offshorion', 54, 56, 15), ('frontierex', 52, 56, 20)]),
    'piree': (12, [('terrara', 55, 56, 5), ('algoritmo', 52, 56, 25), ('cryptou', 52, 56, 25), ('tarifaux', 52, 56, 25), ('pandiplo', 55, 56, 5), ('usbece', 52, 55, 15)]),
}
json.dump({k: {'rate': r, 'slots': [list(s) for s in sl]} for k, (r, sl) in E.items()},
          open(os.path.join(D, 'encounters.json'), 'w'), indent=1)
print('trainers', len(T), 'encounters', len(E))
