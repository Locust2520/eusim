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
t('stagiaire_hugo', 'Hugo', "Intern", [['amendon', 4], ['pigeonix', 5]],
  "Hey, newbie! Here, we settle everything with a debate. Show me what you've got!",
  "Argh… I should have reread my briefing notes.", "Ha! Back to the photocopier!", 'stagiaire', money=15, ai=0)
for st, (rv, pl) in {'v': ('charbonnet', 'verdeal'), 'c': ('atomino', 'charbonnet'), 'a': ('verdeal', 'atomino')}.items():
    t(f'oliver1_{st}', 'Oliver', 'Rival', [[rv, 5]],
      "So, {P}, shall we test our Euromons? Mine is obviously better.", "What?! That was a lucky shot!",
      "Easy. As expected.", 'oliver', 'oliver', 30, 1, 'rival')
    t(f'oliver2_{st}', 'Oliver', 'Rival', [['pigeonix', 8], ['erasmouse', 8], [rv, 10]],
      "{P}! You already have a badge? Never mind, I'll make you regret it.", "Not again… Fine, you'll see in Frankfurt.",
      "Ha! Luxembourg suits me.", 'oliver', 'oliver', 40, 1, 'rival')
    evo1 = {'charbonnet': 'hautfourno', 'atomino': 'euratome', 'verdeal': 'fit55'}[rv]
    t(f'oliver3_{st}', 'Oliver', 'Rival', [['pigeonix', 16], ['erasmouse', 17], ['eurolo', 16], [evo1, 19]],
      "I've just visited the ECB. I understood everything about monetary policy. Almost everything.",
      "Bloody hell… You're really improving fast, {P}.", "As they say in the City: time is money.", 'oliver', 'oliver', 60, 1, 'rival')
    evo2 = {'charbonnet': 'hautfourno', 'atomino': 'euratome', 'verdeal': 'fit55'}[rv]
    t(f'oliver4_{st}', 'Oliver', 'Rival', [['pigeonix', 30], ['erasmusplus', 31], ['eurozone', 31], ['brexitt', 32], [evo2, 34]],
      "{P}… this is our last debate. After this, I'm going back to London. For good. Come on, one last time!",
      "Good game, {P}. At least I'm leaving in style.", "I'm leaving on a win. That's something.", 'oliver', 'oliver', 80, 2, 'rival')
    final = {'charbonnet': 'cecagon', 'atomino': 'fissionix', 'verdeal': 'neutralis'}[rv]
    t(f'oliver5_{st}', 'Oliver', 'Rival', [['brexitt', 62], ['erasmusplus', 62], ['eurozone', 63], ['roamfree', 63], ['iact', 64], [final, 66]],
      "{P}! I'm back. Well… I'm asking to come back. Rejoin? But first, a debate for honour!",
      "Right. I'm filling in the membership application. It's 35 chapters long…", "Ha! Turns out leaving makes you stronger. Or not.", 'oliver', 'oliver', 120, 2, 'rival')
t('r1_stagiaire', 'Léa', "Intern", [['erasmouse', 5], ['amendon', 6]], "I'm an intern too! Unpaid, like you. Let's debate, it's comforting.",
  "Well… back to the photocopies.", "", 'stagiaire_f', money=20, ai=0)
t('r1_fonctionnaire', "Mr Dupont", "Civil servant", [['paperasse_mon', 6], ['paperasse_mon', 6], ['comitologue', 7]],
  "Halt! Has your A-38 hiking form been stamped?", "Fine, I'll stamp it. But in triplicate.", "", 'fonctionnaire', money=30)
t('r1_agriculteur', 'Gérard', "Farmer", [['agrikolo', 7], ['courbana', 7]],
  "The CAP is my life! And my tractor is my family. Come on, let's debate!", "I'll have to raise this with the union…", "", 'agriculteur', money=30)
t('lux_banquier', 'Pierre-Henri', "Private banker", [['eurolo', 9], ['valisette', 10]],
  "Welcome to Luxembourg. Absolute discretion. This debate never happened.", "This debate definitely never happened.", "", 'banquier', money=60)
t('lux_fiscaliste', "Counsel Klein", "Tax adviser", [['valisette', 10], ['paperasse_mon', 10], ['eurolo', 11]],
  "A tax ruling? I'll draft you one in five minutes. But first, a debate.", "My arrangements… collapsed!", "", 'avocat', money=60)
t('juncker', 'Jean-Claude Juncker', "Arena champion", [['eurolo', 12], ['inflaton', 12], ['spreadon', 14]],
  "Ah, a young intern! Come, come, let me pat your cheek. Then we'll debate, like in the good old Eurogroup days.",
  "Bravo! You deserve the Tax Ruling Badge. And that's not confidential!", "Come on, don't make that face, I'm joking… half joking.",
  'juncker', 'juncker', 100, 2, 'gym_leader')
t('r2_touriste', 'Kevin', "Tourist", [['roamy', 11], ['pigeonix', 11]], "I'm cycling the Moselle! And debating in roaming, for free!",
  "Even without roaming charges, I've lost everything.", "", 'touriste', money=40)
t('r2_banquier', 'Hans', "Analyst", [['inflaton', 12], ['eurolo', 12]], "The markets are pricing in my victory at 87%.",
  "The markets were wrong. As usual.", "", 'banquier', money=60)
t('r2_vigneron', 'Jean-Marc', "Winegrower", [['agrikolo', 12], ['fromajus', 12], ['courbana', 13]],
  "My crémant is PDO. So are my Euromons. Almost.", "Well, I'll buy you a drink anyway.", "", 'agriculteur', money=50)
t('bce_trader', 'Karl', 'Trader', [['cryptou', 15], ['eurolo', 16]], "Buy low, sell high, debate hard!", "Crash! I'm overdrawn!", "", 'banquier', money=80)
t('bce_economiste', "Dr Sofia", "Economist", [['inflaton', 16], ['spreadon', 16]],
  "According to my model, you lose. My model is never wrong. Except in 2008.", "I'll have to revise my forecasts.", "", 'fonctionnaire_f', money=80)
t('lagarde', 'Christine Lagarde', "Arena title-holder", [['cryptou', 17], ['inflaton', 18], ['eurozone', 20]],
  "Welcome to the European Central Bank. Here, I set the rates… and the pace of the debate. My attacks depend on today's key rate!",
  "Wonderful. You deserve the Euro Badge. And don't worry: I'm not here to close your spread.",
  "Price stability is also the stability of victories.", 'lagarde', 'lagarde', 110, 2, 'gym_leader')
t('r3_militant', 'Inès', "Climate activist", [['eolion', 16], ['solario', 17]], "Every debate lost is one more degree! Come on!",
  "Well, at least it was carbon-neutral.", "", 'militant', money=40)
t('r3_journaliste', 'Tom', "Journalist", [['fakeon', 17], ['pigeonix', 17]], "An exclusive! “Intern loses miserably”!",
  "I'm changing the headline: “Intern wins miserably well”.", "", 'journaliste', money=50)
t('r3_viticulteur', 'Albert', "Winemaker", [['fromajus', 18], ['agrikolo', 18], ['tracteuron', 19]],
  "Is the Rhine the border? No, it's wine on both sides! We'll drink a toast after the debate.", "Cheers anyway!", "", 'agriculteur', money=50)
t('stras_depute1', "MEP Muller", "Member of Parliament", [['amendon', 21], ['amendomax', 22]], "I tabled 2,000 amendments this morning. The first one is about you.",
  "My amendments were rejected en bloc…", "", 'depute', money=80)
t('stras_depute2', "MEP Rossi", "MEP", [['interpreton', 22], ['transhumon', 22]],
  "The session is in Strasbourg, our trunks have arrived, let's debate!", "I'm going back to Brussels. With my trunks.", "", 'deputee', money=80)
t('metsola', 'Roberta Metsola', "Arena title-holder", [['amendomax', 23], ['interpreton', 23], ['spitzen', 25]],
  "Silence in the hemicycle! The sitting is open. I give the floor to… you. Then I take it back.",
  "Adopted! The Hemicycle Badge is awarded to you by an absolute majority.", "The sitting is closed. Come back for the next session.",
  'metsola', 'metsola', 120, 2, 'gym_leader')
t('ath_economiste', 'Nikos', "Economist", [['inflaton', 26], ['referendo', 27]], "Debt is like moussaka: hard to digest.",
  "OXI to this defeat!", "", 'journaliste', money=80)
t('troika_bce', "Troika agent (ECB)", "Troika", [['austerix', 27], ['eurozone', 27]], "Account inspection! Your Euromons spend too much.",
  "Inspection report: unfavourable.", "", 'banquier', money=90)
t('troika_fmi', "Troika agent (IMF)", "Troika", [['spreadon', 27], ['hyperflaton', 28]], "The International Monetary Fund recommends… your defeat.",
  "Revision of our forecasts: downwards.", "", 'fonctionnaire', money=90)
t('varoufakis', 'Yanis Varoufakis', "Arena champion", [['erasmusplus', 28], ['manneken', 29], ['contractuel', 31]],
  "I came by motorbike, no tie. Like in 2015 against the Eurogroup. We debate, and then we vote: OXI or NAI?",
  "OXI… sorry, NAI: you win. Take the OXI Badge, comrade.", "The people have spoken. And the people is me.",
  'varoufakis', 'varoufakis', 130, 2, 'gym_leader')
t('lon_tabloid', "Editor-in-chief", "Tabloid", [['fakeon', 31], ['pigeonix', 31], ['trollbot', 32]],
  "FRONT PAGE: “Brussels wants to ban bent bananas”! It's false? Who cares, it sells.",
  "Tomorrow's front page: “Historic defeat”.", "", 'journaliste', money=90)
t('lon_johnson', 'Boris Johnson', "Former Prime Minister", [['pigeonix', 32], ['fakeon', 33], ['referendo', 34]],
  "Hello! I was a Brussels correspondent, you know. I wrote things… more or less true. Get debate done!",
  "Crikey. Well, I had another article about straight cucumbers anyway.", "", 'johnson', 'johnson', 120, 2)
t('farage', 'Nigel Farage', "Arena champion", [['tribun', 34], ['vetoadmax', 34], ['brexitt', 36]],
  "You're not laughing now, are you? Welcome to the pub. A debate, a pint, and Article 50.",
  "Right. Take the Article 50 Badge. We don't need it any more.", "Take back control! Of the debate, at least.",
  'farage', 'farage', 140, 2, 'gym_leader')
t('bud_douanier', 'Gábor', "Border guard", [['frontierex', 36], ['vetoad', 36]], "Check! Does your Euromon have a visa?",
  "Go through. But I'm writing it down.", "", 'douanier', money=90)
t('bud_conseiller', "Special adviser", "Adviser", [['austerix', 37], ['demagogor', 37]],
  "The Prime Minister receives no one. Except those who beat me. And that never happens.", "It just happened.", "", 'depute', money=90)
t('orban', 'Viktor Orbán', "Arena champion", [['vetoadmax', 38], ['frontierex', 38], ['austerix', 39], ['demagogor', 40]],
  "You want my agreement? Unanimity is required. And I never agree. Careful: I can use my VETO every turn.",
  "Fine… I'm stepping out for a coffee. Meanwhile, take this Veto Badge. Officially, I abstained.",
  "Veto! Veto! And veto again!", 'orban', 'orban', 150, 3, 'gym_leader')
t('lobby_sbire1', "Oil lobbyist", 'Team Lobby', [['lobbyron', 36], ['diesgate', 37]], "You don't have your access badge? Good, neither do we.",
  "I'll have to declare this meeting in the transparency register…", "", 'lobbyiste', money=100)
t('lobby_sbire2', "Tech lobbyist", 'Team Lobby', [['botfarm', 37], ['trollbot', 36], ['algoritmo', 37]],
  "Our algorithm predicted your defeat. Accept cookies?", "Error 403: defeat.", "", 'lobbyiste_f', money=100)
t('lobby_sbire3', 'Lobbyiste « de l\'étranger »', 'Team Lobby', [['valisette', 38], ['sacabillet', 38]],
  "A little suitcase for your vote? No? Then a debate.", "I never gave anything to anyone. Write that down.", "", 'lobbyiste', money=120)
t('lobbychef', "The Chief Lobbyist", "Team Lobby boss", [['sacabillet', 40], ['botfarm', 40], ['diesgate', 41], ['glyphosaure', 41], ['lobbyzilla', 43]],
  "Welcome to the heart of power, intern. Here, we don't write laws: we “suggest” them. And you're going to sign my suggestion.",
  "Impossible… A mere unpaid intern… has defeated the lobby. I'm retiring. To the private sector. Oh, I'm already there.",
  "Thank you for this contribution to our public consultation.", 'lobbychef', None, 200, 3, 'boss')
t('avocat_tech1', "Big Tech lawyer", "Lawyer", [['consentor', 40], ['iact', 40]], "My client contests the €4.34 billion fine. And this debate.",
  "We will appeal.", "", 'avocat', money=120)
t('avocat_tech2', "Competition lawyer", "Legal expert", [['archivor', 41], ['appellatio', 41]], "Abuse of a dominant position? Me? I'm merely dominant.",
  "Fine accepted…", "", 'avocat', money=120)
t('vestager', 'Margrethe Vestager', "Arena title-holder", [['consentor', 42], ['iact', 42], ['appellatio', 43], ['ratifix', 44]],
  "Google, Apple… I've imposed billions in fines. Does your team respect competition rules? Let's check.",
  "No abuse of a dominant position detected. The Fine Badge is yours.", "Fined! 4% of your turnover.",
  'vestager', 'vestager', 160, 3, 'gym_leader')
for i, (fl, party) in enumerate({'1a': [['assistome', 38]], '1b': [['assistome', 38], ['pailleplast', 38]],
                                 '2a': [['changheure', 39], ['assistome', 39]], '2b': [['manneken', 40], ['assistome', 40]],
                                 '3a': [['emploifictif', 41]], '3b': [['pailleplast', 41], ['emploifictif', 41]]}.items()):
    t(f'fantome_{fl}', "Ghost assistant", "Ghost", party, "Boo… I've worked here… since 2009… well, on paper…",
      "I'm going back… to my fictitious… contract…", "", 'fantome', money=60)
t('fantome_boss', "The Empty Contract", "Spirit of fake jobs", [['changheure', 43], ['sacabillet', 43], ['emploifictif', 45]],
  "I AM… THE SUM OF EVERY CONTRACT THAT NEVER HAD AN OFFICE…", "My… payslips… are fading…", "", 'fantome', None, 150, 3, 'boss')
t('par_enarque', "ENA graduate", "Senior civil servant", [['titularis', 44], ['comitologue', 44]], "I went to the ENA. Well, the INSP. Anyway, I know everything.",
  "I'll write a memo about this failure.", "", 'fonctionnaire_f', money=140)
t('par_ministre', "Junior minister", "Minister", [['spitzen', 44], ['schumark', 45]], "I've been a minister since… this morning. Let's debate before the next reshuffle.",
  "Reshuffled!", "", 'depute', money=140)
t('macron', 'Emmanuel Macron', "Arena champion", [['erasmusplus', 45], ['spitzen', 46], ['eurozone', 46], ['schumark', 47], ['nobelix', 48]],
  "Welcome to the Sorbonne! Here, I spoke about a sovereign Europe in 2017… and in 2024. I'll talk to you for two hours. And at the same time, debate.",
  "Wonderful! You embody strategic autonomy. Take the Sorbonne Badge… and at the same time, my congratulations.",
  "I dissolve… your team!", 'macron', 'macron', 180, 3, 'gym_leader')
# Council (Elite 4) + champion
t('merkel', 'Angela Merkel', "European Council", [['austerix', 50], ['titularis', 50], ['offshorion', 51], ['cecagon', 51], ['ratifix', 52]],
  "Wir schaffen das. Together, we'll get there. But first, you have to beat me. Take your time: I have sixteen years of experience.",
  "You did it. Wir haben es geschafft.", "", 'merkel', 'merkel', 220, 3, 'council')
t('draghi', 'Mario Draghi', "European Council", [['eurozone', 51], ['hyperflaton', 51], ['mica', 52], ['troikat', 52], ['draghizord', 54]],
  "I'll do whatever it takes to win this debate. Whatever it takes. And believe me: it will be enough.",
  "My report recommended 800 billion of investment a year. Invest it in your team.", "", 'draghi', 'draghi', 220, 3, 'council')
t('kallas', 'Kaja Kallas', "European Council", [['schengeon', 52], ['lisbonia' if False else 'trilogon', 52], ['pandiplo', 53], ['roamfree', 53], ['nobelix', 54]],
  "High Representative for Foreign Affairs. My diplomacy is firm. So is my Baltic shield.",
  "A clear victory. Europe will need people like you facing the rest of the world.", "", 'kallas', 'kallas', 220, 3, 'council')
t('costa', 'António Costa', "President of the European Council", [['interpreton', 53], ['transhumax', 53], ['mercosaur', 54], ['trilogon', 54], ['schumark', 55], ['ratifix', 55]],
  "It's 11:59 p.m. My goal: finish this summit before midnight. For the first time in history!",
  "It's… 4:37 in the morning. As usual. Well done, you may go up to the Berlaymont.", "", 'costa', 'costa', 230, 3, 'council')
t('vdl', 'Ursula von der Leyen', "President of the Commission", [['neutralis', 56], ['eurozone', 56], ['iact', 57], ['lobbyzilla', 57], ['schumark', 57], ['emploifictif', 58]],
  "Welcome to the thirteenth floor of the Berlaymont. I live here, you know: I have a bedroom next to my office. So, let's see whether you deserve the directive.",
  "Team Europe… You're the best intern the Commission has ever had. The clock directive is yours!",
  "I'll send you a text. Or maybe not.", 'vdl', 'vdl', 300, 3, 'champion')
# Powers (chapter 11)
t('vance_t', 'JD Vance', "Vice-President", [['fakeon', 55], ['tarifaux', 56], ['demagogor', 57]],
  "I came to Munich to explain democracy to you. Now I've come to Antwerp to explain debating.",
  "Right. I'm going back to writing a speech.", "", 'vance', 'vance', 200, 3, 'powers')
t('trump', 'Donald Trump', "US President", [['tarifaux', 58], ['fakeon', 59], ['brexitt', 59], ['lobbyzilla', 60], ['demagogor', 60], ['tarifator', 62]],
  "TREMENDOUS! The most beautiful debate of all time, everybody says so. I'm putting 200% tariffs on your Euromons. Maybe 15. We'll see.",
  "IT WAS RIGGED! Fine… let's make a deal. 15%. That's my final word. For today.",
  "I won! As always! Nobody wins better than me.", 'trump', 'trump', 300, 3, 'powers')
t('putin', "Vladimir Putin", "Russian President", [['gazoduc', 59], ['frontierex', 59], ['botfarm', 60], ['vetoadmax', 60], ['austerix', 61], ['censourson', 62]],
  "Sit down. No, further away. Even further. There. At six metres, the conversation is more… strategic. Your attacks will take a turn to arrive.",
  "The gas… has been cut off… on my side. Interesting.", "Winter is coming. For you.", 'putin', 'putin', 300, 3, 'powers')
t('xi', 'Xi Jinping', "Chinese President", [['pandiplo', 59], ['terrara', 60], ['iact', 60], ['hyperflaton', 60], ['diesgate', 61], ['trilogon', 62]],
  "Welcome. We are partners. And competitors. And systemic rivals. It depends on the turn.",
  "Hmm. A partner to be respected. I'm lifting the controls on rare earths… for now.", "Content unavailable in your region.",
  'xi', 'xi', 300, 3, 'powers')
t('trump_final', 'Donald Trump', "G-Everything Summit", [['tarifator', 63], ['lobbyzilla', 63], ['demagogor', 64]],
  "ME FIRST. The summit was my idea. Well, I think so.", "Sad!", "", 'trump', 'trump', 200, 3, 'final')
t('putin_final', "Vladimir Putin", "G-Everything Summit", [['gazoduc', 63], ['vetoadmax', 64], ['censourson', 64]],
  "I preferred the long table.", "…", "", 'putin', 'putin', 200, 3, 'final')
t('xi_final', 'Xi Jinping', "G-Everything Summit", [['terrara', 64], ['pandiplo', 64], ['trilogon', 65]],
  "The last word will be… systemic.", "We will talk again in fifty years.", "", 'xi', 'xi', 200, 3, 'final')

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
