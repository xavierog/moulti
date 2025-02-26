# Text search

Moulti offers text search, i.e. the ability to find and iterate over all occurrences of a given pattern found in the contents displayed by Moulti:

- instance title
- step titles
- step top and bottom texts
- questions and logs

!!! warning "Limitations"

    - This feature ignores input fields, buttons, the progress bar and the console.
    - Additionally, searching occurs over plain text: it is possible to find all occurrences of the word "fox", but it is not possible to find blue occurrences of it.

## Reaching the search bar

To start searching, press either `/` (to search forward) or `?` (to search backward).
The search bar appears at the bottom of the screen (but above the console if it is shown).

![Search bar](assets/images/search-bar.svg)

You can exit the search bar by pressing `Escape`, `Enter` or `Backspace`.

## Search patterns

Type a new pattern to search, or look for a previously entered pattern using the up and down arrows.

The pattern can be case-sensitive or case-insensitive: use `Ctrl+t` to switch between these modes.

The pattern can be a [Python regex](https://docs.python.org/3/library/re.html#regular-expression-syntax) or a plain pattern: use `Ctrl+r` to switch between regex and plain pattern.
If the regex you enter is not syntactically correct, it turns red and submission is blocked until you fix it or switch to plain mode.

![Search bar](assets/images/search-bar-regex-pattern-error.svg)

## Browse results

Hit `Enter`. If the pattern is nowhere to be found, a red notification says so. Otherwise, the next occurrence is found, highlighted and scrolled to (expanding its parent step if necessary).
Hit `n` to go to the next occurrence or `N` to go to the previous one.
