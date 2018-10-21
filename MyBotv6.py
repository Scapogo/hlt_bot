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

""" <<<Game Begin>>> """

# This game object contains the initial game state.
game = hlt.Game()
# At this point "game" variable is populated with initial map data.
# This is a good place to do computationally expensive start-up pre-processing.
# As soon as you call "ready" function below, the 2 second per turn timer will start.
ship_status = {}

game.ready("ScapoBotv6")

# Now that your bot is initialized, save a message to yourself in the log file with some important information.
#   Here, you log here your id, which you can always fetch from the game object by using my_id.
logging.info("Successfully created bot! My Player ID is {}.".format(game.my_id))

""" <<<Game Loop>>> """

def get_random_move(ship, game_map, avoid_moves):
    """Generate random move with some checking and addition to avoidance list"""
    options = [ Direction.North, Direction.South, Direction.East, Direction.West ]
    while True:
        move = random.choice(options)
        options.remove(move)
        new_position = ship.position.directional_offset(move)
        if new_position not in avoid_moves:
            avoid_moves.append(new_position)
            move = game_map.naive_navigate(ship, new_position)
            return move
        if len(options) == 0:
            return ship.position

def cheap_navigation(ship, game_map, avoid_moves, destination):
    """Check cheaper way for navigation"""
    directions = []
    logging.info("Ship position: {}".format(ship.position.x))
    ship_position = [ship.position.x, ship.position.y]
    dest_position = [destination.x, destination.y]

    x_dist = destination.x - ship.position.x
    y_dist = destination.y - ship.position.y
    
    if x_dist > 0 or (x_dist < - game_map.width // 2):
        new_position = ship.position.directional_offset(Direction.East)
        if not game_map[new_position].is_occupied and not new_position in avoid_moves:
            x_value = game_map[new_position].halite_amount
            directions.append(Direction.East)
        else:
            oposite_position = ship.position.directional_offset(Direction.West)
            if not game_map[oposite_position].is_occupied and not oposite_position in avoid_moves:
                x_value = game_map[oposite_position].halite_amount + 100
                directions.append(Direction.West)
            else:
                x_value = 9999
                directions.append(Direction.Still)
    elif x_dist < 0 or (x_dist > game_map.width // 2):
        new_position = ship.position.directional_offset(Direction.West)
        if not game_map[new_position].is_occupied and not new_position in avoid_moves:
            x_value = game_map[new_position].halite_amount
            directions.append(Direction.West)
        else:
            oposite_position = ship.position.directional_offset(Direction.East)
            if not game_map[oposite_position].is_occupied and not oposite_position in avoid_moves:
                x_value = game_map[oposite_position].halite_amount + 100
                directions.append(Direction.East)
            else:
                x_value = 9999
                directions.append(Direction.Still)
    else:
        x_value = 9999
        directions.append(Direction.Still)

    if y_dist > 0 or (y_dist < - game_map.height // 2):
        new_position = ship.position.directional_offset(Direction.South)
        if not game_map[new_position].is_occupied and not new_position in avoid_moves:
            y_value = game_map[new_position].halite_amount
            directions.append(Direction.South)
        else:
            oposite_position = ship.position.directional_offset(Direction.North)
            if not game_map[oposite_position].is_occupied and not oposite_position in avoid_moves:
                y_value = game_map[oposite_position].halite_amount + 100
                directions.append(Direction.North)
            else:
                y_value = 9999
                directions.append(Direction.Still)
    elif y_dist < 0 or (y_dist > game_map.height // 2):
        new_position = ship.position.directional_offset(Direction.North)
        if not game_map[new_position].is_occupied and not new_position in avoid_moves:
            y_value = game_map[new_position].halite_amount
            directions.append(Direction.North)
        else:
            oposite_position = ship.position.directional_offset(Direction.South)
            if not game_map[oposite_position].is_occupied and not oposite_position in avoid_moves:
                y_value = game_map[oposite_position].halite_amount + 100
                directions.append(Direction.South)
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

def closest_dropoff(ship, game_map, myself, dist_to_base):
    """Find closest dropoff for actual ship"""
    closest_doff = myself.shipyard.position
    closest_doff_dist = dist_to_base

    if len(myself.get_dropoffs()) > 0:
        for dropoff in myself.get_dropoffs():
            dist_to_dropoff = game_map.calculate_distance(ship.position, dropoff.position)
            if closest_doff_dist > dist_to_dropoff:
                logging.info("Old distance: {} new distance: {}".format(closest_doff_dist, dist_to_dropoff))
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

def get_sweet_spots(game_map):
    """Return array of good spots on map"""
    good_areas = []
    for x in range(game_map.width):
        for y in range(game_map.height):
            pos = Position(x,y)
            if game_map[pos].halite_amount > 600:
                good_areas.append(pos)

    return good_areas

def sort_sweet_spots(game_map, act_position, good_spots):
    """Return 3 closest positions from good spots closest to actual position"""
    distance_list = {}

    for good_spot in good_spots:
        distance = game_map.calculate_distance(act_position, good_spot)
        if distance < 15:
            distance_list[distance] = good_spot
    logging.info("Good spots: {}".format(good_spots))
    
    dist_by_value = sorted(distance_list.items(), key=lambda kv: kv[0])

    if len(dist_by_value) > 3:
        dist_by_value = dist_by_value[:3]

    return_list = []
    for item in dist_by_value:
        return_list.append(item[1])

    logging.info(return_list)

    return return_list

while True:
    # This loop handles each turn of the game. The game object changes every turn, and you refresh that state by
    #   running update_frame().
    game.update_frame()
    # You extract player metadata and the updated map metadata here for convenience.
    me = game.me
    game_map = game.game_map
    # logging.info("Game map size: {},{}".format(game_map.width, game_map.height))
    good_spots = get_sweet_spots(game_map)

    sweet_spots = sort_sweet_spots(game_map, me.shipyard.position, good_spots)

    # A command queue holds all the commands you will run this turn. You build this list up and submit it at the
    #   end of the turn.
    command_queue = []
    avoid_moves = []
    ship_count = len(me.get_ships())
    dropoff_count = len(me.get_dropoffs())
    dropoff_positions = []
    for doff in me.get_dropoffs():
        dropoff_positions.append(doff.position)

    logging.info("Turn start: {}".format(ship_status))

    for ship in me.get_ships():
        # For each of your ships, move randomly if the ship is on a low halite location or the ship is full.
        #   Else, collect halite.
        harvesting_ships = sum(map(("harvesting").__eq__, ship_status.values()))

        if ship.id not in ship_status:
            ship_status[ship.id] = "harvesting"
        if ship_count // 1.1 < harvesting_ships and ship_status[ship.id] == "exploring":
            ship_status[ship.id] = "harvesting"

        if ship_status[ship.id] == "returning":
            if ship.position == me.shipyard.position or ship.position in dropoff_positions:
                ship_status[ship.id] = "harvesting" # "exploring"
            else:
                distance_to_base = game_map.calculate_distance(ship.position, me.shipyard.position)
                close_doff = closest_dropoff(ship, game_map, me, distance_to_base)
                move = cheap_navigation(ship, game_map, avoid_moves, close_doff)
                avoid_moves.append(ship.position.directional_offset(move))
                command_queue.append(ship.move(move))
                continue
        elif ship_status[ship.id] == "harvesting" and not ship.is_full: #ship.halite_amount < constants.MAX_HALITE / 1.5:
            if ship.position != me.shipyard.position:
                surroundings = ship.position.get_surrounding_cardinals()
                # logging.info("Surroundings: {}".format(surroundings))
                actual_cell = ship.position
                best_cell = ship.position
                # logging.info("Actual: {} Best: {}".format(actual_cell, best_cell))
                if game_map[best_cell].halite_amount < 75:
                    # sweet_spots = sort_sweet_spots(game_map, ship.position, good_spots)
                    # if len(sweet_spots) > 0 and not game_map[sweet_spots[0]].is_occupied and not sweet_spots[0] in avoid_moves:
                    #     best_cell = sweet_spots[0]
                    # else:
                    for cell in surroundings:
                        if game_map[best_cell].halite_amount < game_map[cell].halite_amount/2 and not game_map[cell].is_occupied and cell not in avoid_moves:
                            # logging.info("Actual: {} New: {}".format(game_map[best_cell].halite_amount, game_map[cell].halite_amount/3))
                            best_cell = cell
                    

                # logging.info("Selected: {}".format(best_cell))
                if best_cell == actual_cell:
                    if game_map[best_cell].halite_amount == 0:
                        move = get_random_move(ship, game_map, avoid_moves)
                        command_queue.append(ship.move(move))
                    else:
                        command_queue.append(ship.stay_still())
                else:
                    move = game_map.naive_navigate(ship, best_cell)
                    command_queue.append(ship.move(move))
                continue
        elif ship.is_full: # ship.halite_amount >= constants.MAX_HALITE / 1.5:
            distance_to_base = get_distance_to_dropoff(ship, game_map, me)
            if dropoff_count < 2 and distance_to_base > 8 and game_map[ship.position].halite_amount > 200 and me.halite_amount >= constants.DROPOFF_COST:
                command_queue.append(ship.make_dropoff())
            else:
                ship_status[ship.id] = "returning"
                close_doff = closest_dropoff(ship, game_map, me, distance_to_base)
                move = cheap_navigation(ship, game_map, avoid_moves, close_doff)
                avoid_moves.append(ship.position.directional_offset(move))
                command_queue.append(ship.move(move))
            continue

        if game_map[ship.position].halite_amount < constants.MAX_HALITE / 10 or ship.is_full:
            move = get_random_move(ship, game_map, avoid_moves)
            command_queue.append(ship.move(move))
        else:
            command_queue.append(ship.stay_still())

    # If the game is in the first 200 turns and you have enough halite, spawn a ship.
    # Don't spawn a ship if you currently have a ship at port, though - the ships will collide.
    turn_no = game.turn_number

    ship_optimal_count = turn_no // 15
    if game_map.width < 35:
        max_ships = 13 + dropoff_count * 3
    else:
        max_ships = 15 + dropoff_count * 3

    ship_optimal_count = ship_optimal_count if ship_optimal_count < max_ships else max_ships

    # TODO: vic zelvicek
    if me.halite_amount >= constants.SHIP_COST and not game_map[me.shipyard].is_occupied and (ship_count < ship_optimal_count or ship_count < 5) and not me.shipyard.position in avoid_moves:        
        command_queue.append(me.shipyard.spawn())

    logging.info("Ship types: {}".format(ship_status))
    # Send your moves back to the game environment, ending this turn.
    game.end_turn(command_queue)
