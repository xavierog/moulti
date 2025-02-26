# Direction and position


## Default behavior

By default, Moulti displays steps at the top of the screen and adds new steps below existing steps.

!!! example "Default behavior: top down"
    ![--step-position=top--step-direction=down](assets/images/top-down.svg)

## Setting direction and position

This behavior can be changed through `moulti set`:

- `moulti set --step-position=bottom` displays steps at the bottom of the screen
- `moulti set --step-position=top` displays steps at the top of the screen
- `moulti set --step-direction=up` displays steps from last to first (new steps are added above existing steps)
- `moulti set --step-direction=down` displays steps from first to last (new steps are added below existing steps)

## Non-default combinations

!!! example "Top up"
    ![--step-position=top--step-direction=up](assets/images/top-up.svg)

!!! example "Bottom down"
    ![--step-position=bottom --step-direction=down](assets/images/bottom-down.svg)

!!! example "Bottom up"
    ![--step-position=bottom --step-direction=up](assets/images/bottom-up.svg)
