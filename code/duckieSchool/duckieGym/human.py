#!/usr/bin/env python3

"""
This is a custom script developed by FRANK based on duckietown
joystick script in order to allow user drive duckietown with joystick
and obtain log for further training.
"""

import argparse
import json
import sys
import cv2
import time
import gym
import numpy as np
import pyglet
import math
from helperfnc import Logger,SteeringToWheelVelWrapper
import logging

from pyglet.window import key

from gym_duckietown.envs import DuckietownEnv

#! PWM Calculator
pwm_converter = SteeringToWheelVelWrapper()

#! Logger setup:
logging.basicConfig()
logger = logging.getLogger('gym-duckietown')
logger.setLevel(logging.WARNING)

#! Parser sector:
parser = argparse.ArgumentParser()
parser.add_argument('--env-name', default=None)
parser.add_argument('--map-name', default='small_loop_cw')
parser.add_argument('--draw-curve', default=False,
                    help='draw the lane following curve')
parser.add_argument('--draw-bbox', default=False,
                    help='draw collision detection bounding boxes')
parser.add_argument('--domain-rand', default=True,
                    help='enable domain randomization')
parser.add_argument('--playback', default=True,
                    help='enable playback after each session')
parser.add_argument('--distortion', default=True)

parser.add_argument('--raw-log', default=True,
                    help='enables recording high resolution raw log')
parser.add_argument('--steps',default=1500,help='number of steps to record in one batch')

args = parser.parse_args()


def sleep_after_reset(seconds):
    for remaining in range(seconds, 0, -1):
        sys.stdout.write("\r")
        sys.stdout.write("{:2d} seconds remaining.".format(remaining))
        sys.stdout.flush()
        time.sleep(1)
    sys.stdout.write("\rGO!            \n")
    return


#! Start Env
if args.env_name is None:
    env = DuckietownEnv(
        map_name="loop_pedestrians",
        max_steps=args.steps,
        draw_curve=args.draw_curve,
        draw_bbox=args.draw_bbox,
        domain_rand=args.domain_rand,
        distortion=args.distortion,
        accept_start_angle_deg=4,
        full_transparency=True,
    )
else:
    env = gym.make(args.env_name)

env.reset()
env.render()
sleep_after_reset(5)

#! Recorder Setup:
# global variables for demo recording
actions = []
observation = []
datagen = Logger(env, log_file='training_data.log')
rawlog = Logger(env, log_file='raw_log.log')
last_reward = 0


def playback():
    #! Render Image
    if args.playback & args.raw_log:
        for entry in rawlog.recording:
            step = entry['step']
            meta = entry['metadata']
            action = step[1]
            x = action[0]
            z = action[1]
            canvas = step[0].copy()
            reward = meta[1]
            pwm_left, pwm_right = pwm_converter.convert(x, z)
            print('Linear: ', x, ' Angular: ', z, 'Left PWM: ', round(
                pwm_left, 3), ' Right PWM: ', round(pwm_right, 3), ' Reward: ', round(reward, 2))
            #! Speed bar indicator
            cv2.rectangle(canvas, (20, 240), (50, int(240-220*x)),
                        (76, 84, 255), cv2.FILLED)
            cv2.rectangle(canvas, (320, 430), (int(320-150*z), 460),
                        (76, 84, 255), cv2.FILLED)

            cv2.imshow('Playback', canvas)
            cv2.waitKey(20)

    qa = input('1 to commit, 2 to abort:        ')
    #! User interaction for log selection
    while not(qa == '1' or qa == '2'):
        qa = input('1 to commit, 2 to abort:        ')

    if qa == '2':
        print('Reset log. Discard current...')
        rawlog.recording.clear()
        datagen.recording.clear()
        print('Size of rawlog: ', len(rawlog.recording))

    else:
        datagen.on_episode_done()
        rawlog.on_episode_done()
        print('Size of rawlog: ', len(rawlog.recording))
    #! Done
    return


@env.unwrapped.window.event
def on_key_press(symbol, modifiers):
    """
    This handler processes keyboard commands that
    control the simulation
    """

    if symbol == key.BACKSPACE or symbol == key.SLASH:
        print('RESET')
        playback()
        env.reset()
        env.render()
        sleep_after_reset(5)
    elif symbol == key.PAGEUP:
        env.unwrapped.cam_angle[0] = 0
        env.render()
    elif symbol == key.ESCAPE or symbol == key.Q:
        env.close()
        sys.exit(0)


@env.unwrapped.window.event
def on_joybutton_press(joystick, button):
    """
    Event Handler for Controller Button Inputs
    Relevant Button Definitions:
    3 - Y - Resets Env.
    """

    # Y Button
    if button == 3:
        print('RESET')
        playback()

        env.reset()
        env.render()
        sleep_after_reset(5)


def image_resize(image, width=None, height=None, inter=cv2.INTER_AREA):
    # initialize the dimensions of the image to be resized and
    # grab the image size
    dim = None
    (h, w) = image.shape[:2]

    # if both the width and height are None, then return the
    # original image
    if width is None and height is None:
        return image

    # check to see if the width is None
    if width is None:
        # calculate the ratio of the height and construct the
        # dimensions
        r = height / float(h)
        dim = (int(w * r), height)

    # otherwise, the height is None
    else:
        # calculate the ratio of the width and construct the
        # dimensions
        r = width / float(w)
        dim = (width, int(h * r))

    # resize the image
    resized = cv2.resize(image, dim, interpolation=inter)

    # return the resized image
    return resized


def update(dt):
    """
    This function is called at every frame to handle
    movement/stepping and redrawing
    """
    global actions, observation, last_reward

    #print('Debug z and y:',joystick.y,'|||',joystick.z)

    #! Joystick no action do not record
    if round(joystick.z, 2) == 0.0 and round(joystick.y, 2) == 0.0:
        return

    #! Nominal Joystick Interpretation
    x = round(joystick.y, 2) * 0.9  # To ensure maximum trun/velocity ratio
    z = round(joystick.z, 2) * 3.0

    # #! Joystick deadband
    # if (abs(round(joystick.y, 2)) < 0.01):
    #     z = 0.0

    # if (abs(round(joystick.z, 2)) < 0.01):
    #     x = 0.0

    #! DRS enable for straight line
    if joystick.buttons[6]:
        x = -1.0
        z = 0.0

    action = np.array([-x, -z])
    pwm_left, pwm_right = pwm_converter.convert(-x, -z)

    #! GO! and get next
    # * Observation is 640x480 pixels
    obs, reward, done, info = env.step(action)

    if reward != -1000:
        print('Current Command: ', action,
              ' speed. Score: ', reward)
        if ((reward > last_reward-0.02) or True):
            print('log')

            #! resize to Nvidia standard:
            obs_distorted_DS = image_resize(obs, width=200)

            #! ADD IMAGE-PREPROCESSING HERE!!!!!
            height, width = obs_distorted_DS.shape[:2]
            #print('Distorted return image Height: ', height,' Width: ',width)
            cropped = obs_distorted_DS[0:150, 0:200]

            # NOTICE: OpenCV changes the order of the channels !!!
            cropped_final = cv2.cvtColor(cropped, cv2.COLOR_BGR2YUV)

            cv2.imshow('Whats logged', cropped_final)
            cv2.waitKey(1)

            datagen.log(cropped_final, action, reward, done, info)
            rawlog.log(obs, action, reward, done, info)
            last_reward = reward
        else:
            print('Bad Training Data! Discarding...')
            last_reward = reward
    else:
        print('!!!OUT OF BOUND!!!')

    if done:
        playback()
        env.reset()
        env.render()
        sleep_after_reset(5)
        return

    env.render()


#! Enter main event loop
pyglet.clock.schedule_interval(update, 1.0 / env.unwrapped.frame_rate)
#! Get Joystick
# Registers joysticks and recording controls
joysticks = pyglet.input.get_joysticks()
assert joysticks, 'No joystick device is connected'
joystick = joysticks[0]
joystick.open()
joystick.push_handlers(on_joybutton_press)
pyglet.app.run()

#! Log and exit
datagen.close()
rawlog.close()
env.close()