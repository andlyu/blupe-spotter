"""Retime frozen policy output to YAM's saved 10 Hz joint-step envelope.

Targets and their order are preserved; only intermediate samples are inserted.
The gateway still checks the entire packet, including limits and swept collisions.
"""
from copy import deepcopy
import math

from remote_yam.controller_workspace import workspace_for_robot
from remote_yam.session import MAX_COMMANDS, MAX_WAYPOINTS_PER_PACKET
from remote_yam.yam_runpod_policy import YAMRunpodAdapter


def retime(points, observation, first_step_id, max_step_deg, *, cancelled=lambda: False):
    if not math.isfinite(max_step_deg) or max_step_deg <= 0:
        raise ValueError('Invalid joint retiming interval')
    previous = {key: deepcopy(observation[key]) for key in
                ('left_joints_deg', 'right_joints_deg', 'left_gripper', 'right_gripper')}
    result = []
    budget = min(MAX_WAYPOINTS_PER_PACKET, MAX_COMMANDS - first_step_id)
    for target in points:
        distance = max(abs(a-b) for side in ('left', 'right')
                       for a, b in zip(previous[side+'_joints_deg'], target[side+'_joints_deg']))
        count = max(1, math.ceil(distance / max_step_deg))
        if len(result) + count > budget:
            raise ValueError('Retimed policy trajectory exceeds the gateway packet budget; no targets dispatched')
        for index in range(1, count + 1):
            if cancelled(): raise RuntimeError('Policy retiming cancelled')
            fraction = index / count
            point = dict(step_id=first_step_id + len(result))
            for side in ('left', 'right'):
                key = side + '_joints_deg'
                point[key] = (list(target[key]) if index == count else
                              [a+(b-a)*fraction for a,b in zip(previous[key],target[key])])
                key = side + '_gripper'
                point[key] = target[key] if index == count else previous[key]+(target[key]-previous[key])*fraction
            result.append(point)
        previous = target
    return result


class YAMMotionAdapter(YAMRunpodAdapter):
    def build_trajectory(self, prompt, observation, first_step_id):
        points = super().build_trajectory(prompt, observation, first_step_id)
        limits = workspace_for_robot(self._robot_id)._safety()
        # Margin avoids representational boundary failures; no target is clipped.
        step = .9 * math.degrees(min(limits['max_adjacent_delta_rad'],
                                     limits['max_joint_velocity_rad_s'] / 10))
        result = retime(points, observation, first_step_id, step, cancelled=self.cancelled)
        if len(result) != len(points):
            self.interaction_sink('model_progress', 'Policy trajectory slowed to the YAM joint-step envelope',
                progress_type='status', input_waypoints=len(points), output_waypoints=len(result),
                max_step_deg=step)
        return result
