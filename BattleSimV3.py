import random
import logging
from math import floor

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger()

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

    def attack_target(self, target, target_type):
        # Apply static skill modifiers based on target type
        attack_multiplier = 1.0
        if self.name == "Infantry" and target_type == "Lancer":
            attack_multiplier += 0.10  # Master Brawler
        elif self.name == "Lancer" and target_type == "Marksman":
            attack_multiplier += 0.10  # Charge
        elif self.name == "Marksman" and target_type == "Infantry":
            attack_multiplier += 0.10  # Ranged Strike

        effective_attack = self.effective_attack * attack_multiplier

        # Calculate base damage
        damage = effective_attack - (target.effective_defense / 2)
        damage = max(damage, 0)  # Prevent negative damage

        # Handle probabilistic skills using expected triggers
        additional_damage = 0
        if "Ambusher" in self.special_skills:
            triggers = floor(self.count * 0.20)  # 20% chance
            additional_damage += triggers * (self.effective_attack - (target.effective_defense / 2))
        
        if "Volley" in self.special_skills:
            triggers = floor(self.count * 0.10)  # 10% chance
            additional_damage += triggers * (self.effective_attack - (target.effective_defense / 2))

        # Handle lethality for critical hits
        critical_hits = floor(self.count * (self.lethality_bonus / 1000))  # Example scaling
        critical_damage = critical_hits * (self.effective_attack * 0.5)  # 50% extra damage
        additional_damage += critical_damage

        total_damage = (damage * self.count) + additional_damage
        return total_damage

class Player:
    def __init__(self, name, expedition_skills=None):
        self.name = name
        self.troops = {}
        self.expedition_skills = expedition_skills if expedition_skills else []
        # Additional attributes for status effects
        self.status_effects = {}

    def add_troop(self, troop, count):
        self.troops[troop.name] = troop
        troop.count = count

    def total_health(self):
        return sum(t.effective_health * t.count for t in self.troops.values())

    def apply_expedition_skills(self, damage_dealt, target_player):
        for skill in self.expedition_skills:
            if skill.name == "Pyromaniac":
                triggers = floor(damage_dealt * 0.20)  # 20% chance
                burn_damage = triggers * (0.40 * target_player.total_health())
                target_player.apply_status_effect("burning", 3, 0.40)
                logger.info(f"{self.name}'s Pyromaniac triggers {triggers} times, applying burn.")
            elif skill.name == "Immolation":
                triggers = floor(damage_dealt * 0.50)  # 50% chance
                target_player.apply_status_effect("vulnerable", 2, 0.50)
                logger.info(f"{self.name}'s Immolation triggers {triggers} times, applying vulnerability.")
            # Add more expedition skills as needed

    def apply_status_effect(self, effect_name, duration, magnitude):
        if effect_name in self.status_effects:
            self.status_effects[effect_name]['duration'] += duration
            self.status_effects[effect_name]['magnitude'] = max(self.status_effects[effect_name]['magnitude'], magnitude)
        else:
            self.status_effects[effect_name] = {'duration': duration, 'magnitude': magnitude}
        logger.info(f"{self.name} gains status effect '{effect_name}' for {duration} turns with magnitude {magnitude}.")

    def process_status_effects(self):
        total_burn_damage = 0
        total_vulnerable_multiplier = 1.0

        # Apply burning damage
        if "burning" in self.status_effects:
            burn = self.status_effects["burning"]
            burn_damage = burn['magnitude'] * self.total_health()
            total_burn_damage += burn_damage
            burn['duration'] -= 1
            logger.info(f"{self.name} takes {burn_damage} burn damage.")
            if burn['duration'] <= 0:
                del self.status_effects["burning"]
                logger.info(f"{self.name}'s burning effect has ended.")

        # Apply vulnerability
        if "vulnerable" in self.status_effects:
            vulnerable = self.status_effects["vulnerable"]
            total_vulnerable_multiplier += vulnerable['magnitude']
            vulnerable['duration'] -= 1
            logger.info(f"{self.name} has vulnerability multiplier of {vulnerable['magnitude']} for this turn.")
            if vulnerable['duration'] <= 0:
                del self.status_effects["vulnerable"]
                logger.info(f"{self.name}'s vulnerability effect has ended.")

        return total_burn_damage, total_vulnerable_multiplier

def define_target_priority(attacker_name):
    # Define the targeting priority based on attacker type
    priority = {
        "Infantry": ["Lancer", "Marksman", "Infantry"],
        "Lancer": ["Marksman", "Infantry", "Lancer"],
        "Marksman": ["Infantry", "Lancer", "Marksman"]
    }
    return priority.get(attacker_name, ["Infantry", "Lancer", "Marksman"])

def apply_damage(player, total_damage):
    sorted_troops = sorted(player.troops.values(), key=lambda x: x.effective_health, reverse=True)
    remaining_damage = int(total_damage)
    for troop in sorted_troops:
        if troop.count <= 0:
            continue
        troop_total_health = troop.effective_health * troop.count
        damage_to_troop = min(remaining_damage, troop_total_health)
        casualties = damage_to_troop // troop.effective_health
        casualties = int(casualties)
        troop.count -= casualties
        remaining_damage -= casualties * troop.effective_health
        logger.info(f"{player.name}'s {troop.name} takes {casualties} casualties.")
        if remaining_damage <= 0:
            break

def apply_burn_damage(player, burn_damage):
    if burn_damage > 0:
        total_health = player.total_health()
        for troop in player.troops.values():
            if troop.count <= 0:
                continue
            troop_health = troop.effective_health * troop.count
            damage = (troop_health / total_health) * burn_damage
            casualties = int(damage // troop.effective_health)
            casualties = min(casualties, troop.count)
            troop.count -= casualties
            logger.info(f"{player.name}'s {troop.name} takes {casualties} burn casualties.")

def perform_attack(attacker_player, defender_player):
    total_damage = 0
    for attacker in attacker_player.troops.values():
        if attacker.count <= 0:
            continue
        for target_type in define_target_priority(attacker.name):
            target = defender_player.troops.get(target_type)
            if target and target.count > 0:
                damage = attacker.attack_target(target, target_type)
                total_damage += damage
                # Apply expedition skills
                attacker_player.apply_expedition_skills(damage, defender_player)
                break  # Attack only the highest priority target

    # Apply damage to defender
    apply_damage(defender_player, total_damage)

    # Process defender's status effects
    burn_damage, vuln_multiplier = defender_player.process_status_effects()
    apply_burn_damage(defender_player, burn_damage)
    # Vulnerable multiplier can be used to adjust damage in next attacks
    # For simplicity, it's currently not affecting the damage allocation

def simulate_battle(player1, player2):
    turn = 1
    offensive_player = player1  # Assuming player1 is offensive
    defensive_player = player2

    while offensive_player.total_health() > 0 and defensive_player.total_health() > 0 and turn <= 100:
        logger.info(f"--- Turn {turn} ---")
        
        # Offensive player attacks first
        perform_attack(offensive_player, defensive_player)
        
        # Check if defensive player is defeated
        if defensive_player.total_health() <= 0:
            logger.info(f"{offensive_player.name} wins!")
            break
        
        # Defensive player retaliates
        perform_attack(defensive_player, offensive_player)
        
        # Check if offensive player is defeated
        if offensive_player.total_health() <= 0:
            logger.info(f"{defensive_player.name} wins!")
            break

        turn += 1

    if turn > 100:
        logger.info("Battle ended in a draw.")

# Example Usage
# Define troops for Player1 (Dave)
infantry_p1 = Troop(
    name="Infantry",
    base_attack=10,
    base_defense=13,
    base_lethality=10,
    base_health=15,
    attack_bonus=904.6,
    defense_bonus=690.5,
    lethality_bonus=1065.1,
    health_bonus=1181.8,
    special_skills=["Master Brawler", "Bands of Steel"]
)
lancer_p1 = Troop(
    name="Lancer",
    base_attack=13,
    base_defense=11,
    base_lethality=14,
    base_health=11,
    attack_bonus=830.8,
    defense_bonus=643.9,
    lethality_bonus=849.6,
    health_bonus=943.1,
    special_skills=["Charge", "Ambusher"]
)
marksman_p1 = Troop(
    name="Marksman",
    base_attack=14,
    base_defense=10,
    base_lethality=15,
    base_health=10,
    attack_bonus=826.5,
    defense_bonus=638.5,
    lethality_bonus=847.8,
    health_bonus=956.6,
    special_skills=["Ranged Strike", "Volley"]
)

# Define troops for Player2 (Brabo)
infantry_p2 = Troop(
    name="Infantry",
    base_attack=10,
    base_defense=13,
    base_lethality=10,
    base_health=15,
    attack_bonus=779.5,
    defense_bonus=690.5,
    lethality_bonus=989.2,
    health_bonus=824.7,
    special_skills=[]
)
lancer_p2 = Troop(
    name="Lancer",
    base_attack=13,
    base_defense=11,
    base_lethality=14,
    base_health=11,
    attack_bonus=699.1,
    defense_bonus=615.0,
    lethality_bonus=852.3,
    health_bonus=712.8,
    special_skills=[]
)
marksman_p2 = Troop(
    name="Marksman",
    base_attack=14,
    base_defense=10,
    base_lethality=15,
    base_health=10,
    attack_bonus=749.7,
    defense_bonus=661.5,
    lethality_bonus=907.6,
    health_bonus=752.1,
    special_skills=[]
)

# Initialize players with expedition skills
# Assuming Player1 has 'Pyromaniac', 'Burning Resolve', 'Immolation'
player1_expedition_skills = [
    {"name": "Pyromaniac"},
    {"name": "Burning Resolve"},
    {"name": "Immolation"}
]

# Assuming Player2 has 'Battle Manifesto', 'Sword Mentor', etc.
player2_expedition_skills = [
    {"name": "Battle Manifesto"},
    {"name": "Sword Mentor"},
    {"name": "Expert Swordsmanship"},
    {"name": "Onslaught"},
    {"name": "Iron Strength"},
    {"name": "Poison Harpoon"}
]

# Create Player instances
player1 = Player("Dave", expedition_skills=player1_expedition_skills)
player2 = Player("Brabo", expedition_skills=player2_expedition_skills)

# Assign troop counts
player1.add_troop(infantry_p1, 331624)
player1.add_troop(lancer_p1, 317817)
player1.add_troop(marksman_p1, 50366)

player2.add_troop(infantry_p2, 474098)
player2.add_troop(lancer_p2, 232514)
player2.add_troop(marksman_p2, 309520)

# Simulate battle
simulate_battle(player1, player2)
