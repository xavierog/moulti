# Classes

## Default classes

Out of the box, Moulti provides five "classes" that can be applied to widgets (steps, questions, dividers) to change their appearance (typically their background color):

- `standard` (blue)
- `success` (green)
- `warning` (orange)
- `error` (red)
- `inactive` (gray)

![All default classes](assets/images/all-classes.svg)

Here, "class" is a synonym for "style" or "color" and actually refers to the notion of [CSS](https://en.wikipedia.org/wiki/CSS) class.
Moulti is based on the Textual framework, which borrows various principles from the world of web design, starting with their own variant of CSS: [Textual CSS](https://textual.textualize.io/guide/CSS/) (TCSS).

## Setting classes

As demonstrated in [First steps](first-steps.md), classes are assigned through `--classes`:

`moulti <widget> add/update <id> --classes=classname`

Although it does not make sense with default classes, widgets can be assigned multiple classes:

`moulti <widget> add/update <id> --classes='class1 class2 class3'`

!!! warning "Limitation"
    The syntax above sets all classes at once: it is not possible to add/remove/toggle a single class.

    Otherly said, this:
    ```shell
    moulti step add example --classes='foo'
    moulti step update example --classes='bar'
    ```
    is equivalent to:
    ```shell
    moulti step add example --classes='bar'
    ```
    but NOT equivalent to:
    ```shell
    moulti step add example --classes='foo bar'
    ```

This concept starts to make sense when we introduce custom classes.

## Custom classes

Moulti allows end users to define and override whatever they see fit through a TCSS file of theirs, the absolute path of which should be passed through the `MOULTI_CUSTOM_CSS` environment variable.

The snippets below demonstrate how to leverage this mechanism to define custom classes and change the colors of the Moulti header.

!!! abstract "/absolute/path/to/moulti-custom.tcss:"
    ```css
    /* Change the colors of the Moulti header: */
    #header {
        background: red;
        color: yellow;
    }

    /* Define a step class named "customstate" rendered with red text on a yellow background: */
    Step.customstate {
        & CollapsibleTitle {
            color: red;
        }
        color: red;
        background: yellow;
        & MoultiLog { scrollbar-corner-color: yellow; }
    }
    
    /* Customise steps shown by moulti-askpass: */
    .askpass {
        color: gray;
        background: black;
        padding: 2;
        border: panel blue;
    }
    ```

```shell
export MOULTI_CUSTOM_CSS=/absolute/path/to/moulti-custom.tcss
moulti init
moulti step add test_step --classes=customstate --bottom-text=' '
moulti-askpass
```

![custom TCSS](assets/images/custom-tcss.svg)

!!! danger "Beware!"
    If the `MOULTI_CUSTOM_CSS` environment variable is set and the file it indicates exists,
    it must point to a **syntactically valid** TCSS file or the Moulti instance will crash.

!!! info "Refer to [examples/moulti-scoreboard.bash](https://github.com/xavierog/moulti/blob/master/examples/moulti-scoreboard.bash) for an advanced use of TCSS."
