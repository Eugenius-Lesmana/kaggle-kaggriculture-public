"""Part A only: reproducible ID-only teacher-strength tables. Run from repo root."""
import csv
import hashlib
from pathlib import Path
import duckdb

SOURCE = Path('manifests/replays.csv')
c = duckdb.connect()
c.execute("CREATE VIEW raw AS SELECT * FROM read_csv_auto('manifests/replays.csv')")
assert c.sql('SELECT count(*) FROM (SELECT episode FROM raw GROUP BY episode HAVING count(DISTINCT (created,sub_0,sub_1,team_0,team_1,reward_0,reward_1,rating_0,rating_1))>1)').fetchone()[0] == 0
c.execute('CREATE VIEW games AS SELECT DISTINCT * EXCLUDE(folder,bytes,sha256) FROM raw')
assert c.sql('SELECT count(*) FROM games').fetchone()[0] == c.sql('SELECT count(DISTINCT episode) FROM raw').fetchone()[0]
assert c.sql('SELECT count(*) FROM games WHERE reward_0 IS NULL OR reward_1 IS NULL OR rating_0 IS NULL OR rating_1 IS NULL').fetchone()[0] == 0
c.execute('''CREATE VIEW seats AS
 SELECT episode,created,0 seat,sub_0 sub,team_0 team,sub_1 opp_sub,team_1 opp_team,reward_0 bank,reward_1 opp_bank,rating_1 opp_rating FROM games
 UNION ALL SELECT episode,created,1,sub_1,team_1,sub_0,team_0,reward_1,reward_0,rating_0 FROM games''')
assert c.sql('SELECT count(*) FROM (SELECT sub FROM seats GROUP BY sub HAVING count(DISTINCT team)>1)').fetchone()[0] == 0
c.execute('''CREATE VIEW totals AS SELECT sub, min(team) team,count(*) games,
 sum((bank>opp_bank)::INT) wins,sum((bank=opp_bank)::INT) tie_games,
 avg((bank>opp_bank)::INT) win_rate,avg(bank-opp_bank) mean_margin,
 min(created) first_date,max(created) last_date,avg(opp_rating) mean_opponent_rating
 FROM seats GROUP BY sub''')

def query(sql):
    r=c.execute(sql);return [dict(zip([v[0] for v in r.description],row)) for row in r.fetchall()]

def table(rows,columns):
    def fmt(v):
        if isinstance(v,float):return f'{v:,.2f}'
        return str(v)
    return '\n'.join(['| '+' | '.join(columns)+' |','| '+' | '.join(['---']*len(columns))+' |']+['| '+' | '.join(fmt(r.get(k,'—')) for k in columns)+' |' for r in rows])

rows=query('SELECT * FROM totals WHERE games>=100 ORDER BY win_rate DESC,mean_margin DESC,sub')
assert sum(r['games'] for r in query('SELECT * FROM totals')) == 2*c.sql('SELECT count(*) FROM games').fetchone()[0]
for r in rows:r['win_percent']=100*r['win_rate']
# Explicit numerical panel: top eight raw win rates, plus top three with >=500 games.
broad=query('SELECT * FROM totals WHERE games>=500 ORDER BY win_rate DESC,mean_margin DESC,sub LIMIT 3')
panel=list(dict.fromkeys([r['sub'] for r in rows[:8]]+[r['sub'] for r in broad]))
ids=','.join(map(str,panel))
h2h=query(f'''SELECT sub,opp_sub,count(*) games,sum((bank>opp_bank)::INT) wins,
 sum((bank=opp_bank)::INT) tie_games,avg((bank>opp_bank)::INT)*100 win_percent,
 avg(bank-opp_bank) mean_margin FROM seats WHERE sub IN ({ids}) AND opp_sub IN ({ids}) GROUP BY sub,opp_sub''')
lookup={(r['sub'],r['opp_sub']):r for r in h2h}
for (a,b),r in lookup.items():
    reverse=lookup[(b,a)];assert r['games']==reverse['games'] and r['wins']+reverse['wins']+r['tie_games']==r['games']
matrix=[]
for a in panel:
    r={'submission':a}
    for b in panel:
        h=lookup.get((a,b));r[str(b)]=f"{h['win_percent']:.1f}% ({h['games']})" if h else '—'
    matrix.append(r)
refs='56701470,56711476'
reference=query(f'SELECT * FROM totals WHERE sub IN ({refs}) ORDER BY sub')
for r in reference:r['win_percent']=100*r['win_rate']
common=query(f'''WITH shared AS (SELECT opp_sub FROM seats WHERE sub IN ({refs}) GROUP BY opp_sub HAVING count(DISTINCT sub)=2)
 SELECT sub,opp_sub,count(*) games,avg((bank>opp_bank)::INT)*100 win_percent,avg(bank-opp_bank) mean_margin,avg(opp_rating) opponent_rating
 FROM seats WHERE sub IN ({refs}) AND opp_sub IN (SELECT opp_sub FROM shared) GROUP BY sub,opp_sub''')
# Equal opponent-submission weights; each common opponent counts once per reference submission.
matched=[]
for sub in (56701470,56711476):
    group=[r for r in common if r['sub']==sub]
    matched.append({'submission':sub,'common_opponents':len(group),'games':sum(r['games'] for r in group),
                    'equal_opponent_win_percent':sum(r['win_percent'] for r in group)/len(group),
                    'equal_opponent_mean_margin':sum(r['mean_margin'] for r in group)/len(group)})
byday=query(f'''SELECT sub,CAST(created AS DATE) date,count(*) games,avg((bank>opp_bank)::INT)*100 win_percent,
 avg(bank-opp_bank) mean_margin,avg(opp_rating) opponent_rating FROM seats WHERE sub IN ({refs}) GROUP BY sub,date ORDER BY date,sub''')
common_wide=[]
for opp in sorted({r['opp_sub'] for r in common}):
    group={r['sub']:r for r in common if r['opp_sub']==opp}
    if min(r['games'] for r in group.values())<10:continue
    row={'opponent_submission':opp}
    for sub,r in group.items():row[str(sub)]=f"{r['win_percent']:.1f}% / {r['mean_margin']:+,.1f} ({r['games']})"
    common_wide.append(row)
short=[]
for label,group in [('>=100 games',rows[:3]),('>=500 games',broad)]:
    for r in group:
        sub=r['sub']; margins=[x['mean_margin'] for x in h2h if x['sub']==sub and x['opp_sub']!=sub]
        short.append({'screen':label,'submission':sub,'team':r['team'],'games':r['games'],
                      'win_percent':100*r['win_rate'],'mean_margin':r['mean_margin'],'opponent_rating':r['mean_opponent_rating']})
raw_count=c.sql('SELECT count(*) FROM raw').fetchone()[0];unique=c.sql('SELECT count(*) FROM games').fetchone()[0]
text=f'''# Teacher strength: Part A numbers (2026-10-22)

Source: `manifests/replays.csv`, SHA256 `{hashlib.sha256(SOURCE.read_bytes()).hexdigest()}`.
{raw_count:,} listing rows, {unique:,} unique episodes; {raw_count-unique} repeated episodes collapsed after asserting identical dates, submission/team IDs, banks and ratings. Folder, compressed size and hash are download metadata. No missing banks or opponent ratings. Both seats count; tie_games are not wins. Margin is final bank minus opposing final bank, in coins. Dates retain the listing's supplied timezone (unspecified).

## 1. Every submission with at least 100 unique games

Sorted by win rate, then mean margin. Win percentages use all games, including tie_games. This is an observed downloaded corpus, not a balanced tournament or a strategy-consistency test.

{table(rows,['sub','team','games','wins','tie_games','win_percent','mean_margin','first_date','last_date','mean_opponent_rating'])}

## 2. Head-to-head

Panel = top eight win rates above, union top three win rates with >=500 games. Every entry is row win percentage (unique game count); dash means no recorded comparison, including the diagonal. Opposite directions reconcile wins, tie_games and counts. These cells use only direct games.

{table(matrix,['submission']+list(map(str,panel)))}

## 3. Team 16681125: submissions 56701470 and 56711476

{table(reference,['sub','team','games','wins','tie_games','win_percent','mean_margin','first_date','last_date','mean_opponent_rating'])}

Observed win rates and margins differ; these samples do not establish equivalent policies. Opponent mix and dates differ. Equal weighting of each shared opponent submission, without matching dates or seeds:

{table(matched,['submission','common_opponents','games','equal_opponent_win_percent','equal_opponent_mean_margin'])}

Shared opponents with >=10 games for each reference; cells are win percentage / mean margin (games). Complete common-opponent results are in the companion CSV.

{table(common_wide,['opponent_submission','56701470','56711476'])}

Daily results (no pooling across dates):

{table(byday,['sub','date','games','win_percent','mean_margin','opponent_rating'])}

## Numerical shortlist inputs only

Two explicit screens, each retaining its top three win rates; no teacher choice or strategic judgement. The >=500 threshold is a sample-size sensitivity check, not evidence of strategy consistency. Mean opponent rating is descriptive and does not adjust results for difficulty. No Part B behavioural profiling was performed.

{table(short,['screen','submission','team','games','win_percent','mean_margin','opponent_rating'])}

Reproduce: `python tools/teacher_strength.py`. Companion CSVs retain unrounded results. Checks cover episode uniqueness and matching duplicate payload fields, missing outcomes, submission/team mapping, seat totals, and head-to-head complementarity. No causal, policy-equivalence or strategy-consistency claim is made.
'''
Path('reports/2026-10-22-teacher-strength.md').write_text(text,encoding='utf8')
for name,data in [('TEACHER_STRENGTH',rows),('TEACHER_H2H',h2h),('TEACHER_REFERENCE_COMMON',common),('TEACHER_REFERENCE_DAILY',byday)]:
    with Path(f'reports/{name}.csv').open('w',newline='',encoding='utf8') as f:
        w=csv.DictWriter(f,fieldnames=list(data[0]));w.writeheader();w.writerows(data)
print(f'PASS: {unique} games, {len(rows)} submissions >=100, {len(panel)} panel members; report and four CSVs written')

