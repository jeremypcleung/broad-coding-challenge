import unittest
from mbtaFunctions import *

class TestMBTAFunctions(unittest.TestCase):
    # We want to perform the API calls here only once for efficiency
    def setUp(self):
        self.routeInfo = getRouteInfo()
        routeData = self.routeInfo["routeData"]
        self.stopsRoutesInfo = getStopsFromRoutes(routeData)
    
    # Tests Q1
    def test_getRouteInfo(self):
        self.assertEqual(str(self.routeInfo["routeNames"]),
            "['Red Line', 'Mattapan Trolley', 'Orange Line', 'Green Line B', 'Green Line C', 'Green Line D', 'Green Line E', 'Blue Line']")
    
    # Tests Q2
    def test_getStopsFromRoutes(self):
        self.assertEqual(self.stopsRoutesInfo["minStops"], 8)
        self.assertEqual(self.stopsRoutesInfo["minStopsRouteNames"], ['Mattapan Trolley'])
        self.assertEqual(self.stopsRoutesInfo["maxStops"], 25)
        self.assertEqual(self.stopsRoutesInfo["maxStopsRouteNames"], ['Green Line D', 'Green Line E'])
        self.assertEqual(sorted(self.stopsRoutesInfo["stopsWithMultipleRoutes"]),
            ['Arlington','Ashmont','Boylston','Copley','Downtown Crossing','Government Center','Haymarket',
                'Hynes Convention Center','Kenmore','Lechmere','North Station','Park Street','Science Park/West End','State'])
        # Spot check a couple stops to routes mappings
        stopsToRoutes = self.stopsRoutesInfo["stopsToRoutes"]
        self.assertEqual(stopsToRoutes["Arlington"], ['Green Line B', 'Green Line C', 'Green Line D', 'Green Line E'])
        self.assertEqual(stopsToRoutes["Government Center"], ['Green Line B', 'Green Line C', 'Green Line D', 'Green Line E', 'Blue Line'])
        self.assertEqual(stopsToRoutes["State"], ['Orange Line', 'Blue Line'])
        self.assertEqual(stopsToRoutes["Harvard"], ['Red Line'])

    def test_getRouteToConnections(self):
        routeToConnections = getRouteToConnections(self.stopsRoutesInfo["stopsToRoutes"], self.stopsRoutesInfo["stopsWithMultipleRoutes"])
        # Spot check a couple routes of varying number of connections
        self.assertEqual(sorted(list(routeToConnections['Red Line'])), ['Green Line B','Green Line C','Green Line D','Green Line E','Mattapan Trolley','Orange Line'])
        self.assertEqual(sorted(list(routeToConnections['Blue Line'])), ['Green Line B','Green Line C','Green Line D','Green Line E','Orange Line'])
        self.assertEqual(sorted(list(routeToConnections['Mattapan Trolley'])), ['Red Line'])

    def test_getPathBetweenTwoRoutes(self):
        routeToConnections = getRouteToConnections(self.stopsRoutesInfo["stopsToRoutes"], self.stopsRoutesInfo["stopsWithMultipleRoutes"])
        # Spot check a couple varying number of route transfers
        self.assertEqual(getPathBetweenTwoRoutes("Red Line", "Blue Line", routeToConnections),['Red Line','Green Line B','Blue Line'])
        self.assertEqual(getPathBetweenTwoRoutes("Red Line", "Red Line", routeToConnections),['Red Line'])
        self.assertEqual(getPathBetweenTwoRoutes("Red Line", "Mattapan Trolley", routeToConnections),['Red Line','Mattapan Trolley'])
        self.assertEqual(getPathBetweenTwoRoutes("Mattapan Trolley", "Blue Line", routeToConnections),['Mattapan Trolley','Red Line','Green Line B','Blue Line'])

    # tests Q3
    def test_getPathBetweenTwoStations(self):
        routeToConnections = getRouteToConnections(self.stopsRoutesInfo["stopsToRoutes"], self.stopsRoutesInfo["stopsWithMultipleRoutes"])
        stopsToRoutes = self.stopsRoutesInfo["stopsToRoutes"]
        # Most possible route transfers
        self.assertEqual(getPathBetweenTwoStations("Mattapan", "Aquarium", routeToConnections, stopsToRoutes),['Mattapan Trolley','Red Line','Green Line B','Blue Line'])
        # Least possible route transfers
        self.assertEqual(getPathBetweenTwoStations("Harvard", "Alewife", routeToConnections, stopsToRoutes),['Red Line'])
        # Least possible route transfers where both stations intersect with multiple green lines
        self.assertEqual(getPathBetweenTwoStations("Park Street", "Arlington", routeToConnections, stopsToRoutes),['Green Line B'])
        # Check a couple other possible route combinations
        self.assertEqual(getPathBetweenTwoStations("Fenway", "East Somerville", routeToConnections, stopsToRoutes),['Green Line D','Green Line E'])
        self.assertEqual(getPathBetweenTwoStations("Cleveland Circle", "Forest Hills", routeToConnections, stopsToRoutes),['Green Line C','Blue Line','Orange Line'])
        self.assertEqual(getPathBetweenTwoStations("Wonderland", "Medford/Tufts", routeToConnections, stopsToRoutes),['Blue Line','Green Line E'])
        self.assertEqual(getPathBetweenTwoStations("Wonderland", "Oak Grove", routeToConnections, stopsToRoutes),['Blue Line', 'Orange Line'])


if __name__ == '__main__':
    unittest.main()