Tests that check what we can do with pickles when implementing unpicklers with
different levels of restrictions (we are trying to either call something or
change an attribute). Overall, single-acquisition upicklers that restrict
both module and name seem to be the most secure (only Type III bypasses from
the Pain Pickle paper would work).

-- Maybe add some tests for just reading properties of items instead of just
calling stuff/setting properties.
