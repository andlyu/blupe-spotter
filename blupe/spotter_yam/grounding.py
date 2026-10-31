"""Bind repair point references to paired public API RGB-D measurements."""
from copy import deepcopy
import math
import time

from remote_yam.cameras import CameraFrame


class RepairGrounding:
    def __init__(self, source, validate_report):
        self.source, self.validate_report = source, validate_report
        self.snapshot = None

    def capture(self, task, history, supervisor, cancelled):
        for attempt in range(3):
            snapshot = self.source.capture(stopped=True, cancelled=cancelled)
            if snapshot.metadata['captured_at'] > history[-1]['measured']['observed_at']:
                break
            if cancelled(): raise RuntimeError('Spotter grounding cancelled')
            if attempt < 2: time.sleep(.1)
        self.validate_report(snapshot.calibration)
        if snapshot.metadata['captured_at'] <= history[-1]['measured']['observed_at']:
            raise ValueError('Repair depth precedes the settled feedback; no repair motion proposed')
        self.snapshot = snapshot
        # Pixel queries refer to this exact native RGB/depth pair, never the
        # separately rectified live JPEG or a differently sized earlier image.
        latest = {**history[-1], 'frames': (
            CameraFrame('top', snapshot.image(), time.time(),
                        source_captured_at=snapshot.metadata['captured_at']),
            *(frame for frame in history[-1]['frames'] if frame.name != 'top'))}
        history = [*history[:-1], latest]
        result = supervisor.locate(task, [latest])
        if cancelled(): raise RuntimeError('Spotter grounding cancelled')
        selected = result.get('points')
        if not isinstance(selected, list) or len(selected) > 4:
            raise ValueError('Repair grounding needs at most four visible points')
        points, pixels = {}, {}
        h, w = snapshot.rgb.shape[:2]
        for point in selected:
            if not isinstance(point, dict) or set(point) != {'name', 'point_1000'}:
                raise ValueError('Grounding needs a name and normalized image point')
            name, pixel = point['name'], point['point_1000']
            if (not isinstance(name, str) or not name.strip() or len(name) > 80
                    or name in points or not isinstance(pixel, list) or len(pixel) != 2
                    or any(type(v) is not int for v in pixel)
                    or any(not 0 <= v <= 1000 for v in pixel)):
                raise ValueError('Invalid or ambiguous repair point')
            pixel = [min(w-1, round(pixel[0]*w/1000)), min(h-1, round(pixel[1]*h/1000))]
            # A surface measurement is not a grasp pose. The planner must choose
            # a bounded approach/grasp offset; the normal IK/gateway still checks it.
            try:
                measurements = {arm: snapshot.measure(*pixel, arm=arm)
                                for arm in ('left', 'right')}
            except ValueError:
                continue  # Missing/noisy pixels never receive invented depth.
            points[name] = {arm: receipt['point_base_m'] for arm, receipt in measurements.items()}
            pixels[name] = pixel
        context = dict(image_size=[w, h], camera='top',
                       captured_at=snapshot.metadata['captured_at'],
                       calibration_id=snapshot.metadata['calibration_id'],
                       quality=snapshot.calibration['quality'], points=deepcopy(points), pixels=pixels,
                       frame=latest['frames'][0].summary(),
                       meaning='Measured surface points in each named arm base, not gripper targets.')
        return history, context, points

    def resolve(self, result, points):
        if self.snapshot is None or self.snapshot.age() > 5:
            raise ValueError('Repair RGB-D aged during planning; no repair motion proposed')
        result = deepcopy(result)
        for step in result.get('steps', []):
            if step.get('op') == 'move_to_point':
                if (set(step) != {'op', 'arm', 'point', 'offset'}
                        or step['arm'] not in ('left', 'right')
                        or not isinstance(step['point'], str) or step['point'] not in points
                        or not isinstance(step['offset'], list) or len(step['offset']) != 3
                        or any(type(v) not in (int, float) or not math.isfinite(v)
                               or abs(v) > .15 for v in step['offset'])):
                    raise ValueError('Repair target requires a measured point and bounded offset')
                arm = step['arm']
                xyz = [a+b for a, b in zip(points[step['point']][arm], step['offset'])]
                step.clear(); step.update(op='move_to', arm=arm, xyz=xyz)
            elif step.get('op') == 'move_to' or (step.get('op') == 'nudge'
                    and (not isinstance(step.get('dxyz'), list) or len(step['dxyz']) != 3
                         or step['dxyz'][:2] != [0, 0])):
                raise ValueError('Horizontal repair motion requires a measured point reference')
        return result

    def close(self):
        self.source.connection.close()
        self.snapshot = None
