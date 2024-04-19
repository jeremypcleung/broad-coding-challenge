import requests
from requests.auth import HTTPBasicAuth
import sys
from collections import deque

# globals for calling API
baseURL = "https://api-v3.mbta.com"
apiKey = "e0d68c3a96b94dc58eafd648d94fabee"
auth = HTTPBasicAuth("apiKey", apiKey)

def raiseHTTPException(code, reason):
    raise Exception("Status " + str(code) + ": " + reason)

def getRouteData():
    routeResponse = requests.get(baseURL + "/routes", params={"filter[type]":"0,1"}, auth=auth)
    if routeResponse.ok:
        routeData = routeResponse.json()["data"]
        if "q1" in sys.argv:
            routeNames = list(map(lambda x: x["attributes"]["long_name"], routeData))
            print("Routes: ", ", ".join(routeNames))
        return routeData
    else: # error from HTTP response
        raiseHTTPException(routeResponse.status_code, routeResponse.reason)

def getStopsFromRoutes(routeData):
    stopsToRoutes = dict()
    stopsWithMultipleRoutes = set()
    minStops = float("inf")
    maxStops = float("-inf")
    minStopsRouteName = []
    maxStopsRouteName = []

    for route in routeData:
        routeName = route["attributes"]["long_name"]
        stopsResponse = requests.get(baseURL + "/stops", params={"filter[route]":route["id"]}, auth=auth)
        if stopsResponse.ok:
            stopsData = stopsResponse.json()["data"]
            numOfStops = len(stopsData)
            # Track max/min number of stops
            if numOfStops > maxStops:
                maxStops = numOfStops
                maxStopsRouteName = [routeName]
            elif numOfStops == maxStops:
                maxStopsRouteName.append(routeName)
            if numOfStops < minStops:
                minStops = numOfStops
                minStopsRouteName = [routeName]
            elif numOfStops == minStops:
                minStopsRouteName.append(routeName)
            # Construct our stop - route(s) mapping
            for stop in stopsData:
                stopName = stop["attributes"]["name"]
                if stopName in stopsToRoutes: # this stop is touching multiple routes
                    stopsWithMultipleRoutes.add(stopName)
                    stopsToRoutes[stopName].append(routeName)
                else:
                    stopsToRoutes[stopName] = [routeName]
        else:
            raiseHTTPException(stopsResponse.status_code, stopsResponse.reason)

    if "q2" in sys.argv:
        print("Most stops: ", ", ".join(maxStopsRouteName), " with ", maxStops, " stops.")
        print("Least stops: ", ", ".join(minStopsRouteName), " with ", minStops, " stops.")
        print("Stops with multiple routes:")
        for stop in sorted(list(stopsWithMultipleRoutes)):
            print("    -", stop, ": ", stopsToRoutes[stop])
    
    return stopsToRoutes, stopsWithMultipleRoutes

def getRouteToConnections(stopsToRoutes, stopsWithMultipleRoutes):
    routeToConnections = dict() # essential a node - neighbor mapping
    alreadySeenGrouping = set()
    for stop in stopsWithMultipleRoutes:
        if str(stopsToRoutes[stop]) in alreadySeenGrouping: # slight optimization - green line connections repeat a lot
            continue
        for route in stopsToRoutes[stop]:
            for otherRoute in stopsToRoutes[stop]:
                if route in routeToConnections and otherRoute != route:
                    routeToConnections[route].add(otherRoute)
                elif otherRoute != route:
                    routeToConnections[route] = set([otherRoute])
        alreadySeenGrouping.add(str(stopsToRoutes[stop]))
    return routeToConnections

def getPathBetweenTwoRoutes(routeA, routeB, routeToConnections, visited):
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

                
def getPathing(routeToConnections, stopsToRoutes, source, dest):
    shortestDist = float("inf")
    shortestPath = []
    for routeA in stopsToRoutes[source]:
        for routeB in stopsToRoutes[dest]:
            path = getPathBetweenTwoRoutes(routeA, routeB, routeToConnections, set())
            if len(path) < shortestDist:
                shortestPath = path
                shortestDist = len(path)
    return shortestPath

def main():
    routeData = getRouteData()
    stopsToRoutes = dict()
    stopsWithMultipleRoutes = []
    if "q2" in sys.argv or "q3" in sys.argv:
        stopsToRoutes, stopsWithMultipleRoutes = getStopsFromRoutes(routeData)
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
            print(getPathing(routeToConnections, stopsToRoutes, source, dest))
            
if __name__ == "__main__":
    main()