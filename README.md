# PastePortal

A fast and simple utility to paste text from iPhone

## How to Use

### iPhone Shortcut

- Create a new shortcut in the Shortcuts app
- Back out of the shortcut editing and look the shortcut details
- Enable the "Show is Share Sheet" option
- Add a "Get Text from Input" action and set the variable to "Shortcut Input"
- Add a "Get Content of URL" action
- Set the URL variable to `http://pasteportal-a7f2.local:43127/clipboard`
- Choose the `POST` method, `JSON` request body and a text field. Set the input of the text field to the output of the "Get Text from Input" action
