#!/usr/bin/env python3
"""Generates data/types.json, data/moves.json, data/items.json"""
import json, os
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
D = os.path.join(ROOT, 'data')
os.makedirs(D, exist_ok=True)

TYPES = ["TECHNO", "FEDERAL", "SOUVERAIN", "LIBERAL", "SOCIAL", "VERT", "INDUSTRIE", "ENERGIE",
         "JURIDIQUE", "MONETAIRE", "AGRICOLE", "NUMERIQUE", "DIPLO", "LOBBY", "POPULISTE", "FANTOME"]
NAMES = ["Techno", "Federal", "Sovereign", "Liberal", "Social", "Green", "Industry", "Energy",
         "Legal", "Monetary", "Agri", "Digital", "Diplo", "Lobby", "Populist", "Ghost"]
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
 ('amendement', "Amendment", 'TECHNO', 'phys', 40, 100, 35, 'NONE', 0, 0, 0, "Changes the opponent's text, one paragraph at a time."),
 ('paperasse', "Paperwork", 'TECHNO', 'phys', 50, 95, 30, 'NONE', 0, 0, 0, "Buries the target under forms."),
 ('note_de_service', "Memo", 'TECHNO', 'spec', 60, 100, 25, 'NONE', 0, 0, 0, "A very firm internal memo."),
 ('reunion', "Meeting", 'TECHNO', 'status', 0, 100, 20, 'SOMMEIL', 0, 0, 0, "A coordination meeting that puts everyone to sleep."),
 ('tampon_sec', "Dry Stamp", 'TECHNO', 'phys', 70, 100, 20, 'FLINCH', 20, 0, 0, "A clean, official stamp."),
 ('comitologie', "Comitology", 'TECHNO', 'status', 0, 100, 20, 'CONFUSE', 0, 0, 0, "Nobody understands the procedure. Not even the target."),
 ('relire', "Proofreading", 'TECHNO', 'status', 0, 0, 30, 'STAT_UP', 0, 22, 0, "Rereads its file. Sharply raises Resilience."),
 ('directive', 'Directive', 'TECHNO', 'spec', 90, 100, 15, 'NONE', 0, 0, 0, "A binding text to be transposed urgently."),
 ('reglement', "Regulation", 'TECHNO', 'phys', 120, 85, 5, 'NONE', 0, 0, 0, "Directly applicable in all member states."),
 ('trilogue', 'Trilogue', 'TECHNO', 'spec', 25, 90, 10, 'MULTI_HIT', 0, 0, 0, "Parliament, Council, Commission: hits 2 to 5 times."),
 ('procedure_urgence', "Urgency", 'TECHNO', 'phys', 40, 100, 30, 'NONE', 0, 0, 1, "Urgent procedure: goes first."),
 ('pause_cafe', "Coffee Break", 'TECHNO', 'status', 0, 0, 10, 'HEAL_HALF', 0, 0, 0, "A canteen coffee. Restores half the HP."),
 ('plagiat', "Plagiarism", 'TECHNO', 'status', 0, 0, 10, 'COPY', 0, 0, 0, "Copies the opponent's last move."),
 ('rapport_annuel', "Annual Report", 'TECHNO', 'spec', 100, 90, 10, 'CHARGE', 0, 0, 0, "Charges for one turn, then knocks out with 400 pages."),
 # FEDERAL
 ('integration', "Integration", 'FEDERAL', 'spec', 40, 100, 30, 'NONE', 0, 0, 0, "A small step towards an ever closer union."),
 ('subsidiarite', "Subsidiarity", 'FEDERAL', 'status', 0, 0, 20, 'STAT_UP', 0, 41, 0, "Acts at the right level. Raises Diplomacy."),
 ('etats_unis_europe', "United States EU", 'FEDERAL', 'spec', 110, 85, 5, 'NONE', 0, 0, 0, "The great federal dream, launched at full power."),
 ('team_europe', 'Team Europe', 'FEDERAL', 'phys', 75, 100, 15, 'NONE', 0, 0, 0, "All together! A charge of solidarity."),
 ('marche_unique', "Single Market", 'FEDERAL', 'spec', 80, 100, 15, 'STAT_DOWN', 20, 41, 0, "Abolishes borders… and the opponent's Diplomacy."),
 ('drapeau_etoile', "Twelve Stars", 'FEDERAL', 'spec', 60, 0, 20, 'ALWAYS_HIT', 0, 0, 0, "Twelve golden stars that never miss."),
 ('spitzen', "Lead Candidate", 'FEDERAL', 'phys', 90, 100, 10, 'HIGH_CRIT', 0, 0, 0, "A Spitzenkandidat campaign. High critical-hit rate."),
 ('elargissement', "Enlargement", 'FEDERAL', 'status', 0, 0, 10, 'STAT_UP', 0, 12, 0, "Welcomes new members. Argument +2."),
 # SOUVERAIN
 ('veto', 'Veto', 'SOUVERAIN', 'status', 0, 0, 10, 'PROTECT', 0, 0, 3, "Blocks any attack this turn. Unanimity is sacred."),
 ('frontiere', "Border", 'SOUVERAIN', 'phys', 60, 100, 25, 'STAT_DOWN', 30, 51, 0, "Restores checks. May lower Reactivity."),
 ('opt_out', 'Opt-out', 'SOUVERAIN', 'status', 0, 0, 15, 'STAT_UP', 0, 22, 0, "Exempts itself from the common rules. Resilience +2."),
 ('referendum', "Referendum", 'SOUVERAIN', 'spec', 85, 90, 10, 'CONFUSE', 30, 0, 0, "A simple question, complicated consequences."),
 ('article_7', 'Article 7', 'SOUVERAIN', 'spec', 70, 100, 10, 'STAT_DOWN', 100, 12, 0, "Suspends rights. Opponent's Argument -2."),
 ('article_50', 'Article 50', 'SOUVERAIN', 'status', 0, 0, 5, 'LEAVE', 0, 0, 0, "Leaves the battle… if the negotiations succeed."),
 ('rabais', "Rebate", 'SOUVERAIN', 'phys', 75, 95, 15, 'DRAIN', 0, 0, 0, "“I want my money back!” Regains HP."),
 ('souverainete', "Sovereignty", 'SOUVERAIN', 'phys', 100, 90, 10, 'NONE', 0, 0, 0, "Takes back control, with a crash."),
 # LIBERAL
 ('concurrence', "Competition", 'LIBERAL', 'phys', 55, 100, 25, 'NONE', 0, 0, 0, "Free and undistorted, but it hurts."),
 ('libre_echange', "Free Trade", 'LIBERAL', 'spec', 70, 100, 20, 'NONE', 0, 0, 0, "A zero-tariff trade agreement."),
 ('deregulation', "Deregulation", 'LIBERAL', 'status', 0, 100, 20, 'STAT_DOWN', 0, 22, 0, "Removes protections. Opponent's Resilience -2."),
 ('start_up', 'Start-up', 'LIBERAL', 'phys', 40, 100, 30, 'NONE', 0, 0, 1, "Disruptive and fast. Goes first."),
 ('main_invisible', "Invisible Hand", 'LIBERAL', 'phys', 85, 100, 10, 'ALWAYS_HIT', 0, 0, 0, "You never see it coming. Never misses."),
 ('en_meme_temps', "At the Same Time", 'LIBERAL', 'spec', 45, 100, 15, 'MULTI_HIT', 0, 0, 0, "From the right and the left, hits 2 to 5 times."),
 ('macronomie', "Trickle-down", 'LIBERAL', 'spec', 95, 95, 10, 'PAY_DAY', 0, 0, 0, "Makes euros trickle down onto the field."),
 # SOCIAL
 ('greve', "Strike", 'SOCIAL', 'status', 0, 90, 15, 'GEL', 0, 0, 0, "Everything stops. Freezes the target's funds."),
 ('pilier_social', "Social Pillar", 'SOCIAL', 'phys', 65, 100, 20, 'NONE', 0, 0, 0, "A rock-solid European pillar of social rights."),
 ('salaire_minimum', "Minimum Wage", 'SOCIAL', 'spec', 75, 100, 15, 'NONE', 0, 0, 0, "2022 directive on adequate wages."),
 ('manif', "Protest", 'SOCIAL', 'phys', 90, 85, 10, 'FLINCH', 30, 0, 0, "A sea of placards. May intimidate."),
 ('solidarite', "Solidarity", 'SOCIAL', 'status', 0, 0, 10, 'HEAL_HALF', 0, 0, 0, "Shares the effort. Restores half the HP."),
 ('oxi', 'OXI', 'SOCIAL', 'spec', 100, 90, 5, 'RECOIL', 0, 0, 0, "The Greek “no” of July 2015. Recoil guaranteed."),
 ('erasmus', 'Erasmus', 'SOCIAL', 'spec', 50, 100, 25, 'STAT_UP', 30, 31, 0, "An exchange that broadens the mind. May raise Expertise."),
 # VERT
 ('pacte_vert', "Green Deal", 'VERT', 'spec', 60, 100, 25, 'NONE', 0, 0, 0, "The 2019 Green Deal, right in the face."),
 ('reboisement', "Reforestation", 'VERT', 'status', 0, 0, 10, 'HEAL_HALF', 0, 0, 0, "Replants. Restores half the HP."),
 ('taxe_carbone', "Carbon Tax", 'VERT', 'spec', 80, 100, 15, 'STAT_DOWN', 20, 31, 0, "Carbon border adjustment mechanism. May lower Expertise."),
 ('neutralite', "Neutral 2050", 'VERT', 'spec', 110, 85, 5, 'NONE', 0, 0, 0, "Net zero emissions, in a single blow."),
 ('compost', 'Compost', 'VERT', 'phys', 45, 100, 30, 'LOBBY', 20, 0, 0, "It smells strong. May expose to influence."),
 ('bouchon_attache', "Tethered Cap", 'VERT', 'phys', 55, 100, 25, 'TRAP', 50, 0, 0, "Directive 2019/904: the cap won't let go of the target."),
 ('fit_for_55', 'Fit for 55', 'VERT', 'phys', 85, 100, 10, 'NONE', 0, 0, 0, "-55% emissions by 2030, and it hits hard."),
 ('velo', "Bicycle", 'VERT', 'phys', 40, 100, 30, 'NONE', 0, 0, 1, "An express cycle lane. Goes first."),
 # INDUSTRIE
 ('charbon', "Coal", 'INDUSTRIE', 'phys', 45, 100, 30, 'SCANDALE', 10, 0, 0, "The 1951 ECSC as a cannonball. May cause a scandal."),
 ('acier', "Steel", 'INDUSTRIE', 'phys', 70, 100, 20, 'NONE', 0, 0, 0, "A fist of European steel."),
 ('haut_fourneau', "Blast Furnace", 'INDUSTRIE', 'spec', 90, 100, 10, 'SCANDALE', 20, 0, 0, "Extreme heat. May trigger a scandal."),
 ('delocalisation', "Offshoring", 'INDUSTRIE', 'phys', 60, 100, 15, 'STAT_DOWN', 50, 51, 0, "Moves elsewhere. May lower the opponent's Reactivity."),
 ('airbus', 'Airbus', 'INDUSTRIE', 'phys', 110, 85, 5, 'NONE', 0, 0, 0, "A European champion in a nosedive."),
 ('chaine_montage', "Assembly Line", 'INDUSTRIE', 'phys', 20, 100, 20, 'MULTI_HIT', 0, 0, 0, "Production line: hits 2 to 5 times."),
 ('plan_industriel', "Industrial Plan", 'INDUSTRIE', 'status', 0, 0, 15, 'STAT_UP', 0, 12, 0, "Revives production. Argument +2."),
 # ENERGIE
 ('etincelle', "Spark", 'ENERGIE', 'spec', 40, 100, 30, 'GEL', 10, 0, 0, "A little short circuit. May freeze funds."),
 ('fission', 'Fission', 'ENERGIE', 'spec', 90, 100, 15, 'NONE', 0, 0, 0, "Euratom, 1957. The power of the atom."),
 ('eolienne', "Wind Turbine", 'ENERGIE', 'spec', 60, 95, 20, 'CONFUSE', 20, 0, 0, "Blades that spin… and heads too."),
 ('robinet_gaz', "Gas Tap", 'ENERGIE', 'status', 0, 90, 10, 'GEL', 0, 0, 0, "Cuts off supply. Freezes funds."),
 ('repowereu', 'REPowerEU', 'ENERGIE', 'status', 0, 0, 10, 'STAT_UP', 0, 32, 0, "2022 plan to kick the habit. Expertise +2."),
 ('surtension', "Power Surge", 'ENERGIE', 'phys', 80, 100, 15, 'RECOIL', 0, 0, 0, "A brutal discharge, with recoil."),
 ('fusion', 'Fusion', 'ENERGIE', 'spec', 120, 80, 5, 'NONE', 0, 0, 0, "The ITER reactor at full power."),
 ('plafond_prix', "Price Cap", 'ENERGIE', 'status', 0, 100, 15, 'STAT_DOWN', 0, 32, 0, "Puts a cap on the opponent. Expertise -2."),
 # JURIDIQUE
 ('mise_en_demeure', "Formal Notice", 'JURIDIQUE', 'spec', 50, 100, 25, 'NONE', 0, 0, 0, "First official warning."),
 ('infraction', "Infringement", 'JURIDIQUE', 'phys', 70, 100, 20, 'NONE', 0, 0, 0, "A well-aimed infringement procedure."),
 ('arret_cjue', "CJEU Ruling", 'JURIDIQUE', 'spec', 95, 100, 10, 'NONE', 0, 0, 0, "Luxembourg has ruled. No appeal possible."),
 ('amende', "Fine", 'JURIDIQUE', 'phys', 85, 90, 10, 'PAY_DAY', 0, 0, 0, "A billion-euro fine. Coins fly everywhere."),
 ('enquete_olaf', "OLAF Probe", 'JURIDIQUE', 'spec', 75, 100, 15, 'BLOQUE', 10, 0, 0, "The Anti-Fraud Office investigates. May block the target."),
 ('rgpd', "GDPR", 'JURIDIQUE', 'status', 0, 100, 20, 'STAT_DOWN', 0, 72, 0, "Protects data. Opponent's Evasion -2."),
 ('jurisprudence', "Case Law", 'JURIDIQUE', 'status', 0, 0, 15, 'STAT_UP', 0, 32, 0, "Relies on precedent. Expertise +2."),
 ('dsa', 'DSA', 'JURIDIQUE', 'spec', 80, 100, 10, 'STAT_DOWN', 30, 31, 0, "Digital Services Act. May lower Expertise."),
 # MONETAIRE
 ('piece_euro', "Euro Coin", 'MONETAIRE', 'phys', 40, 100, 30, 'NONE', 0, 0, 0, "A €2 coin toss. Heads or tails?"),
 ('taux_directeur', "Key Rate", 'MONETAIRE', 'spec', 70, 100, 20, 'STAT_DOWN', 30, 51, 0, "Raises rates. May slow the target."),
 ('quantitative', "Money Printer", 'MONETAIRE', 'spec', 90, 100, 10, 'NONE', 0, 0, 0, "Quantitative easing at will."),
 ('austerite', "Austerity", 'MONETAIRE', 'status', 0, 100, 15, 'STAT_DOWN', 0, 12, 0, "Tighten your belts. Opponent's Argument -2."),
 ('whatever', 'Whatever it takes', 'MONETAIRE', 'spec', 150, 0, 5, 'ALWAYS_HIT', 0, 0, 0, "“Whatever it takes” (Draghi, July 2012). Always succeeds."),
 ('inflation', 'Inflation', 'MONETAIRE', 'spec', 60, 95, 20, 'LOBBY', 30, 0, 0, "Eats away at purchasing power, turn after turn."),
 ('spread', 'Spread', 'MONETAIRE', 'phys', 75, 95, 15, 'HIGH_CRIT', 0, 0, 0, "The rate gap soars. High critical-hit rate."),
 ('plan_relance', "Recovery Plan", 'MONETAIRE', 'status', 0, 0, 5, 'HEAL_HALF', 0, 0, 0, "NextGenerationEU, €750bn. Restores half the HP."),
 # AGRICOLE
 ('tracteur', "Tractor", 'AGRICOLE', 'phys', 65, 100, 20, 'STAT_DOWN', 30, 51, 0, "Blocks the road. May slow the target."),
 ('pac', "CAP", 'AGRICOLE', 'spec', 75, 100, 15, 'DRAIN', 0, 0, 0, "Common Agricultural Policy: regains HP."),
 ('lisier', "Slurry", 'AGRICOLE', 'phys', 50, 95, 25, 'LOBBY', 30, 0, 0, "Spread in front of the prefecture. May contaminate."),
 ('aop', "PDO", 'AGRICOLE', 'status', 0, 0, 15, 'STAT_UP', 0, 22, 0, "Protected designation. Resilience +2."),
 ('moisson', "Harvest", 'AGRICOLE', 'phys', 90, 100, 10, 'NONE', 0, 0, 0, "A record harvest, straight to the head."),
 ('glyphosate', 'Glyphosate', 'AGRICOLE', 'spec', 70, 90, 15, 'LOBBY', 40, 0, 0, "Reauthorised for ten years in 2023. May poison with influence."),
 ('banane_courbe', "Bent Banana", 'AGRICOLE', 'phys', 55, 90, 20, 'CONFUSE', 30, 0, 0, "1994 regulation on banana quality. Confusing."),
 # NUMERIQUE
 ('cookie', 'Cookie', 'NUMERIQUE', 'status', 0, 100, 20, 'GEL', 0, 0, 0, "A banner you can't close. Freezes the target."),
 ('bug', 'Bug', 'NUMERIQUE', 'spec', 50, 100, 25, 'CONFUSE', 20, 0, 0, "Error 404. May misinform."),
 ('algorithme', "Algorithm", 'NUMERIQUE', 'spec', 80, 100, 15, 'NONE', 0, 0, 0, "A personalised recommendation, very personalised."),
 ('usb_c', 'USB-C', 'NUMERIQUE', 'phys', 60, 100, 25, 'NONE', 0, 0, 0, "The universal charger, mandatory since 2024."),
 ('fake_news', 'Fake news', 'NUMERIQUE', 'status', 0, 90, 15, 'CONFUSE', 0, 0, 0, "A viral rumour. Misinforms the target."),
 ('roaming', 'Roaming', 'NUMERIQUE', 'spec', 40, 100, 30, 'NONE', 0, 0, 1, "No more roaming charges! Goes first."),
 ('ia_act', "AI Act", 'NUMERIQUE', 'spec', 100, 90, 10, 'NONE', 0, 0, 0, "The world's first AI regulation (2024)."),
 ('troll', "Trolling", 'NUMERIQUE', 'phys', 45, 100, 25, 'FLINCH', 30, 0, 0, "A nasty comment. May disconcert."),
 # DIPLO
 ('poignee_main', "Handshake", 'DIPLO', 'phys', 50, 100, 30, 'NONE', 0, 0, 0, "Firm and prolonged, in front of the photographers."),
 ('sommet_nocturne', "Night summit", 'DIPLO', 'status', 0, 75, 10, 'SOMMEIL', 0, 0, 0, "Negotiations until 5 a.m. Puts the target to sleep."),
 ('compromis', "Compromise", 'DIPLO', 'spec', 70, 100, 15, 'DRAIN', 0, 0, 0, "Everyone loses a little, you gain HP."),
 ('sanctions', 'Sanctions', 'DIPLO', 'spec', 85, 100, 10, 'STAT_DOWN', 30, 41, 0, "A new sanctions package. May lower Diplomacy."),
 ('canape', "Sofa", 'DIPLO', 'status', 0, 100, 10, 'STEAL_TURN', 0, 0, 3, "Sofagate (Ankara, 2021): the target loses its turn. First turn only."),
 ('interprete', "Interpreting", 'DIPLO', 'spec', 60, 100, 20, 'CONFUSE', 30, 0, 0, "Translated into 24 languages. Something gets lost."),
 ('accord', "Agreement", 'DIPLO', 'phys', 95, 95, 10, 'NONE', 0, 0, 0, "A historic agreement, signed at the last minute."),
 ('soft_power', 'Soft power', 'DIPLO', 'status', 0, 0, 20, 'STAT_UP', 0, 42, 0, "European charm. Diplomacy +2."),
 # LOBBY
 ('petits_fours', "Canapés", 'LOBBY', 'status', 0, 100, 20, 'LOBBY', 0, 0, 0, "A cocktail party on Place Lux. The target falls under influence."),
 ('valise', "Suitcase", 'LOBBY', 'phys', 60, 100, 25, 'NONE', 0, 0, 0, "A well-filled suitcase, thrown with gusto."),
 ('sac_billets', "Bag of Cash", 'LOBBY', 'phys', 90, 90, 10, 'PAY_DAY', 0, 0, 0, "Banknotes everywhere. The field is covered with them."),
 ('note_position', "Position Paper", 'LOBBY', 'spec', 70, 100, 15, 'NONE', 0, 0, 0, "A ready-made key amendment, already drafted."),
 ('pantouflage', "Revolving Job", 'LOBBY', 'status', 0, 0, 10, 'STAT_UP', 0, 52, 0, "Moves to the private sector. Reactivity +2."),
 ('influence', 'Influence', 'LOBBY', 'spec', 55, 100, 20, 'LOBBY', 30, 0, 0, "A word in the right ear."),
 ('porte_tournante', "Revolving Door", 'LOBBY', 'phys', 80, 100, 10, 'CONFUSE', 30, 0, 0, "Nobody knows who works for whom any more."),
 # POPULISTE
 ('slogan', 'Slogan', 'POPULISTE', 'spec', 50, 100, 25, 'NONE', 0, 0, 0, "Three words, zero nuance."),
 ('bus_rouge', "Red Bus", 'POPULISTE', 'phys', 85, 90, 10, 'CONFUSE', 30, 0, 0, "“350 million a week!” May misinform."),
 ('megaphone', "Megaphone", 'POPULISTE', 'spec', 75, 100, 15, 'FLINCH', 20, 0, 0, "Shouts louder than everyone else."),
 ('euromythe', "Euromyth", 'POPULISTE', 'status', 0, 100, 15, 'CONFUSE', 0, 0, 0, "A legend about Brussels, very convincing."),
 ('tremendous', 'TREMENDOUS', 'POPULISTE', 'status', 0, 0, 10, 'STAT_UP', 0, 13, 0, "The best move of all time. Argument +3."),
 ('droits_douane', "Tariffs", 'POPULISTE', 'phys', 80, 100, 10, 'STAT_DOWN', 50, 22, 0, "Liberation Day (2 April 2025). May lower Resilience."),
 ('tweet_majuscules', "Caps Lock Post", 'POPULISTE', 'spec', 95, 90, 10, 'NONE', 0, 0, 0, "A MESSAGE WRITTEN ENTIRELY IN CAPITAL LETTERS."),
 ('laughing', 'Not laughing', 'POPULISTE', 'spec', 65, 100, 15, 'STAT_DOWN', 50, 41, 0, "“You're not laughing now!” (2016). May lower Diplomacy."),
 # FANTOME
 ('emploi_fictif', "Fake Job", 'FANTOME', 'spec', 60, 100, 20, 'NONE', 0, 0, 0, "A job that doesn't exist, but costs money."),
 ('disparition', "Vanishing", 'FANTOME', 'status', 0, 0, 15, 'STAT_UP', 0, 72, 0, "Nowhere to be found at the office. Evasion +2."),
 ('sms_efface', "Deleted Text", 'FANTOME', 'status', 0, 100, 10, 'ERASE', 0, 0, 0, "No message remains. Cancels the opponent's boosts."),
 ('hantise', "Haunting", 'FANTOME', 'spec', 80, 100, 10, 'CONFUSE', 20, 0, 0, "A file that comes back to haunt its author."),
 ('fantome_payroll', "Payslip", 'FANTOME', 'phys', 70, 100, 15, 'DRAIN', 0, 0, 0, "A salary paid for nothing. Regains HP."),
 ('ectoplasme', "Ectoplasm", 'FANTOME', 'spec', 100, 85, 5, 'NONE', 0, 0, 0, "A spectacular apparition in Parliament."),
 # specials (story / legendaries)
 ('constitution', 'Constitution', 'FEDERAL', 'spec', 130, 70, 5, 'NONE', 0, 0, 0, "Rejected in 2005… but insanely powerful."),
 ('traite_rome', "Treaty of Rome", 'JURIDIQUE', 'phys', 120, 90, 5, 'NONE', 0, 0, 0, "1957: the founding of the EEC."),
 ('traite_maastricht', 'Maastricht', 'MONETAIRE', 'spec', 120, 90, 5, 'NONE', 0, 0, 0, "1992: the Union and the single currency."),
 ('traite_lisbonne', "Lisbon", 'JURIDIQUE', 'spec', 120, 90, 5, 'STAT_UP', 30, 41, 0, "2007: the treaty that replaced the Constitution."),
 ('terres_rares', "Rare Earths", 'INDUSTRIE', 'spec', 90, 95, 10, 'GEL', 30, 0, 0, "Restricts exports. May freeze funds."),
 ('longue_table', "Long Table", 'SOUVERAIN', 'status', 0, 0, 10, 'STAT_UP', 0, 72, 0, "Receives you at the end of a six-metre table. Evasion +2."),
 ('rival_systemique', "Systemic Rival", 'DIPLO', 'spec', 85, 100, 10, 'STAT_DOWN', 30, 42, 0, "Partner, competitor, rival. May lower Diplomacy."),
 ('chantage_groenland', "Greenland", 'POPULISTE', 'phys', 100, 85, 5, 'NONE', 0, 0, 0, "Tries to buy an entire island. Heavy damage."),
]
moves = []
for t in M:
    moves.append(dict(zip(['id', 'name', 'type', 'cat', 'power', 'acc', 'pp', 'effect', 'chance', 'param', 'priority', 'desc'], t)))
json.dump(moves, open(os.path.join(D, 'moves.json'), 'w'), ensure_ascii=False, indent=1)

I = [
 ('tampon', "Official Stamp", 'ball', 200, 10, "Stamps a weakened Euromon to register it."),
 ('super_tampon', "Super Stamp", 'ball', 600, 15, "Reinforced ink. More effective than a plain stamp."),
 ('tampon_qualifie', "Qualified Stamp", 'ball', 1200, 20, "Qualified majority: very good chance of capture."),
 ('tampon_unanime', "Unanimous Stamp", 'ball', 0, 255, "Unanimity! Guaranteed capture. Extremely rare."),
 ('cafe', "Canteen Coffee", 'heal', 200, 20, "Restores 20 HP. Lukewarm, but effective."),
 ('sandwich', "Club Sandwich", 'heal', 500, 50, "Restores 50 HP. The interns' favourite."),
 ('gaufre', "Brussels Waffle", 'heal', 900, 120, "Restores 120 HP. Icing sugar included."),
 ('kniddelen', 'Kniddelen', 'heal', 1500, 200, "A Luxembourg speciality. Restores 200 HP."),
 ('menu_complet', "Full Menu", 'heal', 2500, 999, "Starter, main, dessert: restores all HP."),
 ('avis_juridique', "Legal Opinion", 'status', 300, 0, "Cures all status problems."),
 ('reveil', "Alarm Clock", 'status', 150, 0, "Wakes a Euromon put to sleep by a summit."),
 ('motion_relance', "Revival Motion", 'revive', 1500, 50, "Brings a fainted Euromon back into the debate."),
 ('motion_unanime', "Unanimous Revival", 'revive', 0, 999, "Revives a fainted Euromon with all its HP."),
 ('pause_syndicale', "Union Break", 'pp', 1200, 0, "Restores all of a Euromon's PP."),
 ('x_argument', "Talking Points", 'battle', 500, 11, "In battle: raises Argument."),
 ('x_resilience', "Bulletproof Vest", 'battle', 500, 21, "In battle: raises Resilience."),
 ('x_expertise', "Expert Report", 'battle', 500, 31, "In battle: raises Expertise."),
 ('x_diplomatie', "Address Book", 'battle', 500, 41, "In battle: raises Diplomacy."),
 ('x_reactivite', "Double Espresso", 'battle', 500, 51, "In battle: raises Reactivity."),
 ('non_sollicitation', "Non-solicitation", 'repel', 400, 100, "Anti-canvassing clause: keeps Euromons away for 100 steps."),
 ('ratification', 'Ratification', 'evo', 2000, 0, "Makes certain Euromons evolve. Requires 27 signatures."),
 ('pierre_solaire', "Solar Panel", 'evo', 2000, 0, "Makes certain energy Euromons evolve."),
 ('cle_usb', "USB-C Key", 'evo', 2000, 0, "Makes certain digital Euromons evolve."),
 # key items
 ('eurodex', 'Eurodex', 'key', 0, 0, "Encyclopedia of Euromons, a gift from Jean Monnet."),
 ('badge_acces', "Access Badge", 'key', 0, 0, "Opens Parliament's doors. Colour: intern."),
 ('badge_olaf', "OLAF Badge", 'key', 0, 0, "Lets you see the ghost assistants."),
 ('passeport', "European Passport", 'key', 0, 0, "Burgundy, 32 pages, every border opens."),
 ('pass_interrail', "Interrail Pass", 'key', 0, 0, "Travel by train all over Europe."),
 ('repowereu_item', "REPowerEU Kit", 'key', 0, 0, "To turn the heating back on when the gas is cut off."),
 ('cognac', 'Cognac', 'key', 0, 0, "A precious bottle. Surtaxed since 2024…"),
 ('carte_cantine', "Canteen Card", 'key', 0, 0, "Credit: €3.40. Enough for a coffee."),
 ('directive_heure', "Clock Directive", 'key', 0, 0, "The directive ending the clock change (2019)."),
 ('malle_fer', "Iron Trunk", 'key', 0, 0, "A trunk from the Brussels–Strasbourg move."),
 ('etui_badges', "Badge Case", 'key', 0, 0, "Holds the treaty badges."),
 ('billet_specimen', "Specimen Note", 'key', 0, 0, "Your portrait, engraved at the ECB studio in Frankfurt. Not legal tender."),
]
items = [dict(zip(['id', 'name', 'kind', 'price', 'param', 'desc'], t)) for t in I]
json.dump(items, open(os.path.join(D, 'items.json'), 'w'), ensure_ascii=False, indent=1)
print('types', len(TYPES), 'moves', len(moves), 'items', len(items))
