#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""The Met Eireann ReAnalysis explorer.

General utilities.
"""

import os
import numpy as np
import datetime as dt


def lineparser(line, startword, stopword=None):
    """Extract content from a line of text.
    
    Parameters
    ----------
    line: str
        Line of text from which we extract content
    
    startword: str
        Text pattern marking the begining of the content to extract
    
    stopword: str, optional
        Text pattern marking the end of the content to extract. If not
        provided, the function extracts up to the end of the line.
    
    
    Example
    -------
    >>> line = "This is a line from a log file. Recorded value=0.25645"
    >>> lineparser(line, "Recorded value=")
    "0.25645"
    >>> lineparser(line, "This is a line from ", ".")
    "a log file"
    """
    matchidx = line.index(startword)
    startidx = matchidx + len(startword)
    if stopword is not None:
        endidx = startidx + line[startidx:].index(stopword)
    else:
        endidx = len(line) + 1
    
    return line[startidx:endidx]

def str_to_datetime(strdate):
    """Convert string-formatted date to `datetime.datetime` object
    
    Covers the following formats:
        %Y-%m-%d
        %Y-%m-%d %H
        %Y-%m-%d %H:%M
    """
    if isinstance(strdate, dt.datetime):
        return strdate
    
    if len(strdate) == 10:
        fmt = "%Y-%m-%d"
    elif len(strdate) == 13:
        fmt = "%Y-%m-%d %H"
    elif len(strdate) == 16:
        fmt = "%Y-%m-%d %H:%M"
    else:
        raise ValueError(f"Could not infer the format of the date {strdate}")
    
    return dt.datetime.strptime(strdate, fmt)

def str_to_timedelta(strdelta):
    """Convert string-formatted duration to `datetime.timedelta` object
    
    Covers the following formats (case insensitive):
        3d -> 3 days
        3h -> 3 hours
        3m -> 3 minutes
        3s -> 3 seconds
    """
    if isinstance(strdelta, dt.timedelta):
        return strdelta
    
    if strdelta[-1].lower() == "d":
        return dt.timedelta(days = int(strdelta[:-1]))
    elif strdelta[-1].lower() == "h":
        return dt.timedelta(hours = int(strdelta[:-1]))
    elif strdelta[-1].lower() == "m":
        return dt.timedelta(minutes = int(strdelta[:-1]))
    elif strdelta[-1].lower() == "h":
        return dt.timedelta(seconds = int(strdelta[:-1]))
    else:
        raise ValueError(f"Could not infer the format of the date {strdelta}")

def datetime_arange(start, stop, step):
    """Create a list of regularly spaced `datetime.datetime` objects
    
    
    Parameters
    ----------
    start: str or `datetime.datetime`
        Starting date and time. If str, it must follow the format "%Y-%m-%d-%H-%M"
    
    stop: str or `datetime.datetime`
        Stoping date and time. If str, it must follow the format "%Y-%m-%d-%H-%M"
    
    step: str or `datetime.timedelta`
        Time step
    
    
    Returns
    -------
    ndarray of datetime64[m]
        Array of regularly spaced datetime.datetime (default is double precision up to the minute)
    
    
    Examples
    --------
    >>> start = dt.datetime(2017, 1, 1)
    >>> datetime_arange(start, start + str_to_timedelta("1d"), "3h")
    >>> array(['2017-01-01T00:00', '2017-01-01T03:00', '2017-01-01T06:00',
           '2017-01-01T09:00', '2017-01-01T12:00', '2017-01-01T15:00',
           '2017-01-01T18:00', '2017-01-01T21:00'], dtype='datetime64[m]')
    """
    start = str_to_datetime(start)
    stop = str_to_datetime(stop)
    step = str_to_timedelta(step)
    # return np.arange(start, stop, step, dtype="datetime64[m]")
    return np.arange(start, stop, step, dtype=dt.datetime)

def datetime_from_npdatetime(datetime):
    return dt.datetime.utcfromtimestamp(
        (datetime - np.datetime64(0, 's'))/np.timedelta64(1, 's')
    )

def subsample(x, step =2):
    """Subsample geographical grid in Numpy array
    
    
    Examples
    --------
    >>> import numpy as np
    >>> x = np.random.rand(489, 529)
    >>> subsample(x).shape
    (245, 265)
    
    >>> x = np.random.rand(22, 489, 529)
    >>> subsample(x).shape
    (22, 245, 265)
    
    >>> x = np.random.rand(22, 489, 529, 17)
    >>> subsample(x).shape
    (22, 245, 265, 17)
    """
    
    if x.ndim == 2:
        return x[::step, ::step]
    elif x.ndim == 3:
        return x[:, ::step, ::step]
    elif x.ndim == 4:
        return x[:, ::step, ::step, :]
    else:
        raise NotImplementedError("Only support arrays up to 4d")

# EOF
