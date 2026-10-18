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
 ('verdeal', 'Verdeal', ['VERT'], 309, 'spec', 'parabolic', 45, (16, 'fit55'), 'Pacte vert', 'green', 'quadruped', "Né avec le Pacte vert de 2019. Une pousse jaillit chaque fois qu'une norme d'émission est votée."),
 ('fit55', 'Fit55', ['VERT'], 405, 'spec', 'parabolic', 45, (36, 'neutralis'), 'Objectif climat', 'green', 'quadruped', "Il s'entraîne pour réduire ses émissions de 55 % d'ici 2030. Il compte chaque calorie."),
 ('neutralis', 'Neutralis', ['VERT', 'FEDERAL'], 525, 'spec', 'parabolic', 45, None, 'Neutralité', 'green', 'quadruped', "Il vise la neutralité carbone en 2050. D'ici là, il plante un arbre à chaque pas."),
 ('charbonnet', 'Charbonnet', ['INDUSTRIE'], 309, 'phys', 'parabolic', 45, (16, 'hautfourno'), 'Charbon', 'black', 'biped', "Petit tas de charbon de la CECA de 1951. Il noircit tout ce qu'il touche, avec enthousiasme."),
 ('hautfourno', 'Hautfourno', ['INDUSTRIE'], 405, 'phys', 'parabolic', 45, (36, 'cecagon'), 'Haut-fourneau', 'orange', 'biped', "Sa cheminée crache des étincelles quand il s'énerve. Il rêve de plein emploi."),
 ('cecagon', 'CECAgon', ['INDUSTRIE', 'FEDERAL'], 525, 'phys', 'parabolic', 45, None, 'Acier commun', 'grey', 'biped', "Forgé dans le charbon et l'acier mis en commun. Il est la preuve que la paix se fabrique."),
 ('atomino', 'Atomino', ['ENERGIE'], 309, 'fast', 'parabolic', 45, (16, 'euratome'), 'Atome', 'yellow', 'blob', "Un petit atome curieux, né du traité Euratom de 1957. Il ne tient pas en place."),
 ('euratome', 'Euratome', ['ENERGIE'], 405, 'fast', 'parabolic', 45, (36, 'fissionix'), 'Réacteur', 'yellow', 'blob', "Ses électrons tournent si vite qu'il éclaire une pièce entière. Sobriété en option."),
 ('fissionix', 'Fissionix', ['ENERGIE', 'TECHNO'], 525, 'fast', 'parabolic', 45, None, 'Fission', 'cyan', 'blob', "Il se divise en deux quand il est contrarié. Les Verts et lui ne s'adressent plus la parole."),
 ('tampono', 'Tampono', ['JURIDIQUE'], 280, 'tank', 'medium', 255, (14, 'paraphor'), 'Tampon', 'brown', 'object', "Un tampon vivant qui valide tout ce qu'il croise. Il a déjà tamponné son propre dresseur."),
 ('paraphor', 'Paraphor', ['JURIDIQUE'], 390, 'tank', 'medium', 120, (32, 'ratifix'), 'Parapheur', 'red', 'object', "Il paraphe chaque page en bas à droite. Il lui faut quatre heures par traité."),
 ('ratifix', 'Ratifix', ['JURIDIQUE', 'FEDERAL'], 495, 'tank', 'medium', 45, None, 'Ratification', 'red', 'object', "Il ne bouge que lorsque 27 parlements nationaux ont dit oui. Il dort donc beaucoup."),
 ('amendon', 'Amendon', ['TECHNO'], 260, 'bal', 'fast', 255, (20, 'amendomax'), 'Amendement', 'white', 'insect', "Il se reproduit par milliers à chaque texte de loi. Le Parlement en reçoit parfois 2000 par rapport."),
 ('amendomax', 'Amendomax', ['TECHNO', 'POPULISTE'], 420, 'bal', 'fast', 90, None, 'Obstruction', 'white', 'insect', "Il dépose tant d'amendements qu'il bloque toute la séance. Une technique bien rodée."),
 ('cookiz', 'Cookiz', ['NUMERIQUE'], 270, 'fast', 'medium', 200, (22, 'consentor'), 'Bandeau cookie', 'tan', 'blob', "Il apparaît devant chaque porte depuis le RGPD de 2018. Le refuser ne suffit jamais."),
 ('consentor', 'Consentor', ['NUMERIQUE', 'JURIDIQUE'], 450, 'spec', 'medium', 60, None, 'Consentement', 'tan', 'blob', "Il demande votre accord pour tout, puis pour l'accord lui-même. Il est très poli."),
 ('usbece', 'Usbécé', ['NUMERIQUE'], 400, 'fast', 'medium', 90, None, 'Chargeur', 'grey', 'serpent', "Obligatoire sur tous les appareils depuis fin 2024. Il a mis au chômage un tiroir entier de câbles."),
 ('bouchatach', 'Bouchatach', ['VERT'], 330, 'tank', 'fast', 190, None, 'Bouchon', 'blue', 'object', "Il ne quitte plus sa bouteille depuis juillet 2024. Il vous frappe le nez quand vous buvez."),
 ('pailleplast', 'Pailleplast', ['VERT', 'FANTOME'], 380, 'glass', 'slow', 25, None, 'Paille disparue', 'pink', 'serpent', "Interdit depuis 2021, on le croyait disparu. Il hante les fast-foods la nuit."),
 ('courbana', 'Courbana', ['AGRICOLE'], 300, 'phys', 'fast', 190, None, 'Banane', 'yellow', 'serpent', "Un règlement de 1994 fixe sa qualité. Il passe sa vie à mesurer sa propre courbure."),
 ('roamy', 'Roamy', ['NUMERIQUE'], 290, 'fast', 'fast', 190, (24, 'roamfree'), 'Itinérance', 'cyan', 'flyer', "Il voyage partout sans frais depuis juin 2017. Il appelle sa mère depuis chaque frontière."),
 ('roamfree', 'Roamfree', ['NUMERIQUE', 'DIPLO'], 455, 'fast', 'fast', 75, None, 'Sans frontières', 'cyan', 'flyer', "Il a visité les 27 pays en un week-end et a tout posté en direct. Sans surcoût."),
 ('erasmouse', 'Erasmouse', ['SOCIAL'], 285, 'fast', 'medium', 190, (20, 'erasmusplus'), 'Étudiant', 'beige', 'quadruped', "Ce petit rongeur part un semestre à l'étranger et revient bilingue. Né en 1987."),
 ('erasmusplus', 'Erasmus+', ['SOCIAL', 'LIBERAL'], 460, 'fast', 'medium', 60, None, 'Échange', 'beige', 'quadruped', "Il a habité dans 12 colocations et cuisine des pâtes dans 9 langues."),
 ('eurolo', 'Eurolo', ['MONETAIRE'], 290, 'bal', 'medium', 190, (25, 'eurozone'), 'Pièce', 'gold', 'object', "Une pièce de 2 € qui roule partout depuis 2002. Elle a 27 faces nationales possibles."),
 ('eurozone', 'Eurozone', ['MONETAIRE', 'FEDERAL'], 470, 'bal', 'medium', 60, None, 'Monnaie unique', 'gold', 'object', "Vingt pays partagent sa force. Quand l'un tousse, les autres ont la fièvre."),
 ('schengeon', 'Schengéon', ['DIPLO'], 420, 'fast', 'medium', 90, None, 'Libre circulation', 'blue', 'flyer', "Né sur un bateau sur la Moselle en 1985. Aucune frontière ne le retient."),
 ('glyphosaure', 'Glyphosaure', ['AGRICOLE', 'LOBBY'], 440, 'phys', 'slow', 75, None, 'Herbicide', 'olive', 'quadruped', "Réautorisé pour dix ans en 2023. Les herbes folles tremblent à son passage."),
 ('lobbyrax', 'Lobbyrax', ['LOBBY'], 290, 'mixed', 'medium', 190, (18, 'lobbyron'), 'Démarcheur', 'black', 'humanoid', "Il traîne dans les couloirs avec une mallette plus grande que lui. Il ne fait pas de lobbying, il « informe »."),
 ('lobbyron', 'Lobbyron', ['LOBBY'], 405, 'mixed', 'medium', 90, (38, 'lobbyzilla'), 'Influenceur', 'black', 'humanoid', "Il connaît le numéro de chaque assistant parlementaire. Et leurs allergies."),
 ('lobbyzilla', 'Lobbyzilla', ['LOBBY', 'SOUVERAIN'], 530, 'mixed', 'medium', 45, None, 'Méga-lobby', 'black', 'humanoid', "Un des 25 000 lobbyistes de Bruxelles, en version géante. Il réécrit les lois en dormant."),
 ('transhumon', 'Transhumon', ['TECHNO'], 300, 'tank', 'medium', 190, (30, 'transhumax'), 'Malle en fer', 'grey', 'object', "Une malle en fer qui fait Bruxelles–Strasbourg douze fois par an. Elle a le mal des transports."),
 ('transhumax', 'Transhumax', ['TECHNO', 'DIPLO'], 470, 'tank', 'medium', 75, None, 'Déménagement', 'grey', 'object', "Il transporte un parlement entier dans son ventre. Coût du voyage : à ne pas demander."),
 ('changheure', 'Changheure', ['TECHNO', 'FANTOME'], 450, 'spec', 'slow', 45, None, 'Changement d\'heure', 'purple', 'object', "Le Parlement a voté sa disparition en 2019. Il revient pourtant deux fois par an."),
 ('diesgate', 'Diesgate', ['INDUSTRIE', 'LOBBY'], 430, 'phys', 'medium', 75, None, 'Fraude', 'grey', 'object', "Il triche aux contrôles depuis 2015 : propre au banc d'essai, enfumé sur la route."),
 ('spitzen', 'Spitzen', ['FEDERAL'], 460, 'phys', 'slow', 45, None, 'Tête de liste', 'blue', 'humanoid', "Il fait campagne pour la présidence… puis un autre est nommé à sa place."),
 ('interpreton', 'Interpréton', ['DIPLO'], 300, 'spec', 'fast', 150, None, 'Interprète', 'teal', 'humanoid', "Il parle 24 langues et toujours avec deux secondes de retard."),
 ('trilogon', 'Trilogon', ['JURIDIQUE', 'DIPLO'], 470, 'spec', 'slow', 45, None, 'Trilogue', 'purple', 'blob', "Trois têtes : Parlement, Conseil, Commission. Elles se mettent d'accord vers 4 h du matin."),
 ('comitologue', 'Comitologue', ['TECHNO'], 420, 'wall', 'slow', 75, None, 'Comitologie', 'grey', 'humanoid', "Personne ne sait exactement ce qu'il fait. Il siège pourtant dans 300 comités."),
 ('paperasse_mon', 'Paperassor', ['TECHNO'], 260, 'tank', 'fast', 255, (18, 'archivor'), 'Formulaire', 'white', 'object', "Une pile de formulaires en triple exemplaire. Il manque toujours une page."),
 ('archivor', 'Archivor', ['TECHNO', 'JURIDIQUE'], 430, 'tank', 'fast', 90, None, 'Archives', 'brown', 'object', "Il garde tout, même les post-it de 1958. Classement : alphabétique et émotionnel."),
 ('agrikolo', 'Agrikolo', ['AGRICOLE'], 290, 'tank', 'medium', 190, (18, 'pactor'), 'Petit fermier', 'green', 'biped', "Il touche une aide de la PAC pour chaque hectare. Il compte ses hectares tous les matins."),
 ('pactor', 'PACtor', ['AGRICOLE'], 410, 'tank', 'medium', 90, (36, 'megapac'), 'PAC', 'green', 'biped', "Il absorbe un tiers du budget européen sans broncher. Il a toujours faim."),
 ('megapac', 'MégaPAC', ['AGRICOLE', 'SOUVERAIN'], 525, 'tank', 'medium', 45, None, 'Politique agricole', 'green', 'biped', "Quand il bloque l'autoroute avec ses tracteurs, même le Conseil négocie."),
 ('tracteuron', 'Tracteuron', ['AGRICOLE', 'INDUSTRIE'], 440, 'tank', 'medium', 75, None, 'Manifestation', 'red', 'object', "Il se gare devant le Parlement à chaque réforme. Klaxon garanti."),
 ('fromajus', 'Fromajus', ['AGRICOLE'], 300, 'tank', 'fast', 190, (26, 'appellatio'), 'Fromage', 'yellow', 'blob', "Un petit fromage au lait cru qui sent très fort. Il est fier de son terroir."),
 ('appellatio', 'Appellatio', ['AGRICOLE', 'JURIDIQUE'], 460, 'tank', 'fast', 75, None, 'AOP', 'yellow', 'blob', "Protégé par une appellation d'origine. Toute imitation est poursuivie en justice."),
 ('pralinou', 'Pralinou', ['SOCIAL'], 310, 'bal', 'fast', 190, None, 'Praline', 'brown', 'blob', "Un chocolat belge très gentil. Il fond quand on lui fait un compliment."),
 ('frituron', 'Frituron', ['SOCIAL', 'INDUSTRIE'], 360, 'phys', 'fast', 150, None, 'Frite belge', 'yellow', 'insect', "Cuit deux fois, comme il se doit. Il refuse catégoriquement d'être appelé « French »."),
 ('pigeonix', 'Pigeonix', ['POPULISTE'], 250, 'fast', 'fast', 255, None, 'Pigeon', 'grey', 'flyer', "Il vit place du Luxembourg et vole les frites des lobbyistes. Il connaît tous les ragots."),
 ('manneken', 'Manneken', ['SOCIAL', 'FANTOME'], 400, 'spec', 'medium', 60, None, 'Petit bonhomme', 'bronze', 'humanoid', "Une petite statue de 55 cm qui a plus de costumes que tout le Parlement."),
 ('atomiom', 'Atomiom', ['ENERGIE', 'TECHNO'], 480, 'spec', 'slow', 45, None, 'Atomium', 'silver', 'blob', "Neuf sphères d'acier reliées en cristal, depuis l'Expo 58. Il brille la nuit sur Bruxelles."),
 ('stagion', 'Stagion', ['SOCIAL'], 250, 'fast', 'parabolic', 255, (16, 'contractuel'), 'Stagiaire', 'blue', 'humanoid', "Il travaille beaucoup et n'est pas payé. Il dit que c'est « une expérience formatrice »."),
 ('contractuel', 'Contractuel', ['SOCIAL', 'TECHNO'], 380, 'bal', 'parabolic', 120, (34, 'titularis'), 'Agent temporaire', 'blue', 'humanoid', "Son contrat finit dans trois mois. Il le renouvelle depuis six ans."),
 ('titularis', 'Titularis', ['TECHNO', 'FEDERAL'], 500, 'wall', 'parabolic', 45, None, 'Fonctionnaire', 'navy', 'humanoid', "Il a réussi le concours EPSO. Il ne craint plus rien, sauf la réforme des retraites."),
 ('populo', 'Populo', ['POPULISTE'], 270, 'phys', 'medium', 200, (20, 'tribun'), 'Râleur', 'red', 'biped', "Il est contre. Peu importe quoi, il est contre."),
 ('tribun', 'Tribun', ['POPULISTE'], 400, 'phys', 'medium', 90, (36, 'demagogor'), 'Orateur', 'red', 'biped', "Il monte sur toutes les tables pour haranguer la foule. Même à la cantine."),
 ('demagogor', 'Démagogor', ['POPULISTE', 'SOUVERAIN'], 520, 'phys', 'medium', 45, None, 'Démagogue', 'red', 'biped', "Il promet tout à tout le monde. Ses promesses s'évaporent à l'aube."),
 ('fakeon', 'Fakeon', ['NUMERIQUE', 'POPULISTE'], 410, 'spec', 'fast', 75, None, 'Fausse info', 'orange', 'flyer', "Il change de forme selon la personne qui le regarde. Il est très partagé."),
 ('trollbot', 'Trollbot', ['NUMERIQUE'], 280, 'glass', 'fast', 190, (24, 'botfarm'), 'Faux compte', 'grey', 'object', "Un petit robot qui commente tout en majuscules. Il n'a jamais dormi."),
 ('botfarm', 'Botfarm', ['NUMERIQUE', 'LOBBY'], 450, 'glass', 'fast', 60, None, 'Usine à trolls', 'grey', 'object', "Dix mille comptes dans une seule boîte. Les élections le connaissent bien."),
 ('algoritmo', 'Algoritmo', ['NUMERIQUE'], 300, 'spec', 'medium', 150, (30, 'iact'), 'Algorithme', 'cyan', 'serpent', "Il apprend de tout ce que vous faites. Il sait déjà ce que vous allez capturer."),
 ('iact', 'IAct', ['NUMERIQUE', 'JURIDIQUE'], 480, 'spec', 'medium', 45, None, 'IA régulée', 'cyan', 'serpent', "Le premier règlement mondial sur l'intelligence artificielle (2024) l'a mis en règle."),
 ('inflaton', 'Inflaton', ['MONETAIRE'], 290, 'tank', 'medium', 190, (28, 'hyperflaton'), 'Inflation', 'pink', 'blob', "Il gonfle un peu chaque mois. Les ménages le surveillent de près."),
 ('hyperflaton', 'Hyperflaton', ['MONETAIRE'], 460, 'tank', 'medium', 60, None, 'Hyperinflation', 'pink', 'blob', "Si gros qu'il bouche les rues. La BCE monte les taux pour le faire maigrir."),
 ('spreadon', 'Spreadon', ['MONETAIRE', 'POPULISTE'], 420, 'glass', 'medium', 90, None, 'Écart de taux', 'red', 'serpent', "Il s'étire à chaque déclaration maladroite d'un banquier central."),
 ('cryptou', 'Cryptou', ['MONETAIRE', 'NUMERIQUE'], 290, 'glass', 'erratic' if False else 'fast', 190, (30, 'mica'), 'Cryptomonnaie', 'orange', 'object', "Il vaut une fortune le matin et rien le soir. Il adore les montagnes russes."),
 ('mica', 'MiCA', ['MONETAIRE', 'JURIDIQUE'], 460, 'bal', 'fast', 60, None, 'Crypto régulée', 'orange', 'object', "Le règlement MiCA l'a obligé à porter une cravate. Il est plus calme, maintenant."),
 ('austerix', 'Austérix', ['MONETAIRE', 'SOUVERAIN'], 440, 'wall', 'slow', 75, None, 'Équilibre budgétaire', 'black', 'biped', "Il ne dépense jamais rien, pas même son énergie. Son cri : « Schwarze Null ! »"),
 ('troikat', 'Troïkat', ['MONETAIRE', 'DIPLO'], 470, 'mixed', 'slow', 45, None, 'Troïka', 'grey', 'quadruped', "Trois chats : BCE, Commission, FMI. Ils inspectent ensemble les comptes des autres."),
 ('vetoad', 'Vetoad', ['SOUVERAIN'], 300, 'tank', 'medium', 190, (30, 'vetoadmax'), 'Veto', 'green', 'quadruped', "Un crapaud qui croasse « non ! » à chaque proposition. Il suffit de lui pour tout bloquer."),
 ('vetoadmax', 'Vetoadmax', ['SOUVERAIN', 'POPULISTE'], 480, 'tank', 'medium', 60, None, 'Unanimité', 'green', 'quadruped', "Il exige l'unanimité pour chaque décision, puis la refuse lui-même."),
 ('frontierex', 'Frontièrex', ['SOUVERAIN'], 400, 'tank', 'medium', 90, None, 'Barrière', 'brown', 'object', "Il réapparaît dès qu'on parle de contrôles aux frontières. Il a sa guérite personnelle."),
 ('brexitt', 'Brexitt', ['SOUVERAIN', 'POPULISTE'], 420, 'fast', 'medium', 60, None, 'Sortie', 'navy', 'flyer', "Il a voulu partir en 2016, est parti en 2020, et regrette parfois. Il quitte souvent les combats."),
 ('referendo', 'Référendo', ['POPULISTE', 'SOUVERAIN'], 410, 'spec', 'medium', 75, None, 'Consultation', 'white', 'object', "Une urne qui pose des questions simples aux problèmes compliqués."),
 ('assistome', 'Assistome', ['FANTOME'], 300, 'spec', 'medium', 150, (30, 'emploifictif'), 'Assistant fantôme', 'lavender', 'humanoid', "Payé par le Parlement, il n'y a jamais mis les pieds. Personne ne l'a jamais vu travailler."),
 ('emploifictif', 'Emploifictif', ['FANTOME', 'LOBBY'], 470, 'spec', 'medium', 60, None, 'Emploi fictif', 'lavender', 'humanoid', "Il porte un badge, un contrat et une fiche de paie. Mais aucun bureau."),
 ('sacabillet', 'Sacabillet', ['LOBBY', 'FANTOME'], 450, 'phys', 'slow', 30, None, 'Sac de billets', 'green', 'object', "Retrouvé plein de billets dans un appartement bruxellois en décembre 2022."),
 ('valisette', 'Valisette', ['LOBBY'], 300, 'tank', 'fast', 190, None, 'Mallette', 'brown', 'object', "Une petite valise qui passe de main en main au pied du Parlement."),
 ('gazoduc', 'Gazoduc', ['ENERGIE', 'SOUVERAIN'], 440, 'tank', 'slow', 60, None, 'Pipeline', 'grey', 'serpent', "Long de 1200 km sous la mer. Son robinet est contrôlé par quelqu'un d'autre."),
 ('eolion', 'Éolion', ['ENERGIE', 'VERT'], 330, 'fast', 'medium', 150, (32, 'offshorion'), 'Éolienne', 'white', 'flyer', "Ses pales tournent dès qu'on souffle sur lui. Il déteste les jours sans vent."),
 ('offshorion', 'Offshorion', ['ENERGIE', 'VERT'], 480, 'fast', 'medium', 60, None, 'Éolien en mer', 'white', 'flyer', "Il vit au large de la mer du Nord et alimente des villes entières."),
 ('solario', 'Solario', ['ENERGIE', 'VERT'], 410, 'spec', 'medium', 90, None, 'Panneau solaire', 'blue', 'object', "Il dort la nuit et travaille dur le jour, surtout en Espagne."),
 ('plafonnor', 'Plafonnor', ['ENERGIE', 'MONETAIRE'], 420, 'wall', 'medium', 75, None, 'Plafond de prix', 'red', 'object', "Il empêche les prix de monter trop haut. Il a mal au cou à force de pousser."),
 ('tarifaux', 'Tarifaux', ['POPULISTE'], 300, 'phys', 'medium', 190, (30, 'tarifator'), 'Droit de douane', 'orange', 'quadruped', "Il taxe tout ce qui passe devant lui. Même les feuilles mortes."),
 ('tarifator', 'Tarifator', ['POPULISTE', 'MONETAIRE'], 480, 'phys', 'medium', 60, None, 'Guerre commerciale', 'orange', 'quadruped', "Il brandit un tableau de taxes géant. Les chiffres changent chaque matin."),
 ('terrara', 'Terrara', ['INDUSTRIE', 'NUMERIQUE'], 450, 'tank', 'slow', 45, None, 'Terres rares', 'purple', 'object', "Un petit caillou dont dépendent tous les téléphones. Ses exportations sont surveillées."),
 ('pandiplo', 'Pandiplo', ['DIPLO'], 410, 'wall', 'slow', 45, None, 'Panda diplomate', 'white', 'quadruped', "Prêté pour quelques années à un zoo européen. Il mange du bambou et des accords commerciaux."),
 ('censourson', 'Censourson', ['FANTOME', 'POPULISTE'], 420, 'spec', 'slow', 30, None, 'Contenu indisponible', 'yellow', 'quadruped', "Cet ourson jaune n'est visible dans aucune région. Sa fiche a été retirée."),
 ('pigeon_lux', 'Kirchbergeon', ['JURIDIQUE', 'FLYER'] if False else ['JURIDIQUE', 'DIPLO'], 380, 'fast', 'medium', 150, None, 'Pigeon juriste', 'grey', 'flyer', "Il niche sur les tours de la Cour de justice au Kirchberg et roucoule en latin."),
 ('schumark', 'Schumark', ['FEDERAL', 'DIPLO'], 430, 'bal', 'slow', 45, None, 'Déclaration', 'blue', 'humanoid', "Il récite la déclaration du 9 mai 1950 à qui veut l'entendre. Il apparaît à la Fête de l'Europe."),
 ('nobelix', 'Nobelix', ['DIPLO', 'FEDERAL'], 470, 'wall', 'slow', 30, None, 'Prix Nobel', 'gold', 'object', "Une médaille remise à l'Union européenne en 2012. Elle brille de fierté."),
 ('bruxellair', 'Brumelle', ['TECHNO', 'VERT'], 320, 'spec', 'fast', 190, None, 'Crachin', 'grey', 'flyer', "Un petit nuage bruxellois. Il pleut sur vous 200 jours par an."),
 ('dejeunix', 'Lunchix', ['SOCIAL', 'LOBBY'], 340, 'bal', 'fast', 150, None, 'Déjeuner d\'affaires', 'red', 'blob', "Un déjeuner de travail qui dure trois heures. On y décide plus qu'en séance."),
 ('mercosaur', 'Mercosaur', ['AGRICOLE', 'DIPLO'], 480, 'tank', 'slow', 45, None, 'Accord commercial', 'green', 'quadruped', "Il est en négociation depuis 1999. Quand il avance d'un pas, les tracteurs le repoussent."),
 ('romulus', 'Romulus', ['JURIDIQUE', 'FEDERAL'], 600, 'bal', 'slow', 3, None, 'Traité de Rome', 'marble', 'humanoid', "Né le 25 mars 1957 au Capitole. Il a fondé la Communauté économique européenne."),
 ('maastrichtor', 'Maastrichtor', ['MONETAIRE', 'FEDERAL'], 600, 'mixed', 'slow', 3, None, 'Traité de Maastricht', 'gold', 'serpent', "Né aux Pays-Bas en 1992. Il a créé l'Union et rêvé l'euro."),
 ('lisbonia', 'Lisbonia', ['JURIDIQUE', 'DIPLO'], 600, 'spec', 'slow', 3, None, 'Traité de Lisbonne', 'blue', 'flyer', "Signé en 2007, il a repris l'essentiel d'une constitution qui n'a jamais vu le jour."),
 ('constitutio', 'Constitutio', ['FEDERAL', 'FANTOME'], 640, 'spec', 'slow', 1, None, 'Constitution', 'white', 'flyer', "Rejeté par référendum en France et aux Pays-Bas en 2005. Il fuit dès qu'on l'approche."),
 ('draghizord', 'Draghizord', ['MONETAIRE', 'TECHNO'], 620, 'spec', 'slow', 3, None, 'Whatever it takes', 'navy', 'humanoid', "Il ne connaît qu'une attaque, et elle réussit toujours. Il a sauvé l'euro en une phrase."),
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
