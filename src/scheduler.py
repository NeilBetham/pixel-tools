#!/usr/bin/env python3

import datetime
import multiprocessing
import os
import sys
import time
import zoneinfo

import skyfield.api
import skyfield.almanac

from pixel_animator import main as anim_main

def compute_sunrise_sunset(location, timescale, ephemeris, tz):
    today = datetime.datetime.now()
    t0 = timescale.utc(today.year, today.month, today.day, 0)
    t1 = timescale.utc(t0.utc_datetime() + datetime.timedelta(days=1))
    times, is_sunrises = skyfield.almanac.find_discrete(t0, t1, skyfield.almanac.sunrise_sunset(ephemeris, location))
    sunrise = None
    sunset = None

    for event_time, is_sunrise in zip(times, is_sunrises):
        if is_sunrise:
            sunrise = event_time.astimezone(tz)
        else:
            sunset = event_time.astimezone(tz)
    return (sunrise, sunset)



def main():
    ts = skyfield.api.load.timescale()
    ephem = skyfield.api.load_file(sys.argv[1])

    lat_lon = os.getenv("PIXEL_LATLON")
    elevation = os.getenv("PIXEL_ELEVATION")
    tz = zoneinfo.ZoneInfo(os.getenv("PIXEL_TIMEZONE"))
    loc_n, loc_w = lat_lon.split(',')
    location = skyfield.api.wgs84.latlon(float(loc_n), float(loc_w), float(elevation))


    anim_proc = multiprocessing.Process(target=anim_main)

    while True:
        # Check when sunrise and sunset happens
        sunrise, sunset = compute_sunrise_sunset(location, ts, ephem, tz)
        current_time = datetime.datetime.now(tz=tz)

        if current_time < sunrise or current_time > sunset:
            if not anim_proc.is_alive():
                anim_proc.start()
        else:
            if anim_proc.is_alive():
                anim_proc.terminate()

        time.sleep(60)


if __name__ == "__main__":
    main()
