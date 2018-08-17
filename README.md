# Clash Royale Tournament Finder

This project queries [RoyaleAPI](https://docs.royaleapi.com) and finds tournaments.

When a new tournament is found, it will send a `POST` request to URLs that have subscribed to the appropriate `filter`.

## Subscribing

Create a Github Issue with the JSON Structure. If you wish to keep your data private, please DM me on discord at `4JR#4895` with the JSON structure.

### JSON Structure
```json
{
    "url": "https://url.com",
    "filters": ["all", "50", "100", "200", "1000", "open:all", "open:50", "open:100", "open:200", "open:1000"],
    "app": "A brief description of your application",
    "authorization": "Value sent in the `Authorization` header. This is mostly used if you want your data to be private"
}
```

## POST Requests

The POST Request will contain JSON data of a typical tournament:
```json
{
    "tag": "Tag",
    "name": "Name",
    "open": false,
    "maxPlayers": 50,
    "currentPlayers": 11,
    "status": "inProgress",
    "createTime": 1534075854,
    "prepTime": 7200,
    "duration": 3600,
    "description": "Description",
    "updatedAt": 1534083832,
    "filters": ["tags", "applied"]
},
```
