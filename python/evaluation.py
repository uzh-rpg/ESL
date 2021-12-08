import numpy as np
import cv2
import os
import matplotlib.pyplot as plt
from utils.utilities import utils as ut
import argparse
import glob

# Visualization parameters
min_depth = 20
max_depth = 120
cmap = 'jet'

class evaluation_stats:
    def __init__(self, estimate, groundtruth):
        self.groundtruth = groundtruth
        self.estimate = estimate
        self.margin = 0.01*np.sum(self.groundtruth[self.groundtruth>0])/(np.sum(self.groundtruth>0))
        self.calculate_metrics()
        
    def calculate_fillrate(self):
        diff = np.abs(self.groundtruth-self.estimate)
        diff[self.groundtruth==0]=0
        self.fillrate = (np.sum(diff<self.margin) -np.sum(self.groundtruth==0))/ (diff.shape[0]*diff.shape[1] -np.sum(self.groundtruth==0))

    def calculate_rmse(self):
        diff_sq = pow((self.groundtruth-self.estimate), 2)
        self.rmse = np.sqrt(np.sum(diff_sq[self.groundtruth>0]) / (np.sum(self.groundtruth>0)))

    def middlebury_metrics(self):
        diff_abs = np.abs(self.groundtruth-self.estimate)
        diff_abs[self.groundtruth==0] = 0
        self.perc_1 = 100*np.sum(diff_abs>1)/(diff_abs.shape[0]*diff_abs.shape[1])
        self.perc_5 = 100* np.sum(diff_abs>5)/(diff_abs.shape[0]*diff_abs.shape[1])
        self.perc_10 = 100*np.sum(diff_abs>10)/(diff_abs.shape[0]*diff_abs.shape[1])

    def calculate_metrics(self):
        self.calculate_fillrate()
        self.calculate_rmse()
        self.middlebury_metrics()
        return 0

    def print_metrics(self):
        print("Fill rate: " + str(self.fillrate))
        print("RMSE: " + str(self.rmse))
        print("% Pixels with error greater than 1cm: " + str(self.perc_1))
        print("% Pixels with error greater than 5cm: " + str(self.perc_5))
        print("% Pixels with error greater than 10cm: " + str(self.perc_10))


def main():
    parser = argparse.ArgumentParser(
        description='Evaluation of event camera and projector system using line scanning projection\n',
        formatter_class=argparse.RawTextHelpFormatter
    )

    parser.add_argument('-object_dir',  type=str,default="",help='Directory containing depth files')
    args = parser.parse_args()
    gt_files = sorted(glob.glob(args.object_dir + 'mc3d_dir/*.npy'))
    gt, thresh  = ut.combine_mc3d(gt_files, len(gt_files), min_depth, max_depth)

    esl = np.load(os.path.join(args.object_dir, 'depth_dir/scans003.npy'))


    esl[esl>=max_depth] = 0
    esl[esl<=min_depth] = 0
    esl[gt==0]=0
    print("================================Stats==================================")
    print("========== ESL stats ==============")
    stats_esl = evaluation_stats(esl, gt)
    stats_esl.print_metrics()
    print("=======================================================================")

if __name__ == '__main__':
    main()