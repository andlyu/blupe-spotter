"""Model-facing repair schema and a provenance-checked, non-executed example."""
import hashlib
import json

from . import ROOT


def obj(properties):
    return dict(type='object', properties=properties, required=list(properties), additionalProperties=False)


def repair_schema(context):
    number = {'type': 'number'}
    arm = {'type': 'string', 'enum': ['left', 'right']}
    def vector(limit=None):
        item = dict(number)
        if limit is not None: item.update(minimum=-limit, maximum=limit)
        return dict(type='array', items=item, minItems=3, maxItems=3)
    def step(op, **fields):
        return obj({'op': {'type': 'string', 'enum': [op]}, **({} if op == 'policy' else {'arm': arm}), **fields})
    variants = [step('policy'), step('lift', dz=number,
        intent={'type': 'string', 'enum': ['clearance', 'grasp_check']}),
        step('rotate', yaw=number), step('gripper', value=dict(number, minimum=0, maximum=1))]
    if 'grounding' in context:
        names = sorted(context['grounding'].get('points', {}))
        if names:
            variants.append(step('move_to_point', point={'type': 'string', 'enum': names}, offset=vector(.15)))
    else:
        variants += [step('move_to', xyz=vector()), step('nudge', dxyz=vector())]
    return obj({'why': {'type': 'string'}, 'expectation': {'type': 'string'},
                'steps': dict(type='array', minItems=1, maxItems=8, items={'anyOf': variants})})


def repair_example():
    directory = ROOT / 'blupe/examples/orange-block-repair'
    data = json.loads((directory / 'example.json').read_text())
    content = [{'type': 'text', 'text': json.dumps({key: value for key, value in data.items()
                if key not in ('frames', 'response')}, allow_nan=False)}]
    import base64
    for frame in data['frames']:
        body = (directory / frame['image']).read_bytes()
        if hashlib.sha256(body).hexdigest() != frame['sha256']:
            raise ValueError('Repair example frame provenance mismatch')
        content += [{'type': 'text', 'text': 'RECORDED EXAMPLE ONLY: ' + frame['camera'] + ' camera'},
                    {'type': 'image_url', 'image_url': {'url': 'data:image/jpeg;base64,' + base64.b64encode(body).decode()}}]
    return [{'role': 'user', 'content': content},
            {'role': 'assistant', 'content': json.dumps(data['response'], allow_nan=False)}]
