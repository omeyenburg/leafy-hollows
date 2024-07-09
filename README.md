# Leafy Hollows
A cave game: You fell into a big cave full of monsters. Your goal is to escape alive. Fight monsters and upgrade your weapons to survive.
Leafy Hollows is an immersive cave adventure game where you find yourself trapped in an underground cavern full of dangerous monsters. Your mission is to fight your way through these creatures, upgrade your weapons, and ultimately escape alive.

## Prototype
A prototype version of the game is available in the prototype/ directory.

### Requirements
The prototype requires these packages alongside Python 3.11
- pyinstaller
- pyinstaller-hooks-contrib
- PyOpenGL
- PyOpenGL-accelerate
- pygame-ce
- numba (optional; required for shadows)
- opensimplex
- numpy
- noise

### Gameplay
You have limited resources and health, and you must strategically manage your weapons. While your weapons are essential for fighting monsters, they can also be consumed to restore health. Balancing offense and self-preservation is crucial to making it out alive.

### Creatures
The game features a variety of hostile creatures:

- Green Slime
- Yellow Slime
- Blue Slime
- Bat
- Goblin

### Weapons
Defeating monsters may reward you with powerful weapons. Each weapon comes with unique attributes that enhance your combat abilities. You can equip any weapon you own from your inventory, allowing you to choose the best tool for the situation.

- Stick: A generous weapon to start your journey. While simple, it gets the job done.
- Sword: A versatile weapon with a fast attack speed and decent range, perfect for agile combat.
- Axe: Known for its heavy and powerful swings, the axe delivers high damage.
- Pickaxe: A weapon that deals heavy damage attacks. Its weight allows it to break through tougher enemies.
- Bow: A ranged weapon that allows you to shoot arrows from a distance, keeping you safe while dealing damage to foes afar.

### Item Attribute
Weapons in Leafy Hollows can be enhanced with unique attributes, each providing different advantages in combat. Each weapon has 2 randomly chosen attributes. You can fuse two weapons with at least one common attribute to increase its level, further enhancing its power.

- piercing: Allows your weapon to cut through enemies, hitting 1 additional target per level in its path.
- ferocity: Enhances the weapon's aggressiveness, increasing damage and attack speed by 15 % per level each.
- vampire: Regenerate 5 % per level health with every successful hit, siphoning life from enemies.
- looting: Boosts weapon drop rates by 30 % per level and potential attribute levels on dropped weapons for every third level.
- explosive: Attacks detonate on impact, dealing 15 % per level of your weapon's damage to the target and nearby enemies.
- paralysis: Strikes have a 15 % per level chance to temporarily stun enemies.
- berserker: Increases damage by 25 % per level, but at the cost of a corresponding reduction in defense.
- agility: Increases your movement and attack speed by 20 % per level each, allowing for quicker strikes.
- soul drain: Absorb your enemies' souls, regenerating 20 % per level health with each successfull kill.
- shielding: Reduces damage taken by 5 % per level.
- critical: Increases the chance for a critical hit by 30 % per level.
- warrior: Increases your weapon's damage by 5 % per level per enemy around you.
- assassin: Increases your attack speed and crit chance by 20 % per level each.
- longshot: Expands your weapon's range by 20 % per level, allowing you to hit enemies from a greater distance.
