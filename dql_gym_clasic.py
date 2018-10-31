import gym
import random
from collections import deque
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense
from tensorflow.keras.optimizers import Adam
from tqdm import tqdm
import numpy as np

episodes = 10000
episode_length = 400

n_states = 50
n_actions = 3

class DQNAgent:
    def __init__(self, env):
        self.env = env
        self.memory = deque(maxlen=2000)
        self.gama = 0.95 # discount rate
        self.eps = 0.2 # exploration rate
        self.eps_min = 0.01 # minimum exploration rate
        self.eps_decay = 0.997 # exploration decay
        self.learning_rate = 0.001
        self.model = self.build_model()
        self.state_space = self.env.observation_space.shape[0]

    def build_model(self):
        model = Sequential()
        model.add(Dense(24, input_dim=self.env.observation_space.shape[0], activation='relu'))
        model.add(Dense(32, activation='relu'))
        model.add(Dense(32, activation='relu'))
        model.add(Dense(16, activation='relu'))
        model.add(Dense(self.env.action_space.n, activation='linear'))
        model.compile(optimizer=Adam(lr=self.learning_rate), loss='mse')

        return model

    def remember(self, state, action, reward, next_state, done):
        self.memory.append((state, action, reward, next_state, done))

    def act(self, state):
        if np.random.rand() <= self.eps:
            return np.random.choice(self.env.action_space.n)

        act_values = self.model.predict(state)
        return np.argmax(act_values)

    def replay(self, batch_size=16):
        try:
            mini_batch = random.sample(self.memory, batch_size)
        except:
            return

        for state, action, reward, next_state, done in mini_batch:
            target = reward
            if not done:
                target = reward + self.gama * np.amax(self.model.predict(next_state)[0])
            target_f = self.model.predict(state)
            target_f[0][action] = target
            self.model.fit(state, target_f, epochs=1, verbose=0)

        self.eps = max(self.eps*self.eps_decay, self.eps_min)

    def show_result(self):
        self.env.reset()
        state = self.env.reset().reshape(1, self.state_space)
        done = False
        while not done:
            action = self.act(state)
            state, reward, done, _= self.env.step(action)
            state = state.reshape(1, self.state_space)
            self.env.render()

def obs_to_state(env, obs):
    """ Maps an observation to state """
    env_low = env.observation_space.low
    env_high = env.observation_space.high
    env_dx = (env_high - env_low) / n_states
    a = int((obs[0] - env_low[0])/env_dx[0])
    b = int((obs[1] - env_low[1])/env_dx[1])
    return a, b


if __name__ == "__main__":
    env_name = 'CartPole-v1' # 'MountainCar-v0'
    env = gym.make(env_name)
    env._max_episode_steps = episode_length
    agent = DQNAgent(env)
    state_size = env.observation_space.shape[0]

    for e in range(episodes):
        state = env.reset().reshape(1, state_size)
        for step in range(episode_length):
            action = agent.act(state)

            next_state, reward, done, _= env.step(action)
            # reward -= 0.01
            next_state = next_state.reshape(1, state_size)
            agent.remember(state, action, reward, next_state, done)

            state = next_state

            if done:
                print("Episode: {}/{}, steps: {}, score: {}".format(e, episodes, step, reward))
                # if reward == 0 and step < 200:
                #     agent.show_result()
                break

        agent.replay(32)
        if (e > 0) and (e % 200) == 0:
            agent.show_result()
