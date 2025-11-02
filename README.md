# Live F1 Home Assistant Integration

## Overview

The **Live F1 Integration** allows you to access real-time Formula 1 data directly within Home Assistant. By leveraging the official F1 websocket connection used on their website, this integration provides live session standings and driver information, including track status, session details, lap information, and more. This integration is designed to enhance your Home Assistant setup with live updates during F1 races.

## Disclaimer / Support
This is my first Home Assistant integration, and I’m excited to share it with the community! I welcome any feedback, bug reports, suggestions, or ideas for improvement. If you find any issues or have feature requests, feel free to open an issue. Additionally, pull requests for bug fixes, improvements, or enhancements are highly appreciated!

Thank you for your support and contributions!


## Installation

Follow these steps to install and configure the integration in your Home Assistant setup:

1. **Download and Copy the Files**
   * Copy the `custom_components/livef1` folder from this repository into your Home Assistant `config/custom_components/` directory

2. **Restart Home Assistant**
   * Restart Home Assistant to load the integration

### Configuration

After installation, configure the integration through the Home Assistant UI:

1. **Add Integration**
   * Go to **Settings** > **Devices & Services**
   * Click **"+ ADD INTEGRATION"**
   * Search for **"Live F1"** and select it

2. **Configure Settings**
   * **Update Delay**: Set the delay of data updates to match your broadcast delay (default: 0 seconds)
   * Click **"Submit"** to complete the setup

3. **Integration Ready**
   * The integration will create two entities:
     - **Live F1 Switch**: Turn the data service on/off
     - **Live F1 Update Delay**: Control the update frequency


## Usage

The integration connects to F1's websocket to retrieve live session data. However, since this connection is not intended for continuous use, we recommend the following usage guidelines:

* **Before the Session**: Turn on the switch shortly (a couple of minutes) before the session starts. Example:
```yml
triggers:
  - event: start
    offset: "-0:10:0"
    entity_id: calendar.f1 # https://files-f1.motorsportcalendars.com/de/f1-calendar_p1_p2_p3_qualifying_sprint_gp.ics
    trigger: calendar
actions:
  - action: switch.turn_on
    metadata: {}
    data: {}
    target:
      entity_id: switch.live_f1
```

* **After the Session**: Turn off the switch once the race has concluded to avoid excessive use of the websocket connection. Example:
```yml
triggers:
  - trigger: state
    entity_id:
      - switch.live_f1
    to: Finalised
    attribute: session
conditions: []
actions:
  - action: switch.turn_off
    metadata: {}
    data: {}
    target:
      entity_id: switch.live_f1
```

## Attributes

When the integration is connected and active, the switch will provide the following attributes:

* `track`: Current track status during the race.

  * Possible values: `AllClear`, `Yellow`, `Red`, `VSCDeployed`, `VSCEnding`, etc. (More statuses may be available but not all are fully reverse-engineered yet.)

* `session`: Current session status.

  * Possible values: `Inactive`, `Started`, `Finished`, `Finalised`, `Ends`, etc. (More statuses may be available but not all are fully reverse-engineered yet.)

* `lap`: The current lap number.

* `total_laps`: The total number of laps in the current session.

* `p1` to `p20`: For each position there is a `DRIVEROBJECT` with the information of the driver in this position.

* `d<RacingNumber>` (e.g. `d1` for Max Verstappen): For each driver there is a `DRIVEROBJECT` with the information of the driver with racing number `<RacingNumber>`


> * The `DRIVEROBJECT` consists of the follwing information:
>   * `RacingNumber`: String - Driver's racing number.
>   * `FirstName`: String - Driver's first name.
>   * `LastName`: String - Driver's last name.
>   * `FullName`: String - Driver's full name.
>   * `BroadcastName`: String - Driver's broadcast name (used during the race).
>   * `Tla`: String - Timing screen abbreviation (e.g., `VER` for Max Verstappen).
>   * `TeamName`: String - The team the driver is racing for.
>   * `TeamColour`: String - The team’s color (RGB Array; `'[71, 129, 215]'` for RedBull).
>   * `HeadshotUrl`: String - URL to the driver's headshot image.
>   * `Position`: Integer - Position in Session
>   * `InPit`: Boolean - Is in Pit
>   * `PitStops`: Integer - Number of Pit Stops


## Notes

* **Websocket Connection Limitations**: The websocket connection used by this integration is not designed for constant or infinite use. Please remember to switch off the integration after the session ends to avoid potential issues with excessive usage.

* **Race Data Availability**: The integration fetches live data from the F1 server, so the data available is directly dependent on the current race status and available updates from the official F1 sources.
