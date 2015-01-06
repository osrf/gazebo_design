## Project: Pull request prioritization
***Gazebo Design Document***

### Overview

This project will enhance the [Gazebo dashboard](http://gazebosim.org/dashboard) by:

1. Providing a custom pull-request submission interface.

1. Displaying an ordered queue of pull-requests. The order in the queue indicates the order in which pull requests will be merged. 

### Custom pull-request submission interface 

This interface will act both as a checklist for pull request submissions,
and will facilitate entry of meta-data that helps to determine pull
request priority. A button will be added to the dashboard that accesses this interface.

The interface will consist of the following:

1. Dropdown: Select respository.
1. Text field: Title.
1. Checkbox: There are no compiler warnings.
1. Checkbox: Code check passes ('sh tools/code_check.sh').
1. Checkbox: A test has been written/modified.
1. Checkbox: All tests pass ('make test'). 
1. Checkbox: The changelog and/or migration guide has been modified.
1. Checkbox: If targeted to a release branch, the code is ABI/API compatible.
1. Checkbox: If modifing functionality, related tutorials have been updated.
1. Dropdown with values 0-5: Select priority level, where 0 is low priority.
1. Comma separate list: Enter issue numbers that are resolved, separated by commas.
1. Button: Continue.
1. Button: Cancel.

The continue button will take the user to the bitbucket pull-request creation site. The title will be automatically filled, and the description will contain some preformatted text concerning the issues resolved. At this point the user can complete the pull-request process by adding more description, and selecting the target branch.

The cancel button will clear the selections.

### Pull-request queue

This queue will exist in a separate tab on the dashboard. The queue will list all open pull requests across all projects. The top-most pull request in the queue must be merged before any other pull request in the queue. The order of the queue is determined using the following algorithm:

rank = (issue_votes + issue_priority) + (age * age_scale) + priority + (size_scale/size) + override

where:

1. issue_votes: Total number of votes for each issue resolved.
1. issue_priority: For each issue, a value from 1-5 that maps to trivial-critical.
1. age: Number of days since pull-request creation.
1. age_scale: Scaling factor applied to age, such as 0.1.
1. priority: The number entered in the pull-request submission interface.
1. size: Number of lines of code changed.
1. size_scale: Scaling factor applied to size, such as 50.
1. override: A number that an admin can enter to force a pull-request up or down. This would be used to capture corner-cases, and would be used sparingly. Initially, each member of OSRF would be an admin.

It is expected that the above algorithm is not perfect, and will likely need
to be tweaked.
