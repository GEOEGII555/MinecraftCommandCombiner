import warnings
import enum

class CombineMode(enum.Enum):
    ENTITY_NBT = 0
    SPAWN_EGG_NBT = 1
    SUMMON_CMD = 2
    GIVE_CMD_SPAWN_EGG = 3

def combine_commands_into_entity(commands: list[str]):
    commands.extend(["setblock ~ ~1 ~ command_block[facing=up]{auto:1b, Command:\"fill ~ ~ ~ ~ ~-3 ~ air\"}", "kill @e[type=command_block_minecart,distance=..1]"])
    entity = {
        'id': 'falling_block',
        'BlockState': {'Name': 'activator_rail'},
        'Time': 1,
        'Passengers': [{'id': 'command_block_minecart', 'Command': command} for command in commands]
    }
    entity = {
        'id': 'zombie',
        'Health': 0,
        'DeathTime': 19,
        'Passengers': [entity]
    }
    return {
        'id': 'falling_block',
        'Time': 1,
        'BlockState': {'Name': 'redstone_block'},
        'Passengers': [entity]
    }

def entity_to_summon_cmd(entityNBT: dict, x: int = '~', y: int = '~', z: int = '~'):
    entityID = entityNBT['id']
    del entityNBT['id']
    return f'summon {entityID} {x} {y} {z} {entityNBT}'

def command_to_spawn_egg(command: str):
    return {'EntityTag': {'BlockState': {'Name': 'command_block'}, 'id': 'falling_block', 'TileEntityData': {'auto': 1, 'Command': command}}}

def item_to_give_command(item: str, itemNBT: dict = {}, player: str = '@s'):
    return f'give {player} {item}{itemNBT}'

def combine_commands(commands: list[str], mode: CombineMode = CombineMode.ENTITY_NBT):
    entity = combine_commands_into_entity(commands)
    match mode:
        case CombineMode.ENTITY_NBT:
            return entity
        case CombineMode.SPAWN_EGG_NBT:
            return command_to_spawn_egg(entity_to_summon_cmd(entity))
        case CombineMode.SUMMON_CMD:
            command = entity_to_summon_cmd(entity, y='~1')
            if len(command) > 32000:
                warnings.warn('The command may be too long for a command block.')
            return command
        case CombineMode.GIVE_CMD_SPAWN_EGG:
            command = item_to_give_command('silverfish_spawn_egg', command_to_spawn_egg(entity_to_summon_cmd(entity, y='~1')))
            if len(command) > 32000:
                warnings.warn('The command may be too long for a command block.')
            return command
        case _:
            raise ValueError(f'Invalid combine mode: {mode}.')