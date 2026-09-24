# SeniorGoserver

The backend for SeniorGo, a rideshare app that connects seniors with volunteers from their own community group, such as a church. This server powers the SeniorGo UI: it manages groups, users, and rides, and stores everything in AWS.

> **Texas Invention Convention, State Finalist (2026)**

This repository is the backend only. To use SeniorGo end to end, also clone the UI repo: SeniorGo

## Overview

SeniorGo is built around small, trusted communities. Every user belongs to a group with a local admin, and rides only happen inside a group. This server enforces those rules and keeps track of every ride from request to completion.

## What the Server Does

- **Group management.** Each group, such as a church, has a local admin and a unique group code. Seniors and volunteers join the app using that code.
- **User accounts.** Separate sign up flows for seniors and volunteers, each tied to a group.
- **Group-restricted matching.** Volunteers can only give rides to seniors in their own group.
- **Ride lifecycle.** Every ride moves through 4 stages:
  1. Ride request accepted
  2. Volunteer started
  3. Ride started
  4. Ride ended
- **Scheduled rides.** Seniors can book rides ahead of time, not just on demand.
- **Ride history.** Past rides are stored and can be retrieved for each user.

## Tech Stack

| Layer | Technology |
|-------|------------|
| Cloud | AWS |
| Database | Amazon DynamoDB |
| Runtime / language | [e.g. Node.js / Python] |
| Server framework | [e.g. Express / Flask / AWS Lambda + API Gateway] |
| Auth | [e.g. Amazon Cognito / JWT] |

## Architecture

```
SeniorGo UI  ->  seniorGoserver (API)  ->  Amazon DynamoDB
```


## Data Model

The main entities are groups, users, and rides.
| Table | Purpose | Key fields |
|-------|---------|-----------|
| [Groups] | One record per community group | [groupId, groupCode, adminId] |
| [Users] | Seniors, volunteers, and local admins | [userId, role, groupId] |
| [Rides] | Every ride request and its status | [rideId, seniorId, volunteerId, groupId, status, scheduledTime] |

Ride `status` follows the 4 stage lifecycle above: request accepted, volunteer started, ride started, ride ended.

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `[/groups]` | Create a group (local admin) |
| POST | `[/signup/senior]` | Sign up a senior with a group code |
| POST | `[/signup/volunteer]` | Sign up a volunteer with a group code |
| POST | `[/rides]` | Request or schedule a ride |
| PATCH | `[/rides/:id/status]` | Move a ride to its next stage |
| GET | `[/rides/:id]` | Get a ride and its current stage |
| GET | `[/users/:id/rides]` | Get a user's past rides |




## Recognition

- Texas Invention Convention, State Finalist, 2026

## Author

Built by Lakshitha Vengadeswaran.

## License

[MIT / Apache 2.0 / All rights reserved]
