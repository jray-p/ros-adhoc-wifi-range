#!/usr/bin/env python3

# requires 3.6+. which you have, right? because its 2024
from subprocess import run, PIPE
import logging
import argparse

import rospy
from std_msgs.msg import String


class WifiIF:
    def __init__(self):
        self.pub = rospy.Publisher("/rawr/rssi", String, queue_size=10)
        rospy.init_node("rawr_wifiif", anonymous=False)
        self.rate_hz = 10
        self._dev = rospy.get_param("adhoc-ifname", "wlan0")
        self.macs_to_monitor = rospy.get_param("macs_to_monitor", [])
        self.mac_inactive_threshold_ms = rospy.get_param("mac_inactive_threshold_ms", 1000)

    def run(self):
        rate = rospy.Rate(self.rate_hz)
        while not rospy.is_shutdown():

            iw_dump = run(["iw", "dev", self._dev, "station", "dump"], stdout=PIPE, encoding="utf-8")

            # verify inactive time is low
            stations_raw = iw_dump.stdout.split("Station ")[1:]
            stations = dict()
            for station in stations_raw:
                station_mac = station.split("(on ")[0].strip()
                stations[station_mac] = dict()
                for line in station.split("\n")[1:]:

                    if not line.strip():
                        continue
                    key, val = line.split(":")
                    stations[station_mac][key.strip()] = val.strip()
            for mac in self.macs_to_monitor:
                if not mac in stations:
                    continue
                # if data is too stale
                if int(stations[mac]["inactive time"].split(" ")[0]) > self.mac_inactive_threshold_ms:
                    continue
                # max rssi? only ant 0 or 1 or ...?
                max_rssi = stations[mac]["signal"].split(" ")[0]
                self.pub.publish(String(mac + "," + str(max_rssi)))

            rate.sleep()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--verbose", "-v", action="store_true")
    ap.add_argument("name", help="ignored, required for compat")
    ap.add_argument("log", help="ignored, required for compat")

    args = ap.parse_args()
    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(level=level, format="%(asctime)s :: %(levelname)s :: %(name)s :: %(message)s")
    WifiIF().run()


if __name__ == "__main__":
    main()
