import numpy as np
import blackjack_environ
import matplotlib.pyplot as plt
import seaborn as sns

def main():
    alpha = 0.08 # learning rate
    gamma = 0.95 # discount factor
    epsilon = 1.0 # exploration rate (decays over time)
    episodes = 50000 # number of training episodes
    bankroll = 100  # initial bankroll for betting
    Q, state_visits, diffs, win_amt, total_return, accuracies, checkpoint_Qs, checkpoint_episodes = train(alpha, gamma, epsilon, episodes, bankroll)
    #understanding_q(Q, state_visits)
    eval(win_amt, total_return, episodes)
    #eval_accuracy(accuracies, episodes=2500)
    plot_policy_and_agreement(Q, title_suffix='final', savepath='policy_final.png')
    plot_evolution(checkpoint_Qs, checkpoint_episodes, ncols=3, save_prefix='policy_evo')

def train(alpha=0.1, gamma=0.9, epsilon=1.0, episodes=50000, bankroll=100):
    # create Q-table
    Q = {}
    environment = blackjack_environ.BlackjackEnviron(start_bankroll=bankroll)
    diffs = []
    prev = 0
    win_amt = 0
    total_return = 0
    state_visits = {}
    accuracies = []
    checkpoint_Qs = []
    checkpoint_episodes = []

    for epi in range(episodes):
        # check accuracy every 2500 episodes
        if (epi+1) % 2500 == 0:
            print("Checking accuracy at episode ", epi+1)
            check_accuracy(Q, accuracies, episodes=2500, bankroll=environment.bankroll)
            checkpoint_Qs.append({k: v.copy() for k, v in Q.items()})
            checkpoint_episodes.append(epi+1)

        bet = 1 # standard bet
        environment.place_bet(bet)

        state = environment.start_game()
        done = False
        total_reward = 0

        while not done:
            state_key = make_state_key(state) #unsuring proper format
            # Q-value update
            if state_key not in Q:
                Q[state_key] = {a: 1 for a in environment.actions} # optimistic initial values

            # epsilon-greedy action selection
            if np.random.rand() < epsilon:
                action = np.random.choice(environment.actions)
            else:
                action = max(Q[state_key], key=Q[state_key].get)
            next_state, reward, done = environment.step(action)
            total_reward += reward

            # updating state tracking
            if state not in state_visits:
                state_visits[state] = 0
            state_visits[state] += 1

            # prepare next state key
            if not done: # if not ending round
                next_key = make_state_key(next_state)
                if next_key not in Q:
                    Q[next_key] = {a: 1.0 for a in environment.actions} # optimistic initial values

            if done:
                target = reward # TD update for terminal state
            else:
                target = reward + gamma * max(Q[next_key].values()) # non-terminal state
            Q[state_key][action] += alpha * (target - Q[state_key][action])

            state = next_state

        win_amt += 1 if total_reward > 0 else 0
        total_return += total_reward

        player_total, _ = environment.calculate_hand_value(environment.player_hand)
        dealer_total, _ = environment.calculate_hand_value(environment.dealer_hand)
        if (epi + 1) % 900 == 0:
            print(f"Episode {epi+1} ended. Player total: {player_total}, Dealer total: {dealer_total}, Reward: {total_reward}")

        # Phased decay epsilon
        if epi <= .1*episodes:
            rate = np.exp(np.log(0.1/1)/(.1*episodes)) # go from 1 to 0.1 in first 10%      
        else:
            rate = np.exp(np.log(0.01/0.1)/(.9*episodes)) # go from 0.1 to 0.01 in rest of time
        epsilon = max(0.01, epsilon * rate)

        # replenish bankroll for training purposes
        if environment.bankroll <= 10:
            now = epi
            environment.bankroll += 100
            diffs.append(now-prev)
            prev = now

    return Q, state_visits, diffs, win_amt, total_return, accuracies, checkpoint_Qs, checkpoint_episodes

# comparing against random choice
def random_agent():
    environment = blackjack_environ.BlackjackEnviron()
    diffs_rand = []
    prev_rand = 0
    episodes = 50000 # number of training episodes

    for epi in range(episodes):
        
        print(f"Episode {epi + 1}, Bankroll: {environment.bankroll}, Random Agent")

        bet = 1 # standard bet
        environment.place_bet(bet)

        state = environment.start_game()
        done = False

        while not done:
            #random action
            action = np.random.choice(environment.actions)

            next_state, reward, done = environment.step(action)

            state = next_state

        player_total, _ = environment.calculate_hand_value(environment.player_hand)
        dealer_total, _ = environment.calculate_hand_value(environment.dealer_hand)
        print(f"Episode {epi} ended. Player total: {player_total}, Dealer total: {dealer_total}, Reward: {reward}")

        # replenish bankroll for testing purposes
        if environment.bankroll <= 10:
            now_rand = epi
            print("Replenishing bankroll + 100.")
            environment.bankroll += 100
            diffs_rand.append(now_rand-prev_rand)
            prev_rand = now_rand
    return diffs_rand

# returns 'hit' or 'stand' based on basic blackjack strategy
def basic_strategy_action(player_sum, dealer_upcard, usable_ace):
    # Hard totals
    if not usable_ace:
        if player_sum >= 17:
            return 'stand'
        if 13 <= player_sum <= 16:
            if 2 <= dealer_upcard <= 6:
                return 'stand'
            else:
                return 'hit'
        if player_sum == 12:
            if 4 <= dealer_upcard <= 6:
                return 'stand'
            else:
                return 'hit'
        # 11 or less
        return 'hit'
    # Soft totals (usable ace)
    else:
        if player_sum >= 19:
            return 'stand'
        if player_sum == 18:
            if 2 <= dealer_upcard <= 8:
                return 'stand'
            else:
                return 'hit'
        # soft 17 or less: hit
        return 'hit'

# standarizes state format for keys in Q table
def make_state_key(state):
    return (state[0], state[1], state[2])  # player total, dealer upcard, usable ace

# with epsilon at 0 and no learning, we check how often the agent wins
def check_accuracy(Q, accuracies,episodes=1000, bankroll=100):
    environment_test = blackjack_environ.BlackjackEnviron(start_bankroll=bankroll)
    correct = 0
    bet = 1
    for _ in range(episodes):
        environment_test.place_bet(bet)
        state = environment_test.start_game()
        done = False
        while not done:
            if state in Q:
                action = max(Q[state], key=Q[state].get)
                #print("Action chosen: ", action)
            else:
                action = np.random.choice(environment_test.actions)
            next_state, reward, done = environment_test.step(action)
            state = next_state
        if reward > 0:
            correct += 1
        # replenish bankroll for testing purposes
        if environment_test.bankroll <= 10:
            environment_test.bankroll += 100
    accuracy = correct / episodes
    accuracies.append(accuracy)
    print(f"Accuracy over {episodes} episodes: {accuracy}")
    return accuracy

# returns win rate and average return per hand
def eval(win_amt, total_return, episodes):
    print("Win rate: ", win_amt / episodes)
    print("Average return per hand: ", total_return / episodes)

# Plotting how long it takes for a bankroll replenishment over episodes
def eval_replenish(diffs, diffs_rand=None):
    plt.plot(range(len(diffs)), np.array(diffs), label='Q-Agent')
    if diffs_rand:
        plt.plot(range(len(diffs)), np.array(diffs_rand[:len(diffs)]), label='Random Agent')
    plt.xlabel('Number of Replenishments')
    plt.ylabel('Episodes Since Last Replenishment')
    plt.title('Episodes Since Last Replenishment (Blackjack)')
    plt.show()

# a plot of accuracy over time (evaluated on epsilon = 0 every some amount of episodes)
def eval_accuracy(accuracies, accuracies_rand=None, episodes=1000):
    # Plotting accuracy every 1000 episodes
    plt.plot(range(len(accuracies)), np.array(accuracies), label='Q-Agent')
    if accuracies_rand:
        plt.plot(range(len(accuracies_rand)), np.array(accuracies_rand), label='Random Agent')
    plt.xlabel(f'Trial (every {episodes} episodes)')
    plt.ylabel('Accuracy')
    plt.title('Accuracy (Blackjack)')
    plt.show()

# a similar printout of q table strategy for analysis
def understanding_q(Q, state_visits):
    strategy = {}
    for state, actions in sorted(Q.items()):
        # Choose the action with the highest Q-value for each state
        optimal_action = max(actions, key=actions.get)
        strategy[state] = optimal_action
        print(f"State {state}: {optimal_action} with Q-values {actions}, visited {state_visits.get(state)} times")

# useful for determining how much exploration is needed
def analyze_state_visits(state_visits):
    for state, count in state_visits.items():
        if count < 50:
            print(f"Underexplored state: {state} with {count} visits")

# takes in Q-table and converts to grids for plotting
def q_to_grids(Q, actions=None):
    if actions is None:
        actions = ['hit', 'stand']
    # rows = player total, cols = dealer upcard
    player_range = range(5, 22)
    dealer_range = range(1, 12)

    # set for no usable ace (hard)
    pref_hard = np.full((len(player_range), len(dealer_range)), np.nan)
    qdiff_hard = np.full_like(pref_hard, np.nan, dtype=float)
    covered_hard = np.zeros_like(pref_hard, dtype=bool)
    # set for usable ace (soft)
    pref_soft = np.full((len(player_range), len(dealer_range)), np.nan)
    qdiff_soft = np.full_like(pref_soft, np.nan, dtype=float)
    covered_soft = np.zeros_like(pref_soft, dtype=bool)

    # iterate over possible num_cards values that might exist in Q
    # we aggregate by taking the most visited or the max-value across num_cards
    for i, p in enumerate(player_range):
        for j, d in enumerate(dealer_range):
            hit_vals_hard = []
            stand_vals_hard = []
            hit_vals_soft = []
            stand_vals_soft = []

            for key, action_dict in Q.items():
                try:
                    key_player, key_dealer, key_usable = key
                except Exception:
                    continue
                if key_player == p and key_dealer == d:
                    if key_usable:
                        if 'hit' in action_dict and 'stand' in action_dict:
                            hit_vals_soft.append(action_dict['hit'])
                            stand_vals_soft.append(action_dict['stand'])
                    else:
                        if 'hit' in action_dict and 'stand' in action_dict:
                            hit_vals_hard.append(action_dict['hit'])
                            stand_vals_hard.append(action_dict['stand'])

            # choose the action with highest average Q across num_cards
            if hit_vals_hard:
                avg_hit = np.mean(hit_vals_hard)
                avg_stand = np.mean(stand_vals_hard)
                qdiff_hard[i, j] = avg_hit - avg_stand
                pref_hard[i, j] = 1 if avg_hit > avg_stand else 0
                covered_hard[i, j] = True

            if hit_vals_soft:
                avg_hit = np.mean(hit_vals_soft)
                avg_stand = np.mean(stand_vals_soft)
                qdiff_soft[i, j] = avg_hit - avg_stand
                pref_soft[i, j] = 1 if avg_hit > avg_stand else 0
                covered_soft[i, j] = True

    return {
        'player_range': list(player_range),
        'dealer_range': list(dealer_range),
        'pref_hard': pref_hard,
        'qdiff_hard': qdiff_hard,
        'covered_hard': covered_hard,
        'pref_soft': pref_soft,
        'qdiff_soft': qdiff_soft,
        'covered_soft': covered_soft
    }

# plot the heatmap for a given grid
def plot_heatmap(grid, player_range, dealer_range, title, cmap='RdBu_r', vmin=None, vmax=None, mask=None, ax=None, annot=False):
    if ax is None:
        fig, ax = plt.subplots(figsize=(8, 6))
    # rows correspond to player totals, highest player total at top
    grid_plot = np.flipud(grid)  # flip so 21 is on top
    y_labels = list(reversed(player_range))
    x_labels = dealer_range
    sns.heatmap(grid_plot, xticklabels=x_labels, yticklabels=y_labels, cmap=cmap, vmin=vmin, vmax=vmax, mask=mask, ax=ax, annot=annot, fmt='.2f', cbar_kws={'label': title})
    ax.set_xlabel('Dealer upcard')
    ax.set_ylabel('Player total')
    ax.set_title(title)
    return ax

# Check policy against basic strategy and plot results
def plot_policy_and_agreement(Q, title_suffix='', savepath=None):
    grids = q_to_grids(Q)
    pr = grids['player_range']
    dr = grids['dealer_range']

    # preference heatmaps: 1=hit, 0=stand
    pref_hard = grids['pref_hard']
    pref_soft = grids['pref_soft']
    covered_hard = grids['covered_hard']
    covered_soft = grids['covered_soft']

    # compute basic strategy agreement
    agree_hard = np.full_like(pref_hard, np.nan)
    agree_soft = np.full_like(pref_soft, np.nan)
    for i, p in enumerate(pr):
        for j, d in enumerate(dr):
            if covered_hard[i, j]:
                basic_action = basic_strategy_action(p, d, False)
                learned = 'hit' if pref_hard[i, j] == 1 else 'stand'
                agree_hard[i, j] = 1.0 if learned == basic_action else 0.0
            if covered_soft[i, j]:
                basic_action = basic_strategy_action(p, d, True)
                learned = 'hit' if pref_soft[i, j] == 1 else 'stand'
                agree_soft[i, j] = 1.0 if learned == basic_action else 0.0

    # Q-difference heatmaps
    qdiff_hard = grids['qdiff_hard']
    qdiff_soft = grids['qdiff_soft']

    # Plotting heatmaps
    fig, axes = plt.subplots(2, 3, figsize=(18, 10))
    plot_heatmap(pref_hard, pr, dr, f'Policy Hard {title_suffix} (1=Hit,0=Stand)', cmap='coolwarm', vmin=0, vmax=1, mask=~covered_hard, ax=axes[0,0])
    plot_heatmap(qdiff_hard, pr, dr, f'Q_hit - Q_stand Hard {title_suffix}', cmap='RdBu_r', vmin=-2, vmax=2, mask=~covered_hard, ax=axes[0,1])
    plot_heatmap(agree_hard, pr, dr, f'Agreement Hard {title_suffix}', cmap='Greens', vmin=0, vmax=1, mask=~covered_hard, ax=axes[0,2])

    plot_heatmap(pref_soft, pr, dr, f'Policy Soft {title_suffix} (1=Hit,0=Stand)', cmap='coolwarm', vmin=0, vmax=1, mask=~covered_soft, ax=axes[1,0])
    plot_heatmap(qdiff_soft, pr, dr, f'Q_hit - Q_stand Soft {title_suffix}', cmap='RdBu_r', vmin=-2, vmax=2, mask=~covered_soft, ax=axes[1,1])
    plot_heatmap(agree_soft, pr, dr, f'Agreement Soft {title_suffix}', cmap='Greens', vmin=0, vmax=1, mask=~covered_soft, ax=axes[1,2])

    plt.tight_layout()
    if savepath:
        plt.savefig(savepath, dpi=200)
    plt.show()

    # summary stats
    hard_cov_frac = np.nanmean(covered_hard)
    soft_cov_frac = np.nanmean(covered_soft)
    hard_agree = np.nanmean(agree_hard)
    soft_agree = np.nanmean(agree_soft)
    print(f"Coverage hard: {hard_cov_frac:.3f}, soft: {soft_cov_frac:.3f}")
    print(f"Agreement hard: {hard_agree:.3f}, soft: {soft_agree:.3f}")

    return {
        'coverage_hard': hard_cov_frac,
        'coverage_soft': soft_cov_frac,
        'agreement_hard': hard_agree,
        'agreement_soft': soft_agree
    }

# plot across checkpoints given list of Qs
def plot_evolution(checkpoint_Qs, episodes, ncols=3, save_prefix=None):
    n = len(checkpoint_Qs)
    nrows = int(np.ceil(n / ncols))
    fig, axes = plt.subplots(nrows*2, ncols, figsize=(4*ncols, 3*nrows*2))
    axes = axes.reshape(nrows*2, ncols)
    for idx, (Qsnap, epi) in enumerate(zip(checkpoint_Qs, episodes)):
        row = (idx // ncols) * 2 # floor times 2
        col = idx % ncols
        title = f'Episode {epi}'
        grids = q_to_grids(Qsnap)
        pr = grids['player_range']
        dr = grids['dealer_range']
        # policy for hard
        ax1 = axes[row, col]
        plot_heatmap(grids['pref_hard'], pr, dr, f'Hard Policy {title}', mask=~grids['covered_hard'], ax=ax1, cmap='coolwarm', vmin=0, vmax=1)
        # policy for soft
        ax2 = axes[row+1, col]
        plot_heatmap(grids['pref_soft'], pr, dr, f'Soft Policy {title}', mask=~grids['covered_soft'], ax=ax2, cmap='coolwarm', vmin=0, vmax=1)

    if save_prefix:
        plt.savefig(f"{save_prefix}_snapshot_{idx}.png", dpi=200)

    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    main()