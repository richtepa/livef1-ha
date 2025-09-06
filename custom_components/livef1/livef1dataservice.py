import asyncio
import websockets
import json
import ssl

LOGGING_ENABLED = False

class LiveF1DataService:
    def __init__(self, url, driver_count, callback, logger):
        self.url = url
        self.driver_count = driver_count
        self.callback = callback
        self.logger = logger
        self._stop = False
        self.dataset = {
            "track": None,
            "session": None,
            "lap": None,
            "total_laps": None,
            "drivers": {}
        }
        for i in range(driver_count):
            self.dataset[f"p{i+1}"] = {
                "RacingNumber": None,
                "Tla": None,
                "FirstName": None,
                "LastName": None,
                "TeamName": None,
                "TeamColour": None,
                "HeadshotUrl": None
            }
        self.ssl_context = ssl.create_default_context()
    
    async def run_forever(self):
        self._stop = False
        while not self._stop:
            try:
                await self.connect()
            except Exception as e:
                self.logger.error(f"Error in run_forever: {e}", exc_info=True)
                await asyncio.sleep(10)

    async def connect(self):
        async with websockets.connect(self.url, ssl=self.ssl_context) as ws:
            self.websocket = ws
            await self.send_initial_messages(ws)
            self.logger.info("WebSocket connected.")
            await self.handler(ws)
            
    async def disconnect(self):
        self._stop = True
        self.logger.info("Disconnecting WebSocket.")
        if self.websocket:
            await self.websocket.close()
            self.logger.info("WebSocket closed.")

    async def send_initial_messages(self, ws):
        await ws.send('{"protocol":"json","version":1}')
        await ws.send('{"type":6}')
        await ws.send('{"arguments":[["SessionInfo", "ExtrapolatedClock", "DriverList", "DriverTracker", "LapCount", "TrackStatus", "SessionStatus", "TimingData"]],"invocationId":"1","target":"subscribe","type":1}')

    async def handler(self, websocket):
        try:
            while not self._stop:
                raw = await websocket.recv()
                messages = raw.split("")
                for msg in messages:
                    if msg:
                        await self.handle_message(websocket, msg)
        except websockets.exceptions.ConnectionClosed as e:
            self.logger.warning(f"WebSocket closed: {e}")
            raise

    async def handle_message(self, websocket, msg):
        if msg == "":
            return
        try:
            j = json.loads(msg)
        except json.JSONDecodeError:
            self.logger.debug(f"Incorrect JSON: {msg}")
            return
        self.logger.debug(f"Received message: {msg}")
        LOG(f"Received message: {msg}")
        
        if j.get("type") == 6: # ping / pong
            self.logger.debug("ping")
            await websocket.send('{"type":6}')
            
        elif j.get("type") == 3: # new data
            await self.updateData(j.get("result"))
            
        elif j.get("type") == 1:
            args = j.get("arguments", [])
            if args[0] == "DriverList":
                # ["DriverList",{"23":{"Line":18},"31":{"Line":17},"55":{"Line":19}},"2025-08-02T11:08:38.385Z"]
                item = {
                    "DriverTracker": {
                        "Lines": [
                            
                        ]
                    }
                }
                for driver in args[1].keys():
                    i = {
                        "Position": int(args[1][driver]["Line"]),
                        "RacingNumber": driver
                    }
                    item["DriverTracker"]["Lines"].append(i)
                await self.updateData(item)
                
            elif args[0] == "DriverTracker":
                item = {
                    "DriverTracker": {
                        "Lines": [
                            
                        ]
                    }
                }
                for key in args[1]["Lines"].keys():
                    if not "RacingNumber" in args[1]["Lines"][key]:
                        continue
                    i = {
                        "Position": int(key)+1
                    }
                    for k, v in args[1]["Lines"][key].items():
                        if k in ["RacingNumber", "LapTime", "LapState", "DiffToAhead", "DiffToLeader", "OverallFastest", "PersonalFastest"]:
                            i[k] = v
                    item["DriverTracker"]["Lines"].append(i)
                await self.updateData(item)
                
            else:
                await self.updateData({
                    args[0]: args[1]
                })
        else:
            self.logger.warn(f"Received unknown message: {j}")
                

    async def updateData(self, data):
        LOG(f"updateData: {data}")
        
        try:
            if data.get("LapCount"):
                self.dataset["lap"] = data["LapCount"]["CurrentLap"]
                self.dataset["total_laps"] = data["LapCount"]["TotalLaps"]
                
            if data.get("ExtrapolatedClock"):
                pass
            
            if data.get("DriverList"):
                self.dataset["drivers"] = data["DriverList"]
                
            if data.get("DriverTracker"):
                #{'DriverTracker': {'Lines': [{'Position': 1, 'RacingNumber': '18', 'LapState': 97}, {'Position': 2, 'RacingNumber': '12', 'LapState': 609}, {'Position': 3, 'RacingNumber': '81'}, {'Position': 4, 'RacingNumber': '14'}, {'Position': 5, 'RacingNumber': '6'}, {'Position': 6, 'RacingNumber': '4'}, {'Position': 7, 'RacingNumber': '16'}, {'Position': 8, 'RacingNumber': '5'}, {'Position': 9, 'RacingNumber': '55'}]}}
                for driver in data["DriverTracker"]["Lines"]:
                    pos = int(driver["Position"])
                    lastDriver = self.dataset[f"p{pos}"]
                    if driver.get("RacingNumber"):
                        if lastDriver["RacingNumber"] != driver.get("RacingNumber"):
                            driverStats = self.dataset["drivers"].get(driver.get("RacingNumber"), {})
                            color = driverStats.get("TeamColour", "FFFFFF")
                            r = int(color[0:2], 16)
                            g = int(color[2:4], 16)
                            b = int(color[4:6], 16)
                            self.dataset[f"p{pos}"] = {
                                "RacingNumber": driver.get("RacingNumber"),
                                "Tla": driverStats.get("Tla", ""),
                                "FirstName": driverStats.get("FirstName", ""),
                                "LastName": driverStats.get("LastName", ""),
                                "TeamName": driverStats.get("TeamName", ""),
                                "TeamColour": f"[{r}, {g}, {b}]",
                                "HeadshotUrl": driverStats.get("HeadshotUrl", ""),
                                "InPit": driverStats.get("InPit", None),
                                "NumberOfPitStops": driverStats.get("NumberOfPitStops", None)
                            }
            if data.get("TrackStatus"):
                self.dataset["track"] = data["TrackStatus"]["Message"] # "AllClear" "Yellow" "VSCDeployed" "VSCEnding"
                
            if data.get("SessionStatus"):
                self.dataset["session"] = data["SessionStatus"]["Status"] # "Inactive" "Started" "Finished" "Finalised" "Ends"
            
            if data.get("TimingData"):
                # ["TimingData",{"Lines":{"23":{"InPit":true,"Status":80,"NumberOfPitStops":3}}}
                for key, value in data["TimingData"]["Lines"].items():
                    if "InPit" in value:
                        self.dataset["drivers"][key]["InPit"] = value["InPit"]
                        i = find_driverIndex_by_number(self.dataset, key)
                        self.dataset[f"p{i}"]["InPit"] = value["InPit"]
                    if "NumberOfPitStops" in value:
                        self.dataset["drivers"][key]["NumberOfPitStops"] = value["NumberOfPitStops"]
                        i = find_driverIndex_by_number(self.dataset, key)
                        self.dataset[f"p{i}"]["NumberOfPitStops"] = value["NumberOfPitStops"]
                
            LOG(f"Updated dataset: {self.dataset}")
            await self.callback(self.dataset)
            
        except Exception as e:
            self.logger.error(f"Error in LiveF1Data.updateData {e}", exc_info=True)
            
def find_driverIndex_by_number(dataset, number):
    for i in range(1, len(dataset)):
        driver = dataset.get(f"p{i}")
        if driver and driver.get("RacingNumber") == number:
            return i
    return None
            
            
def LOG(message):
    if not LOGGING_ENABLED:
        return
    with open("./f1.log", 'a') as file:
        file.write(f"{message}\n")