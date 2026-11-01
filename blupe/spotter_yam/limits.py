"""Per-run planning budgets; these never change robot motion/safety limits."""
DEFAULT_STEPS = 16
DEFAULT_ROUNDS = 6
MAX_STEPS = 32
MAX_ROUNDS = 12
DEFAULT_DURATION_S = 600


def repair_limits(value=None):
    if value is None: value = {}
    if not isinstance(value, dict) or set(value) - {'max_plan_steps', 'max_plan_rounds'}:
        raise ValueError('Spotter repair limits need steps per plan and rounds per intervention')
    result = {}
    for name, default, maximum, label in (
            ('max_plan_steps', DEFAULT_STEPS, MAX_STEPS, 'steps per repair plan'),
            ('max_plan_rounds', DEFAULT_ROUNDS, MAX_ROUNDS, 'plan rounds per intervention')):
        number = value.get(name, default)
        if type(number) is not int or not 1 <= number <= maximum:
            raise ValueError(f'Choose 1–{maximum} {label}')
        result[name] = number
    return result
