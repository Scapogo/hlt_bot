#!/usr/bin/env python3
# Python 3.6

# This library allows you to generate random numbers.
import random

# Logging allows you to save messages for yourself. This is required because the regular STDOUT
#   (print statements) are reserved for the engine-bot communication.
import logging

# Import the Halite SDK, which will let you interact with the game.
import hlt

# This library contains constant values.
from hlt import constants

# This library contains direction metadata to better interface with the game.
from hlt.positionals import Direction, Position

import operator
import numpy as np

""" <<<Game Begin>>> """

# This game object contains the initial game state.
game = hlt.Game()
# At this point "game" variable is populated with initial map data.
# This is a good place to do computationally expensive start-up pre-processing.
# As soon as you call "ready" function below, the 2 second per turn timer will start.
ship_status = {}

possible_direction = [Direction.North, Direction.South, Direction.East, Direction.West]

game.ready("ScapoBot")

# Now that your bot is initialized, save a message to yourself in the log file with some important information.
#   Here, you log here your id, which you can always fetch from the game object by using my_id.
logging.info("Successfully created bot! My Player ID is {}.".format(game.my_id))

""" <<<Game Loop>>> """

def get_random_move(ship, game_map, avoid_moves, shipyards):
    """Generate random move with some checking and addition to avoidance list"""
    options = [ Direction.North, Direction.South, Direction.East, Direction.West ]
    while True:
        move = random.choice(options)
        options.remove(move)
        new_position = ship.position.directional_offset(move)
        if new_position not in avoid_moves and new_position not in shipyards:
            avoid_moves.append(new_position)
            move = game_map.naive_navigate(ship, new_position)
            return move
        if len(options) == 0:
            return Direction.Still

def cheap_navigation_2(ship, game_map, avoid_moves, destination):
    """Get best direction to move towards target with avoid move check"""
    directions = game_map.get_unsafe_moves(ship.position, destination)

    forbiden_slots = [destination.directional_offset(Direction.North)]
    forbiden_slots.append(forbiden_slots[0].directional_offset(Direction.North))
    forbiden_slots.append(destination.directional_offset(Direction.South))
    forbiden_slots.append(forbiden_slots[2].directional_offset(Direction.South))

    logging.info("Possible directions: {}".format(directions))
    logging.info("Avoid moves: {}".format(avoid_moves))
    logging.info("Forbiden slots: {}".format(forbiden_slots))

    if len(directions) == 1:
        new_position = ship.position.directional_offset(directions[0])
        if not game_map[new_position].is_occupied and not new_position in avoid_moves and new_position not in forbiden_slots:
            return directions[0]
        else:
            if directions[0] in [Direction.South, Direction.North]:
                new_position = ship.position.directional_offset(Direction.East)
                if not game_map[new_position].is_occupied and not new_position in avoid_moves and new_position not in forbiden_slots:
                    x_value_1 = game_map[new_position].halite_amount + 500
                    direction_1 = Direction.East
                else:
                    x_value_1 = 9999
                
                new_position = ship.position.directional_offset(Direction.West)
                if not game_map[new_position].is_occupied and not new_position in avoid_moves and new_position not in forbiden_slots:
                    x_value_2 = game_map[new_position].halite_amount + 500
                    direction_2 = Direction.West
                else:
                    x_value_2 = 9999

                if x_value_1 == 9999 and x_value_2 == 9999:
                    return Direction.Still

                if x_value_1 <= x_value_2:
                    return direction_1
                else:
                    return direction_2
            elif directions[0] in [Direction.East, Direction.West]:
                new_position = ship.position.directional_offset(Direction.South)
                if not game_map[new_position].is_occupied and not new_position in avoid_moves and new_position not in forbiden_slots:
                    y_value_1 = game_map[new_position].halite_amount + 500
                    direction_1 = Direction.South
                else:
                    y_value_1 = 9999
                    direction_1 = Direction.Still
                
                new_position = ship.position.directional_offset(Direction.North)
                if not game_map[new_position].is_occupied and not new_position in avoid_moves and new_position not in forbiden_slots:
                    y_value_2 = game_map[new_position].halite_amount + 500
                    direction_2 = Direction.North
                else:
                    y_value_2 = 9999
                    direction_2 = Direction.Still

                if y_value_1 == 9999 and y_value_2 == 9999:
                    return Direction.Still

                if y_value_1 <= y_value_2:
                    return direction_1
                else:
                    return direction_2
            else:
                return Direction.Still
    elif len(directions) == 2:
        deadend = False
        new_position = ship.position.directional_offset(directions[0])
        new_directions = game_map.get_unsafe_moves(new_position, destination)
        if len(new_directions) == 1:
            new_position_2 = new_position.directional_offset(new_directions[0])
            if new_position_2 in forbiden_slots:
                deadend = True
        if not game_map[new_position].is_occupied and not new_position in avoid_moves and new_position not in forbiden_slots and not deadend:
            x_value = game_map[new_position].halite_amount
        else:
            x_value = 9999

        deadend = False
        new_position = ship.position.directional_offset(directions[1])
        new_directions = game_map.get_unsafe_moves(new_position, destination)
        if len(new_directions) == 1:
            new_position_2 = new_position.directional_offset(new_directions[0])
            if new_position_2 in forbiden_slots:
                deadend = True
        if not game_map[new_position].is_occupied and not new_position in avoid_moves and new_position not in forbiden_slots and not deadend:
            y_value = game_map[new_position].halite_amount
        else:
            y_value = 9999

        if x_value == 9999 and y_value == 9999:
            return Direction.Still

        if x_value <= y_value:
            return directions[0]
        elif x_value > y_value:
            return directions[1]
    else:
        return Direction.Still

def cheap_navigation(ship, game_map, avoid_moves, destination):
    """Check cheaper way for navigation"""
    directions = []
    # logging.info("Ship position: {}".format(ship.position.x))
    ship_position = [ship.position.x, ship.position.y]
    dest_position = [destination.x, destination.y]

    forbiden_slots = [destination.directional_offset(Direction.North)]
    forbiden_slots.append(forbiden_slots[0].directional_offset(Direction.North))

    x_dist = destination.x - ship.position.x
    y_dist = destination.y - ship.position.y

    logging.info("Navi: shipid {} x_dist {} y_dist {}".format(ship.id, x_dist, y_dist))
    
    if x_dist > 0 or (x_dist < - game_map.width // 2):
        new_position = ship.position.directional_offset(Direction.East)
        if not game_map[new_position].is_occupied and not new_position in avoid_moves and new_position not in forbiden_slots:
            x_value = game_map[new_position].halite_amount
            directions.append(Direction.East)
        else:
            x_value = 9999
            directions.append(Direction.Still)
    elif x_dist < 0 or (x_dist > game_map.width // 2):
        new_position = ship.position.directional_offset(Direction.West)
        if not game_map[new_position].is_occupied and not new_position in avoid_moves and new_position not in forbiden_slots:
            x_value = game_map[new_position].halite_amount
            directions.append(Direction.West)
        else:
            x_value = 9999
            directions.append(Direction.Still)
    else:
        new_position = ship.position.directional_offset(Direction.East)
        if not game_map[new_position].is_occupied and not new_position in avoid_moves and new_position not in forbiden_slots:
            x_value_1 = game_map[new_position].halite_amount + 500
            direction_1 = Direction.East
        else:
            x_value_1 = 9999
            direction_1 = Direction.Still
        
        new_position = ship.position.directional_offset(Direction.West)
        if not game_map[new_position].is_occupied and not new_position in avoid_moves and new_position not in forbiden_slots:
            x_value_2 = game_map[new_position].halite_amount + 500
            direction_2 = Direction.West
        else:
            x_value_2 = 9999
            direction_2 = Direction.Still

        if x_value_1 < x_value_2:
            x_value = x_value_1
            directions.append(direction_1)
        else:
            x_value = x_value_2
            directions.append(direction_2)

    if y_dist > 0 or (y_dist < - game_map.height // 2):
        new_position = ship.position.directional_offset(Direction.South)
        if not game_map[new_position].is_occupied and not new_position in avoid_moves and new_position not in forbiden_slots:
            y_value = game_map[new_position].halite_amount
            directions.append(Direction.South)
        else:
            y_value = 9999
            directions.append(Direction.Still)
    elif y_dist < 0 or (y_dist > game_map.height // 2):
        new_position = ship.position.directional_offset(Direction.North)
        if not game_map[new_position].is_occupied and not new_position in avoid_moves and new_position not in forbiden_slots:
            y_value = game_map[new_position].halite_amount
            directions.append(Direction.North)
        else:
            y_value = 9999
            directions.append(Direction.Still)
    else:
        new_position = ship.position.directional_offset(Direction.South)
        if not game_map[new_position].is_occupied and not new_position in avoid_moves and new_position not in forbiden_slots:
            y_value_1 = game_map[new_position].halite_amount + 500
            direction_1 = Direction.South
        else:
            y_value_1 = 9999
            direction_1 = Direction.Still
        
        new_position = ship.position.directional_offset(Direction.North)
        if not game_map[new_position].is_occupied and not new_position in avoid_moves and new_position not in forbiden_slots:
            y_value_2 = game_map[new_position].halite_amount + 500
            direction_2 = Direction.North
        else:
            y_value_2 = 9999
            direction_2 = Direction.Still

        if y_value_1 < y_value_2:
            y_value = y_value_1
            directions.append(direction_1)
        else:
            y_value = y_value_2
            directions.append(direction_2)

    if x_value < y_value:
        direction = directions[0]
        # logging.info("Selected move: shipid {} source x".format(ship.id))
    else:
        direction = directions[1]
        # logging.info("Selected move: shipid {} source y".format(ship.id))

    return direction

def selfdestruct_navigation(ship, game_map, avoid_moves, destination, myself, dropoff_positions):
    """Check cheaper way for navigation"""
    directions = []
    # logging.info("Ship position: {}".format(ship.position.x))
    ship_position = [ship.position.x, ship.position.y]
    dest_position = [destination.x, destination.y]

    x_dist = destination.x - ship.position.x
    y_dist = destination.y - ship.position.y
    
    if x_dist > 0 or (x_dist < - game_map.width // 2):
        new_position = ship.position.directional_offset(Direction.East)
        if (not game_map[new_position].is_occupied and not new_position in avoid_moves) or new_position in dropoff_positions:
            x_value = game_map[new_position].halite_amount
            directions.append(Direction.East)
        else:
            x_value = 9999
            directions.append(Direction.Still)
    elif x_dist < 0 or (x_dist > game_map.width // 2):
        new_position = ship.position.directional_offset(Direction.West)
        if (not game_map[new_position].is_occupied and not new_position in avoid_moves) or new_position in dropoff_positions:
            x_value = game_map[new_position].halite_amount
            directions.append(Direction.West)
        else:
            x_value = 9999
            directions.append(Direction.Still)
    else:
        x_value = 9999
        directions.append(Direction.Still)

    if y_dist > 0 or (y_dist < - game_map.height // 2):
        new_position = ship.position.directional_offset(Direction.South)
        if (not game_map[new_position].is_occupied and not new_position in avoid_moves) or new_position in dropoff_positions:
            y_value = game_map[new_position].halite_amount
            directions.append(Direction.South)
        else:
            y_value = 9999
            directions.append(Direction.Still)
    elif y_dist < 0 or (y_dist > game_map.height // 2):
        new_position = ship.position.directional_offset(Direction.North)
        if (not game_map[new_position].is_occupied and not new_position in avoid_moves) or new_position in dropoff_positions:
            y_value = game_map[new_position].halite_amount
            directions.append(Direction.North)
        else:
            y_value = 9999
            directions.append(Direction.Still)
    else:
        y_value = 9999
        directions.append(Direction.Still)

    if x_value < y_value:
        direction = directions[0]
    else:
        direction = directions[1]

    return direction

def get_closest_dropoff(ship, game_map, myself):
    """
    Find closest dropoff for actual ship
    Return position of closest dropoff/shipyard
    """
    closest_doff = myself.shipyard.position
    closest_doff_dist = game_map.calculate_distance(ship.position, myself.shipyard.position)

    if len(myself.get_dropoffs()) > 0:
        for dropoff in myself.get_dropoffs():
            dist_to_dropoff = game_map.calculate_distance(ship.position, dropoff.position)
            if closest_doff_dist > dist_to_dropoff:
                # logging.info("Old distance: {} new distance: {}".format(closest_doff_dist, dist_to_dropoff))
                closest_doff_dist = dist_to_dropoff
                closest_doff = dropoff.position
    
    return closest_doff

def get_distance_to_dropoff(ship, game_map, myself):
    """Get distance to closest dropoff"""
    closest_distance = game_map.calculate_distance(ship.position, myself.shipyard.position)

    dooffs = myself.get_dropoffs()

    for dooff in dooffs:
        doff_distance = game_map.calculate_distance(ship.position, dooff.position)
        if closest_distance > doff_distance:
            closest_distance = doff_distance

    return closest_distance

def get_sweet_spots(game_map, turn_number):
    """Return array of good spots on map"""
    good_areas = []
    max_turn = 25*(game_map.width - 32)/8 + 401
    halite_coeff_max = 1.2

    halite_coeff = (max_turn - (max_turn / 2))/turn_number
    logging.info("Halite coeff: {}".format(halite_coeff))

    halite_coeff = halite_coeff_max if halite_coeff > halite_coeff_max else halite_coeff

    for x in range(game_map.width):
        for y in range(game_map.height):
            pos = Position(x,y)
            if game_map[pos].halite_amount > (350 * halite_coeff):
                good_areas.append(pos)

    return good_areas

def sort_sweet_spots(game_map, act_position, good_spots):
    """Return 3 closest positions from good spots closest to actual position"""
    distance_list = {}

    for good_spot in good_spots:
        distance = game_map.calculate_distance(act_position, good_spot)
        if distance < 15:
            distance_list[distance] = good_spot

    dist_by_value = sorted(distance_list.items(), key=lambda kv: kv[0])

    if len(dist_by_value) > 3:
        dist_by_value = dist_by_value[:3]

    return_list = []
    for item in dist_by_value:
        return_list.append(item[1])

    return return_list

def check_direction_space(game_map, ship, myself, cmd_dir, avoid_moves):
    """Look forward if there is any ship move to less occupied space"""
    positions = [ship.position.directional_offset(cmd_dir)]
    positions.append(positions[-1].directional_offset(cmd_dir))
    positions.append(positions[-1].directional_offset(cmd_dir))
    logging.info("Direction space: {}".format(positions))
    ship_present = False

    for position in positions:
        if game_map[position].is_occupied:
            ship_present = True
            break

    if cmd_dir == Direction.East:
        alternative_directions = [Direction.South, Direction.North]
    elif cmd_dir == Direction.West:
        alternative_directions = [Direction.South, Direction.North]
    elif cmd_dir == Direction.South:
        alternative_directions = [Direction.East, Direction.West]
    elif cmd_dir == Direction.North:
        alternative_directions = [Direction.East, Direction.West]

    if ship_present:
        direction = random.choice(alternative_directions)
        move = ship.position.directional_offset(direction)
        alternative_directions.remove(direction)
        if move not in avoid_moves and not game_map[move].is_occupied:
            return direction
        else:
            direction = alternative_directions[0]
            move = ship.position.directional_offset(direction)
            if move not in avoid_moves and not game_map[move].is_occupied:
                return direction
            else:
                return Direction.Still
    else:
        if positions[0] not in avoid_moves and not game_map[positions[0]].is_occupied:
            return cmd_dir
        else:
            return Direction.Still

def get_target_direction(source, target):
    """
    Returns where in the cardinality spectrum the target is from source. e.g.: North, East; South, West; etc.
    NOTE: Ignores toroid
    :param source: The source position
    :param target: The target position
    :return: A list containing the valid Direction.
    """
    directions = []

    vertical = Direction.South if target.y > source.y else Direction.North if target.y < source.y else None
    horizontal = Direction.East if target.x > source.x else Direction.West if target.x < source.x else None

    if vertical is not None:
        directions.append(vertical)
    if horizontal is not None:
        directions.append(horizontal)

    return directions

def get_dropoff_list(myself):
    """Get list of dropoff positions"""
    dropoff_positions = []

    dropoffs = me.get_dropoffs()
    
    for dropoff in dropoffs:
        dropoff_positions.append(dropoff.position)

    dropoff_positions = dropoff_positions + me.shipyard.position

    return dropoff_positions

def get_data(myself, game_map):
    """Collect data to arrray for RL input"""
    out_data = np.zeroes([game_map.width, game_map.height, 4])

    for x in range(game_map.width):
        for y in range(game_map.height):
            actual_position = Position(x, y)
            out_data[x, y, 0] = game_map[act_position].halite_amount
            if game_map[act_position].is_occupied:
                out_data[x, y, 2] = 1
            if game_map[act_position].has_structure:
                out_data[x, y, 3] = 1

    ships = myself.get_ships

    for ship in ships:
        out_data[ship.position.x, ship.position.y, 1] = ship.halite_amount
        out_data[ship.position.x, ship.position.y, 2] = 2

while True:
    # This loop handles each turn of the game. The game object changes every turn, and you refresh that state by
    #   running update_frame().
    game.update_frame()
    # You extract player metadata and the updated map metadata here for convenience.
    me = game.me
    game_map = game.game_map
    # logging.info("Game map size: {},{}".format(game_map.width, game_map.height))
    good_spots = get_sweet_spots(game_map, game.turn_number)

    if game_map.width > 38:
        max_dropoff = 1
    else:
        max_dropoff = 0

    max_turn = 25*(game_map.width - 32)/8 + 401

    self_destruct = False
    if game.turn_number > max_turn - 25:
        self_destruct = True

    halite_available = me.halite_amount

    exit_slot = me.shipyard.position

    # A command queue holds all the commands you will run this turn. You build this list up and submit it at the
    #   end of the turn.
    command_queue = []
    avoid_moves = []
    ship_count = len(me.get_ships())
    dropoff_count = len(me.get_dropoffs())
    dropoff_positions = []
    for doff in me.get_dropoffs():
        dropoff_positions.append(doff.position)

    dropoff_positions.append(me.shipyard.position)

    # logging.info("Dropoffs: {}".format(dropoff_positions))
    # logging.info("Turn start: {}".format(ship_status))

    for ship in me.get_ships():
        # For each of your ships, move randomly if the ship is on a low halite location or the ship is full.
        #   Else, collect halite.
        harvesting_ships = sum(map(("harvesting").__eq__, ship_status.values()))

        if ship.id not in ship_status:
            ship_status[ship.id] = "harvesting"
        if ship_count // 1.1 < harvesting_ships and ship_status[ship.id] == "exploring":
            ship_status[ship.id] = "harvesting"

        if self_destruct:
            if ship.position in dropoff_positions: # ship.position == me.shipyard.position or 
                command_queue.append(ship.stay_still())
                continue
            else:
                close_dropoff = get_closest_dropoff(ship, game_map, me)
                # move = selfdestruct_navigation(ship, game_map, avoid_moves, me.shipyard.position, me)
                move = selfdestruct_navigation(ship, game_map, avoid_moves, close_dropoff, me, dropoff_positions)
                if ship.position.directional_offset(move) not in dropoff_positions: #!= me.shipyard.position:
                    avoid_moves.append(game_map.normalize(ship.position.directional_offset(move)))
                command_queue.append(ship.move(move))
                # logging.info("Selfdestruct: move {} ship id {}".format(move, ship.id))
                continue
        elif ship_status[ship.id] == "returning":
            if ship.position == me.shipyard.position or ship.position in dropoff_positions:
                ship_status[ship.id] = "harvesting"
                harv_direction = random.choice([Direction.North, Direction.South])
                north_position = ship.position.directional_offset(harv_direction)
                if not game_map[north_position].is_occupied and north_position not in avoid_moves:
                    avoid_moves.append(game_map.normalize(north_position))
                    command_queue.append(ship.move(harv_direction))
                    continue
            else:
                # distance_to_base = game_map.calculate_distance(ship.position, me.shipyard.position)
                close_doff = get_closest_dropoff(ship, game_map, me)
                # move = cheap_navigation(ship, game_map, avoid_moves, close_doff)
                move = cheap_navigation_2(ship, game_map, avoid_moves, close_doff)
                logging.info("Chap move 2: ship id {} move {}".format(ship.id, move))
                avoid_moves.append(game_map.normalize(ship.position.directional_offset(move)))
                command_queue.append(ship.move(move))
                continue
        elif ship_status[ship.id] == "harvesting" and not ship.is_full: #ship.halite_amount < constants.MAX_HALITE / 1.5:
            if ship.position != me.shipyard.position:
                """If ship is not in shipyard and looking for halite"""
                surroundings = ship.position.get_surrounding_cardinals()
                actual_cell = ship.position
                best_cell = ship.position
                # logging.info("Actual: {} Best: {}".format(actual_cell, best_cell))
                if game_map[best_cell].halite_amount < 50:
                    """If actual cell halite amount is low then look for new direction"""
                    for cell in surroundings:
                        if game_map[best_cell].halite_amount < game_map[cell].halite_amount/2 and not game_map[cell].is_occupied and cell not in avoid_moves and cell not in dropoff_positions:
                            best_cell = cell
                    # Sort list of good spots based on ship position
                    sweet_spots = sort_sweet_spots(game_map, ship.position, good_spots)
                    
                    if len(sweet_spots) > 0:
                        # Continue on the way to sweet spot only in actual surrounding is not good enought
                        if game_map[sweet_spots[0]].halite_amount > game_map[best_cell].halite_amount*2.5:
                            best_cell = sweet_spots[0]

                # logging.info("Selected: {}".format(best_cell))
                if best_cell == actual_cell:
                    """If we are actually sitting on best cell"""
                    if game_map[best_cell].halite_amount == 0:
                        move = get_random_move(ship, game_map, avoid_moves, dropoff_positions)
                        if move is not None:
                            logging.info("Random move: {}".format(move))
                            command_queue.append(ship.move(move))
                        else:
                            command_queue.append(ship.stay_still())
                    else:
                        command_queue.append(ship.stay_still())
                else:
                    # cmd_dir = possible_direction[ship.id%4]
                    cmd_dir = get_target_direction(actual_cell, best_cell)[0]
                    # logging.info("ADirection: {}".format(cmd_dir))
                    move = check_direction_space(game_map, ship, me, cmd_dir, avoid_moves)
                    logging.info("Returned move: ship id {} move {}".format(ship.id, move))
                    avoid_moves.append(game_map.normalize(ship.position.directional_offset(move)))
                    # move = game_map.naive_navigate(ship, best_cell)
                    command_queue.append(ship.move(move))
                continue
        elif ship.is_full:
            distance_to_base = get_distance_to_dropoff(ship, game_map, me)
            if dropoff_count < max_dropoff and distance_to_base > 10 and game_map[ship.position].halite_amount > 200 and me.halite_amount >= constants.DROPOFF_COST:
                command_queue.append(ship.make_dropoff())
                halite_available -= 4000
            else:
                ship_status[ship.id] = "returning"
                close_doff = get_closest_dropoff(ship, game_map, me)
                # move = cheap_navigation(ship, game_map, avoid_moves, close_doff)
                move = cheap_navigation_2(ship, game_map, avoid_moves, close_doff)
                logging.info("Chap move 2: ship id {} move {}".format(ship.id, move))
                avoid_moves.append(game_map.normalize(ship.position.directional_offset(move)))
                command_queue.append(ship.move(move))
            continue

        if game_map[ship.position].halite_amount < constants.MAX_HALITE / 10 or ship.is_full:
            logging.info("Bad part id: {}".format(ship.id))
            surroundings = ship.position.get_surrounding_cardinals()
            actual_cell = ship.position
            best_cell = ship.position
            # logging.info("Actual: {} Best: {}".format(actual_cell, best_cell))
            if game_map[best_cell].halite_amount < 50:
                """If actual cell halite amount is low then look for new direction"""
                for cell in surroundings:
                    if game_map[best_cell].halite_amount < game_map[cell].halite_amount/2 and not game_map[cell].is_occupied and cell not in avoid_moves and cell not in dropoff_positions:
                        best_cell = cell
                # Sort list of good spots based on ship position
                sweet_spots = sort_sweet_spots(game_map, ship.position, good_spots)
                
                if len(sweet_spots) > 0:
                    # Continue on the way to sweet spot only in actual surrounding is not good enought
                    if game_map[sweet_spots[0]].halite_amount > game_map[best_cell].halite_amount*2.5:
                        best_cell = sweet_spots[0]

            # logging.info("Selected: {}".format(best_cell))
            if best_cell == actual_cell:
                """If we are actually sitting on best cell"""
                if game_map[best_cell].halite_amount == 0:
                    move = get_random_move(ship, game_map, avoid_moves, dropoff_positions)
                    if move is not None:
                        logging.info("Random move: {}".format(move))
                        command_queue.append(ship.move(move))
                    else:
                        command_queue.append(ship.stay_still())
                else:
                    command_queue.append(ship.stay_still())
            else:
                # cmd_dir = possible_direction[ship.id%4]
                cmd_dir = get_target_direction(actual_cell, best_cell)[0]
                # logging.info("ADirection: {}".format(cmd_dir))
                move = check_direction_space(game_map, ship, me, cmd_dir, avoid_moves)
                logging.info("Returned move: ship id {} move {}".format(ship.id, move))
                avoid_moves.append(game_map.normalize(ship.position.directional_offset(move)))
                # move = game_map.naive_navigate(ship, best_cell)
                command_queue.append(ship.move(move))
        else:
            command_queue.append(ship.stay_still())

    # If the game is in the first 200 turns and you have enough halite, spawn a ship.
    # Don't spawn a ship if you currently have a ship at port, though - the ships will collide.
    turn_no = game.turn_number

    ship_optimal_count = turn_no // 5
    if game_map.width < 35:
        max_ships = 26 + dropoff_count * 3
    else:
        max_ships = 28 + dropoff_count * 3

    ship_optimal_count = ship_optimal_count if ship_optimal_count < max_ships else max_ships

    if halite_available >= constants.SHIP_COST and not game_map[me.shipyard].is_occupied and (ship_count < ship_optimal_count or ship_count < 5) and not me.shipyard.position in avoid_moves and not self_destruct:        
        command_queue.append(me.shipyard.spawn())

    # logging.info("Ship types: {}".format(ship_status))
    # Send your moves back to the game environment, ending this turn.
    game.end_turn(command_queue)
