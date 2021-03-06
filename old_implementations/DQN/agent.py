import torch
import torch.nn as nn
import torch.nn.functional as F 
import torch.autograd as autograd
import numpy as np
from utils import ReplayBuffer
from model import DQN, CnnDQN


class Agent:

    def __init__(self, env, use_cnn=False, learning_rate=3e-4, gamma=0.99, buffer_size=10000):
        self.env = env
        self.learning_rate = learning_rate
        self.gamma = gamma
        self.replay_buffer = ReplayBuffer(buffer_size)
        self.dqn = CnnDQN(env.observation_space.shape, env.action_space.n) if use_cnn else DQN(env.observation_space.shape[0], env.action_space.n) 
        self.dqn_optimizer = torch.optim.Adam(self.dqn.parameters())
        self.dqn_loss = torch.nn.MSELoss()

    def update_model(self, batch_size):
        states, actions, rewards, next_states, dones = self.replay_buffer.sample(batch_size)
        states = torch.FloatTensor(states)
        actions = torch.LongTensor(actions)
        rewards = torch.FloatTensor(rewards)
        next_states = torch.FloatTensor(next_states)
        dones = torch.FloatTensor(dones)
        
        curr_Q = self.dqn.forward(states)
        curr_Q = curr_Q.gather(1, actions.unsqueeze(1)).squeeze(1)
        next_Q = self.dqn.forward(next_states)
        max_next_Q = torch.max(next_Q, 1)[0]
        expected_Q = rewards.squeeze(1) + self.gamma * max_next_Q 

        self.dqn_optimizer.zero_grad()
        loss = self.dqn_loss(curr_Q, expected_Q)
        loss.backward()
        self.dqn_optimizer.step()
        
        return loss

    def max_action(self, state):
        state = autograd.Variable(torch.from_numpy(state).float().unsqueeze(0))
        qvals = self.dqn.forward(state)
        action = np.argmax(qvals.detach().numpy())
  
        return action
      
    def train(self, max_episodes, max_steps, batch_size):
        episode_rewards = []
        loss = []
        
        for episodes in range(max_episodes):
            state = self.env.reset()  
            episode_reward = 0
            for steps in range(max_steps):
                action = self.max_action(state)
                next_state, reward, done, _ = self.env.step(action)
                self.replay_buffer.push(state, action, reward, next_state, done)
                state = next_state
                episode_reward += reward
                
                if done:
                  episode_rewards.append(episode_reward)
                  print(episode_reward)
                  break
                
                if(len(self.replay_buffer) > batch_size):
                    step_loss = self.update_model(batch_size)
                    loss.append(step_loss)
                    #self.adjust_temperature(loss)
                
        # return episode_rewards, loss
                  
    def run(self, max_episodes, max_steps):
        episode_rewards = []
        for episodes in range(max_episodes):
            state = self.env.reset()  
            episode_reward = 0
            for steps in range(max_steps):
                action = self.max_action(state)
                next_state, reward, done, _ = env.step(action)
                state = next_state
                episode_reward += reward
                  
                if done:
                  episode_rewards.append(episode_reward)
                  break
                  
        return episode_rewards

    def save_model(self, PATH):
        torch.save(self.dqn.state_dict(), PATH)
