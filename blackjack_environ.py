import random

class BlackjackEnviron:
    def __init__(self, start_bankroll = 100, num_decks=6, num_when_to_shuffle=75):
        """
        Initializes the Blackjack environment (creates deck, starts game).
        
        Args:
            start_bankroll: Beginning amount of money/chips to work with.
            num_decks: Number of decks to use in the shoe.
            num_when_to_shuffle: Number of cards to deal before shuffling.
        """
        self.num_decks = num_decks
        self.num_when_to_shuffle = num_when_to_shuffle
        self.deck = self.create_deck()
        self.player_hand = []
        self.dealer_hand = []
        self.bankroll = start_bankroll
        self.current_bet = 0
        self.actions = ['hit', 'stand'] # can add splitting, doubling down, insurance later
        self.game_over = False
        self.deck = self.create_deck()
        self.start_game()

    def place_bet(self, bet):
        """
        Places bet for the current round. Minimum bet is 1.
        
        Args:
            bet: Bet amount to place.
        """
        if bet < 1: # betting minimum of 1
            raise ValueError("Minimum bet is 1")
        if bet > self.bankroll:
            raise ValueError("Not enough chips")
        self.current_bet = bet
        self.bankroll -= bet

    def create_deck(self):
        """
        Creates and shuffles a shoe of cards based on the number of decks of the Blackjack instance.
        """
        suits = ['Clubs', 'Diamonds', 'Hearts', 'Spades']
        ranks = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
        shoe = [(rank, suit) for suit in suits for rank in ranks] * self.num_decks
        random.shuffle(shoe)
        return shoe

    def needs_shuffle(self):
        """
        Checks if the deck needs to be shuffled based on the number of remaining cards,
        and the threshold set for shuffling.
        """
        return len(self.deck) <= self.num_when_to_shuffle

    def deal_card(self):
        """
        Picks the top card from the deck, shuffling if necessary.
        Returns: a tuple representing the selected card (rank, suit).
        """
        if self.needs_shuffle():
            self.deck = self.create_deck()
        return self.deck.pop()

    def start_game(self):
        """
        Starts a new round of Blackjack, dealing two cards each to player and dealer.
        Returns: the initial state (player total, dealer upcard, usable ace).
        """
        self.game_over = False
        self.player_hand = [self.deal_card(), self.deal_card()]
        self.dealer_hand = [self.deal_card(), self.deal_card()]
        return self._get_state()

    def _get_state(self):
        """
        Gets the current state of the game.
        Returns: the current state as a tuple: (player total, dealer upcard value, usable ace).
        """
        player_total, usable_ace = self.calculate_hand_value(self.player_hand)

        # Dealer upcard value
        dealer_upcard_rank, _ = self.dealer_hand[0]
        if dealer_upcard_rank in ['J', 'Q', 'K']:
            dealer_upcard_value = 10
        elif dealer_upcard_rank == 'A':
            dealer_upcard_value = 11
        else:
            dealer_upcard_value = int(dealer_upcard_rank)
        return (player_total, dealer_upcard_value, usable_ace)

    # 
    def calculate_hand_value(self, hand):
        """
        Calculates hand value, accounting for aces.
        Adjusts ace value from 11 to 1 if busting.
        Args: 
            hand: list of tuples representing the hand (rank, suit).
        Returns: total value of the hand, whether a usable ace is present.
        """
        total = 0
        aces = 0
        for rank, _ in hand:
            if rank in ['J', 'Q', 'K']:
                total += 10
            elif rank == 'A':
                aces += 1
                total += 11
            else:
                total += int(rank)
        # Adjust ace if bust
        while total > 21 and aces:
            total -= 10
            aces -= 1

        usable_ace = aces > 0 and total <= 21
        return total, usable_ace

    def player_hit(self):
        """
        Player takes a hit (draws a card). Updates game over status if bust.
        """
        if not self.game_over:
            self.player_hand.append(self.deal_card())
            if self.calculate_hand_value(self.player_hand)[0] > 21:
                self.game_over = True

    def dealer_play(self):
      """
      Dealer plays according to standard rules: hits until reaching 17 or higher.
      Hits on soft 17.
      """
      while True:
          value = self.calculate_hand_value(self.dealer_hand)[0]
          soft17 = value == 17 and any(rank == 'A' for rank, _ in self.dealer_hand)
          if value < 17 or soft17:
              self.dealer_hand.append(self.deal_card())
          else:
              break

    def check_winner(self):
        """
        Determines the winner of the round and calculates amount won/lost.
        Returns: outcome message, payout amount.
        """
        player_value = self.calculate_hand_value(self.player_hand)[0]
        dealer_value = self.calculate_hand_value(self.dealer_hand)[0]

        player_blackjack = (len(self.player_hand) == 2 and player_value == 21)
        dealer_blackjack = (len(self.dealer_hand) == 2 and dealer_value == 21)

        if player_blackjack and dealer_blackjack:
            return "It's a tie with blackjacks! (Push)", 0
        elif player_blackjack:
            return "Player wins with a blackjack! (Payout 1.5 bet)", 1.5 * self.current_bet
        elif player_value == dealer_value:
            return "It's a tie! (Push)", 0
        elif dealer_blackjack:
            return "Dealer wins with a blackjack! (Dealer takes bet)", -self.current_bet
        if player_value > 21:
            return "Dealer wins!", -self.current_bet
        elif dealer_value > 21 or player_value > dealer_value:
            return "Player wins!", self.current_bet
        elif player_value < dealer_value:
            return "Dealer wins!", -self.current_bet
        
    # currenly only supports hit or stand
    def step(self, action):
      """
      Takes an action ('hit' or 'stand') and updates the game state.
      Args: 
        action: action to take ('hit' or 'stand') at a certain state.
      Returns: tuple of (new state, reward, gameover status).
      """
      if action == "hit":
          self.player_hand.append(self.deal_card())
          player_total, _ = self.calculate_hand_value(self.player_hand)
          if player_total > 21:
              self.game_over = True
              return self._get_state(), -self.current_bet, True
          return self._get_state(), 0, False
      elif action == "stand":
          self.dealer_play()
          outcome, reward = self.check_winner()
          self.bankroll += reward
          self.game_over = True
          return self._get_state(), reward, True

      else:
          raise ValueError("Invalid action")