import random

class BlackjackEnviron:
    def __init__(self, start_bankroll = 100, num_decks=6, num_when_to_shuffle=75):
        self.num_decks = num_decks
        self.num_when_to_shuffle = num_when_to_shuffle
        self.deck = self.create_deck()
        self.player_hand = []
        self.dealer_hand = []
        self.bankroll = start_bankroll
        self.current_bet = 0
        # can add splitting, doubling down, insurance later
        self.actions = ['hit', 'stand'] 
        self.game_over = False
        self.deck = self.create_deck()
        self.start_game()

    def place_bet(self, bet):
        if bet < 1: # betting minimum of 1
            raise ValueError("Minimum bet is 1")
        if bet > self.bankroll:
            raise ValueError("Not enough chips")
        self.current_bet = bet
        self.bankroll -= bet

    def create_deck(self):
        suits = ['Clubs', 'Diamonds', 'Hearts', 'Spades']
        ranks = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
        shoe = [(rank, suit) for suit in suits for rank in ranks] * self.num_decks
        random.shuffle(shoe)
        return shoe

    def needs_shuffle(self):
        return len(self.deck) <= self.num_when_to_shuffle

    def deal_card(self):
        if self.needs_shuffle():
            self.deck = self.create_deck()
        return self.deck.pop()

    def start_game(self):
        self.game_over = False
        self.player_hand = [self.deal_card(), self.deal_card()]
        self.dealer_hand = [self.deal_card(), self.deal_card()]
        return self._get_state()

    def _get_state(self):
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

    # calculates hand value, accounting for aces
    def calculate_hand_value(self, hand):
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
        if not self.game_over:
            self.player_hand.append(self.deal_card())
            if self.calculate_hand_value(self.player_hand)[0] > 21:
                self.game_over = True

    def dealer_play(self):
      while True:
          value = self.calculate_hand_value(self.dealer_hand)[0]
          soft17 = value == 17 and any(rank == 'A' for rank, _ in self.dealer_hand)
          if value < 17 or soft17:
              self.dealer_hand.append(self.deal_card())
          else:
              break

    # returns amount won/lost
    def check_winner(self):
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