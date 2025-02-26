# Dividers

## What are dividers?

Dividers are simplistic widgets that exist solely for cosmetic purposes, like displaying static text or acting as visual separator between two groups of widgets (hence the name).
Unlike other widgets, they are not collapsible.

## How to use dividers?

```bash
moulti divider add my_first_divider --title \
    $'This text is simply displayed.\nMulti-line is possible. So is [i]rich formatting[/]'
moulti divider update my_first_divider --classes=warning
moulti divider delete my_first_divider
```

![Divider](assets/images/divider.svg)

## What next?

Craving for more widgets? Head to [Progress bar](progressbar.md).
