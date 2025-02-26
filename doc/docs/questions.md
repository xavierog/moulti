## Interact with end users through questions

Sometimes, it is necessary to prompt the user for a confirmation, a value or an option.
Since Moulti occupies the entirety of the terminal and its standard input, it is no longer possible to use shell features such as `read`.
This is why Moulti provides **questions**. Questions are special widgets the sole purpose of which is to display interactive components such as buttons and/or input fields.

## InputQuestions

Creating a question is not very different from creating a step:
```shell
moulti inputquestion add my_first_question \
    --title='My first question with Moulti' \
    --text='What is your name?' \
    --bottom-text='We want information... information... information!' \
    --placeholder='Please enter your name in this input field'
```
![inputquestion](assets/images/inputquestion.svg)
Getting the answer is straightforward:
```console
$ moulti inputquestion get-answer my_first_question --wait
Alice
$
```

Once the answer is submitted, the question's interactive components are disabled. This prevents users from submitting multiple answers for a single question.

!!! info "Refer to `moulti inputquestion add --help` to get more control on what users can type in the input field."

## ButtonQuestions

Moulti also supports buttons through `buttonquestion` widgets.
```shell
moulti buttonquestion add my_second_question \
    --title='My second question with Moulti' \
    --text='What is your name?' \
    --bottom-text='What a mess: https://en.wikipedia.org/wiki/Alice_and_Bob' \
    --button alice success Alice \
    --button bob primary Bob \
    --button craig default Craig \
    --button mallory error Mallory \
    --button oscar warning Oscar
```

![buttonquestion](assets/images/buttonquestion.svg)

Each button is defined by exactly three items:

- value: the value returned by `get-answer`
- style: default, primary, error, warning, or success
- label: what the button should display

!!! warning "Limitation: buttons cannot be changed through `moulti buttonquestion update`."

Again, getting the answer is straightforward:
```console
$ moulti buttonquestion get-answer my_second_question --wait
craig
$
```

## Questions

`question` combines the abilities of `buttonquestion` and `inputquestion`:
```shell
moulti question add my_third_question \
    --title='My third question with Moulti' \
    --text='What is your name?' \
    --bottom-text='I live on the second floor' \
    --placeholder='Enter your name in this input field, or click a button' \
    --button 'My name is Alice' default Alice \
    --button 'My name is Bob' default Bob \
    --button 'My name is {input}' success 'Neither, use input'
```

![question](assets/images/question.svg)

`{input}` is an optional placeholder that gets replaced with the input field value.

That makes it possible to return a value that reflects both the input field value and the button that was clicked:
   ```console
   $ moulti question get-answer my_third_question --wait
   My name is Luka
   $
   ```

## Feature recap
The table below offers a summary of "question" widgets and their features:

| Widget \ Feature | Input field | Buttons    |
|------------------|-------------|------------|
| inputquestion    |     yes     |     no     |
| buttonquestion   |      no     | at least 1 |
| question         |     Yes     | at least 1 |

## What next?

Steps and Questions are somewhat complex beasts. Head to [Dividers](dividers.md) for a much simpler widget.
