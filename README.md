# Optimo Python library

This is a python library for [OptimoRoute][optimoroute.com]'s web service.

---

**Note**: This is not yet intended for production usage. It is currently in Pre-Alpha development status. Use at your own risk.
 
---

# Requirements

* Python (has only been tested with python 2.7)
* An access key provided to you by [OptimoRoute][optimoroute.com]

# Installation

Installation using `pip`:

    pip install optimo

# Usage

```python
from datetime import datetime
from decimal import Decimal
from optimo import OptimoAPI, Driver, WorkShift, Order, RoutePlan


# Instantiate the interface to optimoroute's API.
optimo_api = OptimoAPI('https://api.optimoroute.com', 'some_access_key')

# Create a workshift for the driver.
ws = WorkShift(
    start_work=datetime(year=2014, month=12, day=5, hour=8, minute=0), 
    end_work=datetime(year=2014, month=12, day=5, hour=14, minute=0)
)

# Create the driver and also pass the workshift we created above.
drv = Driver(
    id='123', 
    start_lat=Decimal('53.350046'), 
    start_lng=Decimal('-6.274655'), 
    end_lat=Decimal('53.341191'), 
    end_lng=Decimal('-6.260402'),
    work_shifts=[ws]
)

order1 = Order(
    id='123', 
    lat=Decimal('53.343204'), 
    lng=Decimal('-6.269798'), 
    duration=20
)

order2 = Order(
    id='456', 
    lat=Decimal('53.341820'), 
    lng=Decimal('-6.264991'), 
    duration=25
)

# Create the route plan, and also pass the orders and the driver created above.
# The 'request_id' is the one we'll use later to check the results of the 
# plan optimization.
routeplan = RoutePlan(
    request_id='1234',
    callback_url='https://callback.com/1234',
    status_callback_url='https://status.callback.com/1234'
    drivers=[drv],
    orders=[order1, order2]
)

# Start the plan optimization. If there is no exception raised then we assume
# success.
optimo_api.plan(routeplan)

# Get the result of the optimization. We use the 'request_id' we provided to
# optimoroute previously.
data = optimo_api.get('1234')

# If the optimization has finished we can see the result. Otherwise the data 
# will be None.
{
    u'creationTime': u'2014-12-04T17:01:52',
    u'requestId': u'1234',
    u'result': {
        u'routes': [
            {
                u'driverId': u'123',
                u'orders': [
                    {u'id': u'123', u'scheduledAt': u'2014-12-05T08:04'},
                    {u'id': u'456', u'scheduledAt': u'2014-12-05T08:27'}
                ]
            }
        ],
        u'unservedOrders': []
    },
    u'success': True
}

# We can stop an already running optimization. If stopped previously no
# exceptions will be raised, it will return None implying it was successful.
optimo_api.stop('1234')
```


# Todo

* Provide 100% test coverage
* Add docstrings to every function/class.


[optimoroute.com]: http://optimoroute.com
