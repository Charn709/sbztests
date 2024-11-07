import random
import math

# Engagement rate constant
ENGAGEMENT_RATE = 0.5  

class Skill:
    def __init__(self, name, effect_type, value, chance, target=None, duration=1, once_per_battle=False, kills=0):
        self.name = name
        self.effect_type = effect_type  # e.g., 'damage_increase', 'stun', etc.
        self.value = value              
        self.chance = chance            # Probability to trigger (as a decimal)
        self.target = target            
        self.duration = duration        # Duration of the effect in turns
        self.activation_count = 0       
        self.once_per_battle = once_per_battle  
        self.kills = kills              

    def try_activate(self):
        if self.once_per_battle and self.activation_count > 0:
            return False
        activated = random.random() <= self.chance
        if activated:
            self.activation_count += 1
        return activated

class TroopType:
    def __init__(self, name, base_attack, base_defense, base_lethality, base_health, count, bonuses, static_skills, rng_skills, position):
        self.name = name
        self.base_attack = base_attack
        self.base_defense = base_defense
        self.base_lethality = base_lethality
        self.base_health = base_health
        self.count = count
        self.initial_count = count
        self.bonuses = bonuses.copy()  # Dict with keys: attack, defense, lethality, health (percentages)
        self.static_skills = static_skills  # List of always-active Skill objects
        self.rng_skills = rng_skills        # List of RNG Skill
        self.position = position  # 'Front', 'Middle', 'Back'
        self.effective_stats = self.calculate_effective_stats()
        self.total_health = self.effective_stats['health'] * self.count
        self.alive = True
        self.kills = 0  

        # Status effects
        self.status_effects = {}  

    def calculate_effective_stats(self):
        effective_attack = self.base_attack * (1 + self.bonuses.get('attack', 0) / 100)
        effective_defense = self.base_defense * (1 + self.bonuses.get('defense', 0) / 100)
        effective_lethality = self.base_lethality * (1 + self.bonuses.get('lethality', 0) / 100)
        effective_health = self.base_health * (1 + self.bonuses.get('health', 0) / 100)
        return {
            'attack': effective_attack,
            'defense': effective_defense,
            'lethality': effective_lethality,
            'health': effective_health
        }

class Army:
    def __init__(self, name, troops, hero_skills):
        self.name = name
        self.troops = troops  
        self.hero_skills = hero_skills  
        self.skill_activation_log = {}  
        self.update_total_health()
        self.apply_once_skills()  

    def update_total_health(self):
        self.total_health = sum([troop.total_health for troop in self.troops.values() if troop.alive])

    def is_defeated(self):
        return all(not troop.alive for troop in self.troops.values())

    def get_frontline(self):        
        for position in ['Front', 'Middle', 'Back']:
            frontline_troops = [troop for troop in self.troops.values() if troop.position == position and troop.alive]
            if frontline_troops:
                return frontline_troops
        return []

    def apply_once_skills(self):
        for skill in self.hero_skills:
            if skill.once_per_battle:
                # Apply the skill effects globally to all troops
                self.skill_activation_log[skill.name] = 1
                for troop in self.troops.values():
                    if skill.effect_type == 'damage_increase':
                        troop.bonuses['attack'] = troop.bonuses.get('attack', 0) + 100  # 100% increase
                    elif skill.effect_type == 'defense_increase':
                        troop.bonuses['defense'] = troop.bonuses.get('defense', 0) + 100  # 100% increase
                    elif skill.effect_type == 'health_increase':
                        troop.bonuses['health'] = troop.bonuses.get('health', 0) + 100  # 100% increase
                    # Recalculate effective stats
                    troop.effective_stats = troop.calculate_effective_stats()

def calculate_damage(attacker, defender, damage_modifiers):
    attack = attacker.effective_stats['attack']
    lethality = attacker.effective_stats['lethality']
    defense = defender.effective_stats['defense']

    damage_decrease = defender.status_effects.get('damage_decrease', {'value': 0})['value']
    defense *= (1 + damage_decrease / 100)

    # Basic damage formula (per troop)
    damage_per_troop = attack * (1 + lethality / 100) / defense

    # Apply damage modifiers
    for modifier in damage_modifiers:
        damage_per_troop *= (1 + modifier / 100)

    number_of_attackers = max(1, int(attacker.count * ENGAGEMENT_RATE))

    # Total damage is per-troop damage times number of engaged troops
    total_damage = damage_per_troop * number_of_attackers
    return total_damage, number_of_attackers

def apply_damage(defender, damage, attacker=None, skill=None, number_of_attackers=1):
    # Distribute damage across defender's troops
    troops_lost = min(defender.count, damage / defender.effective_stats['health'])
    defender.count -= troops_lost
    defender.total_health -= damage
    if defender.count <= 0:
        defender.alive = False
    # Track kills
    if attacker:
        attacker.kills += troops_lost
        if skill:
            skill.kills += troops_lost

def apply_status_effects(troop, battle_log):
    to_remove = []
    for effect_name, effect in troop.status_effects.items():
        if effect_name == 'burn':
            # Burn damage per troop
            burn_damage_per_troop = effect['damage']
            number_of_burned_troops = max(1, int(troop.count * ENGAGEMENT_RATE))
            total_burn_damage = burn_damage_per_troop * number_of_burned_troops
            troop.total_health -= total_burn_damage
            troops_lost = total_burn_damage / troop.effective_stats['health']
            troop.count -= troops_lost
            battle_log.append(f"{troop.name} takes {total_burn_damage:.2f} burn damage.")

        effect['remaining_turns'] -= 1
        if effect['remaining_turns'] <= 0:
            to_remove.append(effect_name)
    for effect_name in to_remove:
        del troop.status_effects[effect_name]
    if troop.count <= 0:
        troop.alive = False

def simulate_battle(army_a, army_b, max_turns=100):
    turn = 0
    battle_log = []
    while turn < max_turns and not army_a.is_defeated() and not army_b.is_defeated():
        turn += 1
        turn_log = f"\n--- Turn {turn} ---"
        battle_log.append(turn_log)

        # Apply status effects at the start of the turn
        for army in [army_a, army_b]:
            for troop in army.troops.values():
                if troop.alive:
                    apply_status_effects(troop, battle_log)

        for army_attacker, army_defender in [(army_a, army_b), (army_b, army_a)]:
            frontline_targets = army_defender.get_frontline()
            if not frontline_targets:
                continue  # No targets left

            for attacker in army_attacker.troops.values():
                if not attacker.alive:
                    continue

                if 'stun' in attacker.status_effects:
                    attacker.status_effects['stun']['remaining_turns'] -= 1
                    if attacker.status_effects['stun']['remaining_turns'] <= 0:
                        del attacker.status_effects['stun']
                    battle_log.append(f"{army_attacker.name}'s {attacker.name} is stunned and cannot act this turn.")
                    continue

                if attacker.name == 'Lancer':
                    # Lancer might attack backline due to "Ambusher"
                    target = select_target_lancer(attacker, army_defender, army_attacker, battle_log)
                    if not target:
                        continue  # No valid target
                else:
                    frontline_targets = army_defender.get_frontline()
                    if not frontline_targets:
                        continue  # No targets left
                    target = frontline_targets[0]  # Attack the first troop in the frontline

                # Apply skills
                damage_modifiers = []

                # Static troop-specific skills
                for skill in attacker.static_skills:
                    if skill.effect_type == 'damage_increase' and (skill.target == target.name or skill.target == 'All'):
                        damage_modifiers.append(skill.value)
                    if skill.effect_type == 'defense_increase' and (skill.target == target.name or skill.target == 'All'):
                        # Implement defense increase if needed
                        pass

                # RNG skills
                for skill in attacker.rng_skills + [s for s in army_attacker.hero_skills if not s.once_per_battle]:
                    if skill.try_activate():
                        army_attacker.skill_activation_log[skill.name] = army_attacker.skill_activation_log.get(skill.name, 0) + 1
                        if skill.effect_type == 'damage_increase' and (skill.target == target.name or skill.target == 'All'):
                            damage_modifiers.append(skill.value)
                            battle_log.append(f"{attacker.name}'s skill '{skill.name}' activated!")
                        elif skill.effect_type == 'damage_decrease' and (skill.target == target.name or skill.target == 'All'):
                            if 'damage_decrease' not in attacker.status_effects:
                                attacker.status_effects['damage_decrease'] = {'value': skill.value, 'remaining_turns': skill.duration}
                                battle_log.append(f"{attacker.name}'s skill '{skill.name}' activated! Damage taken decreased.")
                        elif skill.effect_type == 'direct_attack' and skill.target == 'Back':
                            # Lancer attacks backline
                            backline_target = army_defender.troops.get('Marksman')
                            if backline_target and backline_target.alive:
                                target = backline_target
                                battle_log.append(f"{attacker.name}'s skill '{skill.name}' activated! Attacking back row.")
                        elif skill.effect_type == 'multi_attack':
                            # Marksman's 'Volley' skill
                            damage_modifiers.append(skill.value)
                            battle_log.append(f"{attacker.name}'s skill '{skill.name}' activated!")
                        elif skill.effect_type == 'burn':
                            # Apply burn status effect
                            burn_damage_per_troop = attacker.effective_stats['attack'] * (skill.value / 100)
                            if 'burn' not in target.status_effects:
                                target.status_effects['burn'] = {'damage': burn_damage_per_troop, 'remaining_turns': skill.duration}
                                battle_log.append(f"{attacker.name}'s skill '{skill.name}' activated! {target.name} is burning.")
                        elif skill.effect_type == 'stun':
                            if 'stun' not in target.status_effects:
                                target.status_effects['stun'] = {'remaining_turns': skill.duration}
                                battle_log.append(f"{attacker.name}'s skill '{skill.name}' activated! {target.name} is stunned.")
                        elif skill.effect_type == 'damage_taken_increase':
                            if 'damage_taken_increase' not in target.status_effects:
                                target.status_effects['damage_taken_increase'] = {'value': skill.value, 'remaining_turns': skill.duration}
                                battle_log.append(f"{attacker.name}'s skill '{skill.name}' activated! {target.name} takes more damage.")

                # Apply damage taken increase debuff
                if 'damage_taken_increase' in target.status_effects:
                    damage_modifiers.append(target.status_effects['damage_taken_increase']['value'])

                # Calculate damage
                damage, number_of_attackers = calculate_damage(attacker, target, damage_modifiers)
                apply_damage(target, damage, attacker, skill, number_of_attackers)
                battle_log.append(f"{army_attacker.name}'s {attacker.name} attacks {army_defender.name}'s {target.name} with {number_of_attackers} troops, dealing {damage:.2f} damage.")

                # Check if target is defeated
                if not target.alive:
                    battle_log.append(f"{army_defender.name}'s {target.name} has been defeated!")
                    army_defender.update_total_health()
                    # Update frontline targets
                    if target.position == 'Front':
                        frontline_targets = army_defender.get_frontline()
                        if not frontline_targets:
                            break  # No more targets

        # Check for victory
        if army_a.is_defeated() or army_b.is_defeated():
            break

    # Determine winner
    if army_a.is_defeated() and army_b.is_defeated():
        winner = "Draw"
    elif army_b.is_defeated():
        winner = army_a.name
    else:
        winner = army_b.name

    # Generate battle report
    battle_report = generate_battle_report(army_a, army_b, winner, turn)
    battle_log.append(battle_report)

    # Print battle log
    for entry in battle_log:
        print(entry)

def select_target_lancer(attacker, army_defender, army_attacker, battle_log):
    # Lancer has 'Ambusher' skill to attack backline
    backline_target = army_defender.troops.get('Marksman')
    ambusher_skill = next((skill for skill in attacker.rng_skills if skill.name == 'Ambusher'), None)
    if ambusher_skill and ambusher_skill.try_activate():
        army_attacker.skill_activation_log[ambusher_skill.name] = army_attacker.skill_activation_log.get(ambusher_skill.name, 0) + 1
        if backline_target and backline_target.alive:
            battle_log.append(f"{attacker.name}'s skill '{ambusher_skill.name}' activated! Attacking back row.")
            return backline_target
    # Otherwise, attack frontline
    frontline_targets = army_defender.get_frontline()
    return frontline_targets[0] if frontline_targets else backline_target

def generate_battle_report(army_a, army_b, winner, total_turns):
    report = f"\n--- Battle Report ---\n"
    report += f"Total Turns: {total_turns}\n"
    report += f"Winner: {winner}\n\n"
    for army in [army_a, army_b]:
        report += f"Army: {army.name}\n"
        total_kills = sum([troop.kills for troop in army.troops.values()])
        total_losses = sum([troop.initial_count - troop.count for troop in army.troops.values()])
        total_injured = total_losses  # Assuming losses represent injured troops
        survivors = sum([troop.count for troop in army.troops.values()])
        report += f"  Total Kills: {int(total_kills)}\n"
        report += f"  Total Injured: {int(total_injured)}\n"
        report += f"  Survivors: {int(survivors)}\n"
        for troop in army.troops.values():
            casualties = int(troop.initial_count - troop.count) if troop.count >= 0 else troop.initial_count
            remaining = int(troop.count) if troop.count >= 0 else 0
            report += f"  {troop.name}:\n"
            report += f"    Kills: {int(troop.kills)}\n"
            report += f"    Starting Count: {troop.initial_count}\n"
            report += f"    Remaining: {remaining}\n"
            report += f"    Injuries: {casualties}\n"
        report += f"  Skills Activated:\n"
        for skill_name, count in army.skill_activation_log.items():
            report += f"    {skill_name}: {count} times\n"
        report += "\n"
    return report

# Define troops and their skills

# Static Skills
master_brawler = Skill("Master Brawler", "damage_increase", 10, 1.0, target="All")  # Changed target to "All" for consistency
bands_of_steel = Skill("Bands of Steel", "defense_increase", 10, 1.0, target="All")
charge = Skill("Charge", "damage_increase", 10, 1.0, target="All")
ranged_strike = Skill("Ranged Strike", "damage_increase", 10, 1.0, target="All")

# RNG Skills
ambusher = Skill("Ambusher", "direct_attack", 0, 0.2, target="Back")
volley = Skill("Volley", "multi_attack", 0, 0.1)

# Hero Skills
# Dave's Hero Skills
pyromaniac = Skill("Pyromaniac", "burn", 40, 0.2, target="All", duration=3)
burning_resolve = Skill("Burning Resolve", "damage_increase", 25, 1.0, target="All", once_per_battle=True)
immolation = Skill("Immolation", "damage_taken_increase", 50, 0.5, target="All", duration=1)
dosage_boost_dave = Skill("Dosage Boost", "damage_increase", 200, 0.25, target="All", duration=1)
numbing_spores_dave = Skill("Numbing Spores", "stun", 0, 0.2, target="All", duration=1)
positional_battler = Skill("Positional Battler", "damage_increase", 25, 1.0, target="All", once_per_battle=True)

vigor_tactics_attack = 15  # Attack increase in percentage
vigor_tactics_defense = 10  # Defense increase in percentage
implacable_health = 10  # Health increase in percentage
implacable_defense = 10  # Defense increase in percentage

# Rally Joiner Health bonuses
rally_health_bonus = 100  # 100% health increase

# Brabo's Hero Skills
battle_manifesto = Skill("Battle Manifesto", "damage_increase", 25, 1.0, target="All", once_per_battle=True)
sword_mentor = Skill("Sword Mentor", "damage_increase", 25, 1.0, target="All", once_per_battle=True)
expert_swordsmanship = Skill("Expert Swordsmanship", "stun", 0, 0.2, target="All", duration=1)
poison_harpoon = Skill("Poison Harpoon", "damage_increase", 50, 0.5, target="All", duration=1)
dosage_boost_brabo = Skill("Dosage Boost", "damage_increase", 200, 0.25, target="All", duration=1)
numbing_spores_brabo = Skill("Numbing Spores", "stun", 0, 0.2, target="All", duration=1)
onslaught = Skill("Onslaught", "stun", 0, 0.2, target="All", duration=1)
iron_strength = Skill("Iron Strength", "damage_decrease", 50, 0.2, target="All", duration=2)

# Create troops for Dave
dave_infantry = TroopType(
    name='Infantry',
    base_attack=10,
    base_defense=13,
    base_lethality=10,
    base_health=15,
    count=60,
    bonuses={
        'attack': 90.46 + vigor_tactics_attack + implacable_health,  # 90.46% + 15% + 10% = 115.46%
        'defense': 69.05 + vigor_tactics_defense + implacable_defense,  # 69.05% + 10% + 10% = 89.05%
        'lethality': 10.65,  # Assuming this is 10.65% lethality bonus
        'health': 118.18 + rally_health_bonus + implacable_health  # 118.18% + 100% + 10% = 228.18%
    },
    static_skills=[master_brawler, bands_of_steel],
    rng_skills=[],
    position='Front'
)

dave_lancer = TroopType(
    name='Lancer',
    base_attack=13,
    base_defense=11,
    base_lethality=14,
    base_health=11,
    count=20,
    bonuses={
        'attack': 83.08 + vigor_tactics_attack + implacable_health,  # 83.08% + 15% + 10% = 108.08%
        'defense': 64.39 + vigor_tactics_defense + implacable_defense,  # 64.39% + 10% + 10% = 84.39%
        'lethality': 8.496,  # 8.496% lethality bonus
        'health': 94.31 + rally_health_bonus + implacable_health  # 94.31% + 100% + 10% = 204.31%
    },
    static_skills=[charge],
    rng_skills=[ambusher],
    position='Middle'
)

dave_marksman = TroopType(
    name='Marksman',
    base_attack=14,
    base_defense=10,
    base_lethality=15,
    base_health=10,
    count=20,
    bonuses={
        'attack': 82.65 + vigor_tactics_attack + implacable_health,  # 82.65% + 15% + 10% = 107.65%
        'defense': 63.85 + vigor_tactics_defense + implacable_defense,  # 63.85% + 10% + 10% = 83.85%
        'lethality': 8.478,  # 8.478% lethality bonus
        'health': 95.66 + rally_health_bonus + implacable_health  # 95.66% + 100% + 10% = 205.66%
    },
    static_skills=[ranged_strike],
    rng_skills=[volley],
    position='Back'
)

# Create troops for Brabo
brabo_infantry = TroopType(
    name='Infantry',
    base_attack=10,
    base_defense=13,
    base_lethality=10,
    base_health=15,
    count=20,
    bonuses={
        'attack': 77.95 + vigor_tactics_attack + implacable_health,  # 77.95% + 15% + 10% = 102.95%
        'defense': 69.05 + vigor_tactics_defense + implacable_defense,  # 69.05% + 10% + 10% = 89.05%
        'lethality': 9.892,  # 9.892% lethality bonus
        'health': 82.47 + rally_health_bonus + implacable_health  # 82.47% + 100% + 10% = 192.47%
    },
    static_skills=[master_brawler, bands_of_steel],
    rng_skills=[],
    position='Front'
)

brabo_lancer = TroopType(
    name='Lancer',
    base_attack=13,
    base_defense=11,
    base_lethality=14,
    base_health=11,
    count=20,
    bonuses={
        'attack': 69.91 + vigor_tactics_attack + implacable_health,  # 69.91% + 15% + 10% = 94.91%
        'defense': 61.50 + vigor_tactics_defense + implacable_defense,  # 61.50% + 10% + 10% = 81.50%
        'lethality': 8.523,  # 8.523% lethality bonus
        'health': 71.28 + rally_health_bonus + implacable_health  # 71.28% + 100% + 10% = 181.28%
    },
    static_skills=[charge],
    rng_skills=[ambusher],
    position='Middle'
)

brabo_marksman = TroopType(
    name='Marksman',
    base_attack=14,
    base_defense=10,
    base_lethality=15,
    base_health=10,
    count=20,
    bonuses={
        'attack': 74.97 + vigor_tactics_attack + implacable_health,  # 74.97% + 15% + 10% = 99.97%
        'defense': 66.15 + vigor_tactics_defense + implacable_defense,  # 66.15% + 10% + 10% = 86.15%
        'lethality': 9.076,  # 9.076% lethality bonus
        'health': 75.21 + rally_health_bonus + implacable_health  # 75.21% + 100% + 10% = 185.21%
    },
    static_skills=[ranged_strike],
    rng_skills=[volley],
    position='Back'
)

# Assemble armies
dave_troops = {
    'Infantry': dave_infantry,
    'Lancer': dave_lancer,
    'Marksman': dave_marksman
}

brabo_troops = {
    'Infantry': brabo_infantry,
    'Lancer': brabo_lancer,
    'Marksman': brabo_marksman
}

# Add hero skills to the armies
dave_army = Army(name='Dave', troops=dave_troops, hero_skills=[
    pyromaniac, burning_resolve, immolation, dosage_boost_dave, numbing_spores_dave, positional_battler
])

brabo_army = Army(name='Brabo', troops=brabo_troops, hero_skills=[
    battle_manifesto, sword_mentor, expert_swordsmanship, poison_harpoon, dosage_boost_brabo, numbing_spores_brabo, onslaught, iron_strength
])

# Simulate the battle
simulate_battle(dave_army, brabo_army)
