# Live F1 Data Home Assistant Integration

## Overview

The **Live F1 Data Integration** allows you to access real-time Formula 1 data directly within Home Assistant. By leveraging the official F1 websocket connection used on their website, this integration provides live session standings and driver information, including track status, session details, lap information, and more. This integration is designed to enhance your Home Assistant setup with live updates during F1 races.

## Disclaimer / Support
This is my first Home Assistant integration, and I’m excited to share it with the community! I welcome any feedback, bug reports, suggestions, or ideas for improvement. If you find any issues or have feature requests, feel free to open an issue. Additionally, pull requests for bug fixes, improvements, or enhancements are highly appreciated!

Thank you for your support and contributions!


## Installation

Follow these steps to install and configure the integration in your Home Assistant setup:

1. **Download and Copy the Files**

   * Copy the `custom_components/livef1data` folder from this repository into your Home Assistant `config/custom_components/` directory.

2. **Add the Integration to Your Switches**

   * Add the following configuration to your `configuration.yaml` file to include the Live F1 switch:

   ```yaml
   switch:
     - platform: livef1
   ```

3. **Restart Home Assistant**

   * Restart Home Assistant to apply the changes.


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
      entity_id: switch.live_f1_data
```

* **After the Session**: Turn off the switch once the race has concluded to avoid excessive use of the websocket connection. Example:
```yml
triggers:
  - trigger: state
    entity_id:
      - switch.live_f1_data
    to: Finalised
    attribute: session
conditions: []
actions:
  - action: switch.turn_off
    metadata: {}
    data: {}
    target:
      entity_id: switch.live_f1_data
```

## Attributes

When the integration is connected and active, the switch will provide the following attributes:

* `track`: Current track status during the race.

  * Possible values: `AllClear`, `Yellow`, `Red`, `VSCDeployed`, `VSCEnding`, etc. (More statuses may be available but not all are fully reverse-engineered yet.)

* `session`: Current session status.

  * Possible values: `Inactive`, `Started`, `Finished`, `Finalised`, `Ends`, etc. (More statuses may be available but not all are fully reverse-engineered yet.)

* `lap`: The current lap number.

* `total_laps`: The total number of laps in the current session.

* `drivers`: An object containing information for all drivers in the session. Each driver entry includes:

  * `RacingNumber`: Driver's racing number.
  * `FirstName`: Driver's first name.
  * `LastName`: Driver's last name.
  * `FullName`: Driver's full name.
  * `BroadcastName`: Driver's broadcast name (used during the race).
  * `Tla`: Timing screen abbreviation (e.g., `VER` for Max Verstappen).
  * `TeamName`: The team the driver is racing for.
  * `TeamColour`: The team’s color (used for identification).
  * `HeadshotUrl`: URL to the driver's headshot image.

* `p1` to `p20`: An object containing driver information sorted by race position. Each entry includes:

  * `racing_number`: Driver’s racing number.
  * `Tla`: Timing screen abbreviation.
  * `FirstName`: Driver’s first name.
  * `LastName`: Driver’s last name.
  * `TeamName`: The driver’s team.
  * `TeamColour`: The team’s color.
  * `HeadshotUrl`: URL to the driver’s headshot image.


## Notes

* **Websocket Connection Limitations**: The websocket connection used by this integration is not designed for constant or infinite use. Please remember to switch off the integration after the session ends to avoid potential issues with excessive usage.

* **Race Data Availability**: The integration fetches live data from the F1 server, so the data available is directly dependent on the current race status and available updates from the official F1 sources.