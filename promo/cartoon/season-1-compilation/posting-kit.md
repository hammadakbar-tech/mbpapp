# Australia vs the World: Season 1 (long-form compilation)

**File:** `australia-vs-the-world-season-1.mp4` (1920×1080 16:9, **26:00**, ~282 MB)
**Thumbnail:** `thumbnail.png` (1280×720)

All 11 Australia episodes plus a bonus, in one long-form video for the **4,000 watch-hours** YouTube Partner Program route. Shorts views don't count towards watch hours, but this does. Each 9:16 episode plays full height in the centre over a blurred copy of itself:
- **left panel:** the episode number, the matchup and a subscribe call;
- **right panel:** a live season leaderboard that fills in after each episode (W/L/T so far, ▶ NOW, "?" for upcoming);
- **between episodes:** a 3.6 s "NEXT UP" card that stamps the previous result;
- **intro (10 s cold open):** a rapid montage of 8 real episode moments with zoom punches and slams, then "DID AUSTRALIA BEAT THE WORLD?" with WINS ? / LOSSES ? / TIES ? (the record stays hidden until the end), then "ALL 12 EPISODES · LET'S GO!";
- **outro:** the final record (**3 wins, 2 losses, 6 ties**), "which rematch first?", and the subscribe button.

## Upload settings (YouTube)

- **Upload as a normal video, not a Short.** It's 16:9 and 26 minutes, so it goes to the long-form shelf automatically.
- **Thumbnail:** `thumbnail.png`
- **Audience:** Not made for kids. Countryballs is general audience, but marking it "for kids" disables comments and personalised ads.
- **Chapters:** paste the timestamps below into the description. The first one must be 0:00.
- **End screen:** in the last 20 s (from the final chapter), add "Subscribe" plus "Best for viewer" or a playlist of the Shorts.
- **Playlist:** put the original Shorts into an "Australia vs the World" playlist and link it.
- **Then point people here:**
  - set this as the **Related video** on every Australia Short (Shorts editor → Related video);
  - add to each Short's pinned comment: "Full Season 1 (26 min) on the channel 👆".

## Title (pick one)

1. Australia vs The World: Full Season 1 (Countryballs, All 12 Episodes)
2. Australia vs Every Country: Who Won? (Countryballs Full Season)
3. I Made Australia Fight 11 Countries… Here's the Final Record (Countryballs)

## Description

Australia took on the world: the USA, Japan, France, the UK, Canada, Greece (twice), Russia + India, the Philippines, the entire cricket world, and a 3-way food fight. All 12 countryballs episodes in one place, with a live season leaderboard. Who should Australia face first in Season 2? Comment below and subscribe 🔔

0:00 Intro: Australia vs the World
0:11 Ep 1: Australia vs USA
2:23 Ep 2: Australia vs Japan
4:54 Ep 3: Australia vs France
7:22 Ep 4: Australia vs The UK
9:34 Ep 5: Australia vs Canada
11:44 Ep 6: Australia vs Greece
13:56 Ep 7: Australia vs Greece II
15:17 Ep 8: Australia + Canada vs Russia + India
17:29 Ep 9: Australia vs Philippines
19:32 Ep 10: Australia vs Cricket World
21:34 Ep 11: Australia vs USA + Philippines
23:37 Bonus: Philippines vs Indonesia (Australia refs)
25:40 Final record & Season 2

#countryballs #australia #geography #polandball #countries

## Tags

```
countryballs, australia vs the world, countryballs full season, countryballs compilation, australia countryball, australia vs usa, australia vs japan, australia vs france, australia vs uk, australia vs canada, australia vs greece, australia vs philippines, cricket war, country comparison, geography facts, polandball, geography war
```

## Pinned comment

Final record: 3 wins, 2 losses, 6 TIES 🤯 You get to settle the ties. Which rematch should open Season 2? 👇

## Notes

- Watch-hours maths: 4,000 h = 240,000 minutes. At around 10 minutes average view duration, that's about 24,000 views.
- Reusing your own Shorts in a compilation is fine for monetisation: it's your original content, edited into a new format with new intro, outro, cards and leaderboard.
- **Repo copy:** GitHub rejects files over 100 MB, so the video is stored in 3 parts in `promo/cartoon/season-1-compilation/video-parts/`. Join them with `cat australia-vs-the-world-season-1.mp4.part* > australia-vs-the-world-season-1.mp4`.
- Rebuild: `python3 season.py <promo/cartoon dir> <data_dir> <out_dir>` (about 15 minutes), then `python3 season_intro.py` with the same arguments to swap in the fast cold-open intro, then re-run the concat.
