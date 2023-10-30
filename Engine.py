import numpy as np
import tensorflow as tf

class Engine:
    def __init__(self,Env,Agent):
        self.Env = Env
        self.Agent = Agent

    def run(self,init_state, explore_prob, limit = 1000):
        """
        Run a simulation through the environment

        Parameters
        ----------
            init_state: The starting location of the agent
            explore_prob: The probability of the agent choosing a random move
            limit = 1000: The limit of steps the agent can take to prevent infinite loop

        Returns
        -------
            A tuple (states,actions,next_states,rewards,dones)

            states: All states agent traversed
            actions: The actions the agent made at each state
            rewards: Reward received by agent at each step
            dones: Boolean array
        """
        # Initialize data arrays
        states,actions,next_states,rewards,dones = ([],[],[],[],[])
        state = init_state
        done = False

        # Main loop to move through environment
        while not done:
            # Get action
            if np.random.rand() < explore_prob: action = np.random.randint(9)
            else: action = int(self.Agent.get_action([state]))

            # Step
            states.append(state)
            actions.append(action)
            _,_,state,reward,done = self.Env.step(state,action)
            next_states.append(state)
            rewards.append(reward)
            dones.append(done)

            # Infinite Loop check
            if limit == 0: break
            limit -= 1

        states.append(state)
        states = np.array(states)
        actions = np.array(actions)
        rewards = np.array(rewards)
        dones = np.array(dones)

        return states, actions, rewards, dones

    def train(self,explore_prob, limit = 1000, batch_size = 1000, trials = 10):
        """
        Train Neural Net on Linear Runs

        Parameters
        ----------
            explore_prob: The probability of the agent choosing a random move
            limit = 1000: The limit of steps the agent can take to prevent infinite loop
            batch_size: Size of each batch in the NN
            trials: Number of trials such that batch_size x trials = training points
        Returns
        -------
            A dictionary holding three arrays

            reward: array holding the reward of each state-action pair
            actor_loss: array holding the total loss of each epoch for the actor NN
            critic_loss: array holding the total loss of each epoch for the critic NN
        """
        # Initialize Metrics
        with open("train_NN.txt","w") as file: file.write("")
        metrics = {'reward':[],'actor_loss':[],'critic_loss':[]}
        lim = limit
        init_states = self.Env.valid_states()
        num_states = len(init_states)

        # Main loop for each trial
        for t in range(trials):

            # Initialize Parameters to train NN
            states = np.zeros([batch_size,4])
            next_states = np.zeros([batch_size,4])
            actions = np.zeros([batch_size,9])
            rewards = np.zeros(batch_size)
            dones = np.zeros(batch_size).astype(bool)

            done = True
            # Main loop to train NN
            for i in range(batch_size):
                # If done get new state
                if done: state = init_states[np.random.randint(num_states)]

                # Get action
                if np.random.rand() < explore_prob:
                    action = np.random.randint(9)
                    probs = np.zeros(9)
                    probs[action] = 1
                else:
                    probs,action = self.Agent.get_action_probs([state])
                    probs = probs[0]
                    action = int(action)

                # Step
                states[i] = state
                actions[i] = probs
                _,_,state,reward,done = self.Env.step(state,action)
                next_states[i] = state
                rewards[i] = reward
                dones[i] = done

                # Infinite loop protection
                if lim == 0:
                    done = True
                    lim = limit
                lim -= 1

            # Finalize Metrics and Update NN
            al,cl = self.Agent.update(states, actions, next_states, rewards, dones)
            metrics['reward'].append(np.sum(rewards)/(np.sum(dones)+1))
            metrics['actor_loss'].append(al)
            metrics['critic_loss'].append(cl)
            # Write progress to file
            with open("train_NN.txt","a") as file:
                file.write(f"Epoch: {t}, Avg Reward:{round(np.sum(rewards)/(np.sum(dones)+1),2)}, Actor Loss:{al}, Critic Loss:{cl}\n")

        return metrics


    def train_vec(self, batch_size, trials):
        """
        Train Neural Net on Random Runs to maximize exploration

        Parameters
        ----------
            batch_size: Size of each batch in the NN
            trials: Number of trials such that batch_size x trials = training points

        Returns
        -------
        A dictionary holding three arrays
            reward: array holding the reward of each state-action pair
            actor_loss: array holding the total loss of each epoch for the actor NN
            critic_loss: array holding the total loss of each epoch for the critic NN
        """
        # Initialize metrics
        with open("train_vec_NN.txt","w") as file: file.write("")
        metrics = {'reward':[],'actor_loss':[],'critic_loss':[]}
        states = self.Env.valid_states()
        num_states = len(states)

        # Main loop to create each batch
        for t in range(trials):
            # Get data
            states = states[np.random.randint(num_states,size=batch_size)]
            probs = np.zeros([batch_size,9])
            actions = np.random.randint(9,size=batch_size)
            probs[np.arange(batch_size),actions] = 1
            _,_,next_states,rewards,dones = self.Env.step_vec(states,actions)

            # Update NN and metrics
            al,cl = self.Agent.update(states, probs, next_states, rewards, dones)
            metrics['reward'].append(np.sum(rewards)/(np.sum(dones)+1))
            metrics['actor_loss'].append(al)
            metrics['critic_loss'].append(cl)
            with open("train_vec_NN.txt","a") as file:
                file.write(f"Epoch: {t}, Avg Reward:{round(np.sum(rewards)/(np.sum(dones)+1),2)}, Actor Loss:{al}, Critic Loss:{cl}\n")

        return metrics
