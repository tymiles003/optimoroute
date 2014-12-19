# -*- coding: utf-8 -*-
import abc
import datetime
from numbers import Number

from .errors import OptimoValidationError


class BaseModel(object):
    """Abstract base class that all OptimoRoute entities must subclass"""
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def validate(self):
        """It must replicate the validation according to the JSON schema
        provided by OptimoRoute.

        Must return None or raise a validation error
        """

    @abc.abstractmethod
    def as_optimo_schema(self):
        """Must return a dict with the key names as expected from OptimoRoute's
        JSON schema.
        """

    def validate_type(self, attr, expected):
        """Validates that ``attr`` is of the ``expected`` type

        :param attr: name of the model attribute to check
        :param expected: expected type of ``attr``
        :return: None if is valid, or it will raise a TypeError
        """
        type_error_msg = "'{}.{}' must be of type {!r}, not {!r}"
        value = getattr(self, attr)

        if not isinstance(value, expected):
            cls_name = self.__class__.__name__
            raise TypeError(
                type_error_msg.format(cls_name, attr, expected, type(value))
            )


ITERABLES = (list, tuple)


class SchedulingInfo(BaseModel):
    def __init__(self, scheduled_at, scheduled_driver, locked=False):
        self.scheduled_at = scheduled_at
        self.scheduled_driver = scheduled_driver
        self.locked = locked

    def validate(self):
        self.validate_type('scheduled_at', datetime.datetime)
        self.validate_type('scheduled_driver', (str, Driver))
        self.validate_type('locked', bool)

    def as_optimo_schema(self):
        self.validate()
        d = {
            'scheduledAt': self.scheduled_at,
            'locked': self.locked,
        }
        if isinstance(self.scheduled_driver, Driver):
            d['scheduledDriver'] = self.scheduled_driver.id
        else:
            d['scheduledDriver'] = self.scheduled_driver
        return d


class TimeWindow(BaseModel):
    def __init__(self, start_time, end_time):
        self.start_time = start_time
        self.end_time = end_time

    def validate(self):
        self.validate_type('start_time', datetime.datetime)
        self.validate_type('end_time', datetime.datetime)

    def as_optimo_schema(self):
        self.validate()
        return {
            'timeFrom': self.start_time,
            'timeTo': self.end_time,
        }


class Order(BaseModel):
    def __init__(self, id, lat, lng, duration, time_window=None, priority='M',
                 skills=None, assigned_to=None, scheduling_info=None):
        self.id = id
        self.lat = lat
        self.lng = lng
        self.duration = duration
        # described as 'tw' in the JSON schema
        self.time_window = time_window
        # (M)edium is the default for the OptimoRoute service
        self.priority = priority
        self.skills = skills or []
        self.assigned_to = assigned_to
        self.scheduling_info = scheduling_info

    def validate(self):
        cls_name = self.__class__.__name__
        self.validate_type('id', str)
        if not self.id:
            raise ValueError("'{}.id' cannot be empty".format(cls_name))

        self.validate_type('lat', Number)
        self.validate_type('lng', Number)

        self.validate_type('duration', (int, long))
        if self.duration < 0:
            raise ValueError("'{}.duration' cannot be negative".format(cls_name))

        if self.time_window is not None:
            self.validate_type('time_window', TimeWindow)

        self.validate_type('priority', basestring)
        if self.priority not in ('L', 'M', 'H', 'C'):
            raise ValueError(
                "'{}.priority' must be one of ('L', 'M', 'H', 'C')"
                .format(cls_name)
            )

        self.validate_type('skills', ITERABLES)
        for skill in self.skills:
            if not isinstance(skill, basestring):
                raise TypeError(
                    "'{}.skills' must contain elements of type str"
                    .format(cls_name)
                )

        if self.assigned_to is not None:
            self.validate_type('assigned_to', basestring)

        if self.scheduling_info is not None:
            self.validate_type('scheduling_info', SchedulingInfo)

    def as_optimo_schema(self):
        self.validate()
        d = {
            'id': self.id,
            'lat': self.lat,
            'lon': self.lng,
            'duration': self.duration,
            'priority': self.priority,
        }

        if self.time_window:
            d['tw'] = self.time_window

        if self.skills:
            d['skills'] = self.skills

        if self.assigned_to:
            d['assignedTo'] = self.assigned_to

        if self.scheduling_info:
            d['schedulingInfo'] = self.scheduling_info

        return d


class Break(BaseModel):

    def __init__(self, start_break, end_break, duration):
        self.start_break = start_break
        self.end_break = end_break
        self.duration = duration

    def validate(self):
        self.validate_type('start_break', datetime.datetime)
        self.validate_type('end_break', datetime.datetime)
        self.validate_type('duration', (int, long))

    def as_optimo_schema(self):
        self.validate()
        return {
            'breakStartFrom': self.start_break,
            'breakStartTo': self.end_break,
            'breakDuration': self.duration,
        }


class WorkShift(BaseModel):

    def __init__(self, start_work, end_work, allowed_overtime=None, break_=None,
                 unavailable_times=None):
        self.start_work = start_work
        self.end_work = end_work
        self.allowed_overtime = allowed_overtime
        self.break_ = break_
        self.unavailable_times = unavailable_times or []

    def validate(self):
        cls_name = self.__class__.__name__
        self.validate_type('start_work', datetime.datetime)
        self.validate_type('end_work', datetime.datetime)

        if self.allowed_overtime is not None:
            self.validate_type('allowed_overtime', (int, long))

        if self.break_ is not None:
            self.validate_type('break_', Break)

        self.validate_type('unavailable_times', ITERABLES)
        for time_window in self.unavailable_times:
            if not isinstance(time_window, TimeWindow):
                raise TypeError(
                    "'{}.unavailable_times' must contain elements of type "
                    "{}".format(cls_name, 'TimeWindow')
                )

    def as_optimo_schema(self):
        self.validate()
        d = {
            'workTimeFrom': self.start_work,
            'workTimeTo': self.end_work,
        }

        if self.allowed_overtime:
            d['allowedOvertime'] = self.allowed_overtime

        if self.break_:
            d['break'] = self.break_

        if self.unavailable_times:
            d['unavailableTimes'] = self.unavailable_times

        return d


class Driver(BaseModel):

    def __init__(self, id, start_lat, start_lng, end_lat, end_lng,
                 work_shifts=None, skills=None, speed_factor=None):

        self.id = id
        self.start_lat = start_lat
        self.start_lng = start_lng
        self.end_lat = end_lat
        self.end_lng = end_lng
        self.work_shifts = work_shifts or []
        self.skills = skills or []
        self.speed_factor = speed_factor

    def validate(self):
        cls_name = self.__class__.__name__
        self.validate_type('id', basestring)
        if not self.id:
            raise ValueError("'{}.id' cannot be empty".format(cls_name))

        self.validate_type('start_lat', Number)
        self.validate_type('start_lng', Number)

        self.validate_type('end_lat', Number)
        self.validate_type('end_lng', Number)

        self.validate_type('work_shifts', ITERABLES)
        if not self.work_shifts:
            raise ValueError(
                "'{}.work_shifts' must contain at least 1 "
                "element".format(cls_name)
            )
        for ws in self.work_shifts:
            if not isinstance(ws, WorkShift):
                raise TypeError(
                    "'{}.work_shifts' must contain elements of type {}"
                    .format(cls_name, 'WorkShift')
                )

        self.validate_type('skills', ITERABLES)
        for skill in self.skills:
            if not isinstance(skill, basestring):
                raise TypeError(
                    "'{}.skills' must contain elements of type str"
                    .format(cls_name)
                )

        if self.speed_factor is not None:
            self.validate_type('speed_factor', Number)

    def as_optimo_schema(self):
        self.validate()
        d = {
            'id': self.id,
            'startLat': self.start_lat,
            'startLon': self.start_lng,
            'endLat': self.end_lat,
            'endLon': self.end_lng,
            'workShifts': self.work_shifts,
            'skills': self.skills,
        }
        if self.speed_factor:
            d['speedFactor'] = self.speed_factor
        return d


class RoutePlan(BaseModel):
    NO_LOAD_CAPACITIES_MIN = 0
    NO_LOAD_CAPACITIES_MAX = 4

    def __init__(self, request_id, callback_url, status_callback_url,
                 orders=None, drivers=None, no_load_capacities=None):
        # TODO: support for serviceRegions and optimizationParamaters
        self.request_id = request_id
        self.callback_url = callback_url
        self.status_callback_url = status_callback_url
        self.orders = orders or []
        self.drivers = drivers or []
        self.no_load_capacities = no_load_capacities

    def validate(self):
        cls_name = self.__class__.__name__
        self.validate_type('request_id', basestring)
        if not self.request_id:
            raise ValueError("'{}.request_id' cannot be an empty string".format(cls_name))

        self.validate_type('callback_url', basestring)

        self.validate_type('status_callback_url', basestring)

        self.validate_type('orders', ITERABLES)
        if not self.orders:
            raise ValueError("'{}.orders' must have at least 1 element".format(cls_name))
        else:
            for order in self.orders:
                if not isinstance(order, Order):
                    raise TypeError("'{}.orders' must contain elements of "
                                    "type {}".format(cls_name, 'Order'))

        self.validate_type('drivers', ITERABLES)
        if not self.drivers:
            raise ValueError("'{}.drivers' must have at least 1 element".format(cls_name))
        else:
            for drv in self.drivers:
                if not isinstance(drv, Driver):
                    raise TypeError("'{}.drivers' must contain elements of type"
                                    " {}".format(cls_name, 'Driver'))

        if self.no_load_capacities is not None:
            self.validate_type('no_load_capacities', (int, long))
            if (self.no_load_capacities < self.NO_LOAD_CAPACITIES_MIN or
                    self.no_load_capacities > self.NO_LOAD_CAPACITIES_MAX):
                raise ValueError(
                    "'{}.no_load_capacities' must be between 0-4".
                    format(cls_name)
                )

        # ascertain that all driver id references of scheduling_info, inside
        # each order, correspond to actual driver objects inside 'drivers'.
        driver_ids = [drv.id for drv in self.drivers]
        for order in self.orders:
            if order.scheduling_info:
                si_schema = order.scheduling_info.as_optimo_schema()
                si_driver_id = si_schema['scheduledDriver']
                if si_driver_id not in driver_ids:
                    raise OptimoValidationError(
                        "SchedulingInfo defines driver with id: '{}' that is "
                        "not present in 'drivers' list".format(si_driver_id)
                    )

    def as_optimo_schema(self):
        self.validate()
        d = {
            'requestId': self.request_id,
            'callback': self.callback_url,
            'statusCallback': self.status_callback_url,
            'orders': self.orders,
            'drivers': self.drivers,
        }
        if self.no_load_capacities:
            d['noLoadCapacities'] = self.no_load_capacities
        return d
