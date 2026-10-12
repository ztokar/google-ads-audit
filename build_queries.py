"""Prepare the skill's audit queries with explicit account-local dates."""
import argparse
import json
import re
from pathlib import Path
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

def build(out, timezone):
    out.mkdir(parents=True, exist_ok=True)
    now = datetime.now(ZoneInfo(timezone))
    end = now.date() - timedelta(days=1)
    start = end - timedelta(days=89)
    date = f"segments.date BETWEEN '{start}' AND '{end}'"
    text = (Path(__file__).parent / 'skills/google-ads-audit/references/queries.md').read_text(encoding='utf-8')
    jobs = []
    for block in re.split(r'\n## ', text)[1:]:
        key = block.split(' ', 1)[0]
        current = None
        n = 0
        for line in block.splitlines():
            if line.startswith('- resource:'):
                if current:
                    jobs.append(current)
                n += 1
                current = {'key': key if n == 1 else f'{key}_{n}', 'resource': re.findall(r'`([^`]+)`', line)[0]}
            elif current and line.startswith('- fields:'):
                current['fields'] = re.findall(r'`([^`]+)`', line)[0].split(', ')
            elif current and line.startswith('- conditions:'):
                current['conditions'] = [date if item == 'DATE' else item.replace('{RECENT_START_TIMESTAMP}', (now-timedelta(days=29)).strftime('%Y-%m-%d %H:%M:%S')).replace('{NOW_TIMESTAMP}',now.strftime('%Y-%m-%d %H:%M:%S')) for item in re.findall(r'`([^`]+)`',line)]
            elif current and line.startswith('- orderings:'):
                current['orderings'] = re.findall(r'`([^`]+)`',line)
            elif current and line.startswith('- limit:'):
                current['limit'] = int(re.findall(r'`([^`]+)`',line)[0])
        if current:
            jobs.append(current)
    q8 = next(x for x in jobs if x['key']=='Q8')
    jobs.append({**q8,'key':'Q8b','conditions':['metrics.conversions > 0',date],'limit':200})
    q2 = next(x for x in jobs if x['key']=='Q2')
    jobs.append({**q2,'key':'campaigns_30d','conditions':["campaign.status != 'REMOVED'",f"segments.date BETWEEN '{end-timedelta(days=29)}' AND '{end}'"]})
    jobs.extend([
        {'key':'goal_config','resource':'conversion_goal_campaign_config','fields':['campaign.id','conversion_goal_campaign_config.goal_config_level','conversion_goal_campaign_config.custom_conversion_goal']},
        {'key':'custom_goals','resource':'custom_conversion_goal','fields':['custom_conversion_goal.resource_name','custom_conversion_goal.name','custom_conversion_goal.status','custom_conversion_goal.conversion_actions']},
        {'key':'conversion_lag','resource':'customer','fields':['segments.conversion_lag_bucket','metrics.conversions','metrics.conversions_value'],'conditions':[date]},
    ])
    (out/'queries.json').write_text(json.dumps(jobs,indent=2), encoding='utf-8')
    (out/'period.json').write_text(json.dumps({'start':str(start),'end':str(end),'time_zone':timezone,'retrieved_at':now.isoformat(),'days':90},indent=2), encoding='utf-8')
    print(f'Period {start} to {end}; {len(jobs)} queries')

if __name__ == '__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--timezone',required=True)
    args=p.parse_args()
    build(args.output,args.timezone)
