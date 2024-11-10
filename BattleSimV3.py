import random

class Troop:
    def __init__(self, name, base_attack, base_defense, base_lethality, base_health, 
                 attack_bonus, defense_bonus, lethality_bonus, health_bonus, 
                 special_skills):
        self.name = name
        self.base_attack = base_attack
        self.base_defense = base_defense
        self.base_lethality = base_lethality
        self.base_health = base_health
        self.attack_bonus = attack_bonus
        self.defense_bonus = defense_bonus
        self.lethality_bonus = lethality_bonus
        self.health_bonus = health_bonus
        self.special_skills = special_skills
        self.effective_attack = self.base_attack * (1 + self.attack_bonus / 100)
        self.effective_defense = self.base_defense * (1 + self.defense_bonus / 100)
        self.effective_health = self.base_health * (1 + self.health_bonus / 100)
        self.count = 0  # Number of troops

    def attack_target(self, target):
        damage = self.effective_attack - (target.effective_defense / 2)
        damage = max(damage, 0)  # Prevent negative damage
        total_damage = damage * self.count
        return total_damage

class Player:
    def __init__(self, name):
        self.name = name
        self.troops = {}
    
    def add_troop(self, troop, count):
        self.troops[troop.name] = troop
        troop.count = count
    
    def total_health(self):
        return sum(t.effective_health * t.count for t in self.troops.values())

def simulate_battle(player1, player2):
    turn = 1
    while player1.total_health() > 0 and player2.total_health() > 0 and turn <= 100:
        print(f"--- Turn {turn} ---")
        # Player1 attacks Player2
        total_damage_p1 = sum(t.attack_target(opponent) for t, opponent in zip(player1.troops.values(), player2.troops.values()))
        # Apply damage to Player2
        for troop in player2.troops.values():
            damage = total_damage_p1 / len(player2.troops)
            casualties = damage / troop.effective_health
            casualties = min(casualties, troop.count)
            troop.count -= casualties
            print(f"{player1.name} attacks {player2.name}'s {troop.name}: {casualties} casualties")
        
        # Check if Player2 is defeated
        if player2.total_health() <= 0:
            print(f"{player1.name} wins!")
            break
        
        # Player2 attacks Player1
        total_damage_p2 = sum(t.attack_target(opponent) for t, opponent in zip(player2.troops.values(), player1.troops.values()))
        # Apply damage to Player1
        for troop in player1.troops.values():
            damage = total_damage_p2 / len(player1.troops)
            casualties = damage / troop.effective_health
            casualties = min(casualties, troop.count)
            troop.count -= casualties
            print(f"{player2.name} attacks {player1.name}'s {troop.name}: {casualties} casualties")
        
        # Check if Player1 is defeated
        if player1.total_health() <= 0:
            print(f"{player2.name} wins!")
            break
        
        turn += 1

    if turn > 100:
        print("Battle ended in a draw.")

# Player 1 Troops
infantry_p1 = Troop("Infantry", 10, 13, 10, 15, 904.6, 690.5, 1065.1, 1181.8, ["Master Brawler", "Bands of Steel"])
lancer_p1 = Troop("Lancer", 13, 11, 14, 11, 830.8, 643.9, 849.6, 943.1, ["Charge", "Ambusher"])
marksman_p1 = Troop("Marksman", 14, 10, 15, 10, 826.5, 638.5, 847.8, 956.6, ["Ranged Strike", "Volley"])

# Player 2 Troops
infantry_p2 = Troop("Infantry", 10, 13, 10, 15, 779.5, 690.5, 989.2, 824.7, [])
lancer_p2 = Troop("Lancer", 13, 11, 14, 11, 699.1, 615.0, 852.3, 712.8, [])
marksman_p2 = Troop("Marksman", 14, 10, 15, 10, 749.7, 661.5, 907.6, 752.1, [])

# Initialize players
p1 = Player("Player1")
p2 = Player("Player2")

# Assign troop counts
p1.add_troop(infantry_p1, 331624)
p1.add_troop(lancer_p1, 317817)
p1.add_troop(marksman_p1, 50366)

p2.add_troop(infantry_p2, 474098)
p2.add_troop(lancer_p2, 232514)
p2.add_troop(marksman_p2, 309520)

# Simulate battle
simulate_battle(p1, p2)
