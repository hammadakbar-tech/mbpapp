"""Narration + shot list. All numbers are pulled from the data at build time."""


def words(n):
    small = 'zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen ' \
            'seventeen eighteen nineteen'.split()
    tens = 'x x twenty thirty forty fifty sixty seventy eighty ninety'.split()
    if n < 20: return small[n]
    if n < 100: return tens[n // 10] + ('' if n % 10 == 0 else '-' + small[n % 10])
    if n < 1000:
        r = n % 100
        return small[n // 100] + ' hundred' + ('' if r == 0 else ' and ' + words(r))
    th, r = divmod(n, 1000)
    return words(th) + ' thousand' + ('' if r == 0 else (' and ' if r < 100 else ' ') + words(r))


def meters(v):
    v = int(round(v))
    return f"{words(v)} meter{'s' if v != 1 else ''}"


CAMS = {  # hand-tuned cameras for awkward shapes (lon, lat, span in degrees of longitude)
    'Russia': (95, 60, 130), 'United States of America': (-97, 40, 62), 'Canada': (-96, 60, 95),
    'Indonesia': (118, -2, 52), 'Maldives': (73.3, 3.5, 14), 'Kiribati': (-160, 0, 120), 'Tuvalu': (178, -8, 14),
    'Marshall Is.': (169, 9, 18), 'Netherlands': (5.3, 52.1, 9), 'Denmark': (10.5, 56, 11),
    'United Kingdom': (-3, 54.5, 17), 'Japan': (137, 37, 26), 'Australia': (134, -26, 52), 'Brazil': (-53, -12, 52),
    'India': (80, 22, 40), 'Pakistan': (69.5, 30, 22), 'China': (102, 35, 58), 'France': (2.5, 46.5, 15),
    'Germany': (10.4, 51, 13), 'Chile': (-71, -36, 50), 'Norway': (15, 65, 30), 'New Zealand': (173, -41, 24),
}

LINES = {
    'Maldives': ("Next, the Maldives. Most of this island nation sits barely a meter above the sea.",
                 'Average height: about a meter'),
    'Netherlands': ("The Netherlands. A quarter of the country already lies below sea level, protected by dikes. "
                    "Without them, half the country is underwater almost immediately.", 'A quarter is already below sea level'),
    'Bangladesh': ("Bangladesh is built on one of the biggest river deltas on Earth. With more than a hundred and seventy million people, "
                   "it's half underwater at just {m}.", 'A giant, flat river delta'),
    'Denmark': ("Denmark is famously flat. Its highest hill is only about one hundred and seventy meters tall. "
                "Half of Denmark is gone at {m}.", 'Highest hill: about 170 m'),
    'United Kingdom': ("The United Kingdom breaks into a chain of hilly islands. Half of Britain is underwater at {m}.",
                       'Britain becomes an archipelago'),
    'Russia': ("Russia, the largest country on Earth, loses half of its land at just {m}. "
               "The plains of western Russia and Siberia are remarkably flat.", 'The largest country, but very flat'),
    'France': ("France holds on to the Alps and the Massif Central, but the rest disappears at {m}.", 'The plains flood first'),
    'Germany': ("Germany's northern plain vanishes, and the country is half underwater at {m}.", 'The North German Plain is gone'),
    'Japan': ("Japan is a land of mountains, but most of its cities sit on narrow coastal plains. Half of Japan sinks at {m}.",
              'Mountains, but crowded coasts'),
    'Australia': ("Australia is the flattest inhabited continent on Earth. It sinks at {m}.", 'The flattest inhabited continent'),
    'Brazil': ("The Amazon basin becomes an inland sea, and Brazil goes under at {m}.", 'The Amazon becomes a sea'),
    'India': ("In India, the Ganges plain fills with water, and half the country is gone at {m}.", 'The Ganges plain floods'),
    'Canada': ("Canada, the second-largest country, survives on the Rockies and the Canadian Shield until {m}.",
               'Second-largest country on Earth'),
    'Italy': ("Italy shrinks to the Alps and the spine of the Apennines. It sinks at {m}.", 'Down to the mountains'),
    'United States of America': ("The United States splits apart. The Appalachians become islands in the east, "
                                 "and the Rockies hold the west. Half the country is underwater at {m}.",
                                 'East and west drift apart'),
    'Pakistan': ("Pakistan. The Indus valley floods all the way to the mountains, but the north holds out, "
                 "home to K2, the second-highest mountain on Earth. Half of Pakistan is underwater at {m}.",
                 'Home of K2'),
    'Saudi Arabia': ("Saudi Arabia keeps its western mountains for a long time, but the desert interior sinks at {m}.",
                     'The western highlands hold on'),
    'Spain': ("Spain is protected by the Meseta, a huge high plateau at its center. It finally sinks at {m}.",
              'The high central plateau'),
    'Mexico': ("Mexico's high central plateau keeps it alive past a thousand meters. It sinks at {m}.", 'Above 1,000 m!'),
    'South Africa': ("South Africa's high interior plateau holds until {m}.", 'The Highveld holds on'),
    'Turkey': ("Turkey's Anatolian plateau finally slips under at {m}.", 'The Anatolian plateau'),
    'Switzerland': ("Switzerland, the land of the Alps, sinks at {m}.", 'Land of the Alps'),
    'Ethiopia': ("Ethiopia's highlands, the roof of Africa, go under at {m}.", 'The roof of Africa'),
    'China': ("China's eastern plains vanished long ago, but the Tibetan Plateau, the highest plateau on Earth, "
              "keeps China in the game until {m}.", 'Kept alive by Tibet'),
    'Iran': ("Iran's high plateau gives up at {m}.", 'A country on a plateau'),
    'Mongolia': ("Mongolia, a country of high, windy steppe, sinks at {m}.", 'High steppe country'),
    'Nepal': ("Nepal is home to Mount Everest, but its southern lowlands pull it under at {m}.", 'Home of Everest'),
    'Afghanistan': ("Afghanistan, ringed by the Hindu Kush, goes under at {m}.", 'The Hindu Kush'),
    'Rwanda': ("Rwanda, a tiny country of high, green hills, sinks at {m}.", 'High hills in the heart of Africa'),
    'Armenia': ("Armenia, high in the Caucasus, holds on until {m}.", 'High in the Caucasus'),
    'Andorra': ("Tiny Andorra, tucked high in the Pyrenees, sinks at {m}.", 'High in the Pyrenees'),
    'Lesotho': ("Lesotho is the only country on Earth that lies entirely above one thousand meters. "
                "Even so, half of it is gone at {m}.", 'Entirely above 1,000 m'),
    'Kyrgyzstan': ("Kyrgyzstan, among the towering Tian Shan mountains, sinks at {m}.", 'The Tian Shan'),
}


def build_script(S, BYNAME, ORDER, N):
    B = []
    h = lambda n: BYNAME[n]['half']
    def gone_at(L): return sum(1 for s in ORDER if s['half'] <= L)
    def add(**k): B.append(k)

    add(kind='title', say="What if the ocean just kept rising? Not by one meter, or two, but on and on, "
                          "until only one country was left above the waves?", music=0.25, min=7.5)
    add(say=f"Here are the rules. We start with {words(N)} countries. A country sinks when half of its land is underwater. "
            "The heights come from real NOAA elevation data, and water can only flood land it can reach from the sea.",
        cap='A country sinks when half of its land is underwater.', music=0.3)

    feats = [n for n in LINES if n in BYNAME]
    feats.sort(key=lambda n: h(n))
    acts = [(70, 'ACT 1', 'RISING TIDES', 'This much ice really exists', '0 m → 70 m', 0.45,
             "Act one. Rising tides. If every glacier and ice sheet on Earth melted, the sea would rise around seventy meters. "
             "So everything in this act could actually happen."),
            (300, 'ACT 2', 'THE GREAT FLOOD', 'Now we go far beyond reality', '70 m → 300 m', 0.6,
             "Act two. The great flood. From here on, there isn't enough water on Earth to do this. But let's keep going."),
            (1000, 'ACT 3', 'LOST CONTINENTS', 'The continents break apart', '300 m → 1,000 m', 0.75,
             "Act three. Lost continents. The great plains are gone, and the continents start breaking into islands."),
            (1e9, 'ACT 4', 'THE LAST PEAKS', 'Only the mountains remain', '1,000 m and up', 0.9,
             "Act four. The last peaks. Only the highest countries on Earth are still in the game.")]
    act_i = -1
    L = 0.0

    def start_act(k):
        lo = 0 if k == 0 else acts[k - 1][0]
        _, no, name, sub, rng, mus, say = acts[k]
        add(kind='act', act_no=no, act=name, act_sub=sub, act_range=rng, say=say, music=mus, min=6)

    # early islands group (first few meters)
    early = [s for s in ORDER if s['half'] <= 3 and s['name'] not in LINES][:6]
    for n in feats:
        lv = h(n)
        while act_i + 1 < len(acts) and (act_i < 0 or lv > acts[act_i][0]):
            act_i += 1
            # finish the previous act's rise to its ceiling before the next title card
            if act_i > 0:
                top = acts[act_i - 1][0]
                if L < top:
                    add(level=top, say=f"{meters(top).capitalize()}. {words(gone_at(top)).capitalize()} countries are already gone.",
                        cap=f'+{top:,} m: {gone_at(top)} countries gone', music=acts[act_i - 1][5], riser=True)
                    L = top
            start_act(act_i)
            if act_i == 0 and early:
                pass
        mus = acts[act_i][5]
        say, card = LINES[n]
        say = say.format(m=meters(lv))
        add(kind='feature', feature=n, level=lv, cam=CAMS.get(n, n), say=say, card=card, music=mus,
            rise=(0.05, 0.72), min=6.0)
        L = lv
        if n == 'Maldives' and early:
            names = [s['disp'] for s in early if s['name'] != 'Maldives'][:4]
            top = max(s['half'] for s in early) + 1
            add(level=top, say="Within the first few meters, " + ', '.join(names[:-1]) + ' and ' + names[-1] +
                " are gone too. These are some of the lowest nations on the planet.",
                cap='The low island nations go first', music=mus)
            L = top
    # final showdown
    last2 = ORDER[-2:]
    a, b = last2
    add(level=max(L, a['half'] * 0.97), cam=(80, 36, 40), labels=[a['name'], b['name']],
        say=f"And then there were two. {a['disp']} and {b['disp']}, both deep in the highest mountains on Earth.",
        cap=f"The final two: {a['disp']} vs {b['disp']}", music=0.95, riser=True)
    add(kind='feature', feature=a['name'], level=a['half'], cam=a['name'],
        say=f"{a['disp']} finally sinks at {meters(a['half'])}.", card='So close...', music=0.95, rise=(0.05, 0.6), min=5.5)
    add(kind='feature', feature=b['name'], level=a['half'] + 15, cam=b['name'], stamp='safe',
        say=f"Which means the last country standing is {b['disp']}. Half of its land stays dry until the ocean reaches "
            f"{meters(b['half'])}.", card='The last country standing', music=1.0, min=7.5)
    BYNAME[b['name']]['survivor'] = True
    # board
    groups = []
    bounds = [(0, 70, 'RISING TIDES', '0–70 m'), (70, 300, 'THE GREAT FLOOD', '70–300 m'),
              (300, 1000, 'LOST CONTINENTS', '300–1,000 m'), (1000, 1e9, 'THE LAST PEAKS', '1,000 m +')]
    for lo, hi, nm, rg in bounds:
        mem = [s for s in ORDER if lo < s['half'] <= hi or (lo == 0 and s['half'] <= 0)]
        groups.append((nm, rg, mem))
    add(kind='board', groups=groups, level=a['half'] + 15,
        say=f"So, when did your country sink? Tell us in the comments. And if you think {b['disp']} deserved to win, "
            "you know what to do.", music=0.6, min=13)
    return B
