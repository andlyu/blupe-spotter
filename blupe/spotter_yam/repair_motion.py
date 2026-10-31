"""Keep unrequested actuators exact and validate complete repairs before dispatch."""
from remote_yam.robocurve_trajectory import RoboCurveTrajectory
from remote_yam.session import _trajectory_waypoints


class RepairTrajectory(RoboCurveTrajectory):
    def build(self, targets, observation, first_step_id):
        # Keep the pinned target bounds, measured-state checks, IK and pacing.
        points = super().build(targets, observation, first_step_id)
        for arm in ('left', 'right'):
            grip = arm + '_gripper'
            moving_pose = any(name.startswith(arm + '_') and name != grip for name in targets)
            for point in points:
                if not moving_pose:
                    point[arm + '_joints_deg'] = list(observation[arm + '_joints_deg'])
                if grip not in targets:
                    point[grip] = observation[grip]
            if grip in targets:
                # The target was already strictly validated above. Preserve its
                # exact endpoint instead of introducing interpolation roundoff.
                points[-1][grip] = targets[grip]
        return _trajectory_waypoints(points)
