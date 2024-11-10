import random

def simulate_battle(player1_stats, player2_stats):
    rounds = 100  # Assume 100 rounds max or until one side loses all troops
    for round in range(rounds):
        # Infantry phase
        player1_infantry_damage = calculate_damage(player1_stats['infantry'], player2_stats['infantry'])
        player2_infantry_damage = calculate_damage(player2_stats['infantry'], player1_stats['infantry'])
        
        # Apply RNG skills
        if random.random() < 0.2:  # Example for 20% chance skill
            player1_infantry_damage *= 1.5  # Modify damage
        
        # Update troop counts
        player1_stats['infantry']['troops'] -= player2_infantry_damage
        player2_stats['infantry']['troops'] -= player1_infantry_damage

        # Check if either side lost all troops
        if player1_stats['infantry']['troops'] <= 0 or player2_stats['infantry']['troops'] <= 0:
            break

    # Determine the winner
    if player1_stats['infantry']['troops'] > 0:
        return "Player 1 wins"
    else:
        return "Player 2 wins"

def calculate_damage(attacker, defender):
    base_damage = (attacker['attack'] + attacker['attack_bonus']) * (1 + attacker['lethality'] / 100)
    defense = defender['defense'] + defender['defense_bonus']
    damage = max(0, base_damage - defense)
    return damage
