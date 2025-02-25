import random
from dataclasses import dataclass, field
from typing import List, Dict, Optional
import time

# Pokemon Card Game Implementation
EVOLUTION_CHAINS = {
    'Charmeleon': 'Charmander',
    'Charizard': 'Charmeleon',
    'Wartortle': 'Squirtle', 
    'Blastoise': 'Wartortle',
    'Ivysaur': 'Bulbasaur',
    'Venusaur': 'Ivysaur',
    'Raichu': 'Pikachu'
}

def can_evolve_from(pokemon_name: str, potential_basic: str) -> bool:
    return EVOLUTION_CHAINS.get(pokemon_name) == potential_basic

@dataclass(frozen=True)  # Make it hashable by setting frozen=True
class PokemonCard:
    name: str
    hp: int
    type: str  # Fire, Water, Grass, Electric, etc.
    attacks: Dict[str, int]  # Attack name -> damage
    weakness: Optional[str] = None
    resistance: Optional[str] = None
    retreat_cost: int = 1
    
    def __str__(self):
        attacks_str = ", ".join([f"{name} ({damage})" for name, damage in self.attacks.items()])
        return f"{self.name} [{self.type}] - HP: {self.hp} - Attacks: {attacks_str}"

@dataclass(frozen=True)  # Make it hashable
class EnergyCard:
    type: str  # Fire, Water, Grass, Electric, etc.
    
    def __str__(self):
        return f"{self.type} Energy"

@dataclass(frozen=True)  # Make it hashable
class TrainerCard:
    name: str
    effect: str
    
    def __str__(self):
        return f"{self.name} - {self.effect}"

Card = PokemonCard | EnergyCard | TrainerCard

# We need a mutable wrapper for PokemonCard since we need to modify HP
class PlayedPokemonCard:
    def __init__(self, card: PokemonCard):
        self.card = card
        self.hp = card.hp
        
    @property
    def name(self):
        return self.card.name
        
    @property
    def type(self):
        return self.card.type
        
    @property
    def attacks(self):
        return self.card.attacks
        
    @property
    def weakness(self):
        return self.card.weakness
        
    @property
    def resistance(self):
        return self.card.resistance
        
    @property
    def retreat_cost(self):
        return self.card.retreat_cost
    
    def __str__(self):
        attacks_str = ", ".join([f"{name} ({damage})" for name, damage in self.card.attacks.items()])
        return f"{self.card.name} [{self.card.type}] - HP: {self.hp} - Attacks: {attacks_str}"

class Player:
    def __init__(self, name: str, deck: List[Card]):
        self.name = name
        self.deck = deck.copy()
        self.hand: List[Card] = []
        self.active_pokemon: Optional[PlayedPokemonCard] = None
        self.bench: List[PlayedPokemonCard] = []
        self.attached_energy: Dict[PlayedPokemonCard, List[EnergyCard]] = {}
        self.discard_pile: List[Card] = []
        self.prize_cards: List[Card] = []
    
    def shuffle_deck(self):
        random.shuffle(self.deck)
    
    def draw_card(self) -> Optional[Card]:
        if not self.deck:
            return None
        card = self.deck.pop(0)
        self.hand.append(card)
        return card
    
    def draw_initial_hand(self):
        self.hand = []
        for _ in range(7):
            self.draw_card()
    
    def setup_prize_cards(self):
        self.prize_cards = []
        for _ in range(6):
            if self.deck:
                self.prize_cards.append(self.deck.pop(0))
    
    def has_basic_pokemon(self) -> bool:
        return any(isinstance(card, PokemonCard) for card in self.hand)
    
    def play_pokemon(self, card_index: int, as_active: bool = False) -> bool:
        if card_index < 0 or card_index >= len(self.hand):
            return False
    
        card = self.hand[card_index]
        if not isinstance(card, PokemonCard):
            return False

        # Evolution check
        if card.name in EVOLUTION_CHAINS:
            basic_name = EVOLUTION_CHAINS[card.name]
            # Check active and bench for the basic form
            valid_evolution = False
            if self.active_pokemon and self.active_pokemon.name == basic_name:
                valid_evolution = True
            for pokemon in self.bench:
                if pokemon.name == basic_name:
                    valid_evolution = True
                    break

            if not valid_evolution:
                print(f"You need {basic_name} in play to evolve into {card.name}")
                return False

        # Create a PlayedPokemonCard wrapper
        played_card = PlayedPokemonCard(card)

        # Play as active if requested and no active Pokemon
        if as_active and self.active_pokemon is None:
            self.active_pokemon = played_card
            self.hand.pop(card_index)
            self.attached_energy[played_card] = []
            return True
        # Play to bench if not full
        elif not as_active and len(self.bench) < 5:
            self.bench.append(played_card)
            self.hand.pop(card_index)
            self.attached_energy[played_card] = []
            return True

        return False
    
    def attach_energy(self, energy_index: int, pokemon_index: int, is_active: bool = False) -> bool:
        if energy_index < 0 or energy_index >= len(self.hand):
            return False
        
        energy_card = self.hand[energy_index]
        if not isinstance(energy_card, EnergyCard):
            return False
        
        target_pokemon = None
        if is_active and self.active_pokemon:
            target_pokemon = self.active_pokemon
        elif not is_active and 0 <= pokemon_index < len(self.bench):
            target_pokemon = self.bench[pokemon_index]
        
        if target_pokemon:
            self.attached_energy[target_pokemon].append(energy_card)
            self.hand.pop(energy_index)
            return True
        
        return False
    
    def count_energy(self, pokemon: PlayedPokemonCard, energy_type: Optional[str] = None) -> int:
        if pokemon not in self.attached_energy:
            return 0
        
        if energy_type:
            return sum(1 for e in self.attached_energy[pokemon] if e.type == energy_type)
        else:
            return len(self.attached_energy[pokemon])
    
    def perform_attack(self, attack_name: str) -> int:
        if not self.active_pokemon:
            return 0
        
        if attack_name not in self.active_pokemon.attacks:
            return 0
        
        # For simplicity, we're not checking energy requirements for attacks
        # In a real implementation, you would check if the Pokemon has enough energy of the right types
        return self.active_pokemon.attacks[attack_name]

    def take_damage(self, damage: int, attacking_type: str) -> bool:
        """Apply damage to active Pokemon. Returns True if knocked out."""
        if not self.active_pokemon:
            return False
        
        # Apply weakness/resistance
        if self.active_pokemon.weakness == attacking_type:
            damage *= 2
        if self.active_pokemon.resistance == attacking_type:
            damage -= 30
            if damage < 0:
                damage = 0
        
        self.active_pokemon.hp -= damage
        
        # Check if knocked out
        if self.active_pokemon.hp <= 0:
            # Move to discard pile
            self.discard_pile.append(self.active_pokemon.card)
            # Also discard attached energy
            self.discard_pile.extend(self.attached_energy[self.active_pokemon])
            del self.attached_energy[self.active_pokemon]
            self.active_pokemon = None
            return True
        
        return False
    
    def take_prize_card(self) -> Optional[Card]:
        if not self.prize_cards:
            return None
        
        card = self.prize_cards.pop(0)
        self.hand.append(card)
        return card
    
    def can_play_trainer(self, card_index: int) -> bool:
        if card_index < 0 or card_index >= len(self.hand):
            return False
        
        return isinstance(self.hand[card_index], TrainerCard)
    
    def promote_from_bench(self, bench_index: int) -> bool:
        if self.active_pokemon is not None:
            return False
        
        if bench_index < 0 or bench_index >= len(self.bench):
            return False
        
        self.active_pokemon = self.bench.pop(bench_index)
        return True


class PokemonGame:
    def __init__(self, player1: Player, player2: Player):
        self.players = [player1, player2]
        self.current_player_idx = 0
        self.turn_count = 0
        self.game_over = False
        self.winner = None
    
    @property
    def current_player(self) -> Player:
        return self.players[self.current_player_idx]
    
    @property
    def opponent(self) -> Player:
        return self.players[1 - self.current_player_idx]
    
    def setup_game(self):
        # Shuffle decks
        for player in self.players:
            player.shuffle_deck()
            player.draw_initial_hand()
            
            # Mulligan if no basic Pokemon
            while not player.has_basic_pokemon():
                print(f"{player.name} has no basic Pokemon! Mulligan!")
                # In real Pokemon TCG, opponent can draw a card for each mulligan
                player.deck.extend(player.hand)
                player.shuffle_deck()
                player.draw_initial_hand()

                player.setup_prize_cards()
    
    def start_game(self):
        self.setup_game()
        
        # Players set up their active Pokemon and bench
        for player in self.players:
            self.setup_player_board(player)
        
        # Randomly determine who goes first
        self.current_player_idx = random.randint(0, 1)
        print(f"{self.current_player.name} goes first!")
        
        # Main game loop
        while not self.game_over:
            self.play_turn()
    
    def setup_player_board(self, player: Player):
        print(f"\n{player.name}, set up your active Pokemon:")
        self.display_hand(player)
        
        valid_choice = False
        while not valid_choice:
            try:
                choice = int(input("Choose a Pokemon card number to play as your active Pokemon: "))
                if player.play_pokemon(choice - 1, as_active=True):
                    valid_choice = True
                    print(f"You played {player.active_pokemon.name} as your active Pokemon.")
                else:
                    print("Invalid choice. Try again.")
            except ValueError:
                print("Please enter a valid number.")
        
        # Set up bench (optional)
        while len(player.bench) < 5:
            if not any(isinstance(card, PokemonCard) for card in player.hand):
                break
                
            self.display_hand(player)
            choice = input("Choose a Pokemon card number to play to your bench (or 'done' to finish): ")
            
            if choice.lower() == 'done':
                break
            
            try:
                card_idx = int(choice) - 1
                if player.play_pokemon(card_idx, as_active=False):
                    print(f"You played {player.bench[-1].name} to your bench.")
                else:
                    print("Invalid choice. Try again.")
            except ValueError:
                print("Please enter a valid number or 'done'.")
    
    def display_hand(self, player: Player):
        print("\nYour hand:")
        for i, card in enumerate(player.hand):
            print(f"{i+1}. {card}")
    
    def display_board(self):
        print("\n" + "="*50)
        print(f"Turn {self.turn_count}: {self.current_player.name}'s turn")
        print("="*50)
        
        # Display opponent's board
        print(f"\n{self.opponent.name}'s board:")
        print(f"Prize cards remaining: {len(self.opponent.prize_cards)}")
        if self.opponent.active_pokemon:
            energy_count = self.opponent.count_energy(self.opponent.active_pokemon)
            print(f"Active: {self.opponent.active_pokemon} (HP: {self.opponent.active_pokemon.hp}) - Energy: {energy_count}")
        else:
            print("No active Pokemon")
        
        print("Bench:")
        for i, pokemon in enumerate(self.opponent.bench):
            energy_count = self.opponent.count_energy(pokemon)
            print(f"  {i+1}. {pokemon} (HP: {pokemon.hp}) - Energy: {energy_count}")
        
        # Display current player's board
        print(f"\n{self.current_player.name}'s board:")
        print(f"Prize cards remaining: {len(self.current_player.prize_cards)}")
        if self.current_player.active_pokemon:
            energy_count = self.current_player.count_energy(self.current_player.active_pokemon)
            print(f"Active: {self.current_player.active_pokemon} - Energy: {energy_count}")
            print("Attacks:")
            for i, (attack_name, damage) in enumerate(self.current_player.active_pokemon.attacks.items()):
                print(f"  {i+1}. {attack_name} - {damage} damage")
        else:
            print("No active Pokemon")
        
        print("Bench:")
        for i, pokemon in enumerate(self.current_player.bench):
            energy_count = self.current_player.count_energy(pokemon)
            print(f"  {i+1}. {pokemon} - Energy: {energy_count}")
        
        # Display hand
        self.display_hand(self.current_player)
    
    def play_turn(self):
        self.turn_count += 1
        
        # Draw a card to start the turn (except for first player's first turn)
        if not (self.turn_count == 1 and self.current_player_idx == 0):
            drawn_card = self.current_player.draw_card()
            if drawn_card:
                print(f"\n{self.current_player.name} draws: {drawn_card}")
            else:
                print(f"\n{self.current_player.name} has no cards left to draw!")
                self.game_over = True
                self.winner = self.opponent
                print(f"{self.opponent.name} wins because {self.current_player.name} ran out of cards!")
                return
        
        # Display the current board state
        self.display_board()
        
        # Main action phase
        self.action_phase()
        
        # Check for game end conditions
        if self.check_game_end():
            return
        
        # End turn
        print(f"\n{self.current_player.name}'s turn ends.")
        self.current_player_idx = 1 - self.current_player_idx
    
    def action_phase(self):
        # If no active Pokemon, must promote from bench
        if self.current_player.active_pokemon is None and self.current_player.bench:
            self.force_promote_from_bench()
        
        # No valid actions if no active Pokemon
        if self.current_player.active_pokemon is None:
            print("You have no active Pokemon and no bench Pokemon. You cannot take any actions.")
            return
        
        # Flag to track if energy has been attached this turn
        energy_attached = False
        
        # Main action loop
        while True:
            action = self.get_player_action(energy_attached)
            
            if action == 'attack':
                # Perform attack
                if self.handle_attack():
                    break  # End turn after attacking
            
            elif action == 'bench':
                # Play a Pokemon to bench
                self.play_to_bench()
            
            elif action == 'energy':
                # Attach energy
                if not energy_attached:
                    if self.attach_energy_card():
                        energy_attached = True
                else:
                    print("You have already attached an energy card this turn.")
            
            elif action == 'end':
                # End turn without attacking
                break
    
    def handle_switch(self):
        # Switch active with bench Pokemon
        if not self.current_player.bench:
            print("No Pokemon on bench to switch with!")
            return

        print("\nChoose a Pokemon from bench to switch with active:")
        for i, pokemon in enumerate(self.current_player.bench):
            print(f"{i+1}. {pokemon}")

        try:
            choice = int(input("Enter choice (0 to cancel): "))
            if 1 <= choice <= len(self.current_player.bench):
                # Swap active with chosen bench Pokemon
                bench_idx = choice - 1
                temp = self.current_player.active_pokemon
                self.current_player.active_pokemon = self.current_player.bench[bench_idx]
                self.current_player.bench[bench_idx] = temp
                print(f"Switched active Pokemon to {self.current_player.active_pokemon.name}!")
        except ValueError:
            print("Invalid choice.")


    def handle_professors_research(self):
        # Discard hand and draw 7 new cards
        self.current_player.discard_pile.extend(self.current_player.hand)
        self.current_player.hand.clear()
        for _ in range(7):
            self.current_player.draw_card()
        print("Discarded hand and drew 7 new cards!")    


    def handle_super_potion(self):
        # Heal 60 damage but must discard an energy
        target = self.choose_pokemon_to_heal()
        if target and self.current_player.count_energy(target) > 0:
            # Remove one energy
            energy = self.current_player.attached_energy[target].pop()
            self.current_player.discard_pile.append(energy)
            # Heal
            target.hp = min(target.card.hp, target.hp + 60)
            print(f"Discarded energy and healed {target.name} for 60 HP!")
        else:
            print("Cannot use Super Potion - Pokemon needs attached energy!")                

    def handle_potion(self):
        # Heal 30 damage from one Pokemon
        target = self.choose_pokemon_to_heal()
        if target:
            target.hp = min(target.card.hp, target.hp + 30)
            print(f"Healed {target.name} for 30 HP!")

    def play_trainer_card(self):
        # Check if hand has any trainer cards
        trainer_cards = [(i, card) for i, card in enumerate(self.current_player.hand) 
                        if isinstance(card, TrainerCard)]

        if not trainer_cards:
            print("You don't have any Trainer cards in your hand!")
            return

        print("\nTrainer cards in your hand:")
        for i, (_, card) in enumerate(trainer_cards):
            print(f"{i+1}. {card}")

        try:
            choice = int(input("Choose a Trainer card to play (0 to cancel): "))
            if choice == 0:
                return

            if 1 <= choice <= len(trainer_cards):
                card_idx, card = trainer_cards[choice - 1]

                # Implement effects based on card name
                if card.name == "Potion":
                    self.handle_potion()
                elif card.name == "Switch":
                    self.handle_switch()
                elif card.name == "Professor's Research":
                    self.handle_professors_research()
                elif card.name == "Super Potion":
                    self.handle_super_potion()
                elif card.name == "Energy Retrieval":
                    self.handle_energy_retrieval()
                elif card.name == "Great Ball":
                    self.handle_great_ball()
                elif card.name == "Boss's Orders":
                    self.handle_boss_orders()
                # Remove the played card
                self.current_player.hand.pop(card_idx)
                self.current_player.discard_pile.append(card)
            
        except ValueError:
            print("Please enter a valid number.")



    def get_player_action(self, energy_attached: bool) -> str:
        print("\nChoose an action:")
        print("1. Attack (ends your turn)")
        print("2. Play a Pokemon to your bench")
        print("3. Attach an energy card" + (" (already done this turn)" if energy_attached else ""))
        print("4. Play a Trainer card")
        print("5. End turn without attacking")

        while True:
            choice = input("Enter your choice (1-5): ")
            if choice == '1':
                return 'attack'
            elif choice == '2':
                return 'bench'
            elif choice == '3':
                return 'energy'
            elif choice == '4':
                return 'trainer'
            elif choice == '5':
                return 'end'
            else:
                print("Invalid choice. Try again.")
    
    def force_promote_from_bench(self):
        print(f"\n{self.current_player.name}, you must promote a Pokemon from your bench.")
        
        if not self.current_player.bench:
            print("You have no Pokemon on your bench!")
            return
        
        print("Your bench:")
        for i, pokemon in enumerate(self.current_player.bench):
            print(f"{i+1}. {pokemon}")
        
        valid_choice = False
        while not valid_choice:
            try:
                choice = int(input("Choose a Pokemon to promote (1-5): "))
                if self.current_player.promote_from_bench(choice - 1):
                    valid_choice = True
                    print(f"You promoted {self.current_player.active_pokemon.name} to active.")
                else:
                    print("Invalid choice. Try again.")
            except ValueError:
                print("Please enter a valid number.")
    
    def play_to_bench(self):
        # Check if bench is full
        if len(self.current_player.bench) >= 5:
            print("Your bench is full!")
            return
        
        # Check if hand has any Pokemon
        pokemon_in_hand = [i for i, card in enumerate(self.current_player.hand) 
                          if isinstance(card, PokemonCard)]
        
        if not pokemon_in_hand:
            print("You don't have any Pokemon in your hand!")
            return
        
        # Display Pokemon in hand
        print("\nPokemon in your hand:")
        for i, idx in enumerate(pokemon_in_hand):
            print(f"{i+1}. {self.current_player.hand[idx]}")
        
        # Get player choice
        try:
            choice = int(input("Choose a Pokemon to play to bench (or 0 to cancel): "))
            if choice == 0:
                return
            
            if 1 <= choice <= len(pokemon_in_hand):
                card_idx = pokemon_in_hand[choice - 1]
                if self.current_player.play_pokemon(card_idx, as_active=False):
                    print(f"You played {self.current_player.bench[-1].name} to your bench.")
            else:
                print("Invalid choice.")
        except ValueError:
            print("Please enter a valid number.")
    
    def attach_energy_card(self) -> bool:
        # Check if hand has any energy cards
        energy_in_hand = [i for i, card in enumerate(self.current_player.hand) 
                         if isinstance(card, EnergyCard)]
        
        if not energy_in_hand:
            print("You don't have any Energy cards in your hand!")
            return False
        
        # Display energy cards in hand
        print("\nEnergy cards in your hand:")
        for i, idx in enumerate(energy_in_hand):
            print(f"{i+1}. {self.current_player.hand[idx]}")
        
        # Get player choice for energy card
        try:
            energy_choice = int(input("Choose an Energy card to attach (or 0 to cancel): "))
            if energy_choice == 0:
                return False
            
            if 1 <= energy_choice <= len(energy_in_hand):
                energy_idx = energy_in_hand[energy_choice - 1]
                
                # Choose target Pokemon
                print("\nChoose a Pokemon to attach energy to:")
                print("0. Active Pokemon" + (f" ({self.current_player.active_pokemon.name})" if self.current_player.active_pokemon else " (None)"))
                
                for i, pokemon in enumerate(self.current_player.bench):
                    print(f"{i+1}. Bench: {pokemon.name}")
                
                target_choice = int(input("Enter your choice: "))
                
                if target_choice == 0 and self.current_player.active_pokemon:
                    # Attach to active
                    if self.current_player.attach_energy(energy_idx, 0, is_active=True):
                        energy_card = self.current_player.attached_energy[self.current_player.active_pokemon][-1]
                        print(f"You attached {energy_card} to your active {self.current_player.active_pokemon.name}.")
                        return True
                elif 1 <= target_choice <= len(self.current_player.bench):
                    # Attach to bench
                    bench_idx = target_choice - 1
                    if self.current_player.attach_energy(energy_idx, bench_idx, is_active=False):
                        pokemon = self.current_player.bench[bench_idx]
                        energy_card = self.current_player.attached_energy[pokemon][-1]
                        print(f"You attached {energy_card} to your benched {pokemon.name}.")
                        return True
                else:
                    print("Invalid choice.")
            else:
                print("Invalid choice.")
        except ValueError:
            print("Please enter a valid number.")
        
        return False
    
    def handle_attack(self) -> bool:
        if not self.current_player.active_pokemon:
            print("You don't have an active Pokemon!")
            return False
        
        # Display available attacks
        attacks = list(self.current_player.active_pokemon.attacks.items())
        print("\nAvailable attacks:")
        for i, (attack_name, damage) in enumerate(attacks):
            print(f"{i+1}. {attack_name} - {damage} damage")
        print("0. Cancel")
        
            # Get player choice
        try:
            choice = int(input("Choose an attack: "))
            if choice == 0:
                return False

            if 1 <= choice <= len(attacks):
                attack_name, base_damage = attacks[choice - 1]

                print(f"\n{self.current_player.active_pokemon.name} uses {attack_name}!")

                # Apply attack
                if self.opponent.active_pokemon:
                    damage = base_damage
                    attacking_type = self.current_player.active_pokemon.type
                    defending_pokemon_name = self.opponent.active_pokemon.name  # Store name before knockout

                    # Apply weakness/resistance calculation message
                    if self.opponent.active_pokemon.weakness == attacking_type:
                        print(f"It's super effective! Damage doubled due to weakness to {attacking_type}!")
                        damage *= 2
                    if self.opponent.active_pokemon.resistance == attacking_type:
                        reduction = min(30, damage)
                        print(f"It's not very effective... Damage reduced by {reduction} due to resistance to {attacking_type}.")
                        damage -= reduction

                    print(f"{self.opponent.active_pokemon.name} takes {damage} damage!")

                    # Apply damage and check if knocked out
                    if self.opponent.take_damage(damage, attacking_type):
                        print(f"{defending_pokemon_name} is knocked out!")

                        # Take a prize card
                        prize = self.current_player.take_prize_card()
                        if prize:
                            print(f"{self.current_player.name} takes a prize card: {prize}")
                else:
                    print(f"But the opponent has no active Pokemon!")

                return True  # Attack performed
            else:
                print("Invalid choice.")
        except ValueError:
            print("Please enter a valid number.")

        return False
    
    def check_game_end(self) -> bool:
        # Check if a player has taken all prize cards
        if not self.current_player.prize_cards:
            self.game_over = True
            self.winner = self.current_player
            print(f"\n{self.current_player.name} has taken all prize cards and wins the game!")
            return True
        
        # Check if opponent has no Pokemon left
        if (self.opponent.active_pokemon is None and not self.opponent.bench and 
            not any(isinstance(card, PokemonCard) for card in self.opponent.hand)):
            self.game_over = True
            self.winner = self.current_player
            print(f"\n{self.opponent.name} has no Pokemon left and {self.current_player.name} wins the game!")
            return True
        
        return False


    def handle_energy_retrieval(self):
        energy_cards = [card for card in self.current_player.discard_pile if isinstance(card, EnergyCard)]
        if len(energy_cards) < 2:
            print("Not enough Energy cards in discard pile!")
            return False

        print("\nEnergy cards in discard pile:")
        for i, card in enumerate(energy_cards):
            print(f"{i+1}. {card}")

        selected = []
        for i in range(2):
            choice = int(input(f"Choose Energy card #{i+1} to retrieve: "))
            if 1 <= choice <= len(energy_cards):
                selected.append(energy_cards[choice-1])

        for card in selected:
            self.current_player.discard_pile.remove(card)
            self.current_player.hand.append(card)
        print("Retrieved 2 Energy cards to hand!")
        return True


    def handle_great_ball(self):
        if len(self.current_player.deck) < 7:
            print("Not enough cards in deck!")
            return False

        top_cards = self.current_player.deck[:7]
        pokemon_cards = [(i, card) for i, card in enumerate(top_cards) if isinstance(card, PokemonCard)]

        if not pokemon_cards:
            print("No Pokemon found in top 7 cards!")
            return True

        print("\nPokemon found:")
        for i, (_, card) in enumerate(pokemon_cards):
            print(f"{i+1}. {card}")

        choice = int(input("Choose a Pokemon to add to hand (0 to decline): "))
        if 1 <= choice <= len(pokemon_cards):
            idx, chosen = pokemon_cards[choice-1]
            self.current_player.deck.pop(idx)
            self.current_player.hand.append(chosen)
            print(f"Added {chosen.name} to hand!")
        return True
    

    def handle_boss_orders(self):
        if not self.opponent.bench:
            print("Opponent has no benched Pokemon!")
            return False

        print("\nOpponent's bench:")
        for i, pokemon in enumerate(self.opponent.bench):
            print(f"{i+1}. {pokemon}")

        choice = int(input("Choose Pokemon to switch with active: "))
        if 1 <= choice <= len(self.opponent.bench):
            bench_idx = choice - 1
            temp = self.opponent.active_pokemon
            self.opponent.active_pokemon = self.opponent.bench[bench_idx]
            self.opponent.bench[bench_idx] = temp
            print(f"Forced opponent to switch to {self.opponent.active_pokemon.name}!")
        return True

# Create sample cards for testing
def create_sample_deck(pokemon_type: str, secondary_type: str = None) -> List[Card]:
    deck = []

    if pokemon_type == "Fire":
        deck.extend([EnergyCard("Flying") for _ in range(5)])  # For Charizard, Moltres, Ho-Oh
        deck.extend([EnergyCard("Dragon") for _ in range(5)])  # For Reshiram
    elif pokemon_type == "Water":
        deck.extend([EnergyCard("Dragon") for _ in range(5)])  # For Kingdra, Palkia
        deck.extend([EnergyCard("Dark") for _ in range(5)])    # For Greninja
    elif pokemon_type == "Grass":
        deck.extend([EnergyCard("Ghost") for _ in range(5)])   # For Decidueye
        deck.extend([EnergyCard("Fighting") for _ in range(5)]) # For Kartana, Virizion
    elif pokemon_type == "Electric":
        deck.extend([EnergyCard("Flying") for _ in range(5)])  # For Zapdos
        deck.extend([EnergyCard("Fighting") for _ in range(5)]) # For Zeraora
    elif pokemon_type == "Psychic":
        deck.extend([EnergyCard("Dragon") for _ in range(5)])  # For Latios
        deck.extend([EnergyCard("Fairy") for _ in range(5)])   # For Gardevoir
    elif pokemon_type == "Fighting":
        deck.extend([EnergyCard("Fire") for _ in range(5)])    # For Blaziken
        deck.extend([EnergyCard("Psychic") for _ in range(5)]) # For Gallade
    elif pokemon_type == "Dark":
        deck.extend([EnergyCard("Dragon") for _ in range(5)])  # For Hydreigon
        deck.extend([EnergyCard("Fire") for _ in range(5)])    # For Houndoom
    elif pokemon_type == "Dragon":
        deck.extend([EnergyCard("Flying") for _ in range(5)])  # For Rayquaza, Salamence
        deck.extend([EnergyCard("Ghost") for _ in range(5)])   # For Dragapult
    
    # Add Pokemon
    if pokemon_type == "Fire":
        deck.extend([
            PokemonCard("Charmander", 70, "Fire", {"Ember": 30, "Scratch": 10}, weakness="Water", resistance="Grass"),
            PokemonCard("Charmeleon", 90, "Fire", {"Flamethrower": 50, "Fire Spin": 70}, weakness="Water", resistance="Grass"),
            PokemonCard("Charizard", 120, "Fire", {"Fire Blast": 100, "Wing Attack": 60}, weakness="Water", resistance="Fighting"),
            PokemonCard("Vulpix", 60, "Fire", {"Ember": 30, "Quick Attack": 20}, weakness="Water"),
            PokemonCard("Ninetales", 90, "Fire", {"Fire Spin": 70, "Confuse Ray": 30}, weakness="Water"),
            PokemonCard("Arcanine", 100, "Fire", {"Flame Wheel": 60, "Extreme Speed": 80}, weakness="Water"),
            PokemonCard("Flareon", 90, "Fire", {"Fire Spin": 70, "Bite": 40}, weakness="Water"),
            PokemonCard("Moltres", 130, "Fire", {"Sky Attack": 110, "Fire Spin": 90}, weakness="Water", resistance="Fighting"),
            PokemonCard("Magmar", 80, "Fire", {"Fire Punch": 50, "Smog": 30}, weakness="Water"),
            PokemonCard("Typhlosion", 110, "Fire", {"Eruption": 90, "Quick Attack": 40}, weakness="Water"),
            PokemonCard("Entei", 120, "Fire", {"Sacred Fire": 100, "Stomp": 50}, weakness="Water"),
            PokemonCard("Reshiram", 130, "Fire", {"Blue Flare": 120, "Dragon Breath": 60}, weakness="Water", resistance="Electric"),
            PokemonCard("Volcarona", 110, "Fire", {"Fiery Dance": 80, "Bug Buzz": 70}, weakness="Water", resistance="Grass"),
            PokemonCard("Incineroar", 120, "Fire", {"Darkest Lariat": 90, "Flare Blitz": 100}, weakness="Water"),
            PokemonCard("Ho-Oh", 140, "Fire", {"Sacred Fire": 110, "Sky Attack": 80}, weakness="Water", resistance="Fighting"),

        ])
    elif pokemon_type == "Water":
        deck.extend([
            PokemonCard("Squirtle", 70, "Water", {"Bubble": 30, "Tackle": 10}, weakness="Electric", resistance="Fire"),
            PokemonCard("Wartortle", 90, "Water", {"Water Gun": 50, "Aqua Tail": 70}, weakness="Electric", resistance="Fire"),
            PokemonCard("Blastoise", 120, "Water", {"Hydro Pump": 100, "Skull Bash": 60}, weakness="Electric", resistance="Fire"),
            PokemonCard("Starmie", 80, "Water", {"Swift": 40, "Hydro Pump": 80}, weakness="Electric"),
            PokemonCard("Gyarados", 130, "Water", {"Waterfall": 90, "Dragon Rage": 70}, weakness="Electric"),
            PokemonCard("Vaporeon", 90, "Water", {"Aqua Jet": 60, "Aurora Beam": 50}, weakness="Electric"),
            PokemonCard("Lapras", 110, "Water", {"Ice Beam": 70, "Body Slam": 50}, weakness="Electric"),
            PokemonCard("Suicune", 120, "Water", {"Hydro Pump": 90, "Aurora Beam": 60}, weakness="Electric"),
            PokemonCard("Feraligatr", 120, "Water", {"Hydro Cannon": 100, "Crunch": 70}, weakness="Electric"),
            PokemonCard("Kingdra", 110, "Water", {"Dragon Pulse": 80, "Waterfall": 60}, weakness="Electric"),
            PokemonCard("Milotic", 100, "Water", {"Aqua Tail": 70, "Dragon Breath": 50}, weakness="Electric"),
            PokemonCard("Kyogre", 130, "Water", {"Origin Pulse": 110, "Ice Beam": 70}, weakness="Electric", resistance="Fire"),
            PokemonCard("Palkia", 120, "Water", {"Spacial Rend": 100, "Aqua Tail": 80}, weakness="Electric"),
            PokemonCard("Greninja", 110, "Water", {"Water Shuriken": 80, "Night Slash": 60}, weakness="Electric"),
            PokemonCard("Primarina", 120, "Water", {"Sparkling Aria": 90, "Moonblast": 70}, weakness="Electric"),
        ])
    elif pokemon_type == "Grass":
        deck.extend([
            PokemonCard("Bulbasaur", 70, "Grass", {"Vine Whip": 30, "Tackle": 10}, weakness="Fire", resistance="Water"),
            PokemonCard("Ivysaur", 90, "Grass", {"Razor Leaf": 50, "Vine Whip": 40}, weakness="Fire", resistance="Water"),
            PokemonCard("Venusaur", 120, "Grass", {"Solar Beam": 100, "Body Slam": 60}, weakness="Fire", resistance="Water"),
            PokemonCard("Exeggutor", 100, "Grass", {"Solar Beam": 80, "Psyshock": 50}, weakness="Fire"),
            PokemonCard("Victreebel", 90, "Grass", {"Leaf Blade": 70, "Acid": 40}, weakness="Fire"),
            PokemonCard("Tangela", 80, "Grass", {"Vine Whip": 50, "Stun Spore": 30}, weakness="Fire"),
            PokemonCard("Leafeon", 90, "Grass", {"Leaf Blade": 60, "Quick Attack": 40}, weakness="Fire"),
            PokemonCard("Meganium", 120, "Grass", {"Frenzy Plant": 100, "Body Slam": 60}, weakness="Fire"),
            PokemonCard("Sceptile", 110, "Grass", {"Leaf Blade": 90, "Quick Attack": 40}, weakness="Fire"),
            PokemonCard("Celebi", 100, "Grass", {"Magical Leaf": 70, "Ancient Power": 50}, weakness="Fire", resistance="Psychic"),
            PokemonCard("Shaymin", 90, "Grass", {"Seed Flare": 80, "Synthesis": 0}, weakness="Fire"),
            PokemonCard("Virizion", 120, "Grass", {"Sacred Sword": 90, "Leaf Blade": 80}, weakness="Fire", resistance="Water"),
            PokemonCard("Rillaboom", 110, "Grass", {"Drum Beating": 80, "Wood Hammer": 100}, weakness="Fire"),
            PokemonCard("Decidueye", 120, "Grass", {"Spirit Shackle": 90, "Leaf Storm": 80}, weakness="Fire"),
            PokemonCard("Kartana", 130, "Grass", {"Leaf Blade": 110, "Sacred Sword": 90}, weakness="Fire"),
        ])
    elif pokemon_type == "Psychic":
        deck.extend([
            PokemonCard("Mewtwo", 150, "Psychic", {"Psystrike": 120, "Future Sight": 90}, weakness="Dark", resistance="Fighting"),
            PokemonCard("Alakazam", 110, "Psychic", {"Psychic": 90, "Recover": 0}, weakness="Dark"),
            PokemonCard("Espeon", 100, "Psychic", {"Psybeam": 70, "Morning Sun": 0}, weakness="Dark"),
            PokemonCard("Gardevoir", 130, "Psychic", {"Moonblast": 100, "Psychic": 80}, weakness="Dark"),
            PokemonCard("Mew", 100, "Psychic", {"Ancient Power": 60, "Psychic": 90}, weakness="Dark", resistance="Fighting"),
            PokemonCard("Lugia", 130, "Psychic", {"Aeroblast": 100, "Extrasensory": 80}, weakness="Dark", resistance="Fighting"),
            PokemonCard("Celebi", 100, "Psychic", {"Psychic": 70, "Leaf Storm": 90}, weakness="Dark", resistance="Fighting"),
            PokemonCard("Latios", 120, "Psychic", {"Luster Purge": 90, "Dragon Breath": 60}, weakness="Dark", resistance="Fighting")
        ])
    elif pokemon_type == "Fighting":
        deck.extend([
            PokemonCard("Machamp", 130, "Fighting", {"Dynamic Punch": 100, "Cross Chop": 80}, weakness="Psychic"),
            PokemonCard("Lucario", 110, "Fighting", {"Aura Sphere": 80, "Close Combat": 100}, weakness="Psychic"),
            PokemonCard("Conkeldurr", 140, "Fighting", {"Hammer Arm": 90, "Superpower": 110}, weakness="Psychic"),
            PokemonCard("Blaziken", 120, "Fighting", {"Blaze Kick": 85, "Sky Uppercut": 70}, weakness="Psychic"),
            PokemonCard("Heracross", 110, "Fighting", {"Megahorn": 90, "Close Combat": 100}, weakness="Psychic"),
            PokemonCard("Hariyama", 130, "Fighting", {"Arm Thrust": 80, "Force Palm": 60}, weakness="Psychic"),
            PokemonCard("Gallade", 120, "Fighting", {"Close Combat": 100, "Psycho Cut": 70}, weakness="Psychic"),
            PokemonCard("Pangoro", 130, "Fighting", {"Hammer Arm": 90, "Night Slash": 70}, weakness="Psychic")
        ])
    elif pokemon_type == "Dark":
        deck.extend([
            PokemonCard("Tyranitar", 140, "Dark", {"Dark Pulse": 90, "Stone Edge": 100}, weakness="Fighting"),
            PokemonCard("Darkrai", 120, "Dark", {"Dark Void": 80, "Nightmare": 70}, weakness="Fighting"),
            PokemonCard("Umbreon", 110, "Dark", {"Foul Play": 70, "Mean Look": 0}, weakness="Fighting"),
            PokemonCard("Hydreigon", 130, "Dark", {"Dragon Rush": 100, "Dark Pulse": 80}, weakness="Fighting"),
            PokemonCard("Houndoom", 110, "Dark", {"Dark Pulse": 80, "Flamethrower": 70}, weakness="Fighting"),
            PokemonCard("Absol", 100, "Dark", {"Night Slash": 70, "Psycho Cut": 60}, weakness="Fighting"),
            PokemonCard("Zoroark", 110, "Dark", {"Night Daze": 90, "Foul Play": 70}, weakness="Fighting"),
            PokemonCard("Grimmsnarl", 120, "Dark", {"Spirit Break": 85, "Dark Pulse": 80}, weakness="Fighting")
        ])
    elif pokemon_type == "Dragon":
        deck.extend([
            PokemonCard("Rayquaza", 150, "Dragon", {"Dragon Ascent": 120, "Outrage": 90}, weakness="Ice"),
            PokemonCard("Garchomp", 130, "Dragon", {"Dragon Claw": 90, "Earthquake": 80}, weakness="Ice"),
            PokemonCard("Dragonite", 140, "Dragon", {"Dragon Rush": 100, "Hurricane": 80}, weakness="Ice"),
            PokemonCard("Salamence", 130, "Dragon", {"Double-Edge": 90, "Dragon Tail": 70}, weakness="Ice"),
            PokemonCard("Latias", 120, "Dragon", {"Mist Ball": 80, "Dragon Breath": 60}, weakness="Ice"),
            PokemonCard("Haxorus", 130, "Dragon", {"Outrage": 110, "Dragon Claw": 80}, weakness="Ice"),
            PokemonCard("Goodra", 120, "Dragon", {"Dragon Pulse": 85, "Aqua Tail": 70}, weakness="Ice"),
            PokemonCard("Dragapult", 130, "Dragon", {"Dragon Darts": 100, "Phantom Force": 90}, weakness="Ice")
        ])    
    else:  # Electric
        deck.extend([
            PokemonCard("Pikachu", 70, "Electric", {"Thunder Shock": 30, "Quick Attack": 10}, weakness="Fighting", resistance="Electric"),
            PokemonCard("Raichu", 90, "Electric", {"Thunderbolt": 80, "Thunder Punch": 50}, weakness="Fighting", resistance="Electric"),
            PokemonCard("Jolteon", 90, "Electric", {"Thunder Fang": 60, "Pin Missile": 40}, weakness="Fighting"),
            PokemonCard("Electabuzz", 80, "Electric", {"Thunder Punch": 50, "Swift": 30}, weakness="Fighting"),
            PokemonCard("Magneton", 90, "Electric", {"Zap Cannon": 80, "Thunder Wave": 40}, weakness="Fighting"),
            PokemonCard("Electrode", 80, "Electric", {"Volt Tackle": 70, "Rollout": 30}, weakness="Fighting"),
            PokemonCard("Zapdos", 120, "Electric", {"Thunder": 100, "Drill Peck": 60}, weakness="Rock"),
            PokemonCard("Raikou", 120, "Electric", {"Thunder Fang": 90, "Extrasensory": 60}, weakness="Ground"),
            PokemonCard("Ampharos", 110, "Electric", {"Thunder": 100, "Signal Beam": 50}, weakness="Ground"),
            PokemonCard("Manectric", 90, "Electric", {"Thunder Wave": 70, "Quick Attack": 30}, weakness="Ground"),
            PokemonCard("Luxray", 100, "Electric", {"Wild Charge": 90, "Crunch": 60}, weakness="Ground"),
            PokemonCard("Thundurus", 120, "Electric", {"Thunder": 100, "Hammer Arm": 70}, weakness="Ice"),
            PokemonCard("Zeraora", 110, "Electric", {"Plasma Fists": 90, "Close Combat": 80}, weakness="Ground"),
            PokemonCard("Vikavolt", 100, "Electric", {"Zap Cannon": 120, "Bug Buzz": 70}, weakness="Fire"),
            PokemonCard("Xurkitree", 130, "Electric", {"Thunder": 110, "Energy Ball": 60}, weakness="Ground")
        ])
    
    # Add secondary type Pokemon if specified
    if secondary_type:
        if secondary_type == "Fire":
            deck.append(PokemonCard("Ponyta", 60, "Fire", {"Flame Charge": 30, "Stomp": 20}, weakness="Water"))
            deck.append(PokemonCard("Vulpix", 60, "Fire", {"Ember": 30, "Quick Attack": 20}, weakness="Water"))
        elif secondary_type == "Water":
            deck.append(PokemonCard("Horsea", 60, "Water", {"Bubble": 30, "Smokescreen": 0}, weakness="Electric"))
            deck.append(PokemonCard("Krabby", 60, "Water", {"Bubble": 30, "Vice Grip": 20}, weakness="Electric"))
        elif secondary_type == "Grass":
            deck.append(PokemonCard("Tangela", 70, "Grass", {"Vine Whip": 30, "Absorb": 20}, weakness="Fire"))
            deck.append(PokemonCard("Paras", 60, "Grass", {"Scratch": 20, "Stun Spore": 0}, weakness="Fire"))
        else:  # Electric
            deck.append(PokemonCard("Magnemite", 60, "Electric", {"Thunder Shock": 30, "Tackle": 10}, weakness="Fighting"))
            deck.append(PokemonCard("Pikachu", 70, "Electric", {"Thunder Shock": 30, "Quick Attack": 10}, weakness="Fighting", resistance="Electric"))
    
    # Add energy cards
    for _ in range(15):
        deck.append(EnergyCard(pokemon_type))
    
    if secondary_type:
        for _ in range(7):
            deck.append(EnergyCard(secondary_type))
    
    # Add trainer cards
    deck.append(TrainerCard("Potion", "Heal 30 damage from one of your Pokemon"))
    deck.append(TrainerCard("Super Potion", "Heal 60 damage from one of your Pokemon. Discard 1 Energy card attached to that Pokemon"))
    deck.append(TrainerCard("Professor's Research", "Discard your hand and draw 7 cards"))
    deck.append(TrainerCard("Switch", "Switch your active Pokemon with one of your benched Pokemon"))
    deck.append(TrainerCard("Energy Retrieval", "Return 2 Energy cards from discard pile to hand"))
    deck.append(TrainerCard("Pokemon Center Lady", "Heal 60 damage and remove all status conditions"))
    deck.append(TrainerCard("Great Ball", "Look at top 7 cards of deck. You may reveal a Pokemon and put it into your hand"))
    deck.append(TrainerCard("Ultra Ball", "Discard 2 cards from hand. Search deck for a Pokemon and add it to hand"))
    deck.append(TrainerCard("Boss's Orders", "Switch opponent's benched Pokemon with their active Pokemon"))
    
    return deck

def main():
    print("Welcome to the Pokemon Card Game!")
    print("\nPlayer 1, choose your primary Pokemon type:")
    print("1. Fire")
    print("2. Water")
    print("3. Grass")
    print("4. Electric")
    
    type_map = {
        1: "Fire", 
        2: "Water", 
        3: "Grass", 
        4: "Electric",
        5: "Psychic",
        6: "Fighting",
        7: "Dark",
        8: "Dragon"
    }    
    choice1 = int(input("Enter your choice (1-4): "))
    player1_type = type_map.get(choice1, "Fire")
    
    print("\nPlayer 2, choose your primary Pokemon type:")
    print("1. Fire")
    print("2. Water")
    print("3. Grass")
    print("4. Electric")
    
    choice2 = int(input("Enter your choice (1-4): "))
    player2_type = type_map.get(choice2, "Water")
    
    # Create a secondary type for variety
    player1_secondary = type_map.get((choice1 % 4) + 1)
    player2_secondary = type_map.get((choice2 % 4) + 1)
    
    player1_deck = create_sample_deck(player1_type, player1_secondary)
    player2_deck = create_sample_deck(player2_type, player2_secondary)
    
    player1 = Player("Player 1", player1_deck)
    player2 = Player("Player 2", player2_deck)
    
    game = PokemonGame(player1, player2)
    game.start_game()
    
    if game.winner:
        print(f"\nGame Over! {game.winner.name} wins!")

if __name__ == "__main__":
    main()