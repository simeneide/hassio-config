def calc_min(sensor_values, STATE_UNKNOWN = None):
    """Calculate min value, honoring unknown states."""
    val = STATE_UNKNOWN
    for sval in sensor_values:
        if sval != STATE_UNKNOWN:
            if val == STATE_UNKNOWN or val > sval:
                val = sval
    return val
def calc_max(sensor_values, STATE_UNKNOWN = None):
    """Calculate max value, honoring unknown states."""
    val = STATE_UNKNOWN
    for sval in sensor_values:
        if sval != STATE_UNKNOWN:
            if val == STATE_UNKNOWN or val < sval:
                val = sval
    return val
def distance(origin, destination):
    """
    Calculate the Haversine distance.

    Parameters
    ----------
    origin : tuple of float
        (lat, long)
    destination : tuple of float
        (lat, long)

    Returns
    -------
    distance_in_km : float

    Examples
    --------
    >>> origin = (48.1372, 11.5756)  # Munich
    >>> destination = (52.5186, 13.4083)  # Berlin
    >>> round(distance(origin, destination), 1)
    504.2
    """
    lat1, lon1 = origin
    lat2, lon2 = destination
    radius = 6371  # km

    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) * math.sin(dlat / 2) +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2) * math.sin(dlon / 2))
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    d = radius * c

    return d


###############################
### CALC DISTANCE FROM HOME ###
###############################

dist_from_home = {}
for device_id in ['simen_pixel', 'kamilla_samsung']:
    device_state = hass.states.get('device_tracker.' + device_id)
    device_lat = device_state.attributes.get('latitude')
    device_lon = device_state.attributes.get('longitude')
    device_pos = (device_lat, device_lon)
    home_pos = (61.2255604, 7.0982758)
    d = distance(device_pos, home_pos)
    dist_from_home[device_id] = round(d,3)
    
dist_from_home['minimum'] = calc_min(dist_from_home.values())

# Update distance states:
for device_id, value in dist_from_home.items():
    hass.states.set("sensor.disthome_{}".format(device_id), value)

#######################
### SET THERMOSTATS ###
#######################

rooms = ['livingroom','office']
target_temp_away =  float(hass.states.get("input_number.away_temp").state)

hour = datetime.datetime.now().hour

for room in rooms:
    sensor_name = room + "_temp"
    
    # Get input set target temp for room:
    ### HOUR FILTER ###
    if (hour < 22) & (hour > 6):
        target_temp = float(hass.states.get("input_number." + sensor_name).state)
    else:
        target_temp = target_temp_away
    
    # Calculate distance factor:
    if room == "office":
        dist = dist_from_home.get('simen_pixel',0)
    else:
        dist = dist_from_home.get('minimum',0)
    
    final_target_temp = calc_max([target_temp_away, target_temp - round(math.sqrt(dist),1) ])
    if final_target_temp is not None:
        hass.states.set("climate." + room, target_temp, {"temperature" : final_target_temp})
        logger.info("hour {}: For room {}, distance {} km, set temperture to {}".format(hour, room, dist, final_target_temp))
    