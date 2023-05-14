import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
import gym
import random
from collections import deque
from torch import Tensor
import os
from tqdm import tqdm
import buildEnv
import math
total_rewards = []


class replay_buffer():
    '''
    A deque storing trajectories
    '''
    def __init__(self, capacity):
        self.capacity = capacity  # the size of the replay buffer
        self.memory = deque(maxlen=capacity)  # replay buffer itself

    def insert(self, state, action, reward, next_state, done):
        '''
        Insert a sequence of data gotten by the agent into the replay buffer.
        Parameter:
            state: the current state
            action: the action done by the agent
            reward: the reward agent got
            next_state: the next state
            done: the status showing whether the episode finish        
        Return:
            None
        '''
        self.memory.append([state.reshape(48), action, reward, next_state.reshape(48), done])

    def sample(self, batch_size):
        '''
        Sample a batch size of data from the replay buffer.
        Parameter:
            batch_size: the number of samples which will be propagated through the neural network
        Returns:
            observations: a batch size of states stored in the replay buffer
            actions: a batch size of actions stored in the replay buffer
            rewards: a batch size of rewards stored in the replay buffer
            next_observations: a batch size of "next_state"s stored in the replay buffer
            done: a batch size of done stored in the replay buffer
        '''
        batch = random.sample(self.memory, batch_size)
        observations, actions, rewards, next_observations, done = zip(*batch)
        return observations, actions, rewards, next_observations, done

    def __len__(self):
        return len(self.memory)


class Net(nn.Module):
    '''
    The structure of the Neural Network calculating Q values of each state.
    '''
    def __init__(self,  num_actions, hidden_layer_size=600):
        super(Net, self).__init__()
        self.input_state = 48  # the dimension of state space
        self.num_actions = num_actions  # the dimension of action space
        self.fc1 = nn.Linear(self.input_state, 32*12)  # input layer
        self.fc2 = nn.Linear(32*12, hidden_layer_size)  # hidden layer
        self.fc3 = nn.Linear(hidden_layer_size, hidden_layer_size)
        self.fc4 = nn.Linear(hidden_layer_size, num_actions)  # output layer

    def forward(self, states):
        '''
        Forward the state to the neural network.        
        Parameter:
            states: a batch size of states
        Return:
            q_values: a batch size of q_values
        '''
        x = F.relu(self.fc1(states))
        x = F.relu(self.fc2(x))
        x = self.fc3(x)
        q_values = self.fc4(x)
        return q_values


class Agent():
    def __init__(self, env, epsilon=0, learning_rate=0.0002, GAMMA=0.7, batch_size=32, capacity=10000):
        """
        The agent learning how to control the action of the cart pole.
        Hyperparameters:
            epsilon: Determines the explore/expliot rate of the agent
            learning_rate: Determines the step size while moving toward a minimum of a loss function
            GAMMA: the discount factor (tradeoff between immediate rewards and future rewards)
            batch_size: the number of samples which will be propagated through the neural network
            capacity: the size of the replay buffer/memory
        """
        self.env = env
        self.n_actions = 2  # the number of actions
        self.count = 0

        self.epsilon = epsilon
        self.learning_rate = learning_rate
        self.gamma = GAMMA
        self.batch_size = batch_size
        self.capacity = capacity

        self.buffer = replay_buffer(self.capacity)
        self.evaluate_net = Net(self.n_actions)  # the evaluate network
        self.target_net = Net(self.n_actions)  # the target network
        self.optimizer = torch.optim.Adam(
            self.evaluate_net.parameters(), lr=self.learning_rate)  # Adam is a method using to optimize the neural network

    def learn(self, state, next_state, reward, done, action):
        '''
        - Implement the learning function.
        - Here are the hints to implement.
        Steps:
        -----
        1. Update target net by current net every 100 times. (we have done this for you)
        2. Sample trajectories of batch size from the replay buffer.
        3. Forward the data to the evaluate net and the target net.
        4. Compute the loss with MSE.
        5. Zero-out the gradients.
        6. Backpropagation.
        7. Optimize the loss function.
        -----
        Parameters:
            self: the agent itself.
            (Don't pass additional parameters to the function.)
            (All you need have been initialized in the constructor.)
        Returns:
            None (Don't need to return anything)
        '''
        if self.count % 5 == 0:
            self.target_net.load_state_dict(self.evaluate_net.state_dict())

        # Begin your code
        # TODO
        # Step2: Sample the data stored in the buffer and store them into data type Tensor 
        state = torch.tensor(np.array(state.reshape(48)), dtype=torch.float)
        action = torch.tensor(np.array(action), dtype=torch.int64).unsqueeze(-1)
        #print(action.shape)
        reward = torch.tensor(np.array(reward), dtype=torch.float)
        next_state = torch.tensor(np.array(next_state.reshape(48)), dtype=torch.float)
        done = torch.tensor(np.array(done), dtype=torch.float)
        #print(state.shape)
        # Step3: Forward the data to the evaluate net and the target net with a few adjustment of the size
        q_value = self.evaluate_net(state)[action]
        #print(q_value.shape)
        next_action = torch.argmax(self.evaluate_net(next_state)).unsqueeze(-1)
        next_q_value = self.target_net(next_state)[next_action]
        #next_q_value = torch.tensor(next_q_values, dtype = torch.float)
        #print(type(next_action))
        #print(next_action.shape)
        target_q_value = (reward + self.gamma * (1 - done) * next_q_value)
        #print(target_q_values.shape)
        # Step4: Compute the loss with MSE.
        loss = F.mse_loss(q_value, target_q_value)
        
        # Step5: Zero-out the gradients.
        self.optimizer.zero_grad()

        # Step6: Backpropagation.
        loss.backward()
        
        # Step7: Optimize the loss function.
        self.optimizer.step()

        # End your code
        try:
            torch.save(self.target_net.state_dict(), "./Tables/DDQN.pt")
        except RuntimeError:
            print("!")


    def choose_action(self, state):

        with torch.no_grad():
            # Begin your code
            # TODO
            if np.random.random() < math.exp(-self.epsilon):
                #print(math.exp(-self.epsilon))
                return np.random.randint(self.n_actions)
            # forward the state to nn and find the argmax of the actions
            
            action = torch.argmax(self.evaluate_net(Tensor(state).reshape(48))).item()
            #print(action) 
            # End your code
        return action


def train(env):
    """
    Train the agent on the given environment.
    Paramenters:
        env: the given environment.
    Returns:
        None (Don't need to return anything)
    """
    agent = Agent(env)
    episode = 1000
    rewards = []
    for _ in tqdm(range(episode)):
        state = env.reset()
        #print(state)
        count0 = 0
        count1 = 0
        while True:
            agent.count += 1
            action = agent.choose_action(state)
            next_state, reward, done, _ = env.step(action)
            #print(reward)
            #agent.buffer.insert(state, int(action), reward, next_state, int(done))
            #if len(agent.buffer) >= 100:
            #env.render()
            if(action == 0):
                count0+=1
            else:
                count1+=1
            agent.learn(state, next_state, reward, done, action)

            if done:
                rewards.append(env._total_reward)
                print("!")
                print(env._total_reward)
                print(env._total_profit)
                print(count0)
                print(count1)
                
                break
            state = next_state
        agent.epsilon += 0.5
    total_rewards.append(rewards)


def test(env):
    """
    Test the agent on the given environment.
    Paramenters:
        env: the given environment.
    Returns:
        None (Don't need to return anything)
    """
    rewards = []
    testing_agent = Agent(env)
    testing_agent.target_net.load_state_dict(torch.load("./Tables/DDQN.pt"))
    for _ in range(30):
        state = env.reset().reshape(48)
        reward = 0
        while True:
            Q = testing_agent.target_net(
                torch.FloatTensor(state)).squeeze(0).detach()
            action = int(torch.argmax(Q).numpy())
            next_state, temp, done, _ = env.step(action)
            reward = reward + temp
            if done:
                rewards.append(reward)
                break
            state = next_state.reshape(48)

    print(f"reward: {np.mean(rewards)}")
    print(env.max_possible_profit())


if __name__ == "__main__":
    env = buildEnv.createEnv(2330)        
    os.makedirs("./Tables", exist_ok=True)

    # training section:
    for i in range(5):
        print(f"#{i + 1} training progress")
        train(env)
        
    # testing section:
    test(env)
    env.close()

    os.makedirs("./Rewards", exist_ok=True)
    np.save("./Rewards/DDQN_rewards.npy", np.array(total_rewards))
