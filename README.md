# मेरा हक़ — content

This repository holds the **content** for the मेरा हक़ app, and nothing else.

- No application code.
- No signing keys.
- No secrets of any kind.

## Why this repository exists

The app fetches its content from here so that the law can be corrected or extended
**without anyone reinstalling the app**. Update a file here, and every phone picks up
the change on its next launch.

It is public on purpose. A phone cannot sign in to a private repository, so the app
could not read it otherwise. And there is nothing private here: this is the text of
public laws, plus our own plain-language explanations of them.

## Layout

```
kb/fundamental_rights.json   Constitution of India, Part III, and free legal aid
kb/general.json              basic documents (Aadhaar, UDID, voter ID), Constitution structure
kb/other_rights.json         RTI, education, disability, MGNREGA, food security
kb/consumer_rights.json      Consumer Protection Act, 2019
kb/helplines.json            government helpline numbers
```

## Entry format

```json
{
  "id": "unique-id",
  "category": "grouping shown on the Topics screen",
  "title": "short title",
  "keywords": ["words", "a", "user", "might", "say"],
  "answer": "plain-language answer, in Hindi, that will be spoken aloud",
  "source": "the law and section this answer comes from",
  "sourceUrl": "the government website to check it at"
}
```

## A warning that matters

The plain-language answers here are written by us. They are grounded in the official
texts, but **every entry must be reviewed by a qualified lawyer before the app is
published**. Legal information that is wrong is worse than no information at all.
