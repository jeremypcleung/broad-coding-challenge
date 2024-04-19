import requests
from requests.auth import HTTPBasicAuth
import sys
from collections import deque

# Design/documentation
# https://docs.google.com/document/d/1WAllS6r6vXY0IxxWnZK1iQ5dJqtoLjlR8EO-_-eGpJ8/edit?usp=sharing

# globals for calling API
baseURL = "https://api-v3.mbta.com"
apiKey = "e0d68c3a96b94dc58eafd648d94fabee"
headers = {'Accept': 'application/json', 'x-api-key': apiKey}

# raiseHTTPException takes a HTTP status code and reason and raises a generic
# exception printing the code/reason
def raiseHTTPException(code, reason):
    raise Exception("Status " + str(code) + ": " + reason)

# getRouteInfo calls the MBTA /routes endpoint and returns the full set of
# route data received, as well as the route names in the response as a list
def getRouteInfo():
    routeResponse = requests.get(baseURL + "/routes", headers=headers,
        params={"filter[type]":"0,1"})
    if routeResponse.ok:
        routeData = routeResponse.json()["data"]
        routeNames = list(map(lambda x: x["attributes"]["long_name"], routeData))
        return {"routeData": routeData, "routeNames": routeNames}
    else: # error from HTTP response
        raiseHTTPException(routeResponse.status_code, routeResponse.reason)

# getStopsFromRoutes takes the route data received from getRouteInfo and calls
# the MBTA /stops endpoint and gets the stops contained in each respective route
# and constructs the stop to routes map, the stops with multiple routes list,
# as well as returning which routes have the most/least stops
def getStopsFromRoutes(routeData):
    stopsToRoutes, stopsWithMultipleRoutes = dict(), set()
    minStops, minStopsRouteNames = float("inf"), []
    maxStops, maxStopsRouteNames = float("-inf"), []

    for route in routeData:
        routeName = route["attributes"]["long_name"]
        stopsResponse = requests.get(baseURL + "/stops", headers=headers,
            params={"filter[route]":route["id"]})
        if stopsResponse.ok:
            stopsData = stopsResponse.json()["data"]
            numOfStops = len(stopsData)
            # Track max/min number of stops
            if numOfStops > maxStops:
                maxStops = numOfStops
                maxStopsRouteNames = [routeName]
            elif numOfStops == maxStops:
                maxStopsRouteNames.append(routeName)
            if numOfStops < minStops:
                minStops = numOfStops
                minStopsRouteNames = [routeName]
            elif numOfStops == minStops:
                minStopsRouteNames.append(routeName)
            # Construct our stop to route(s) mapping
            for stop in stopsData:
                stopName = stop["attributes"]["name"]
                # this stop is touching multiple routes
                if stopName in stopsToRoutes:
                    stopsWithMultipleRoutes.add(stopName)
                    stopsToRoutes[stopName].append(routeName)
                else:
                    stopsToRoutes[stopName] = [routeName]
        else:
            raiseHTTPException(stopsResponse.status_code, stopsResponse.reason)
    
    return {
        "stopsToRoutes": stopsToRoutes,
        "stopsWithMultipleRoutes": stopsWithMultipleRoutes,
        "maxStopsRouteNames": maxStopsRouteNames,
        "maxStops": maxStops,
        "minStopsRouteNames": minStopsRouteNames,
        "minStops": minStops
    }

# getRouteToConnections takes in the stops to routes map and the stops with
# multiple routes list, and returns a route to connections mapping
def getRouteToConnections(stopsToRoutes, stopsWithMultipleRoutes):
    routeToConnections = dict()
    alreadySeenGrouping = set()
    for stop in stopsWithMultipleRoutes:
        # slight optimization - green line connections repeat a lot
        # convert to string since list type is not hashable
        if str(stopsToRoutes[stop]) in alreadySeenGrouping:
            continue
        for route in stopsToRoutes[stop]:
            for otherRoute in stopsToRoutes[stop]:
                if route in routeToConnections and otherRoute != route:
                    routeToConnections[route].add(otherRoute)
                elif otherRoute != route:
                    routeToConnections[route] = set([otherRoute])
        alreadySeenGrouping.add(str(stopsToRoutes[stop]))
    return routeToConnections

# getPathBetweenTwoRoutes takes in two route names, the route to connections
# mapping, and runs DFS to obtain the path with least route transfers
def getPathBetweenTwoRoutes(routeA, routeB, routeToConnections, visited=set()):
    if routeA == routeB:
        return [routeB]
    elif routeA in visited:
        return []
    visited.add(routeA)
    shortestLength = float("inf")
    shortestPath = []
    neighbors = sorted(list(routeToConnections[routeA])) # sort so the route returned is deterministic
    for neighbor in neighbors:
        pathToB = getPathBetweenTwoRoutes(neighbor, routeB, routeToConnections, visited)
        if len(pathToB) > 0 and len(pathToB) < shortestLength:
            shortestPath = pathToB
            shortestLength = len(pathToB)
    visited.remove(routeA)
    if shortestPath == []:
        return []
    return [routeA] + shortestPath

# getPathBetweenTwoStations takes in the routes to connections and stops to
# routes maps, a source and destination station, and calls getPathBetweenTwoRoutes
# on the routes these stations are connected to, to find the route list between
# two stations that requires the least transfers
def getPathBetweenTwoStations(source, dest, routeToConnections, stopsToRoutes):
    shortestDist = float("inf")
    shortestPath = []
    for routeA in stopsToRoutes[source]:
        for routeB in stopsToRoutes[dest]:
            path = getPathBetweenTwoRoutes(routeA, routeB, routeToConnections)
            if len(path) < shortestDist:
                shortestPath = path
                shortestDist = len(path)
    return shortestPath

# main handles calling individual functions based on the q1/q2/q3 input passed
# in and handles printing the output from these functions as well
def main():
    routeInfo = getRouteInfo()
    routeData = routeInfo["routeData"]
    if "q1" in sys.argv:
        print("Routes: ", ", ".join(routeInfo["routeNames"]))
    # We separate this out since it requires a new API call
    if "q2" in sys.argv or "q3" in sys.argv:
        stopsRoutesInfo = getStopsFromRoutes(routeData)
        stopsWithMultipleRoutes = stopsRoutesInfo["stopsWithMultipleRoutes"]
        stopsToRoutes = stopsRoutesInfo["stopsToRoutes"]
        if "q2" in sys.argv:
            print("Most stops: ", ", ".join(stopsRoutesInfo["maxStopsRouteNames"]), " with ", stopsRoutesInfo["maxStops"], " stops.")
            print("Least stops: ", ", ".join(stopsRoutesInfo["minStopsRouteNames"]), " with ", stopsRoutesInfo["minStops"], " stops.")
            print("Stops with multiple routes:")
            for stop in sorted(list(stopsWithMultipleRoutes)):
                print("    -", stop, ": ", stopsToRoutes[stop])
        if "q3" in sys.argv:
            routeToConnections = getRouteToConnections(stopsToRoutes, stopsWithMultipleRoutes)
            print("Please enter source,dest station names separated by a comma, i.e. 'Park Street,State', or 'exit' to quit:")
            while True:
                userInput = input(">>> ")
                if userInput == "exit":
                    break
                stations = userInput.split(",")
                if len(stations) != 2:
                    print("Invalid input provided, try again")
                    continue
                source, dest = stations[0].strip(), stations[1].strip()
                if source not in stopsToRoutes or dest not in stopsToRoutes:
                    print("Station not found, try again")
                    continue
                print(getPathBetweenTwoStations(source, dest, routeToConnections, stopsToRoutes))
            
if __name__ == "__main__":
    main()