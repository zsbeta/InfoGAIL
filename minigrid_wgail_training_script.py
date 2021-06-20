import copy
import os

import gym
import gym_minigrid
import numpy as np
import pickle5 as pickle
import torch
from gym_minigrid import wrappers
from imitation.algorithms import adversarial
from imitation.data import rollout
from imitation.util import logger, util
from stable_baselines3 import PPO
from stable_baselines3.common import policies


from utils.env_utils import minigrid_render, minigrid_get_env
import os, time
import numpy as np

import argparse

import matplotlib.pyplot as plt


import pickle5 as pickle
from imitation.data import rollout
from imitation.util import logger, util
from imitation.algorithms import bc

import gym
import gym_minigrid


from stable_baselines3.common.policies import ActorCriticCnnPolicy, ActorCriticPolicy


import argparse

parser = argparse.ArgumentParser()
parser.add_argument(
    "--env",
    "-e",
    help="minigrid gym environment to train on",
    default="MiniGrid-Empty-6x6-v0",
)
parser.add_argument("--run", "-r", help="Run name", default="sample_run")

parser.add_argument(
    "--save-name", "-s", help="BC weights save name", default="saved_testing"
)

parser.add_argument("--traj-name", "-t", help="Run name", default="saved_testing")


parser.add_argument(
    "--seed", type=int, help="random seed to generate the environment with", default=1
)

parser.add_argument(
    "--nepochs", type=int, help="number of epochs to train till", default=50
)

parser.add_argument(
    "--flat",
    "-f",
    default=False,
    help="Partially Observable FlatObs or Fully Observable Image ",
    action="store_true",
)

parser.add_argument(
    "--vis-trained",
    default=False,
    help="Render 10 traj of trained BC",
    action="store_true",
)

args = parser.parse_args()

save_path = "./logs/" + args.env + "/gail/" + args.run + "/"
os.makedirs(save_path, exist_ok=True)
traj_dataset_path = "./traj_datasets/" + args.traj_name + ".pkl"

print(f"Expert Dataset: {args.traj_name}")


with open(traj_dataset_path, "rb") as f:
    trajectories = pickle.load(f)

transitions = rollout.flatten_trajectories(trajectories)


train_env =  minigrid_get_env(args.env, 1, args.flat)

policy_type = ActorCriticPolicy if args.flat else ActorCriticCnnPolicy

base_ppo = PPO(policy_type, train_env, verbose=1, batch_size=32, n_steps=50)

logger.configure(save_path)

gail_trainer = adversarial.WGAIL(
    train_env,
    expert_data=transitions,
    expert_batch_size=32,
    gen_algo=base_ppo,
    n_disc_updates_per_round=1,
    normalize_reward=False,
    normalize_obs=False
)

total_timesteps = 100000
gail_trainer.train(total_timesteps=total_timesteps)
    # gail_trainer.gen_algo.save("gens/gail_gen_"+str(i))

    # with open('discrims/gail_discrim'+str(i)+'.pkl', 'wb') as handle:
    #     pickle.dump(gail_trainer.discrim, handle, protocol=pickle.HIGHEST_PROTOCOL)



if args.vis_trained:
    for traj in range(10):
        obs = train_env.reset()
        train_env.render()
        for i in range(20):
            action, _ = gail_trainer.gen_algo.predict(obs, deterministic=True)
            obs, reward, done, info = train_env.step(action)
            train_env.render()
            if done:
                break
        print("done")
