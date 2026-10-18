#!/usr/bin/env python3
"""Generates data/types.json, data/moves.json, data/items.json"""
import json, os
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
D = os.path.join(ROOT, 'data')
os.makedirs(D, exist_ok=True)

TYPES = ["TECHNO", "FEDERAL", "SOUVERAIN", "LIBERAL", "SOCIAL", "VERT", "INDUSTRIE", "ENERGIE",
         "JURIDIQUE", "MONETAIRE", "AGRICOLE", "NUMERIQUE", "DIPLO", "LOBBY", "POPULISTE", "FANTOME"]
NAMES = ["Techno", "Fédéral", "Souverain", "Libéral", "Social", "Vert", "Industrie", "Énergie",
         "Juridique", "Monétaire", "Agricole", "Numérique", "Diplo", "Lobby", "Populiste", "Fantôme"]
STRONG = {
    'TECHNO': ['POPULISTE'],
    'FEDERAL': ['SOUVERAIN', 'INDUSTRIE'],
    'SOUVERAIN': ['JURIDIQUE', 'DIPLO'],
    'LIBERAL': ['INDUSTRIE', 'MONETAIRE'],
    'SOCIAL': ['LIBERAL', 'MONETAIRE', 'LOBBY'],
    'VERT': ['ENERGIE', 'AGRICOLE'],
    'INDUSTRIE': ['VERT', 'NUMERIQUE'],
    'ENERGIE': ['INDUSTRIE', 'NUMERIQUE'],
    'JURIDIQUE': ['LOBBY', 'NUMERIQUE', 'FANTOME'],
    'MONETAIRE': ['SOUVERAIN', 'AGRICOLE'],
    'AGRICOLE': ['FEDERAL', 'MONETAIRE'],
    'NUMERIQUE': ['TECHNO', 'DIPLO'],
    'DIPLO': ['POPULISTE', 'SOCIAL'],
    'LOBBY': ['TECHNO', 'FEDERAL', 'VERT'],
    'POPULISTE': ['FEDERAL', 'JURIDIQUE', 'DIPLO'],
    'FANTOME': ['TECHNO'],
}
WEAK = {  # attacker -> defenders resisting (0.5)
    'TECHNO': ['LOBBY', 'SOUVERAIN'],
    'FEDERAL': ['POPULISTE', 'FEDERAL', 'TECHNO'],
    'SOUVERAIN': ['FEDERAL', 'SOUVERAIN', 'MONETAIRE'],
    'LIBERAL': ['SOCIAL', 'VERT', 'LIBERAL'],
    'SOCIAL': ['SOUVERAIN', 'POPULISTE', 'SOCIAL'],
    'VERT': ['INDUSTRIE', 'LOBBY', 'VERT'],
    'INDUSTRIE': ['ENERGIE', 'INDUSTRIE', 'SOCIAL'],
    'ENERGIE': ['VERT', 'ENERGIE', 'SOUVERAIN'],
    'JURIDIQUE': ['SOUVERAIN', 'POPULISTE', 'JURIDIQUE'],
    'MONETAIRE': ['LIBERAL', 'MONETAIRE', 'SOCIAL'],
    'AGRICOLE': ['VERT', 'LIBERAL', 'AGRICOLE'],
    'NUMERIQUE': ['JURIDIQUE', 'NUMERIQUE', 'INDUSTRIE'],
    'DIPLO': ['SOUVERAIN', 'NUMERIQUE', 'DIPLO'],
    'LOBBY': ['JURIDIQUE', 'SOCIAL', 'LOBBY'],
    'POPULISTE': ['TECHNO', 'POPULISTE'],
    'FANTOME': ['JURIDIQUE'],
}
chart = {}
for a in TYPES:
    row = {}
    for d in STRONG[a]:
        row[d] = 2.0
    for d in WEAK[a]:
        row[d] = 0.5
    if a not in ('JURIDIQUE', 'FANTOME'):
        row['FANTOME'] = 0
    chart[a] = row
json.dump({"types": TYPES, "names": NAMES, "chart": chart}, open(os.path.join(D, 'types.json'), 'w'),
          ensure_ascii=False, indent=1)

# (id, name, type, cat, power, acc, pp, effect, chance, param, priority, desc)
M = [
 # TECHNO
 ('amendement', 'Amendement', 'TECHNO', 'phys', 40, 100, 35, 'NONE', 0, 0, 0, "Modifie le texte adverse, un alinéa à la fois."),
 ('paperasse', 'Paperasse', 'TECHNO', 'phys', 50, 95, 30, 'NONE', 0, 0, 0, "Ensevelit la cible sous les formulaires."),
 ('note_de_service', 'Note de service', 'TECHNO', 'spec', 60, 100, 25, 'NONE', 0, 0, 0, "Une note interne, très ferme."),
 ('reunion', 'Réunion', 'TECHNO', 'status', 0, 100, 20, 'SOMMEIL', 0, 0, 0, "Une réunion de coordination qui endort tout le monde."),
 ('tampon_sec', 'Tampon sec', 'TECHNO', 'phys', 70, 100, 20, 'FLINCH', 20, 0, 0, "Un coup de tampon net et officiel."),
 ('comitologie', 'Comitologie', 'TECHNO', 'status', 0, 100, 20, 'CONFUSE', 0, 0, 0, "Personne ne comprend la procédure. Pas même la cible."),
 ('relire', 'Relecture', 'TECHNO', 'status', 0, 0, 30, 'STAT_UP', 0, 22, 0, "Relit son dossier. Augmente beaucoup la Résilience."),
 ('directive', 'Directive', 'TECHNO', 'spec', 90, 100, 15, 'NONE', 0, 0, 0, "Un texte contraignant à transposer d'urgence."),
 ('reglement', 'Règlement', 'TECHNO', 'phys', 120, 85, 5, 'NONE', 0, 0, 0, "Directement applicable dans tous les États membres."),
 ('trilogue', 'Trilogue', 'TECHNO', 'spec', 25, 90, 10, 'MULTI_HIT', 0, 0, 0, "Parlement, Conseil, Commission : frappe 2 à 5 fois."),
 ('procedure_urgence', 'Urgence', 'TECHNO', 'phys', 40, 100, 30, 'NONE', 0, 0, 1, "Procédure d'urgence : agit en premier."),
 ('pause_cafe', 'Pause café', 'TECHNO', 'status', 0, 0, 10, 'HEAL_HALF', 0, 0, 0, "Un café à la cantine. Restaure la moitié des PV."),
 ('plagiat', 'Plagiat', 'TECHNO', 'status', 0, 0, 10, 'COPY', 0, 0, 0, "Recopie la dernière attaque de l'adversaire."),
 ('rapport_annuel', 'Rapport annuel', 'TECHNO', 'spec', 100, 90, 10, 'CHARGE', 0, 0, 0, "Charge un tour, puis assomme avec 400 pages."),
 # FEDERAL
 ('integration', 'Intégration', 'FEDERAL', 'spec', 40, 100, 30, 'NONE', 0, 0, 0, "Un petit pas vers une union sans cesse plus étroite."),
 ('subsidiarite', 'Subsidiarité', 'FEDERAL', 'status', 0, 0, 20, 'STAT_UP', 0, 41, 0, "Agit au bon niveau. Augmente la Diplomatie."),
 ('etats_unis_europe', 'États-Unis UE', 'FEDERAL', 'spec', 110, 85, 5, 'NONE', 0, 0, 0, "Le grand rêve fédéral, lancé à pleine puissance."),
 ('team_europe', 'Team Europe', 'FEDERAL', 'phys', 75, 100, 15, 'NONE', 0, 0, 0, "Tous ensemble ! Une charge solidaire."),
 ('marche_unique', 'Marché unique', 'FEDERAL', 'spec', 80, 100, 15, 'STAT_DOWN', 20, 41, 0, "Abolit les frontières… et la Diplomatie adverse."),
 ('drapeau_etoile', 'Douze étoiles', 'FEDERAL', 'spec', 60, 0, 20, 'ALWAYS_HIT', 0, 0, 0, "Douze étoiles dorées qui ne ratent jamais."),
 ('spitzen', 'Tête de liste', 'FEDERAL', 'phys', 90, 100, 10, 'HIGH_CRIT', 0, 0, 0, "Une campagne de Spitzenkandidat. Critiques fréquents."),
 ('elargissement', 'Élargissement', 'FEDERAL', 'status', 0, 0, 10, 'STAT_UP', 0, 12, 0, "Accueille de nouveaux membres. Argumentation +2."),
 # SOUVERAIN
 ('veto', 'Veto', 'SOUVERAIN', 'status', 0, 0, 10, 'PROTECT', 0, 0, 3, "Bloque toute attaque ce tour-ci. L'unanimité, c'est sacré."),
 ('frontiere', 'Frontière', 'SOUVERAIN', 'phys', 60, 100, 25, 'STAT_DOWN', 30, 51, 0, "Rétablit un contrôle. Peut baisser la Réactivité."),
 ('opt_out', 'Opt-out', 'SOUVERAIN', 'status', 0, 0, 15, 'STAT_UP', 0, 22, 0, "S'exempte des règles communes. Résilience +2."),
 ('referendum', 'Référendum', 'SOUVERAIN', 'spec', 85, 90, 10, 'CONFUSE', 30, 0, 0, "Une question simple, des conséquences compliquées."),
 ('article_7', 'Article 7', 'SOUVERAIN', 'spec', 70, 100, 10, 'STAT_DOWN', 100, 12, 0, "Suspend des droits. Argumentation adverse -2."),
 ('article_50', 'Article 50', 'SOUVERAIN', 'status', 0, 0, 5, 'LEAVE', 0, 0, 0, "Quitte le combat… si les négociations aboutissent."),
 ('rabais', 'Rabais', 'SOUVERAIN', 'phys', 75, 95, 15, 'DRAIN', 0, 0, 0, "« I want my money back ! » Récupère des PV."),
 ('souverainete', 'Souveraineté', 'SOUVERAIN', 'phys', 100, 90, 10, 'NONE', 0, 0, 0, "Reprend le contrôle avec fracas."),
 # LIBERAL
 ('concurrence', 'Concurrence', 'LIBERAL', 'phys', 55, 100, 25, 'NONE', 0, 0, 0, "Libre et non faussée, mais ça fait mal."),
 ('libre_echange', 'Libre-échange', 'LIBERAL', 'spec', 70, 100, 20, 'NONE', 0, 0, 0, "Un accord commercial à droits nuls."),
 ('deregulation', 'Dérégulation', 'LIBERAL', 'status', 0, 100, 20, 'STAT_DOWN', 0, 22, 0, "Supprime les protections. Résilience adverse -2."),
 ('start_up', 'Start-up', 'LIBERAL', 'phys', 40, 100, 30, 'NONE', 0, 0, 1, "Disruptive et rapide. Agit en premier."),
 ('main_invisible', 'Main invisible', 'LIBERAL', 'phys', 85, 100, 10, 'ALWAYS_HIT', 0, 0, 0, "On ne la voit pas venir. Ne rate jamais."),
 ('en_meme_temps', 'En même temps', 'LIBERAL', 'spec', 45, 100, 15, 'MULTI_HIT', 0, 0, 0, "De droite et de gauche, frappe 2 à 5 fois."),
 ('macronomie', 'Ruissellement', 'LIBERAL', 'spec', 95, 95, 10, 'PAY_DAY', 0, 0, 0, "Fait ruisseler des euros sur le terrain."),
 # SOCIAL
 ('greve', 'Grève', 'SOCIAL', 'status', 0, 90, 15, 'GEL', 0, 0, 0, "Tout s'arrête. Gèle les fonds de la cible."),
 ('pilier_social', 'Pilier social', 'SOCIAL', 'phys', 65, 100, 20, 'NONE', 0, 0, 0, "Un pilier européen des droits sociaux bien solide."),
 ('salaire_minimum', 'Salaire minimum', 'SOCIAL', 'spec', 75, 100, 15, 'NONE', 0, 0, 0, "Directive de 2022 sur des salaires adéquats."),
 ('manif', 'Manifestation', 'SOCIAL', 'phys', 90, 85, 10, 'FLINCH', 30, 0, 0, "Une marée de pancartes. Peut intimider."),
 ('solidarite', 'Solidarité', 'SOCIAL', 'status', 0, 0, 10, 'HEAL_HALF', 0, 0, 0, "Mutualise l'effort. Restaure la moitié des PV."),
 ('oxi', 'OXI', 'SOCIAL', 'spec', 100, 90, 5, 'RECOIL', 0, 0, 0, "Le « non » grec de juillet 2015. Contrecoup assuré."),
 ('erasmus', 'Erasmus', 'SOCIAL', 'spec', 50, 100, 25, 'STAT_UP', 30, 31, 0, "Un échange qui ouvre l'esprit. Peut monter l'Expertise."),
 # VERT
 ('pacte_vert', 'Pacte vert', 'VERT', 'spec', 60, 100, 25, 'NONE', 0, 0, 0, "Le Green Deal de 2019 en pleine figure."),
 ('reboisement', 'Reboisement', 'VERT', 'status', 0, 0, 10, 'HEAL_HALF', 0, 0, 0, "Replante. Restaure la moitié des PV."),
 ('taxe_carbone', 'Taxe carbone', 'VERT', 'spec', 80, 100, 15, 'STAT_DOWN', 20, 31, 0, "Mécanisme d'ajustement aux frontières. Peut baisser l'Expertise."),
 ('neutralite', 'Neutralité 2050', 'VERT', 'spec', 110, 85, 5, 'NONE', 0, 0, 0, "Zéro émission nette, en un seul coup."),
 ('compost', 'Compost', 'VERT', 'phys', 45, 100, 30, 'LOBBY', 20, 0, 0, "Ça sent fort. Peut exposer à l'influence."),
 ('bouchon_attache', 'Bouchon attaché', 'VERT', 'phys', 55, 100, 25, 'TRAP', 50, 0, 0, "Directive 2019/904 : le bouchon ne lâche plus la cible."),
 ('fit_for_55', 'Fit for 55', 'VERT', 'phys', 85, 100, 10, 'NONE', 0, 0, 0, "-55 % d'émissions d'ici 2030, et ça cogne."),
 ('velo', 'Vélo', 'VERT', 'phys', 40, 100, 30, 'NONE', 0, 0, 1, "Une piste cyclable express. Agit en premier."),
 # INDUSTRIE
 ('charbon', 'Charbon', 'INDUSTRIE', 'phys', 45, 100, 30, 'SCANDALE', 10, 0, 0, "La CECA de 1951 en boulet. Peut créer un scandale."),
 ('acier', 'Acier', 'INDUSTRIE', 'phys', 70, 100, 20, 'NONE', 0, 0, 0, "Un poing en acier européen."),
 ('haut_fourneau', 'Haut-fourneau', 'INDUSTRIE', 'spec', 90, 100, 10, 'SCANDALE', 20, 0, 0, "Chaleur extrême. Peut déclencher un scandale."),
 ('delocalisation', 'Délocalisation', 'INDUSTRIE', 'phys', 60, 100, 15, 'STAT_DOWN', 50, 51, 0, "Part ailleurs. Peut baisser la Réactivité adverse."),
 ('airbus', 'Airbus', 'INDUSTRIE', 'phys', 110, 85, 5, 'NONE', 0, 0, 0, "Un champion européen en piqué."),
 ('chaine_montage', 'Chaîne', 'INDUSTRIE', 'phys', 20, 100, 20, 'MULTI_HIT', 0, 0, 0, "Chaîne de montage : frappe 2 à 5 fois."),
 ('plan_industriel', 'Plan industriel', 'INDUSTRIE', 'status', 0, 0, 15, 'STAT_UP', 0, 12, 0, "Relance l'outil productif. Argumentation +2."),
 # ENERGIE
 ('etincelle', 'Étincelle', 'ENERGIE', 'spec', 40, 100, 30, 'GEL', 10, 0, 0, "Petit court-circuit. Peut geler les fonds."),
 ('fission', 'Fission', 'ENERGIE', 'spec', 90, 100, 15, 'NONE', 0, 0, 0, "Euratom, 1957. L'énergie de l'atome."),
 ('eolienne', 'Éolienne', 'ENERGIE', 'spec', 60, 95, 20, 'CONFUSE', 20, 0, 0, "Des pales qui tournent… et la tête aussi."),
 ('robinet_gaz', 'Robinet du gaz', 'ENERGIE', 'status', 0, 90, 10, 'GEL', 0, 0, 0, "Coupe l'approvisionnement. Gèle les fonds."),
 ('repowereu', 'REPowerEU', 'ENERGIE', 'status', 0, 0, 10, 'STAT_UP', 0, 32, 0, "Plan de 2022 pour se sevrer. Expertise +2."),
 ('surtension', 'Surtension', 'ENERGIE', 'phys', 80, 100, 15, 'RECOIL', 0, 0, 0, "Une décharge brutale, avec contrecoup."),
 ('fusion', 'Fusion', 'ENERGIE', 'spec', 120, 80, 5, 'NONE', 0, 0, 0, "Le réacteur ITER à pleine puissance."),
 ('plafond_prix', 'Plafond de prix', 'ENERGIE', 'status', 0, 100, 15, 'STAT_DOWN', 0, 32, 0, "Plafonne l'adversaire. Expertise -2."),
 # JURIDIQUE
 ('mise_en_demeure', 'Mise en demeure', 'JURIDIQUE', 'spec', 50, 100, 25, 'NONE', 0, 0, 0, "Premier avertissement officiel."),
 ('infraction', 'Infraction', 'JURIDIQUE', 'phys', 70, 100, 20, 'NONE', 0, 0, 0, "Une procédure d'infraction bien sentie."),
 ('arret_cjue', 'Arrêt de la CJUE', 'JURIDIQUE', 'spec', 95, 100, 10, 'NONE', 0, 0, 0, "Luxembourg a tranché. Pas d'appel possible."),
 ('amende', 'Amende', 'JURIDIQUE', 'phys', 85, 90, 10, 'PAY_DAY', 0, 0, 0, "Une amende milliardaire. Des pièces volent partout."),
 ('enquete_olaf', 'Enquête OLAF', 'JURIDIQUE', 'spec', 75, 100, 15, 'BLOQUE', 10, 0, 0, "L'office antifraude enquête. Peut bloquer la cible."),
 ('rgpd', 'RGPD', 'JURIDIQUE', 'status', 0, 100, 20, 'STAT_DOWN', 0, 72, 0, "Protège les données. Esquive adverse -2."),
 ('jurisprudence', 'Jurisprudence', 'JURIDIQUE', 'status', 0, 0, 15, 'STAT_UP', 0, 32, 0, "S'appuie sur les précédents. Expertise +2."),
 ('dsa', 'DSA', 'JURIDIQUE', 'spec', 80, 100, 10, 'STAT_DOWN', 30, 31, 0, "Règlement sur les services numériques. Peut baisser l'Expertise."),
 # MONETAIRE
 ('piece_euro', 'Pièce d\'euro', 'MONETAIRE', 'phys', 40, 100, 30, 'NONE', 0, 0, 0, "Un lancer de pièce de 2 €. Pile ou face ?"),
 ('taux_directeur', 'Taux directeur', 'MONETAIRE', 'spec', 70, 100, 20, 'STAT_DOWN', 30, 51, 0, "Remonte les taux. Peut ralentir la cible."),
 ('quantitative', 'Planche à billets', 'MONETAIRE', 'spec', 90, 100, 10, 'NONE', 0, 0, 0, "Assouplissement quantitatif à volonté."),
 ('austerite', 'Austérité', 'MONETAIRE', 'status', 0, 100, 15, 'STAT_DOWN', 0, 12, 0, "Serrez-vous la ceinture. Argumentation adverse -2."),
 ('whatever', 'Whatever it takes', 'MONETAIRE', 'spec', 150, 0, 5, 'ALWAYS_HIT', 0, 0, 0, "« Quoi qu'il en coûte » (Draghi, juillet 2012). Réussit toujours."),
 ('inflation', 'Inflation', 'MONETAIRE', 'spec', 60, 95, 20, 'LOBBY', 30, 0, 0, "Grignote le pouvoir d'achat, tour après tour."),
 ('spread', 'Spread', 'MONETAIRE', 'phys', 75, 95, 15, 'HIGH_CRIT', 0, 0, 0, "L'écart de taux s'envole. Critiques fréquents."),
 ('plan_relance', 'Plan de relance', 'MONETAIRE', 'status', 0, 0, 5, 'HEAL_HALF', 0, 0, 0, "NextGenerationEU, 750 Md€. Restaure la moitié des PV."),
 # AGRICOLE
 ('tracteur', 'Tracteur', 'AGRICOLE', 'phys', 65, 100, 20, 'STAT_DOWN', 30, 51, 0, "Bloque la route. Peut ralentir la cible."),
 ('pac', 'PAC', 'AGRICOLE', 'spec', 75, 100, 15, 'DRAIN', 0, 0, 0, "Politique agricole commune : récupère des PV."),
 ('lisier', 'Lisier', 'AGRICOLE', 'phys', 50, 95, 25, 'LOBBY', 30, 0, 0, "Épandu devant la préfecture. Peut contaminer."),
 ('aop', 'AOP', 'AGRICOLE', 'status', 0, 0, 15, 'STAT_UP', 0, 22, 0, "Appellation protégée. Résilience +2."),
 ('moisson', 'Moisson', 'AGRICOLE', 'phys', 90, 100, 10, 'NONE', 0, 0, 0, "Une récolte record, en pleine tête."),
 ('glyphosate', 'Glyphosate', 'AGRICOLE', 'spec', 70, 90, 15, 'LOBBY', 40, 0, 0, "Réautorisé dix ans en 2023. Peut empoisonner d'influence."),
 ('banane_courbe', 'Banane courbe', 'AGRICOLE', 'phys', 55, 90, 20, 'CONFUSE', 30, 0, 0, "Règlement de 1994 sur la qualité des bananes. Déroutant."),
 # NUMERIQUE
 ('cookie', 'Cookie', 'NUMERIQUE', 'status', 0, 100, 20, 'GEL', 0, 0, 0, "Un bandeau impossible à fermer. Gèle la cible."),
 ('bug', 'Bug', 'NUMERIQUE', 'spec', 50, 100, 25, 'CONFUSE', 20, 0, 0, "Erreur 404. Peut désinformer."),
 ('algorithme', 'Algorithme', 'NUMERIQUE', 'spec', 80, 100, 15, 'NONE', 0, 0, 0, "Une recommandation personnalisée, très personnalisée."),
 ('usb_c', 'USB-C', 'NUMERIQUE', 'phys', 60, 100, 25, 'NONE', 0, 0, 0, "Le chargeur universel, obligatoire depuis 2024."),
 ('fake_news', 'Fake news', 'NUMERIQUE', 'status', 0, 90, 15, 'CONFUSE', 0, 0, 0, "Une rumeur virale. Désinforme la cible."),
 ('roaming', 'Roaming', 'NUMERIQUE', 'spec', 40, 100, 30, 'NONE', 0, 0, 1, "Plus de frais d'itinérance ! Agit en premier."),
 ('ia_act', 'IA Act', 'NUMERIQUE', 'spec', 100, 90, 10, 'NONE', 0, 0, 0, "Premier règlement mondial sur l'IA (2024)."),
 ('troll', 'Trollage', 'NUMERIQUE', 'phys', 45, 100, 25, 'FLINCH', 30, 0, 0, "Un commentaire désagréable. Peut décontenancer."),
 # DIPLO
 ('poignee_main', 'Poignée de main', 'DIPLO', 'phys', 50, 100, 30, 'NONE', 0, 0, 0, "Ferme et prolongée, devant les photographes."),
 ('sommet_nocturne', 'Sommet nocturne', 'DIPLO', 'status', 0, 75, 10, 'SOMMEIL', 0, 0, 0, "Négociations jusqu'à 5 h du matin. Endort la cible."),
 ('compromis', 'Compromis', 'DIPLO', 'spec', 70, 100, 15, 'DRAIN', 0, 0, 0, "Tout le monde perd un peu, vous gagnez des PV."),
 ('sanctions', 'Sanctions', 'DIPLO', 'spec', 85, 100, 10, 'STAT_DOWN', 30, 41, 0, "Un nouveau paquet de sanctions. Peut baisser la Diplomatie."),
 ('canape', 'Canapé', 'DIPLO', 'status', 0, 100, 10, 'STEAL_TURN', 0, 0, 3, "Sofagate (Ankara, 2021) : la cible perd son tour. 1er tour seulement."),
 ('interprete', 'Interprétariat', 'DIPLO', 'spec', 60, 100, 20, 'CONFUSE', 30, 0, 0, "Traduit en 24 langues. Quelque chose se perd."),
 ('accord', 'Accord', 'DIPLO', 'phys', 95, 95, 10, 'NONE', 0, 0, 0, "Un accord historique, signé à l'arraché."),
 ('soft_power', 'Soft power', 'DIPLO', 'status', 0, 0, 20, 'STAT_UP', 0, 42, 0, "Le charme européen. Diplomatie +2."),
 # LOBBY
 ('petits_fours', 'Petits fours', 'LOBBY', 'status', 0, 100, 20, 'LOBBY', 0, 0, 0, "Un cocktail place Lux. La cible passe sous influence."),
 ('valise', 'Valise', 'LOBBY', 'phys', 60, 100, 25, 'NONE', 0, 0, 0, "Une valise bien remplie, lancée avec élan."),
 ('sac_billets', 'Sac de billets', 'LOBBY', 'phys', 90, 90, 10, 'PAY_DAY', 0, 0, 0, "Des billets partout. Le terrain en est couvert."),
 ('note_position', 'Note de position', 'LOBBY', 'spec', 70, 100, 15, 'NONE', 0, 0, 0, "Un amendement clé en main, déjà rédigé."),
 ('pantouflage', 'Pantouflage', 'LOBBY', 'status', 0, 0, 10, 'STAT_UP', 0, 52, 0, "Passe dans le privé. Réactivité +2."),
 ('influence', 'Influence', 'LOBBY', 'spec', 55, 100, 20, 'LOBBY', 30, 0, 0, "Un mot glissé à la bonne oreille."),
 ('porte_tournante', 'Porte tournante', 'LOBBY', 'phys', 80, 100, 10, 'CONFUSE', 30, 0, 0, "On ne sait plus qui travaille pour qui."),
 # POPULISTE
 ('slogan', 'Slogan', 'POPULISTE', 'spec', 50, 100, 25, 'NONE', 0, 0, 0, "Trois mots, aucune nuance."),
 ('bus_rouge', 'Bus rouge', 'POPULISTE', 'phys', 85, 90, 10, 'CONFUSE', 30, 0, 0, "« 350 millions par semaine ! » Peut désinformer."),
 ('megaphone', 'Mégaphone', 'POPULISTE', 'spec', 75, 100, 15, 'FLINCH', 20, 0, 0, "Crie plus fort que tout le monde."),
 ('euromythe', 'Euromythe', 'POPULISTE', 'status', 0, 100, 15, 'CONFUSE', 0, 0, 0, "Une légende sur Bruxelles, très convaincante."),
 ('tremendous', 'TREMENDOUS', 'POPULISTE', 'status', 0, 0, 10, 'STAT_UP', 0, 13, 0, "Le meilleur coup de tous les temps. Argumentation +3."),
 ('droits_douane', 'Droits de douane', 'POPULISTE', 'phys', 80, 100, 10, 'STAT_DOWN', 50, 22, 0, "Liberation Day (2 avril 2025). Peut baisser la Résilience."),
 ('tweet_majuscules', 'Post majuscules', 'POPULISTE', 'spec', 95, 90, 10, 'NONE', 0, 0, 0, "UN MESSAGE ÉCRIT ENTIÈREMENT EN MAJUSCULES."),
 ('laughing', 'Not laughing', 'POPULISTE', 'spec', 65, 100, 15, 'STAT_DOWN', 50, 41, 0, "« You're not laughing now! » (2016). Peut baisser la Diplomatie."),
 # FANTOME
 ('emploi_fictif', 'Emploi fictif', 'FANTOME', 'spec', 60, 100, 20, 'NONE', 0, 0, 0, "Un travail qui n'existe pas, mais qui coûte."),
 ('disparition', 'Disparition', 'FANTOME', 'status', 0, 0, 15, 'STAT_UP', 0, 72, 0, "Introuvable au bureau. Esquive +2."),
 ('sms_efface', 'SMS effacé', 'FANTOME', 'status', 0, 100, 10, 'ERASE', 0, 0, 0, "Aucun message ne subsiste. Annule les bonus adverses."),
 ('hantise', 'Hantise', 'FANTOME', 'spec', 80, 100, 10, 'CONFUSE', 20, 0, 0, "Un dossier qui revient hanter son auteur."),
 ('fantome_payroll', 'Fiche de paie', 'FANTOME', 'phys', 70, 100, 15, 'DRAIN', 0, 0, 0, "Un salaire versé pour rien. Récupère des PV."),
 ('ectoplasme', 'Ectoplasme', 'FANTOME', 'spec', 100, 85, 5, 'NONE', 0, 0, 0, "Une apparition spectaculaire au Parlement."),
 # specials (story / legendaries)
 ('constitution', 'Constitution', 'FEDERAL', 'spec', 130, 70, 5, 'NONE', 0, 0, 0, "Rejetée en 2005… mais d'une puissance folle."),
 ('traite_rome', 'Traité de Rome', 'JURIDIQUE', 'phys', 120, 90, 5, 'NONE', 0, 0, 0, "1957 : la fondation de la CEE."),
 ('traite_maastricht', 'Maastricht', 'MONETAIRE', 'spec', 120, 90, 5, 'NONE', 0, 0, 0, "1992 : l'Union et la monnaie unique."),
 ('traite_lisbonne', 'Lisbonne', 'JURIDIQUE', 'spec', 120, 90, 5, 'STAT_UP', 30, 41, 0, "2007 : le traité qui a remplacé la Constitution."),
 ('terres_rares', 'Terres rares', 'INDUSTRIE', 'spec', 90, 95, 10, 'GEL', 30, 0, 0, "Restreint les exportations. Peut geler les fonds."),
 ('longue_table', 'Longue table', 'SOUVERAIN', 'status', 0, 0, 10, 'STAT_UP', 0, 72, 0, "Reçoit au bout d'une table de six mètres. Esquive +2."),
 ('rival_systemique', 'Rival systémique', 'DIPLO', 'spec', 85, 100, 10, 'STAT_DOWN', 30, 42, 0, "Partenaire, concurrent, rival. Peut baisser la Diplomatie."),
 ('chantage_groenland', 'Groenland', 'POPULISTE', 'phys', 100, 85, 5, 'NONE', 0, 0, 0, "Tente d'acheter une île entière. Gros dégâts."),
]
moves = []
for t in M:
    moves.append(dict(zip(['id', 'name', 'type', 'cat', 'power', 'acc', 'pp', 'effect', 'chance', 'param', 'priority', 'desc'], t)))
json.dump(moves, open(os.path.join(D, 'moves.json'), 'w'), ensure_ascii=False, indent=1)

I = [
 ('tampon', 'Tampon officiel', 'ball', 200, 10, "Tamponne un Euromon affaibli pour l'enregistrer."),
 ('super_tampon', 'Super Tampon', 'ball', 600, 15, "Encre renforcée. Plus efficace qu'un tampon simple."),
 ('tampon_qualifie', 'Tampon qualifié', 'ball', 1200, 20, "Majorité qualifiée : très bonne chance de capture."),
 ('tampon_unanime', 'Tampon unanime', 'ball', 0, 255, "L'unanimité ! Capture garantie. Extrêmement rare."),
 ('cafe', 'Café cantine', 'heal', 200, 20, "Restaure 20 PV. Tiède, mais efficace."),
 ('sandwich', 'Sandwich club', 'heal', 500, 50, "Restaure 50 PV. Le préféré des stagiaires."),
 ('gaufre', 'Gaufre de Bruxelles', 'heal', 900, 120, "Restaure 120 PV. Sucre glace inclus."),
 ('kniddelen', 'Kniddelen', 'heal', 1500, 200, "Spécialité luxembourgeoise. Restaure 200 PV."),
 ('menu_complet', 'Menu complet', 'heal', 2500, 999, "Entrée, plat, dessert : restaure tous les PV."),
 ('avis_juridique', 'Avis juridique', 'status', 300, 0, "Soigne tous les problèmes de statut."),
 ('reveil', 'Réveil-matin', 'status', 150, 0, "Réveille un Euromon endormi par un sommet."),
 ('motion_relance', 'Motion de relance', 'revive', 1500, 50, "Remet un Euromon K.O. en état de débattre."),
 ('motion_unanime', 'Relance unanime', 'revive', 0, 999, "Ranime un Euromon K.O. avec tous ses PV."),
 ('pause_syndicale', 'Pause syndicale', 'pp', 1200, 0, "Restaure tous les PP d'un Euromon."),
 ('x_argument', 'Argumentaire', 'battle', 500, 11, "En combat : augmente l'Argumentation."),
 ('x_resilience', 'Gilet pare-balles', 'battle', 500, 21, "En combat : augmente la Résilience."),
 ('x_expertise', 'Rapport d\'expert', 'battle', 500, 31, "En combat : augmente l'Expertise."),
 ('x_diplomatie', 'Carnet d\'adresses', 'battle', 500, 41, "En combat : augmente la Diplomatie."),
 ('x_reactivite', 'Double expresso', 'battle', 500, 51, "En combat : augmente la Réactivité."),
 ('non_sollicitation', 'Non-sollicitation', 'repel', 400, 100, "Clause anti-démarchage : éloigne les Euromons 100 pas."),
 ('ratification', 'Ratification', 'evo', 2000, 0, "Fait évoluer certains Euromons. Il faut 27 signatures."),
 ('pierre_solaire', 'Panneau solaire', 'evo', 2000, 0, "Fait évoluer certains Euromons énergétiques."),
 ('cle_usb', 'Clé USB-C', 'evo', 2000, 0, "Fait évoluer certains Euromons numériques."),
 # key items
 ('eurodex', 'Eurodex', 'key', 0, 0, "Encyclopédie des Euromons, offerte par Jean Monnet."),
 ('badge_acces', 'Badge d\'accès', 'key', 0, 0, "Ouvre les portes du Parlement. Couleur : stagiaire."),
 ('badge_olaf', 'Badge OLAF', 'key', 0, 0, "Permet de voir les assistants fantômes."),
 ('passeport', 'Passeport européen', 'key', 0, 0, "Bordeaux, 32 pages, toutes les frontières s'ouvrent."),
 ('pass_interrail', 'Pass Interrail', 'key', 0, 0, "Voyagez en train dans toute l'Europa."),
 ('repowereu_item', 'Kit REPowerEU', 'key', 0, 0, "Pour rallumer le chauffage quand le gaz est coupé."),
 ('cognac', 'Cognac', 'key', 0, 0, "Une bouteille précieuse. Surtaxée depuis 2024…"),
 ('carte_cantine', 'Carte de cantine', 'key', 0, 0, "Crédit : 3,40 €. Suffisant pour un café."),
 ('directive_heure', 'Directive heure', 'key', 0, 0, "La directive sur la fin du changement d'heure (2019)."),
 ('malle_fer', 'Malle en fer', 'key', 0, 0, "Une malle du déménagement Bruxelles–Strasbourg."),
 ('etui_badges', 'Étui à badges', 'key', 0, 0, "Contient les badges des traités."),
]
items = [dict(zip(['id', 'name', 'kind', 'price', 'param', 'desc'], t)) for t in I]
json.dump(items, open(os.path.join(D, 'items.json'), 'w'), ensure_ascii=False, indent=1)
print('types', len(TYPES), 'moves', len(moves), 'items', len(items))
