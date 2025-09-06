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
        changed = False
        
        try:
            if data.get("LapCount"):
                if "CurrentLap" in data["LapCount"] and data["LapCount"]["CurrentLap"] != self.dataset["lap"]:
                    self.dataset["lap"] = data["LapCount"]["CurrentLap"]
                    changed = True
                if "TotalLaps" in data["LapCount"] and data["LapCount"]["TotalLaps"] != self.dataset["total_laps"]:
                    self.dataset["total_laps"] = data["LapCount"]["TotalLaps"]
                    changed = True
                
            if data.get("ExtrapolatedClock"):
                pass
            
            if data.get("DriverList"):
                for key, value in data["DriverList"].items():
                    if not key.isdigit():
                        continue
                    
                    self.dataset["drivers"][key] = value
                    color = self.dataset["drivers"][key].get("TeamColour", "FFFFFF")
                    r = int(color[0:2], 16)
                    g = int(color[2:4], 16)
                    b = int(color[4:6], 16)
                    self.dataset["drivers"][key]["TeamColour"] = f"[{r}, {g}, {b}]"
                            
                    if not self.dataset["drivers"][key].get("Position"):
                        self.dataset["drivers"][key]["Position"] = None
                    if not self.dataset["drivers"][key].get("InPit"):
                        self.dataset["drivers"][key]["InPit"] = None
                    if not self.dataset["drivers"][key].get("PitStops"):
                        self.dataset["drivers"][key]["PitStops"] = None
                changed = True
                    
                
            if data.get("DriverTracker"):
                #{'DriverTracker': {'Lines': [{'Position': 1, 'RacingNumber': '18', 'LapState': 97}, {'Position': 2, 'RacingNumber': '12', 'LapState': 609}, {'Position': 3, 'RacingNumber': '81'}, {'Position': 4, 'RacingNumber': '14'}, {'Position': 5, 'RacingNumber': '6'}, {'Position': 6, 'RacingNumber': '4'}, {'Position': 7, 'RacingNumber': '16'}, {'Position': 8, 'RacingNumber': '5'}, {'Position': 9, 'RacingNumber': '55'}]}}
                for driver in data["DriverTracker"]["Lines"]:
                    pos = int(driver["Position"])
                    num = driver.get("RacingNumber")
                    if not num in self.dataset["drivers"]:
                        continue
                    lastPos = self.dataset["drivers"][num]["Position"]
                    if lastPos == pos:
                        continue
                    self.dataset["drivers"][num]["Position"] = pos
                    changed = True
            
            if data.get("TrackStatus"):
                if "Message" in data["TrackStatus"] and data["TrackStatus"]["Message"] != self.dataset["track"]:
                    self.dataset["track"] = data["TrackStatus"]["Message"] # "AllClear" "Yellow" "VSCDeployed" "VSCEnding"
                    changed = True
                
            if data.get("SessionStatus"):
                if "Status" in data["SessionStatus"] and data["SessionStatus"]["Status"] != self.dataset["session"]:
                    self.dataset["session"] = data["SessionStatus"]["Status"] # "Inactive" "Started" "Finished" "Finalised" "Ends"
                    changed = True

            if data.get("TimingData"):
                # ["TimingData",{"Lines":{"23":{"InPit":true,"Status":80,"NumberOfPitStops":3}}}
                for key, value in data["TimingData"]["Lines"].items():
                    if not key in self.dataset["drivers"]:
                        continue
                    if "InPit" in value and value["InPit"] != self.dataset["drivers"][key]["InPit"]:
                        self.dataset["drivers"][key]["InPit"] = value["InPit"]
                        changed = True
                    if "NumberOfPitStops" in value and value["NumberOfPitStops"] != self.dataset["drivers"][key]["PitStops"]:
                        self.dataset["drivers"][key]["PitStops"] = value["NumberOfPitStops"]
                        changed = True
            
            if not changed:
                return    
            LOG(f"Updated dataset: {self.dataset}")
            await self.callback(self.data)
            
        except Exception as e:
            LOG(f"Error in LiveF1Data.updateData {e}")
            self.logger.error(f"Error in LiveF1Data.updateData {e}", exc_info=True)
    
    @property
    def data(self):
        data = {}
        data.update(self.dataset)
        for key, value in data["drivers"].items():
            data[f"d{key}"] = value
            if value.get("Position"):
                data[f"p{value['Position']}"] = value
        return data


def LOG(message):
    if not LOGGING_ENABLED:
        return
    with open("./f1.log", 'a') as file:
        file.write(f"{message}\n")