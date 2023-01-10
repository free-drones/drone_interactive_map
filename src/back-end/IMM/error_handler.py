"""
This file contains functions related to checking for errors in retrived requets.
"""

from flask_socketio import emit

def check_client_id(client_id, func_name, logger):
    """Checks so that the client_id is an integer, else try emit a error message."""
    if client_id is None:
        emit_error_response(func_name, "client_id not specified", logger)
        return False

    if not isinstance(client_id, int):
        emit_error_response(func_name, f"The client_id ({client_id}) is not an integer. ", logger)
        return False
    # OK
    return True

def check_coordinates_list(obj, func_name, logger):
    "Checks to see if obj is a list"
    if obj is None:
        emit_error_response(func_name, "Coordinates not specified. ", logger)
        return False

    if not isinstance(obj, list):
        emit_error_response(func_name, f"The coordinates ({obj}) are not a list.", logger)
        return False
    # OK
    return True


def check_coords_in_list(coord_list, func_name, logger):
    """Checks every element if coordinates are in list format [wp0, wp1, ..]"""
    if coord_list is None:
        emit_error_response(func_name, f"Coordinates not specified. ", logger)
        return False

    if not isinstance(coord_list, list):
        emit_error_response(func_name, f"Coordinates not list ({coord_list}). ", logger)
        return False


    if len(coord_list) < 3:
        emit_error_response(func_name, f"The list ({coord_list}) is not valid, \
                            it has too few coordinates", logger)
        return False

    for item in coord_list:
        if isinstance(item, dict):
            if len(item.keys()) == 2:
                if ("lat" and "long") in item.keys():
                    if (isinstance(item["lat"], float) or isinstance(item["lat"], int)) and (isinstance(item["long"], float) or isinstance(item["long"], int)):
                        pass

                    else:
                        lat_value = item["lat"]
                        long_value = item["long"]
                        emit_error_response(func_name, f"The coordinate must be float ({lat_value}, {long_value})", logger)
                        return False
                else:
                    emit_error_response(func_name, f"Wrong keys in dict ({coord_list[item]})", logger)
                    return False

            else:
                emit_error_response(func_name, f"The coordinate ({item} has to many keys ({dict.keys()})", logger)
                return False

        else:
            emit_error_response(func_name, f"The coordinate ({item} in the list is not a dictionary", logger)
            return False
    # OK
    return True


def check_coord_dict(coord_dict, func_name, logger):
    """Checks the coordinates when in dictionary format (up_left, up_right, etc)"""

    if coord_dict is None:
        emit_error_response(func_name, f"Coordinates not specified. ", logger)
        return False

    if not isinstance(coord_dict, dict):
        emit_error_response(func_name, f"Coordinates not list ({coord_dict}). ", logger)
        return False

    if len(coord_dict) != 5:
        emit_error_response(func_name, f"Missing cordinates in dictionary ({coord_dict})", logger)
        return False

    if ("up_left" and "up_right" and "down_left" and "down_right" and "center") not in coord_dict.keys():
        emit_error_response(func_name, f"Wrong keys in dict ({coord_dict.keys()})", logger)
        return False

    for item in coord_dict:
        if isinstance(coord_dict[item], dict):
            if len(coord_dict[item].keys()) == 2:
                if ("lat" and "long") in coord_dict[item].keys():
                    if (isinstance(coord_dict[item]["lat"], float) or isinstance(coord_dict[item]["lat"], int)) and (isinstance(coord_dict[item]["long"], float) or isinstance(coord_dict[item]["long"], int)):
                        pass
                    else:
                        lat_value = coord_dict[item]["lat"]
                        long_value = coord_dict[item]["long"]
                        emit_error_response(func_name, f"The coordinate must be float ({lat_value}, {long_value})", logger)
                        return False
                else:
                    emit_error_response(func_name, f"Wrong keys in dict ({coord_dict[item]})", logger)
                    return False
            else:
                emit_error_response(func_name, f"The coordinate ({item} has to many keys ({dict.keys()})", logger)
                return False

        else:
            emit_error_response(func_name, f"The key ({item}) in ({coord_dict}) is not a dictionary", logger)
            return False
    # OK
    return True

def check_type(type, func_name, logger):
    if type is None:
        emit_error_response(func_name, "Type not specified.", logger)
        return False

    if not ("RGB" == type or "IR" == type or "Map" == type):
        emit_error_response(func_name, f"Specified image type ({type}) is not RGB, IR or Map", logger)
        return False

    # OK
    return True

def check_mode(mode, func_name, logger):
    if mode is None:
        emit_error_response(func_name, f"Mode not specified. ", logger)
        return False

    if not ("AUTO" == mode or "MAN" == mode):
        emit_error_response(func_name, f"Specified mode ({mode}) is not AUTO or MAN", logger)
        return False

    # OK
    return True

def emit_error_response(function_name, error_message, logger):
    logger.error(f"{function_name} {error_message}")
    error_response = {}
    error_response["fcn"] = "error"
    error_response["fcn_name"] = function_name
    error_response["error_report"] = error_message
    emit("response", error_response)
