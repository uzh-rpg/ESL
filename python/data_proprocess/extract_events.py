import argparse
import copy
import os
import sys
import time
from datetime import datetime
from pathlib import Path

import cv2
import matplotlib.pyplot as plt
import numpy as np
from prophesee_utils import load_td_data


def convertImageToList(event_image):
    event_arr = np.zeros((0,3), np.int32) # count/ts, x, y
    for y in range(event_image.shape[0]):
        for x in range(event_image.shape[1]):
            if  event_image[y,x]!=0:
                event_arr = np.append(event_arr, np.array([[event_image[y,x]*1000, x, y]]), axis=0)
    return event_arr

def colorize_image(motion_events, illum_events):
    viz_diff = np.zeros((480, 640), np.uint8)
    colorize = np.ones((480, 640, 3), np.uint8)*255
    viz_diff[motion_events!=0] = 1
    viz_diff[illum_events!=0] = 2
    colorize[illum_events!=0] = [0, 0, 255]
    colorize[motion_events!=0] = [0, 255,0]
    return colorize


class DataProvider:
    def __init__(self, cd_file: Path, trigger_file: Path, start_index: int,  num_triggers: int):
        self.cd_data = load_td_data(cd_file)
        self.cd_ts = self.cd_data['t']
        self.current_index = 0
        self.start_index = start_index
        if trigger_file is not None:
            self.trigger_data = load_td_data(trigger_file)['t']
            self.trigger_start_time = self.trigger_data[start_index]
            # self.skip_triggers = 10 # Every 10th trigger correspoind to the start of the projector
            self.trigger_end_time = self.trigger_data[start_index + num_triggers]
        else:
            self.trigger_data = self.generate_triggers()
            self.trigger_start_time = self.trigger_data[0]
            self.trigger_end_time = self.trigger_data[0] + 16667*num_triggers

        self.event_data =  self.cd_data[self.cd_ts>self.trigger_start_time]
        self.event_data =  self.event_data[self.event_data['t']<self.trigger_end_time]
        self.threshold = 1000
    
    def __iter__(self):
        return self
    
    def generate_triggers(self):
        ts = self.cd_ts
        ids = np.where(np.gradient(ts)>=self.threshold)[0]
        plt.plot(ts)
        plt.plot(np.gradient(ts))
        plt.plot(ids,  [ts[f] for f in ids], 'rx')
        plt.xlabel("Event id")
        plt.ylabel("Event timestamp")
        plt.show()
        return [ids[0]]
    
    def __next__(self):
        # start = time.time()
        start_trigger = self.trigger_data[self.start_index]+16666*self.current_index
        end_trigger = start_trigger+16666 # self.trigger_data[self.current_index+self.skip_triggers]
        events_before_trigger = self.event_data[self.event_data['t']<end_trigger]
        events_between_trigger = events_before_trigger[events_before_trigger['t']>start_trigger]
        # print("Events procured in time "+ str(time.time() - start))
        self.current_index += 1
        return [events_between_trigger,start_trigger, end_trigger]
    

def main():
    parser = argparse.ArgumentParser(
        description='Generate numpy array of event time surfaces from .h5 files \n'
        '        |      .       |        .\n'
        '        |      .       |        .\n',
        formatter_class=argparse.RawTextHelpFormatter
    )

    parser.add_argument('-object_dir', type=str, default="data", help='Directory containing dat files')
    parser.add_argument('-num_scans', type=int, default=60,help='Number of scans to compute')
    parser.add_argument('-start_scan_id', type=int, default=0,help='Scan to start from to average over')
    
    args = parser.parse_args()
    cd_file =Path(args.object_dir+'data_td.dat')
    trigger_file = Path(args.object_dir+'data_trigger.dat')
    np_dir = Path(args.object_dir+'scans_np')

    assert cd_file.exists()
    assert cd_file.name.endswith('.dat')
    if trigger_file.exists() and trigger_file.name.endswith('.dat'):
        print("Using trigger data")
    else:
        print("No trigger file found")
        trigger_file=None
    # assert not np_dir.exists() 

    if not os.path.isdir(np_dir):
        os.mkdir(np_dir)
    start_id = 0
    data_engine = DataProvider(cd_file, trigger_file, start_id, 500)
    scan_id = 0 # to stop by scan or stop by num of triggers
    seq = 0
    only_illum = True

    allmotionevents = np.zeros((0,3))
    start = time.time()
    for data, t_start, t_end in data_engine:
        if len(data)>0:
            if t_end-t_start>10000 and t_end-t_start<17000:
                illum_events = np.zeros((480, 640), np.float32)
                for e in data:
                    if e[3]!=0:
                        #only consider positive polarity events
                        illum_events[int(e[2]), int(e[1])] = e[0]
                min_time = np.min(illum_events[illum_events>0])
                max_time = np.max(illum_events[illum_events>0])
                print("Events max time:"+str(max_time))
                print("Events min time:"+str(min_time))
                print("Events diff"+str(max_time-min_time))
                viz_events = (illum_events-min_time)/(max_time-min_time)
                viz_events[viz_events<0]=0
                cv2.imshow('viz', viz_events)
                cv2.waitKey(10)
                # np.save(os.path.join(np_dir, 'scan'+str(start_id+scan_id).zfill(2)+'.npy'), viz_events)

        scan_id+=1
        if scan_id>args.num_scans:
            break

if __name__ == '__main__':
    main()
