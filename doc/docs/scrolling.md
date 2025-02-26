# Scrolling

## Manually scrolling through steps

You can scroll through steps:

- by grabbing the main scrollbar handle using the mouse pointer;
- using the mouse wheel (or its laptop equivalent) -- tip: ensure the cursor is not over a scrollable step log part;
- by hitting the `Up`, `PgUp`, `Home` or `End` key -- tip: ensure the focus is not held by a step log part.

If moulti is already scrolling through steps automatically (see next section `Programmatically scrolling through steps`),
but you want to read a part of the output while the job is still running, hit `l` or click "L Lock scroll" in the footer
to prevent programmatic scrolling from interfering with your actions.

The main scrollbar handle turns green to indicate that the lock is enabled and automatic scrolling is disengaged.

## Programmatically scrolling through steps

### moulti scroll

Use `moulti scroll step_name` to make Moulti scroll to a given step.
If this step cannot be displayed entirely, `moulti scroll` will display its upper part.

It is possible to define which line of the step should absolutely be displayed by specifying an offset as second argument.
Important: here, a line does not mean a line of the text output shown by the chosen step but rather one of the lines that make up the entire chosen step on screen.

```console
# Ensure the first line of the step is displayed:
moulti scroll step_name 0
# Ensure the second line of the step is displayed:
moulti scroll step_name 1
# Ensure the third line of the step is displayed:
moulti scroll step_name 2

# Ensure the last line of the step is displayed:
moulti scroll step_name -1
# Ensure the second to last line of the step is displayed:
moulti scroll step_name -2
```

It often makes sense to call `moulti scroll` after adding an interactive step (buttonquestion, inputquestion).

### Scroll on activity

Sometimes, it is desirable to make a step visible when a new line of output shows up.
This can be achieved using `--scroll-on-activity`:

```console
# By default, steps do not scroll on activity:
moulti step add foo --bottom-text=' ' --title='Your shiny title here'
moulti pass foo <<< 'do not scroll'

# Enable scroll on activity:
moulti step update foo --scroll-on-activity=true
# Try it:
moulti pass foo --append <<< 'scroll!'

# A typical use case is to ensure the last line of output is displayed:
moulti step update foo --max-height=0 --scroll-on-activity=-1
# Try it:
yes 'scroll to the last line!' | nl -ba | head -500 | moulti pass foo --append

# Disable scroll on activity:
moulti step update foo --scroll-on-activity=false
moulti pass foo --append <<< 'do not scroll!'
```

## Manually scrolling inside steps

By default, Moulti enables auto-scrolling, i.e. it strives to display the latest lines it received and thus keeps scrolling down as long as lines keep coming.
Auto-scrolling stops as soon as you scroll up:

- using the mouse wheel (or its laptop equivalent);
- by grabbing the scrollbar handle using the mouse pointer;
- by hitting the `Up`, `PgUp` or `Home` key.

If enabled (cf next section), auto-scrolling resumes when you hit the `End` key.

## Programmatically scrolling inside steps

Moulti currently offers no support for programmatic scrolling inside steps.
It is, however, possible to enable or disable auto-scrolling:
```
# Disable auto-scroll:
moulti step add foo --no-auto-scroll
yes 'Do not scroll.' | nl -ba | head -500 | moulti pass foo
# Enable auto-scroll again:
moulti step update foo --auto-scroll
moulti pass --append foo <<< 'Now, scroll!'
```
