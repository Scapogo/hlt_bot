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
from hlt.positionals import Direction

""" <<<Game Begin>>> """

# This game object contains the initial game state.
game = hlt.Game()
# At this point "game" variable is populated with initial map data.
# This is a good place to do computationally expensive start-up pre-processing.
# As soon as you call "ready" function below, the 2 second per turn timer will start.
ship_status = {}

game.ready("ScapoBotv5")

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
    if ship_position[0] < dest_position[0]:
        new_position = ship.position.directional_offset(Direction.East)
        if not game_map[new_position].is_occupied and not new_position in avoid_moves:
            x_value = game_map[new_position].halite_amount
            directions.append(Direction.East)
        else:
            x_value = 9999
            directions.append(Direction.Still)
    elif ship_position[0] > dest_position[0]:
        new_position = ship.position.directional_offset(Direction.West)
        if not game_map[new_position].is_occupied and not new_position in avoid_moves:
            x_value = game_map[new_position].halite_amount
            directions.append(Direction.West)
        else:
            x_value = 9999
            directions.append(Direction.Still)
    else:
        x_value = 9999
        directions.append(Direction.Still)

    if ship_position[1] < dest_position[1]:
        new_position = ship.position.directional_offset(Direction.South)
        if not game_map[new_position].is_occupied and not new_position in avoid_moves:
            y_value = game_map[new_position].halite_amount
            directions.append(Direction.South)
        else:
            y_value = 9999
            directions.append(Direction.Still)
    elif ship_position[1] > dest_position[1]:
        new_position = ship.position.directional_offset(Direction.North)
        if not game_map[new_position].is_occupied and not new_position in avoid_moves:
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


while True:
    # This loop handles each turn of the game. The game object changes every turn, and you refresh that state by
    #   running update_frame().
    game.update_frame()
    # You extract player metadata and the updated map metadata here for convenience.
    me = game.me
    game_map = game.game_map

    # A command queue holds all the commands you will run this turn. You build this list up and submit it at the
    #   end of the turn.
    command_queue = []
    avoid_moves = []
    ship_count = len(me.get_ships())

    logging.info("Turn start: {}".format(ship_status))

    for ship in me.get_ships():
        # For each of your ships, move randomly if the ship is on a low halite location or the ship is full.
        #   Else, collect halite.
        harvesting_ships = sum(map(("harvesting").__eq__, ship_status.values()))

        if ship.id not in ship_status:
            ship_status[ship.id] = "harvesting"
        if ship_count // 2 < harvesting_ships and ship_status[ship.id] == "exploring":
            ship_status[ship.id] = "harvesting"

        if ship_status[ship.id] == "returning":
            if ship.position == me.shipyard.position:
                ship_status[ship.id] = "exploring"
            else:
                move = cheap_navigation(ship, game_map, avoid_moves, me.shipyard.position)
                # move = game_map.naive_navigate(ship, me.shipyard.position)
                avoid_moves.append(ship.position.directional_offset(move))
                command_queue.append(ship.move(move))
                continue
        elif ship_status[ship.id] == "harvesting" and not ship.is_full: #ship.halite_amount < constants.MAX_HALITE / 1.5:
            if ship.position != me.shipyard.position:
                surroundings = ship.position.get_surrounding_cardinals()
                logging.info("Surroundings: {}".format(surroundings))
                actual_cell = ship.position
                best_cell =  ship.position
                logging.info("Actual: {} Best: {}".format(actual_cell, best_cell))
                if game_map[best_cell].halite_amount < 50:
                    for cell in surroundings:
                        if game_map[best_cell].halite_amount < game_map[cell].halite_amount/3 and not game_map[cell].is_occupied:
                            logging.info("Actual: {} New: {}".format(game_map[best_cell].halite_amount, game_map[cell].halite_amount/3))
                            best_cell = cell

                logging.info("Selected: {}".format(best_cell))
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
            ship_status[ship.id] = "returning"
            move = game_map.naive_navigate(ship, me.shipyard.position)
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

    # TODO: vic zelvicek
    if game.turn_number <= 200 and me.halite_amount >= constants.SHIP_COST and not game_map[me.shipyard].is_occupied and (ship_count < ship_optimal_count or ship_count < 5) and not me.shipyard.position in avoid_moves:
        command_queue.append(me.shipyard.spawn())

    logging.info("Ship types: {}".format(ship_status))
    # Send your moves back to the game environment, ending this turn.
    game.end_turn(command_queue)
