"""Replay-learned schedule_value replacement; no training dependency at runtime."""
import json
from pathlib import Path

OPS = ('WATER', 'FERTILIZE', 'HARVEST', 'COLLECT_FERTILIZER', 'FEED', 'CARE', 'PLANT', 'DIG')
CROPS = ('WHEAT', 'CARROT', 'TOMATO', 'STRAWBERRY', 'MELON')
ANIMALS = ('GOOSE', 'COW', 'SHEEP')
PRODUCT = {'GOOSE': 'EGG', 'COW': 'MILK', 'SHEEP': 'WOOL'}
MODEL = None


def due(tile, inventory, day):
    """Executable cell jobs used for replay evaluation; planner keeps its own eligibility."""
    if not isinstance(tile, dict):
        return []
    if tile.get('kind') == 'PLANT':
        jobs = []
        if not tile.get('watered_today'):
            jobs.append('WATER')
        if inventory.get('FERTILIZER', 0) and tile.get('fertilized_until_day', -1) < day:
            jobs.append('FERTILIZE')
        if tile.get('yield_units', 0) > 0:
            jobs.append('HARVEST')
        return jobs
    if tile.get('animal'):
        jobs = []
        if tile.get('fertilizer_available', 0):
            jobs.append('COLLECT_FERTILIZER')
        if not tile.get('fed_today') and inventory.get('WHEAT', 0):
            jobs.append('FEED')
        if tile.get('yield_units', 0) > 0:
            jobs.append('HARVEST')
        if not tile.get('cared_today'):
            jobs.append('CARE')
        return jobs
    return []


def features(obs, op, target, inventory, position):
    x, y = target
    tile = obs['farms'][obs['player']]['tiles'][y][x]
    tile = tile if isinstance(tile, dict) else {}
    crop, animal = tile.get('crop'), tile.get('animal')
    product = crop or PRODUCT.get(animal, '')
    price = obs['market']['prices'].get(product, 0)
    return [OPS.index(op) if op in OPS else len(OPS),
            1 if crop else 2 if animal else 0,
            CROPS.index(crop) + 1 if crop in CROPS else 0,
            ANIMALS.index(animal) + 1 if animal in ANIMALS else 0,
            obs['day'] - tile.get('planted_day', obs['day']) if crop else 0,
            obs['hour'], tile.get('yield_units', 0),
            int(bool(tile.get('watered_today'))), tile.get('consecutive_unwatered', 0),
            tile.get('fertilized_until_day', -1) - obs['day'],
            int(bool(tile.get('fed_today'))), tile.get('consecutive_unfed', 0),
            int(bool(tile.get('cared_today'))), tile.get('fertilizer_available', 0),
            inventory.get('WHEAT', 0), inventory.get('FERTILIZER', 0),
            sum(inventory.values()), price,
            abs(position[0] - x) + abs(position[1] - y), x, y]


def _tree_score(tree, row):
    node = 0
    while tree['feature'][node] >= 0:
        feature = tree['feature'][node]
        node = tree['left'][node] if row[feature] <= tree['threshold'][node] else tree['right'][node]
    return tree['value'][node]


def load_model(path=None):
    global MODEL
    if path is None and MODEL is not None:
        return MODEL
    source = Path(path) if path else Path(__file__).with_name('model.json')
    model = json.loads(source.read_text(encoding='utf-8'))
    if path is None:
        MODEL = model
    return model


def job_value(obs, jobs, model=None):
    """Same (obs, jobs) input as v0.10 schedule_value; returns a route benefit."""
    model = model or load_model()
    farm = obs['farms'][obs['player']]
    units = [farm['farmer']] + list(farm.get('hands') or [])
    inventories = obs['private']['inventories']
    total = 0.0
    for job in jobs:
        if job.operation not in OPS:
            continue
        indexes = ([job.owner] if job.owner is not None else
                   range(min(len(units), len(inventories))))
        scores = []
        for index in indexes:
            if index < 0 or index >= min(len(units), len(inventories)):
                continue
            row = features(obs, job.operation, job.target, inventories[index], units[index])
            tree = model['within'] if row[18] == 0 else model['next']
            scores.append(_tree_score(tree, row))
        if scores:
            total += max(scores) * model['scale']
    return total


schedule_value = job_value


def rank_cell_jobs(obs, jobs, unit_index, model=None):
    """Order the planner's available jobs on the hand's current cell."""
    model = model or load_model()
    farm = obs['farms'][obs['player']]
    positions = [farm['farmer']] + list(farm.get('hands') or [])
    inventory = obs['private']['inventories'][unit_index]
    return sorted(jobs, key=lambda job: -_tree_score(
        model['within'], features(obs, job.operation, job.target, inventory,
                                  positions[unit_index])))
