## Project: TITLE
***Gazebo Design Document***

### Overview

This amazing proposal brings about a great new feature to CloudSim: multiple users per simulator machine. The idea is simple: instead of having each "machine" belong to a single "user", we allow each "machine" to be "accessed" by a list of users. Furthermore, in a future design, each user will have a "role" for this access (admin, officer, user, contestant).

The benefits are: 
- When you want to share your simulation, you "add your friends" to the "machine".
- When you create a contest, you add entire teams to each competition "machine" (as simple contestant users)
- When you don't care, nothing is different (you "own" your "machines")
- The Master admin user (TBD) is always in the list, and therefore "sees" all machines, all the time. 

### Requirements

This project must fulfill this set of requirements:

Define roles, and add role checking for the following tasks: 
- CRUD (Create, Read, Update, Delete) users
- CRUD simulations (launch, terminate, set worlds)

For example:

1. Up to any amount of users per simulator is allowed... but no duplicates!
1. Only one role per user should be supported.

### Architecture

1. Simulation Shema should have an array of users, instead of a user field.
1. There must always be at least one user per machine that has the priviledge to terminate it.

### Interfaces

UI: Add a user! set the role! change the role! remove a user!
    Also: you can't do that because you don't have privileges!

Add UX design drawings.

### Performance Considerations

Not really. Users are slow animals.

### Tests
List and describe the tests that will be created. For example:

1. Test: create sim, and 2 users: Bob and Alice
    1. case: Create sim as Bob, check that he is in the list
    1. case: Add a second user, Alixe . Log in as Alice, verify access.
    1. case: Remove Bob, verify Alice can't be removed.

